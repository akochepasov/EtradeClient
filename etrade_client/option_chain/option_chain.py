import json
import csv
import io
import xml.etree.ElementTree as ET
from logger import get_logger

import pandas as pd

logger = get_logger()


class OptionChain:
    """
    Option chain API client.

    :param session: authenticated session
    :param base_url: base URL for API calls
    :param symbol: The market symbol for the instrument (e.g., GOOG)
    :param option_category: The option category. Default: STANDARD. Options: STANDARD, ALL, MINI
    :param chain_type: The type of option chain. Default: CALLPUT. Options: CALL, PUT, CALLPUT
    """

    CSV_HEADERS = [
        "optionType", "symbol", "displaySymbol", "osiKey",
        "strikePrice", "bid", "ask", "bidSize", "askSize",
        "lastPrice", "netChange", "volume", "openInterest", "inTheMoney",
        "delta", "gamma", "theta", "vega", "rho", "iv",
        "optionCategory", "optionRootSymbol", "adjustedFlag",
    ]

    def __init__(self, session, base_url, symbol=None, option_category="STANDARD", chain_type="CALLPUT"):
        """
        Initialize OptionChain object with session and base URL

        :param session: authenticated session
        :param base_url: base URL for API calls
        :param symbol: The market symbol for the instrument (e.g., GOOG)
        :param option_category: The option category. Default: STANDARD. Options: STANDARD, ALL, MINI
        :param chain_type: The type of option chain. Default: CALLPUT. Options: CALL, PUT, CALLPUT
        """
        self.session = session
        self.base_url = base_url
        self.symbol = symbol.upper() if symbol else None
        self.option_category = option_category
        self.chain_type = chain_type

    def view(self, expiry_year=None, expiry_month=None, expiry_day=None,
             strike_price_near=None, no_of_strikes=None, include_weekly=False,
             skip_adjusted=True, option_category=None, chain_type=None,
             price_type="ATNM", as_dataframe=False):
        """
        Retrieves option chain data for a given symbol and expiration date

        :param expiry_year: Indicates the expiry year corresponding to which the optionchain needs to be fetched
        :param expiry_month: Indicates the expiry month corresponding to which the optionchain needs to be fetched
        :param expiry_day: Indicates the expiry day corresponding to which the optionchain needs to be fetched
        :param strike_price_near: The optionchains fetched will have strike price nearer to this value
        :param no_of_strikes: Indicates number of strikes for which the optionchain needs to be fetched
        :param include_weekly: The include weekly options request. Default: false
        :param skip_adjusted: The skip adjusted request. Default: true
        :param option_category: Optional override for constructor option_category
        :param chain_type: Optional override for constructor chain_type
        :param price_type: The price type. Default: ATNM. Options: ATNM, ALL
        :param as_dataframe: If true, return a pandas DataFrame instead of CSV text
        :return: CSV formatted string or pandas DataFrame with option chain data
        """

        effective_symbol = self.symbol
        effective_option_category = option_category or self.option_category
        effective_chain_type = chain_type or self.chain_type

        if not effective_symbol:
            print("Error: symbol is required")
            logger.error("Symbol parameter is required")
            return None

        # URL for the API endpoint per E*TRADE docs  
        url = f"{self.base_url}/v1/market/optionchains"

        params = {
            "symbol": effective_symbol.upper(),
        }

        # Add optional parameters if provided
        if expiry_year:
            params["expiryYear"] = expiry_year
        if expiry_month:
            params["expiryMonth"] = expiry_month
        if expiry_day:
            params["expiryDay"] = expiry_day
        if strike_price_near:
            params["strikePriceNear"] = strike_price_near
        if no_of_strikes:
            params["noOfStrikes"] = no_of_strikes

        # Add default parameters
        params["includeWeekly"] = "true" if include_weekly else "false"
        params["skipAdjusted"] = "true" if skip_adjusted else "false"
        params["optionCategory"] = effective_option_category
        params["chainType"] = effective_chain_type
        params["priceType"] = price_type

        # Make API call
        response = None
        try:
            response = self.session.get(url, params=params, headers={"Accept": "application/json"})
            logger.debug("Request Header: %s", response.request.headers)
            logger.debug("Request URL: %s", response.request.url)
        except Exception as exc:
            logger.error("Request failed: %s", exc)
            print(f"Error: Request failed - {exc}")
            return None

        data = None
        xml_error = None
        if response is not None:
            try:
                data = response.json()
            except ValueError:
                # E*TRADE returns XML error bodies on 4xx responses
                xml_error = self._parse_xml_error(response.text)
                logger.debug("Non-JSON response body: %s", response.text)

        # Handle and parse response
        if response is not None and response.status_code == 200 and data is not None:
            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))

            if as_dataframe:
                return self._generate_dataframe(data)

            # Generate CSV from response
            return self._generate_csv(data)
        else:
            # Log actual response for debugging
            logger.debug("Response status: %s", response.status_code if response is not None else "none")
            logger.debug("Response body: %s", response.text if response is not None else "none")
            # Show the most useful error message available
            if xml_error:
                print(f"Error: {xml_error}")
                logger.error("API Error: %s", xml_error)
            elif data is not None and "OptionChainResponse" in data and "Messages" in data["OptionChainResponse"]:
                messages = data["OptionChainResponse"]["Messages"]
                for error_message in (messages.get("Message") or []):
                    print(f"Error: {error_message.get('description', 'Option Chain API service error')}")
                    logger.error("API Error: %s", error_message.get('description', 'Option Chain API service error'))
            else:
                status = response.status_code if response is not None else "none"
                print(f"Error: Option Chain API service error (HTTP {status})")
            return None

    def _parse_xml_error(self, text):
        """
        Parse an E*TRADE XML error response and return a human-readable string.

        E*TRADE returns errors in the form:
            <Error><code>10031</code><message>There are no options for the given month.</message></Error>

        :param text: raw response text
        :return: formatted error string, or None if parsing fails
        """
        try:
            root = ET.fromstring(text.strip())
            code = root.findtext("code", default="")
            message = root.findtext("message", default="")
            if message:
                return f"{message} (code {code})" if code else message
        except ET.ParseError:
            pass
        return None

    def _generate_csv(self, data):
        """
        Generate CSV formatted string from option chain data

        :param data: JSON response data from the API
        :return: CSV formatted string
        """
        rows = self._extract_rows(data)
        if not rows:
            return None

        csv_buffer = io.StringIO()
        csv_writer = csv.DictWriter(csv_buffer, fieldnames=self.CSV_HEADERS, extrasaction="ignore")
        csv_writer.writeheader()
        csv_writer.writerows(rows)

        csv_output = csv_buffer.getvalue()
        csv_buffer.close()

        return csv_output if csv_output.strip() else None

    def _generate_dataframe(self, data):
        """
        Generate a pandas DataFrame from option chain data.

        :param data: JSON response data from the API
        :return: pandas DataFrame or None
        """
        rows = self._extract_rows(data)
        if not rows:
            return None

        return pd.DataFrame(rows, columns=self.CSV_HEADERS)

    def _extract_rows(self, data):
        """
        Flatten option pair response into a list of row dictionaries.

        :param data: JSON response data from the API
        :return: list of row dictionaries
        """
        if data is None or "OptionChainResponse" not in data:
            return []

        option_chain_resp = data["OptionChainResponse"]
        if "OptionPair" not in option_chain_resp or not option_chain_resp["OptionPair"]:
            logger.warning("No option chain data found in response")
            return []

        rows = []
        for option_pair in option_chain_resp["OptionPair"]:
            if option_pair is None:
                continue
            for option_key in ["Call", "Put"]:
                option = option_pair.get(option_key)
                if option is None:
                    continue
                rows.append(self._extract_row(option))

        return rows

    def _extract_row(self, option):
        """
        Extract a CSV row dict from an option object.
        Greeks are nested under the 'OptionGreeks' key.

        :param option: OptionDetails object from API response
        :return: Dictionary with option data
        """
        greeks = option.get("OptionGreeks") or {}
        row = {
            "optionType":       option.get("optionType", ""),
            "symbol":           option.get("symbol", ""),
            "displaySymbol":    option.get("displaySymbol", ""),
            "osiKey":           option.get("osiKey", ""),
            "strikePrice":      option.get("strikePrice", ""),
            "bid":              option.get("bid", ""),
            "ask":              option.get("ask", ""),
            "bidSize":          option.get("bidSize", ""),
            "askSize":          option.get("askSize", ""),
            "lastPrice":        option.get("lastPrice", ""),
            "netChange":        option.get("netChange", ""),
            "volume":           option.get("volume", ""),
            "openInterest":     option.get("openInterest", ""),
            "inTheMoney":       option.get("inTheMoney", ""),
            # Greeks (nested)
            "delta":            greeks.get("delta", ""),
            "gamma":            greeks.get("gamma", ""),
            "theta":            greeks.get("theta", ""),
            "vega":             greeks.get("vega", ""),
            "rho":              greeks.get("rho", ""),
            "iv":               greeks.get("iv", ""),
            # Metadata
            "optionCategory":   option.get("optionCategory", ""),
            "optionRootSymbol": option.get("optionRootSymbol", ""),
            "adjustedFlag":     option.get("adjustedFlag", ""),
        }
        return row

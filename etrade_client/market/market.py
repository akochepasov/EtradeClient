import json
from urllib.parse import quote as urllib_quote
from etrade_client.logger import get_logger

logger = get_logger()


class Market:
    QUOTE_COLUMNS = [
        "dateTime",
        "symbol",
        "securityType",
        "lastPrice",
        "changeClose",
        "changeClosePercentage",
        "open",
        "previousClose",
        "bid",
        "bidSize",
        "ask",
        "askSize",
        "low",
        "high",
        "volume",
    ]

    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url

    def _get_pandas(self):
        try:
            return __import__("pandas")
        except ImportError:
            logger.error("pandas is required for Market.quote DataFrame output")
            return None

    def _empty_dataframe(self):
        pd = self._get_pandas()
        if pd is None:
            return None
        return pd.DataFrame(columns=self.QUOTE_COLUMNS)

    def quote(self, symbols):
        """
        Calls quotes API to provide quote details for equities, options, and mutual funds

        :param self: Passes authenticated session in parameter
        :param symbols: Stock symbol or comma-separated list of symbols
        :return: pandas DataFrame with quote rows
        """
        pd = self._get_pandas()
        if pd is None:
            return None

        if not symbols or not str(symbols).strip():
            logger.error("Symbol parameter is required")
            return self._empty_dataframe()

        symbols = str(symbols).strip().upper()

        # URL for the API endpoint per E*TRADE docs
        symbol_path = urllib_quote(symbols, safe=",")
        url = f"{self.base_url}/v1/market/quote/{symbol_path}"
        params = {
            "detailFlag": "ALL",
            "requireEarningsDate": "true",
            "format": "json",
        }

        # Make API call for GET request
        try:
            response = self.session.get(url, params=params, headers={"Accept": "application/json"})
            logger.debug("Request Header: %s", response.request.headers)
            logger.debug("Request URL: %s", response.request.url)
        except Exception as exc:
            logger.error("Quote request failed: %s", exc)
            return self._empty_dataframe()

        data = None
        if response is not None:
            try:
                data = response.json()
            except ValueError:
                logger.debug("Non-JSON response body: %s", response.text)

        if response is not None and response.status_code == 200 and data is not None:
            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
            if "QuoteResponse" in data and "QuoteData" in data["QuoteResponse"]:
                rows = self._extract_quote_rows(data["QuoteResponse"]["QuoteData"])
                return pd.DataFrame(rows, columns=self.QUOTE_COLUMNS)

            if "QuoteResponse" in data and "Messages" in data["QuoteResponse"]:
                for error_message in (data["QuoteResponse"]["Messages"].get("Message") or []):
                    logger.error("Quote API Error: %s", error_message.get("description", "Quote API service error"))
            else:
                logger.error("Quote API service error")
            return self._empty_dataframe()
        else:
            if data is not None and "QuoteResponse" in data and "Messages" in data["QuoteResponse"] \
                    and "Message" in data["QuoteResponse"]["Messages"]:
                for error_message in data["QuoteResponse"]["Messages"]["Message"]:
                    logger.error("Quote API Error: %s", error_message.get("description", "Quote API service error"))
            else:
                logger.debug("Response status/body: %s / %s", response.status_code if response else "none", response.text if response else "none")
                logger.error("Quote API service error")

        return self._empty_dataframe()

    def _extract_quote_rows(self, quote_items):
        """
        Flatten QuoteData records into a consistent DataFrame row format.
        """
        rows = []
        for quote_item in (quote_items or []):
            if quote_item is None:
                continue

            product = quote_item.get("Product") or {}
            all_data = quote_item.get("All") or {}

            rows.append(
                {
                    "dateTime": quote_item.get("dateTime"),
                    "symbol": product.get("symbol"),
                    "securityType": product.get("securityType"),
                    "lastPrice": all_data.get("lastTrade"),
                    "changeClose": all_data.get("changeClose"),
                    "changeClosePercentage": all_data.get("changeClosePercentage"),
                    "open": all_data.get("open"),
                    "previousClose": all_data.get("previousClose"),
                    "bid": all_data.get("bid"),
                    "bidSize": all_data.get("bidSize"),
                    "ask": all_data.get("ask"),
                    "askSize": all_data.get("askSize"),
                    "low": all_data.get("low"),
                    "high": all_data.get("high"),
                    "volume": all_data.get("totalVolume"),
                }
            )

        return rows

    def quotes(self):
        """
        Interactively prompts for a stock symbol and calls quote().

        :return: pandas DataFrame from quote()
        """
        symbols = input("\nPlease enter Stock Symbol: ").strip().upper()
        if not symbols:
            print("Error: symbol is required")
            return self._empty_dataframe()

        return self.quote(symbols)

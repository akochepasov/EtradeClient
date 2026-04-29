import json
from urllib.parse import quote
from etrade_client.logger import get_logger

logger = get_logger()


class Market:
    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url

    def quotes(self):
        """
        Calls quotes API to provide quote details for equities, options, and mutual funds

        :param self: Passes authenticated session in parameter
        """
        symbols = input("\nPlease enter Stock Symbol: ").strip().upper()
        if not symbols:
            print("Error: symbol is required")
            return

        # URL for the API endpoint per E*TRADE docs
        symbol_path = quote(symbols, safe=",")
        url = f"{self.base_url}/v1/market/quote/{symbol_path}"
        params = {
            "detailFlag": "ALL",
            "requireEarningsDate": "true",
            "format": "json",
        }

        # Make API call for GET request
        response = self.session.get(url, params=params, headers={"Accept": "application/json"})
        logger.debug("Request Header: %s", response.request.headers)
        logger.debug("Request URL: %s", response.request.url)

        data = None
        if response is not None:
            try:
                data = response.json()
            except ValueError:
                logger.debug("Non-JSON response body: %s", response.text)

        if response is not None and response.status_code == 200 and data is not None:

            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))

            # Handle and parse response
            print("")
            if data is not None and "QuoteResponse" in data and "QuoteData" in data["QuoteResponse"]:
                for quote_item in data["QuoteResponse"]["QuoteData"]:
                    if quote_item is None:
                        print("Error: Quote data is empty: " + str(quote_item))
                        continue
                    if "dateTime" in quote_item:
                        print("Date Time: " + quote_item["dateTime"])
                    if "Product" in quote_item and "symbol" in quote_item["Product"]:
                        print("Symbol: " + quote_item["Product"]["symbol"])
                    if "Product" in quote_item and "securityType" in quote_item["Product"]:
                        print("Security Type: " + quote_item["Product"]["securityType"])
                    if "All" in quote_item and "lastTrade" in quote_item["All"]:
                        print("Last Price: " + str(quote_item["All"]["lastTrade"]))
                    if "All" in quote_item and "changeClose" in quote_item["All"] \
                        and "changeClosePercentage" in quote_item["All"]:
                        print("Today's Change: " + str('{:,.3f}'.format(quote_item["All"]["changeClose"])) + " (" +
                              str(quote_item["All"]["changeClosePercentage"]) + "%)")
                    if "All" in quote_item and "lastTrade" in quote_item["All"]:
                        print("Open: " + str('{:,.2f}'.format(quote_item["All"]["lastTrade"])))
                    if "All" in quote_item and "previousClose" in quote_item["All"]:
                        print("Previous Close: " + str('{:,.2f}'.format(quote_item["All"]["previousClose"])))
                    if "All" in quote_item and "bid" in quote_item["All"] and "bidSize" in quote_item["All"]:
                        print("Bid (Size): " + str('{:,.2f}'.format(quote_item["All"]["bid"])) + "x" + str(
                            quote_item["All"]["bidSize"]))
                    if "All" in quote_item and "ask" in quote_item["All"] and "askSize" in quote_item["All"]:
                        print("Ask (Size): " + str('{:,.2f}'.format(quote_item["All"]["ask"])) + "x" + str(
                            quote_item["All"]["askSize"]))
                    if "All" in quote_item and "low" in quote_item["All"] and "high" in quote_item["All"]:
                        print("Day's Range: " + str(quote_item["All"]["low"]) + "-" + str(quote_item["All"]["high"]))
                    if "All" in quote_item and "totalVolume" in quote_item["All"]:
                        print("Volume: " + str('{:,}'.format(quote_item["All"]["totalVolume"])))
            else:
                # Handle errors
                if data is not None and 'QuoteResponse' in data and 'Messages' in data["QuoteResponse"] \
                        and 'Message' in data["QuoteResponse"]["Messages"] \
                        and data["QuoteResponse"]["Messages"]["Message"] is not None:
                    for error_message in data["QuoteResponse"]["Messages"]["Message"]:
                        print("Error: " + error_message["description"])
                else:
                    print("Error: Quote API service error")
        else:
            if data is not None and "QuoteResponse" in data and "Messages" in data["QuoteResponse"] \
                    and "Message" in data["QuoteResponse"]["Messages"]:
                for error_message in data["QuoteResponse"]["Messages"]["Message"]:
                    print("Error: " + error_message.get("description", "Quote API service error"))
            else:
                logger.debug("Response status/body: %s / %s", response.status_code if response else "none", response.text if response else "none")
                print("Error: Quote API service error")

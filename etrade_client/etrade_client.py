"""This Python script provides examples on using the E*TRADE API endpoints"""
from __future__ import print_function
import webbrowser
import configparser
import datetime
from pathlib import Path
from requests import RequestException
from requests_oauthlib import OAuth1Session
from logger import get_logger
from accounts.accounts import Accounts
from market.market import Market
from option_chain.option_chain import OptionChain

# loading configuration file
config = configparser.ConfigParser()
ini_file = Path(__file__).parent / "config.ini"
config.read(ini_file)

logger = get_logger()


def oauth():
    """Allows user authorization for the sample application with OAuth 1"""

    cfg = config["DEFAULT"]

    menu_items = {"1": "Sandbox Consumer Key",
                  "2": "Live Consumer Key",
                  "3": "Exit"}
    while True:
        print("")
        options = menu_items.keys()
        for entry in options:
            print(entry + ")\t" + menu_items[entry])
        selection = input("Please select Consumer Key Type: ")
        if selection == "1":
            base_url = cfg["SANDBOX_BASE_URL"]
            break
        elif selection == "2":
            base_url = cfg["PROD_BASE_URL"]
            break
        elif selection == "3":
            return
        else:
            print("Unknown Option Selected!")
    print("")

    request_token_url = f"{base_url}/oauth/request_token"
    access_token_url = f"{base_url}/oauth/access_token"

    consumer_key = cfg["CONSUMER_KEY"]
    consumer_secret = cfg["CONSUMER_SECRET"]

    oauth_session = OAuth1Session(
        client_key=consumer_key,
        client_secret=consumer_secret,
        callback_uri="oob"
    )

    # Step 1: Get OAuth 1 request token and secret
    try:
        request_token_data = oauth_session.fetch_request_token(
            request_token_url,
            params={"format": "json"}
        )
    except (RequestException, ValueError) as exc:
        raise RuntimeError("Unable to fetch OAuth request token from E*TRADE.") from exc

    request_token = request_token_data.get("oauth_token")
    request_token_secret = request_token_data.get("oauth_token_secret")
    if not request_token or not request_token_secret:
        raise RuntimeError("E*TRADE did not return a valid OAuth request token response.")

    # Step 2: Go through the authentication flow. Login to E*TRADE.
    # After you login, the page will provide a verification code to enter.
    authorize_url = (
        "https://us.etrade.com/e/t/etws/authorize"
        f"?key={consumer_key}&token={request_token}"
    )
    webbrowser.open(authorize_url)
    text_code = input("Please accept agreement and enter verification code from browser: ").strip()

    # Step 3: Exchange the authorized request token for an authenticated OAuth 1 session
    try:
        oauth_session = OAuth1Session(
            client_key=consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=request_token,
            resource_owner_secret=request_token_secret,
            verifier=text_code
        )
        access_token_data = oauth_session.fetch_access_token(access_token_url)
        access_token = access_token_data["oauth_token"]
        access_token_secret = access_token_data["oauth_token_secret"]
        session = OAuth1Session(
            client_key=consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
    except (KeyError, RequestException, ValueError) as exc:
        raise RuntimeError(
            "OAuth access token exchange failed. This usually means one of: "
            "(1) wrong consumer key/secret environment, "
            "(2) request token expired or already used, "
            "(3) incorrect verifier code."
        ) from exc

    main_menu(session, base_url)


def option_chain_view(option_chain):
    """
    Interactive option chain view with user input for parameters

    :param option_chain: OptionChain instance
    """
    # Get required parameter
    symbol = input("\nPlease enter Stock Symbol: ").strip().upper()
    if not symbol:
        print("Error: symbol is required")
        return

    # Get optional expiration date parameters
    expiry_year = input("Enter expiry year (optional, press Enter to skip): ").strip()
    expiry_month = input("Enter expiry month (1-12, optional, press Enter to skip): ").strip()
    expiry_day = input("Enter expiry day (optional, press Enter to skip): ").strip()

    # Get other optional parameters
    strike_price_near = input("Enter strike price near (optional, press Enter to skip): ").strip()
    no_of_strikes = input("Enter number of strikes (optional, press Enter to skip): ").strip()
    include_weekly = input("Include weekly options? (true/false, default: false): ").strip().lower() == "true"
    skip_adjusted = input("Skip adjusted options? (true/false, default: true): ").strip().lower() != "false"

    # Option category
    print("\nOption Category (default: STANDARD):")
    print("1) STANDARD")
    print("2) ALL")
    print("3) MINI")
    category_input = input("Select option category (1-3, press Enter for default): ").strip()
    option_category_map = {"1": "STANDARD", "2": "ALL", "3": "MINI"}
    option_category = option_category_map.get(category_input, "STANDARD")

    # Chain type
    print("\nChain Type (default: CALLPUT):")
    print("1) CALL")
    print("2) PUT")
    print("3) CALLPUT")
    chain_input = input("Select chain type (1-3, press Enter for default): ").strip()
    chain_type_map = {"1": "CALL", "2": "PUT", "3": "CALLPUT"}
    chain_type = chain_type_map.get(chain_input, "CALLPUT")

    # Price type
    print("\nPrice Type (default: ATNM):")
    print("1) ATNM")
    print("2) ALL")
    price_input = input("Select price type (1-2, press Enter for default): ").strip()
    price_type_map = {"1": "ATNM", "2": "ALL"}
    price_type = price_type_map.get(price_input, "ATNM")

    ticker_option_chain = OptionChain(
        option_chain.session,
        option_chain.base_url,
        symbol=symbol,
        option_category=option_category,
        chain_type=chain_type,
    )

    # Convert string inputs to appropriate types
    params = {
        "include_weekly": include_weekly,
        "skip_adjusted": skip_adjusted,
        "price_type": price_type,
    }

    if expiry_year:
        params["expiry_year"] = int(expiry_year) if expiry_year.isdigit() else None
    if expiry_month:
        params["expiry_month"] = int(expiry_month) if expiry_month.isdigit() else None
        # If month is given but year is not, infer the year: use current year unless
        # that month has already passed, in which case use next year.
        if not expiry_year and expiry_month.isdigit():
            today = datetime.date.today()
            month = int(expiry_month)
            inferred_year = today.year if month >= today.month else today.year + 1
            params["expiry_year"] = inferred_year
            print(f"(expiry year defaulted to {inferred_year})")
    if expiry_day:
        params["expiry_day"] = int(expiry_day) if expiry_day.isdigit() else None
    if strike_price_near:
        try:
            params["strike_price_near"] = float(strike_price_near)
        except ValueError:
            pass
    if no_of_strikes:
        params["no_of_strikes"] = int(no_of_strikes) if no_of_strikes.isdigit() else None

    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    # Call the view method
    csv_result = ticker_option_chain.view(**params)

    if csv_result:
        print("\n" + "="*80)
        print("OPTION CHAIN DATA (CSV FORMAT)")
        print("="*80)
        print(csv_result)
        print("="*80)

        # Optionally save to file
        save_to_file = input("\nSave to file? (yes/no): ").strip().lower()
        if save_to_file == "yes":
            filename = input("Enter filename (default: option_chain.csv): ").strip()
            if not filename:
                filename = "option_chain.csv"
            try:
                with open(filename, "w") as f:
                    f.write(csv_result)
                print(f"Data saved to {filename}")
                logger.info("Option chain data saved to %s", filename)
            except IOError as e:
                print(f"Error saving file: {e}")
                logger.error("Error saving option chain data: %s", e)
    else:
        print("Error: Unable to retrieve option chain data")


def main_menu(session, base_url):
    """
    Provides the different options for the sample application: Market Quotes, Account List, Option Chain

    :param session: authenticated session
    """

    menu_items = {"1": "Market Quotes",
                  "2": "Account List",
                  "3": "Option Chain",
                  "4": "Exit"}

    while True:
        print("")
        options = menu_items.keys()
        for entry in options:
            print(entry + ")\t" + menu_items[entry])
        selection = input("Please select an option: ")
        if selection == "1":
            market = Market(session, base_url)
            market.quotes()
        elif selection == "2":
            accounts = Accounts(session, base_url)
            accounts.account_list()
        elif selection == "3":
            option_chain = OptionChain(session, base_url)
            option_chain_view(option_chain)
        elif selection == "4":
            break
        else:
            print("Unknown Option Selected!")


if __name__ == "__main__":
    oauth()

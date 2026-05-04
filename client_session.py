"""This Python script provides examples on using the E*TRADE API endpoints"""
from __future__ import print_function
import configparser
import datetime
from pathlib import Path
from etrade_client.logger import get_logger
from etrade_client.auth.auth import EtradeAuthorization
from etrade_client.accounts.accounts import Accounts
from etrade_client.market.market import Market
from etrade_client.option_chain.option_chain import OptionChain

# loading configuration file
config = configparser.ConfigParser()
ini_file = Path(__file__).parent / "config.ini"
config.read(ini_file)

logger = get_logger()


def main():
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

    auth = EtradeAuthorization()
    auth_result = auth.authorize(cfg, base_url)

    main_menu(auth_result.session, auth_result.base_url)


def option_chain_view(session, base_url):
    """
    Interactive option chain view with user input for parameters

    :param session: authenticated session
    :param base_url: base URL for API calls
    """
    # Get required parameter
    symbol = input("\nPlease enter Stock Symbol: ").strip().upper()
    if not symbol:
        print("Error: symbol is required")
        return

    # Get optional expiration date parameter
    expiry_date = input("Enter expiry date (MM-DD-YYYY, optional, press Enter to skip): ").strip()

    # Get other optional parameters
    strike_price_near = input("Enter strike price near (optional, press Enter to skip): ").strip()
    no_of_strikes = input("Enter number of strikes (optional, press Enter to skip): ").strip()
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
        session,
        base_url,
        symbol=symbol,
        option_category=option_category,
        chain_type=chain_type,
    )

    # Convert string inputs to appropriate types
    params = {
        "skip_adjusted": skip_adjusted,
        "price_type": price_type,
    }

    if expiry_date:
        params["expiry_date"] = expiry_date
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
            option_chain_view(session, base_url)
        elif selection == "4":
            break
        else:
            print("Unknown Option Selected!")


if __name__ == "__main__":
    main()

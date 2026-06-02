"""Interactive helper for storing E*TRADE API credentials in keyring."""

from getpass import getpass

from etrade_client.auth.auth import (
    get_consumer_key,
    get_consumer_secret,
    set_consumer_key,
    set_consumer_secret,
)


def _prompt_required(prompt: str, *, secret: bool = False) -> str:
    """Prompt until a non-empty value is provided."""
    while True:
        value = (getpass(prompt) if secret else input(prompt)).strip()
        if value:
            return value
        print("Value cannot be empty. Please try again.")


def main() -> None:
    """Collect and store consumer credentials in the system keyring."""
    existing_key = get_consumer_key()
    existing_secret = get_consumer_secret()

    if existing_key or existing_secret:
        print("Existing E*TRADE credentials were found in keyring for service 'EtradeClient'.")
        overwrite = input("Overwrite them? [y/N]: ").strip().lower()
        if overwrite not in {"y", "yes"}:
            print("No changes made.")
            return

    consumer_key = _prompt_required("Enter E*TRADE consumer key: ")
    consumer_secret = _prompt_required("Enter E*TRADE consumer secret: ", secret=True)

    set_consumer_key(consumer_key)
    set_consumer_secret(consumer_secret)
    print("Credentials saved to keyring (service: 'EtradeClient').")


if __name__ == "__main__":
    main()
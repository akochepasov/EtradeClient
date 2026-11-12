import webbrowser
from typing import NamedTuple

import keyring
from requests import RequestException
from requests_oauthlib import OAuth1Session

from etrade_client.common import DEFAULT_TIMEOUT


def get_consumer_key() -> str:
    """Return the E*TRADE consumer key from the system keychain."""
    return keyring.get_password("EtradeClient", "CONSUMER_KEY")


def get_consumer_secret() -> str:
    """Return the E*TRADE consumer secret from the system keychain."""
    return keyring.get_password("EtradeClient", "CONSUMER_SECRET")


def set_consumer_key(value: str) -> None:
    """Store the E*TRADE consumer key in the system keychain."""
    keyring.set_password("EtradeClient", "CONSUMER_KEY", value)


def set_consumer_secret(value: str) -> None:
    """Store the E*TRADE consumer secret in the system keychain."""
    keyring.set_password("EtradeClient", "CONSUMER_SECRET", value)

# Ensure credentials are in keyring (prompts only if missing)
def ensure_credentials():
    if not get_consumer_key():
        print('No E*TRADE API credentials found.')
        print('Get these from the E*TRADE Developer Portal.\n')
        ck = input('Consumer key: ').strip()
        cs = input('Consumer secret: ').strip()
        if ck and cs:
            set_consumer_key(ck)
            set_consumer_secret(cs)
            print('Credentials saved.\n')
        else:
            raise RuntimeError('Consumer key and secret are required.')


class AuthorizationResult(NamedTuple):
    """Authorization session and base URL, unpackable in that order."""

    session: OAuth1Session
    base_url: str


def EtradeAuthorization(cfg, open_browser=True, timeout=DEFAULT_TIMEOUT):
    """
    Authorize user with OAuth and return session + base_url.

    Note: OAuth access tokens are not persisted across runs — the full
    browser authorization flow runs every time.  A future improvement
    would be to store tokens in keyring and reuse them until a 401.

    :param cfg: selected config section (for example: config["DEFAULT"])
    :param open_browser: open the default browser; if False, print the authorization URL
    :param timeout: request timeout in seconds
    :return: AuthorizationResult
    """
    base_url = cfg.get("PROD_BASE_URL") # or cfg.get("SANDBOX_BASE_URL")
    if not base_url:
        raise RuntimeError("base_url is required")

    request_token_url = f"{base_url}/oauth/request_token"
    access_token_url = f"{base_url}/oauth/access_token"

    consumer_key = get_consumer_key()
    consumer_secret = get_consumer_secret()

    oauth_session = OAuth1Session(
        client_key=consumer_key,
        client_secret=consumer_secret,
        callback_uri="oob",
    )

    # Step 1: Get OAuth 1 request token and secret
    try:
        request_token_data = oauth_session.fetch_request_token(
            request_token_url,
            params={"format": "json"},
            timeout=timeout,
        )
    except (RequestException, ValueError) as exc:
        raise RuntimeError("Unable to fetch OAuth request token from E*TRADE.") from exc

    request_token = request_token_data.get("oauth_token")
    request_token_secret = request_token_data.get("oauth_token_secret")
    if not request_token or not request_token_secret:
        raise RuntimeError("E*TRADE did not return a valid OAuth request token response.")

    # Step 2: Direct user to authorize and provide verifier code.
    authorize_url = (
        "https://us.etrade.com/e/t/etws/authorize"
        f"?key={consumer_key}&token={request_token}"
    )
    if open_browser:
        webbrowser.open(authorize_url)
    else:
        print(f"{authorize_url}")
    verifier = input("Please accept agreement and enter verification code from browser: ").strip()

    # Step 3: Exchange request token for access token and build authenticated session.
    try:
        oauth_session = OAuth1Session(
            client_key=consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=request_token,
            resource_owner_secret=request_token_secret,
            verifier=verifier,
        )
        access_token_data = oauth_session.fetch_access_token(access_token_url, timeout=timeout)

        access_token = access_token_data["oauth_token"]
        access_token_secret = access_token_data["oauth_token_secret"]
        session = OAuth1Session(
            client_key=consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
    except (KeyError, RequestException, ValueError) as exc:
        raise RuntimeError(
            "OAuth access token exchange failed. This usually means one of: "
            "(1) wrong consumer key/secret environment, "
            "(2) request token expired or already used, "
            "(3) incorrect verifier code."
        ) from exc

    return AuthorizationResult(session=session, base_url=base_url)

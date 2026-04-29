import webbrowser
from dataclasses import dataclass

from requests import RequestException
from requests_oauthlib import OAuth1Session


@dataclass
class AuthorizationResult:
    session: OAuth1Session
    base_url: str


class EtradeAuthorization:
    """Handles OAuth 1 authorization flow for E*TRADE."""

    def authorize(self, cfg, base_url):
        """
        Authorize user and return session + base_url.

        :param cfg: selected config section (for example: config["DEFAULT"])
        :param base_url: selected base URL
        :return: AuthorizationResult
        """
        if not base_url:
            raise RuntimeError("base_url is required")

        request_token_url = f"{base_url}/oauth/request_token"
        access_token_url = f"{base_url}/oauth/access_token"

        consumer_key = cfg["CONSUMER_KEY"]
        consumer_secret = cfg["CONSUMER_SECRET"]

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
        webbrowser.open(authorize_url)
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
            access_token_data = oauth_session.fetch_access_token(access_token_url)

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

# etrade-client

Python client for E*TRADE API workflows in command-line apps and Jupyter notebooks.

## Install

```bash
pip install etrade-client
```

For local development:

```bash
pip install -e .
```

## Imports

```python
from etrade_client.auth import EtradeAuthorization
from etrade_client.accounts import Accounts
from etrade_client.market import Market
from etrade_client.option_chain import OptionChain
```

## Configuration

API secrets are stored securely via the
[`keyring`](https://pypi.org/project/keyring/) library (service: `EtradeClient`).
Run the helper to save your key/secret interactively:

```bash
python -m etrade_client.authorize
```

Or store them manually:

```bash
python -c "
import keyring
keyring.set_password('EtradeClient', 'CONSUMER_KEY', 'YOUR_KEY')
keyring.set_password('EtradeClient', 'CONSUMER_SECRET', 'YOUR_SECRET')
"
```

`config.ini` holds non-sensitive base URLs only:

```ini
[DEFAULT]
SANDBOX_BASE_URL=https://apisb.etrade.com
PROD_BASE_URL=https://api.etrade.com
```

## Authorization

`EtradeAuthorization(cfg)` opens the default browser.
To use a different browser, print the authorization URL instead:

```python
session, base_url = EtradeAuthorization(cfg, open_browser=False)
```

Open the printed URL in your preferred browser and enter the verification code
when prompted. Treat the URL as sensitive; it contains an OAuth request token.
The result also supports named access via `.session` and `.base_url`.

## Timeouts and logging

OAuth and API requests default to a 30-second timeout. Set `timeout` on
`EtradeAuthorization`, `Market`, `Accounts`, `OptionChain`, or `Order` to
override it; connect/read timeout tuples are also supported.

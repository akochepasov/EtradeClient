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

## CLI

After install, run:

```bash
etrade-client
```

## Configuration

API secrets are stored securely via the
[`keyring`](https://pypi.org/project/keyring/) library (service: `EtradeClient`).
The CLI will prompt you on first run, or you can store them manually:

```bash
python3 -c "
import keyring
keyring.set_password('EtradeClient', 'CONSUMER_KEY', 'YOUR_KEY')
keyring.set_password('EtradeClient', 'CONSUMER_SECRET', 'YOUR_SECRET')
"
```

`config.ini` still holds the (non-sensitive) base URLs:

```ini
[DEFAULT]
SANDBOX_BASE_URL=https://apisb.etrade.com
PROD_BASE_URL=https://api.etrade.com
```
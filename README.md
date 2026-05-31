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

Create a `config.ini` with the required API keys and E*TRADE base URLs.
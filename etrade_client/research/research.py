from logger import get_logger
from option_chain.option_chain import OptionChain

import pandas as pd

logger = get_logger()


class OptionsResearch:
    """
    Research utility that scans option chains for multiple tickers and returns
    a compact DataFrame with pricing and greek fields.
    """

    def __init__(self, gamma_lo=None, gamma_hi=None, include=True):
        """
        Initialize OptionsResearch object.

        :param gamma_lo: minimum gamma (inclusive)
        :param gamma_hi: maximum gamma (inclusive)
        :param include: if true, keep rows with gamma inside [gamma_lo, gamma_hi];
                        if false, keep rows with gamma outside [gamma_lo, gamma_hi]
        """
        self.gamma_lo = gamma_lo
        self.gamma_hi = gamma_hi
        self.include = bool(include)

    def Find(self, option_chains):
        """
        Find and filter options from the provided list of OptionChain objects.

        Returns a DataFrame with rows containing options ticker, buy, sell,
        mark, volume, and delta.

        :param option_chains: list of OptionChain instances
        :return: pandas DataFrame
        """

        rows = []
        for chain in option_chains:
            chain_df = chain.view(as_dataframe=True)
            if chain_df is None or chain_df.empty:
                logger.info("No option chain data for symbol: %s", getattr(chain, "symbol", None))
                continue

            filtered_df = self._filter_chain(chain_df)
            if filtered_df.empty:
                continue

            for _, row in filtered_df.iterrows():
                buy = self._to_float(row.get("bid"))
                sell = self._to_float(row.get("ask"))
                mark = None
                if buy is not None and sell is not None:
                    mark = (buy + sell) / 2.0

                options_ticker = row.get("displaySymbol") or row.get("symbol") or row.get("osiKey")
                rows.append(
                    {
                        "options_ticker": options_ticker,
                        "buy": buy,
                        "sell": sell,
                        "mark": mark,
                        "volume": self._to_int(row.get("volume")),
                        "delta": self._to_float(row.get("delta")),
                    }
                )

        if not rows:
            return pd.DataFrame(columns=["options_ticker", "buy", "sell", "mark", "volume", "delta"])

        return pd.DataFrame(rows, columns=["options_ticker", "buy", "sell", "mark", "volume", "delta"])

    def _filter_chain(self, chain_df):
        """
        Apply gamma range filtering to the option chain DataFrame.
        """
        df = chain_df.copy()

        gamma_series = pd.to_numeric(df.get("gamma"), errors="coerce")

        if self.gamma_lo is None and self.gamma_hi is None:
            return df

        # Build in-range mask first, then include or invert it based on the flag.
        in_range_mask = pd.Series(True, index=df.index)
        if self.gamma_lo is not None:
            in_range_mask = in_range_mask & (gamma_series >= float(self.gamma_lo))
        if self.gamma_hi is not None:
            in_range_mask = in_range_mask & (gamma_series <= float(self.gamma_hi))

        if self.include:
            df = df[in_range_mask]
        else:
            df = df[~in_range_mask]

        return df

    def _to_float(self, value):
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_int(self, value):
        try:
            if value is None or value == "":
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None

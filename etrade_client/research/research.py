from etrade_client.logger import get_logger

import datetime as dt

import pandas as pd
import io

logger = get_logger()


_RESEARCH_COLUMNS = [
    "optionType", "strikePrice", "delta",
    "openInterest", "volume",
    "lastPrice", "bid", "ask",
]


class OptionsResearchDelta:
    """
    Research utility that scans option chains for multiple tickers and returns
    a compact DataFrame with pricing and greek fields.
    """

    def __init__(self, opt_type, delta_lo=0.05, delta_hi=0.3, include=True):
        """
        Initialize OptionsResearchDelta object.

        :param delta_lo: minimum delta (inclusive)
        :param delta_hi: maximum delta (inclusive)
        :param include: if true, keep rows with delta inside [delta_lo, delta_hi];
                        if false, keep rows with delta outside [delta_lo, delta_hi]
        """
        self.opt_type = opt_type
        self.include = bool(include)
        self.delta_lo = delta_lo
        self.delta_hi = delta_hi

    def find(self, chain_data):
        """
        Find and filter options by delta from option chain data returned by OptionChain.view().

        Returns a DataFrame with rows containing options ticker, buy, sell,
        mark, volume, and delta.

        :param chain_data: OptionChain.view() result (pandas DataFrame or CSV text)
        :return: pandas DataFrame
        """
        chain_df = self._to_dataframe(chain_data)
        if chain_df is None or chain_df.empty:
            logger.info("No option chain data available for research filtering")
            return pd.DataFrame(columns=["options_ticker", "buy", "sell", "mark", "volume", "delta"])

        filtered_df = self._filter_chain(chain_df)
        if filtered_df.empty:
            return pd.DataFrame(columns=["options_ticker", "buy", "sell", "mark", "volume", "delta"])

        rows = []
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

    def result(self, chain, cost_basis, date, qty=100):
        """
        Add premium and annualized yield columns.

        Puts use strike price as capital per share. Other option types use cost_basis.

        :param chain: option chain DataFrame
        :param cost_basis: per-share capital used for non-put yields
        :param date: expiration date; must be in the future
        :param qty: share multiplier, 100 for one contract
        :return: DataFrame with gain_total and annual_rate
        """
        days = (date - dt.datetime.today()).days
        if days <= 0:
            raise ValueError(f"Date should be in the future: {date}")

        result = self._get_research(chain)
        result = result.assign(mark=lambda frame: (frame.ask + frame.bid) / 2)
        result = result.assign(gain_total=lambda frame: frame.mark * qty)
        capital_per_share = result.strikePrice.where(result.optionType == "PUT", cost_basis)
        return result.assign(annual_rate=100 * result.mark / capital_per_share * 365 / days)

    def _to_dataframe(self, chain_data):
        if chain_data is None:
            return None
        if isinstance(chain_data, pd.DataFrame):
            return chain_data
        if isinstance(chain_data, str):
            text = chain_data.strip()
            if not text:
                return None
            try:
                return pd.read_csv(io.StringIO(text))
            except Exception:
                return None
        return None

    def _filter_chain(self, chain_df):
        """
        Apply delta filtering to the option chain DataFrame.
        """
        df = chain_df.copy()

        delta_series = pd.to_numeric(df.get("delta"), errors="coerce")

        if self.delta_lo is None and self.delta_hi is None:
            return df

        # Build in-range mask first, then include or invert it based on the flag.
        in_range_mask = pd.Series(True, index=df.index)
        if self.delta_lo is not None:
            in_range_mask = in_range_mask & (delta_series >= float(self.delta_lo))
        if self.delta_hi is not None:
            in_range_mask = in_range_mask & (delta_series <= float(self.delta_hi))

        if self.include:
            df = df[in_range_mask]
        else:
            df = df[~in_range_mask]

        return df

    def _get_research(self, chain_df, query_param=None):
        """
        Filter an option-chain DataFrame for a given option type and delta range.

        :param chain_df: option chain DataFrame
        :param query_param: optional pandas query string
        :return: filtered DataFrame with a midpoint mark column
        """
        opt_type = self.opt_type
        delta_min = self.delta_lo
        delta_max = self.delta_hi
        option_mask = chain_df["optionType"] == opt_type
        delta_mask = (abs(chain_df["delta"]) >= delta_min) & (abs(chain_df["delta"]) < delta_max)
        open_interest_mask = chain_df["openInterest"] != 0
        result = chain_df[option_mask & delta_mask & open_interest_mask]
        if query_param:
            result = result.query(query_param)
        result = result[_RESEARCH_COLUMNS]
        return result

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

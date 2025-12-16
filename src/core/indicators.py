import numpy as np
import pandas as pd
from scipy import stats
import logging

logger = logging.getLogger('indicators')


class RSIIndicator:
    """
    RSI Indicator class that maintains internal state for recursive RSI calculation

    Attributes:
        period (int): The lookback period (N) for RSI calculation.
        avg_gain (float): Internal state for smoothed average gain.
        avg_loss (float): Internal state for smoothed average loss.
        value (float): The most recently computed RSI value.
    """

    def __init__(self, period: int = 2):
        """
        Initialize the RSI Indicator.

        Parameters
        ----------
        period : int
            Lookback period. Defaults to 2.
        """
        self.period = period
        # Initialization flags (-1.0: "not initialized")
        self.avg_gain = -1
        self.avg_loss = -1
        self.value = float('nan')

    def compute(self, series: pd.Series) -> float:
        """
        Compute the next RSI value based on the input series.

        Parameters
        ----------
        series : pd.Series
            Price series.

        Returns
        ----------
        float
            The computed RSI value.

        Notes
        -----
        - If initialized: Requires the last 2 pricesù
        - If NOT initialized: Requires at least (period + 1) prices.
        """
        if series is None or len(series) == 0:
            logger.error("RSIIndicator: empty series or None")
            return float("nan")
        if len(series.dropna()) < self.period + 1:
            logger.error("RSIIndicator: insuff. data (min %d, found %d)",
                         self.period + 1, len(series.dropna()))
            return float('nan')

        smoothing_factor = 1 / self.period

        # Initialization (First Run)
        if self.avg_gain == -1 and self.avg_loss == -1:
            if len(series.dropna()) < self.period + 1:
                logger.error("RSIIndicator: insuff. data for init (min %d, found %d)",
                             self.period + 1, len(series.dropna()))
                return float('nan')
            # computes daily returns for last 'period' days
            delta = series.diff().tail(self.period)
            gain = delta.clip(lower=0)  # positive returns
            loss = -delta.clip(upper=0)  # negative returns
            self.avg_gain = gain.mean()
            self.avg_loss = loss.mean()

        # Recursive Update (Subsequent Runs)
        else:
            if len(series) < 2:
                logger.error(
                    "RSIIndicator: insuff. data for update (need last 2 prices)")
                return self.value
            change = series.iloc[-1] - series.iloc[-2]
            gain = max(change, 0.0)
            loss = max(-change, 0.0)
            self.avg_gain = self.avg_gain + \
                smoothing_factor * (gain - self.avg_gain)
            self.avg_loss = self.avg_loss + \
                smoothing_factor * (loss - self.avg_loss)

        # Calculate RSI from State
        if self.avg_loss == 0.0:
            if self.avg_gain > 0.0:
                rsi = 100.0
            else:
                rsi = 0.0
        elif self.avg_gain == 0.0 and self.avg_loss > 0.0:
            rsi = 0.0
        else:
            rs = self.avg_gain / self.avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

        logger.debug(f'RSI value is {rsi}')
        if not np.isfinite(rsi):
            logger.error("RSIIndicator: inf value calculated (%.5f)", rsi)
        self.value = rsi

        return rsi


def hurst_local(series: pd.Series) -> float:
    """
    Compute the Hurst exponent for a single contiguous series segment using the R/S (rescaled range) method.

    This function splits the input segment into multiple sub-windows (log-spaced sizes), computes the
    rescaled range R/S for each sub-window size, and estimates the Hurst exponent as the slope of the
    linear fit on the log10(window_size) vs log10(R/S) values.

    Parameters
    ----------
    series : pd.Series
        1-dimensional sequence of prices (or returns) for which the local Hurst exponent is estimated.

    Returns
    -------
    float
        Estimated Hurst exponent (slope). Returns ``np.nan`` when the segment is too short or when
        there are insufficient valid R/S observations for regression.

    Notes
    -----
    - The implementation requires at least a small number of points (function returns NaN for N < 8).
    - Uses ddof=0 standard deviation and ignores subsegments with zero variance.
    """
    ts = np.asarray(series, dtype=float)  # Convert to numpy array
    N = len(ts)
    if N < 8:
        logger.error("hurst_local: insuff. data (N=%d, min 8)", N)
        return np.nan

    # Range of segment sizes
    max_window = N // 2
    if max_window < 4:
        logger.error(
            "hurst_local: max_window too short (max_window=%d)", max_window)
        return np.nan
    window_sizes = np.unique(np.floor(np.logspace(
        np.log10(4), np.log10(max_window), num=10)).astype(int))

    RS_vals = []
    used_windows = []
    for w in window_sizes:
        if w >= N:
            continue
        n_segments = N // w
        RS_seg = []
        for i in range(n_segments):
            seg = ts[i*w:(i+1)*w]  # current segment
            seg = seg - np.mean(seg)  # detrend
            Y = np.cumsum(seg)  # cumulative deviation from mean
            R = np.max(Y) - np.min(Y)  # max range of cumulative dev
            S = np.std(seg)  # standard deviation of segment
            if S != 0:
                RS_seg.append(R/S)
        if RS_seg:
            RS_vals.append(np.mean(RS_seg))
            used_windows.append(w)
    if len(RS_vals) < 2:
        logger.error(
            "hurst_local: R/S insuff. observations (len=%d)", len(RS_vals))
        return np.nan
    # The Hurst exponent is the slope of the log-log plot
    lx = np.log10(np.array(used_windows))
    ly = np.log10(RS_vals)
    slope, _, _, _, _ = stats.linregress(lx, ly)
    return slope


def hurst_exponent(series: pd.Series, window: int = 20) -> float:
    """
    Compute a rolling (moving-window) Hurst exponent series.

    For each time index this function takes the previous `window` observations and runs
    :func:`hurst_local` to estimate the Hurst exponent on that local window. This produces a
    time series of Hurst estimates which can be used for regime detection (trend vs mean-reversion).

    Parameters
    ----------
    series : pd.Series
        Input price (or return) series with a datetime-like index.
    window : int, optional
        Rolling window length in number of samples used for each local Hurst estimation (default=20).

    Returns
    -------
    float
        Last rolling Hurst value (np.nan if window is not full).

    Notes
    -----
    - The function delegates the actual R/S calculation to :func:`hurst_local`.
    - Caller may choose to post-process the output (e.g., smoothing or forward-filling) depending
      on downstream use-cases.
    """
    '''if series is None or len(series) == 0:
        logger.error("hurst_exponent: empty series or None")
        return float("nan")
    if len(series.dropna()) < window:
        logger.error("hurst_exponent: insuff. data (window=%d, found=%d)", window, len(series.dropna()))
        return

    H_series = series.rolling(window).apply(lambda x: hurst_local(x), raw=False)
    H = float(H_series.iloc[-1])'''
    # TEMPORANEO
    H = np.random.rand()

    logger.debug(f"H is {H}")
    # TEMPORANEO
    return H


class CompositeRSIIndicator:
    """
    Composite RSI Indicator class that computes a weighted average of short-term and long-term RSI.

    Attributes:
        short_period (int): Lookback period for the short RSI.
        long_period (int): Lookback period for the long RSI.
        rsi_short (RSIIndicator): Instance handling the short RSI state.
        rsi_long (RSIIndicator): Instance handling the long RSI state.
        value (float): The most recently computed Composite RSI value.
    """

    def __init__(self, short_period: int, long_period: int):
        """
        Initialize the Composite RSI Indicator.

        Parameters
        ----------
        short_period (int): Short lookback period 
        long_period (int): Long lookback period
        """
        self.short_period = short_period
        self.long_period = long_period
        self.value = float('nan')

        self.rsi_short = RSIIndicator(period=short_period)
        self.rsi_long = RSIIndicator(period=long_period)

    def compute(self, series: pd.Series) -> float:
        """
        Compute the Composite RSI value as average of short and long RSI.

        Parameters
        ----------
        series : pd.Series 
            Input price series

        Returns
        ----------
        float
            The computed Composite RSI value

        Notes
        -----
        - The function relies on the 2 internal RSIIndicator instances to maintain state
        """

        if series is None or len(series) == 0:
            logger.error("CompositeRSIIndicator: empty series or None")
            return float("nan")

        # Check if enough data for the long period
        if (self.rsi_long.avg_gain == -1.0) and (len(series.dropna()) < self.long_period + 1):
            return float('nan')

        # Pass the series to both internal indicators, that will update their own internal states
        val_short = self.rsi_short.compute(series)
        val_long = self.rsi_long.compute(series)

        if np.isnan(val_short) or np.isnan(val_long):
            logger.debug(
                "CompositeRSIIndicator: RSI sub-indicators returned NaN")
            return float('nan')

        self.value = (0.5 * val_short) + (0.5 * val_long)

        logger.debug(f"CompositeRSI value is {self.value}")
        return self.value

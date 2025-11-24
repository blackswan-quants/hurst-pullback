import numpy as np
import pandas as pd
from scipy import stats

def rsi(series: pd.Series, period: int = 2) -> float:
    """
    Compute Relative Strength Index (RSI)

    Args
        series (pd.Series): Series of prices
        period (int): Lookback period (default=2)

    Returns
        float: last RSI value
    """
    delta = series.diff() # computes daily returns
    gain = delta.clip(lower=0) # positive returns
    loss = -delta.clip(upper=0) # negative returns

    # allegedly this Exponentially weighted smoothing should match EasyLanguage's standard
    # Wilder's smoothing — exponential moving average with alpha = 1/period
    # avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    # avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()

    # Rolling mean directly over the last N bars, no smoothing
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    RS = avg_gain / avg_loss
    RSI = 100 - (100 / (1 + RS))
    RSI = RSI.fillna(0)

    return float(RSI.iloc[-1])


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
    ts = np.asarray(series, dtype=float) # Convert to numpy array
    N = len(ts)
    if N < 8:
        return np.nan

    # Range of segment sizes
    max_window = N // 2
    window_sizes = np.unique(np.floor(np.logspace(np.log10(4), np.log10(max_window), num=10)).astype(int))
    
    RS_vals = []
    for w in window_sizes:
        if w >= N:
            continue
        n_segments = N // w
        RS_seg = []
        for i in range(n_segments):
            seg = ts[i*w:(i+1)*w] # current segment
            seg = seg - np.mean(seg) # detrend
            Y = np.cumsum(seg) # cumulative deviation from mean
            R = np.max(Y) - np.min(Y) # max range of cumulative dev
            S = np.std(seg) # standard deviation of segment
            if S != 0:
                RS_seg.append(R/S)
        if RS_seg:
            RS_vals.append(np.mean(RS_seg))
    if len(RS_vals) < 2:
        return np.nan
    # The Hurst exponent is the slope of the log-log plot
    lx = np.log10(window_sizes[:len(RS_vals)])
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
    H_series = series.rolling(window).apply(lambda x: hurst_local(x), raw=False)
    H = float(H_series.iloc[-1])
    return H


def _rsi_series(series: pd.Series, period: int) -> pd.Series:
    """Internal helper: full RSI series (used by composite_rsi)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    RS = avg_gain / avg_loss
    RSI = 100 - (100 / (1 + RS))
    return RSI.fillna(0)

def composite_rsi(series: pd.Series, short: int, long: int) -> float:
    """
    Compute a composite (smoothed) short-term RSI by applying exponential smoothing over a
    longer timescale.

    Parameters
    ----------
    series : pd.Series
        Price series (close prices) used to compute the short-term RSI.
    short : int
        Lookback period for the short-term RSI (e.g., 2).
    long : int
        Smoothing span for the EWMA applied to the short RSI (e.g., 24).

    Returns
    -------
    float
        Last value of the EWMA-smoothed short RSI

    Notes
    -----
    - This helper is commonly used in signal generation when a very short RSI is noisy and a
      smoothed version is preferred for rule-based entries/exits.
    """
    short_rsi_series = _rsi_series(series, period=short)
    comp_rsi_series = short_rsi_series.ewm(span=long, adjust=False).mean()
    return float(comp_rsi_series.iloc[-1])

import numpy as np
import pandas as pd
from scipy import stats
import warnings

def rsi(series: pd.Series, period: int = 2) -> pd.Series:
    """
    Compute Relative Strength Index (RSI) using the recursive Welles Wilder's smoothing method.

    This vectorized function calculates the RSI value for the entire series.

    Args
        series (pd.Series): The sequence of prices (usually Close prices).
        period (int): The lookback period (N) for the RSI calculation.

    Returns
        pd.Series: A series containing the RSI values mapped to the original index.
    """
    if series is None or len(series) == 0:
        return pd.Series(index=series.index if series is not None else [], dtype=float)
        
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    # Use exponential moving average as per Wilder smoothing
    ema_up = up.ewm(com=period-1, adjust=False).mean()
    ema_down = down.ewm(com=period-1, adjust=False).mean()
    
    rs = ema_up / ema_down
    rsi_vals = 100 - (100 / (1 + rs))
    
    return rsi_vals


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
    if max_window < 4:
        return np.nan
    window_sizes = np.unique(np.floor(np.logspace(np.log10(4), np.log10(max_window), num=10)).astype(int))
    
    RS_vals = []
    used_windows = []
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
            used_windows.append(w)
    if len(RS_vals) < 2:
        return np.nan
        
    # The Hurst exponent is the slope of the log-log plot
    lx = np.log10(np.array(used_windows))
    ly = np.log10(RS_vals)
    
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        slope, _, _, _, _ = stats.linregress(lx, ly) 
        
    return slope


def hurst_exponent(series: pd.Series, window: int = 20) -> pd.Series:
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
    pd.Series
        Rolling Hurst values mapped to the original index.
    """
    if series is None or len(series) == 0:
        return pd.Series(index=series.index if series is not None else [], dtype=float)
        
    return series.rolling(window).apply(hurst_local, raw=False)

def composite_rsi(series: pd.Series, short: int, long: int) -> pd.Series:
    """
    Computes a Composite RSI based on 50/50 weights of short and long RSI values.

    Args:
        series: Price series data
        short: Lookback period for the short RSI
        long: Lookback period for the long RSI
    
    Returns:
        pd.Series: Vector array containing composite RSI results
    """
    if series is None or len(series) == 0:
        return pd.Series(index=series.index if series is not None else [], dtype=float)
        
    short_rsi = rsi(series, period=short)
    long_rsi = rsi(series, period=long)
    
    return (0.5 * short_rsi) + (0.5 * long_rsi)
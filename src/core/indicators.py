import numpy as np
import pandas as pd
from scipy import stats
import logging

logger = logging.getLogger('indicators')

def rsi(series: pd.Series, avg_gain : float, avg_loss : float, period: int = 2) -> float:
    """
    Compute Relative Strength Index (RSI) using the recursive Welles Wilder's smoothing method.

    This function calculates the RSI value for the *last* price in the series, 
    updating the running averages (avg_gain and avg_loss) for the next iteration.

    Args
        series (pd.Series): 
            - For the first call (initialization): must contain the first PERIOD + 1 prices.
            - For subsequent calls (recursion): must contain the last 2 prices (Price[today] and Price[yesterday]).
        avg_gain (float): The smoothed average gain from the previous calculation. Use -1 for initialization.
        avg_loss (float): The smoothed average loss from the previous calculation. Use -1 for initialization.
        period (int): The lookback period (N) for the RSI calculation.

    Returns
        tuple[float, float, float]: (RSI value, New Avg Gain, New Avg Loss)
    """
    """
    TO BE CHANGED WITH A CLASS THAT SAVES AND UPDATES INTERNALLY THE FOLLOWING QUANTITIES:
        avg_gain
        avg_loss
        period
        value
    """
    if series is None or len(series) == 0:
        logger.error("rsi: empty series or None")
        return float("nan") , -1 , -1
    if len(series.dropna()) < period + 1:
        logger.error("rsi: insuff. data (min %d, found %d)", period + 1, len(series.dropna()))
        return float('nan') , -1 , -1

    smoothing_factor = 1/period

    if avg_gain ==-1 and avg_loss == -1:
        delta = series.diff().tail(period) # computes daily returns
        gain = delta.clip(lower=0) # positive returns
        loss = -delta.clip(upper=0) # negative returns
        avg_gain = gain.mean()
        avg_loss = loss.mean()
    else:
        change = series[-1] - series[-2]
        gain = max(change,0)
        loss = max(-change,0)
        avg_gain = avg_gain + smoothing_factor*(gain - avg_gain)
        avg_loss = avg_loss + smoothing_factor*(loss - avg_loss)


    if avg_loss == 0.0:
        if avg_gain > 0.0:
            RSI =100.0 
        else:
            RSI = 0.0
    elif avg_gain == 0.0 and avg_loss > 0.0:
        RSI = 0.0

    else:
        RS = avg_gain / avg_loss
        RSI = 100 - (100 / (1 + RS))
    

    logger.debug(f'RSI value is {RSI}')
    if not np.isfinite(RSI):
        logger.error("rsi: inf value (%.5f)", RSI)
    return RSI , avg_gain , avg_loss


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
        logger.error("hurst_local: insuff. data (N=%d, min 8)", N)
        return np.nan

    # Range of segment sizes
    max_window = N // 2
    if max_window < 4:
        logger.error("hurst_local: max_window too short (max_window=%d)", max_window)
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
        logger.error("hurst_local: R/S insuff. observations (len=%d)", len(RS_vals))
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
    #### TEMPORANEO
    H = np.random.rand()

    logger.debug(f"H is {H}")
    #### TEMPORANEO
    return H

def composite_rsi(series: pd.Series,avg_gain_short:float , avg_loss_short:float, avg_gain_long:float ,avg_loss_long:float, short: int, long: int) -> float:
    """
    TO BE CHANGED WITH A CLASS THAT SAVES AND UPDATES THE FOLLOWING QUANTITIES INTERNALLY:

        avg_loss_short
        avg_gain_short
        avg_loss_long
        avg_gain_long
        short_period
        long_period
        value

    """
    # weights initialized to 0.5
    if series is None or len(series) == 0:
        logger.error("composite_rsi: empty series or None")
        return float("nan") , -1 , -1 , -1 , -1
    if len(series.dropna()) < long + 1:
        logger.error("composite_rsi: insuff. data for long=%d (found=%d)", long, len(series.dropna()))
    short_rsi, avg_gain_short, avg_loss_short = rsi(series, avg_gain_short, avg_loss_short, period=short)
    long_rsi, avg_gain_long, avg_loss_long = rsi(series, avg_gain_long, avg_loss_long, period=short)
    comp_rsi = (0.5 * short_rsi) + (0.5 * long_rsi)
    logger.debug(f"composite_rsi is {comp_rsi}")
    return comp_rsi , avg_gain_short , avg_loss_short , avg_gain_long , avg_loss_long
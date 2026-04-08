import numpy as np
import pandas as pd

def _wilder_smoothing(series: pd.Series, period: int) -> pd.Series:
    """
    Helper to perform Wilder's smoothing with SMA initialization.
    Matches TradeStation logic: 
    If CurrentBar = 1 then Avg = SMA(series, period)
    Else Avg = Avg[1] + (1/period) * (Value - Avg[1])
    """
    if len(series) < period:
        return pd.Series(index=series.index, dtype=float)
        
    smoothed = np.full(len(series), np.nan)
    sf = 1.0 / period
    
    # First valid bar (index = period-1) is the SMA of the first 'period' values
    first_val = series.iloc[:period].mean()
    smoothed[period-1] = first_val
    
    # Use the recursive formula for the rest
    series_v = series.values
    for i in range(period, len(series)):
        smoothed[i] = smoothed[i-1] + sf * (series_v[i] - smoothed[i-1])
        
    return pd.Series(smoothed, index=series.index)

def rsi(series: pd.Series, period: int = 2) -> pd.Series:
    """
    Compute Relative Strength Index (RSI) using the exact TradeStation EasyLanguage formula.
    SF = 1 / Length
    NetChgAvg = NetChgAvg[1] + SF * (Change - NetChgAvg[1])
    TotChgAvg = TotChgAvg[1] + SF * (Abs(Change) - TotChgAvg[1])
    RSI = 50 * (NetChgAvg / TotChgAvg + 1)
    """
    if series is None or len(series) <= period:
        return pd.Series(index=series.index if series is not None else [], dtype=float).fillna(np.nan)
        
    change = series.diff()
    
    # We drop the first NaN to get clean changes
    change_clean = change.dropna()
    
    net_chg_avg = _wilder_smoothing(change_clean, period)
    tot_chg_avg = _wilder_smoothing(change_clean.abs(), period)
    
    # Realign with original index
    net_chg_avg = net_chg_avg.reindex(series.index)
    tot_chg_avg = tot_chg_avg.reindex(series.index)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        chg_ratio = net_chg_avg / tot_chg_avg
        # Replace infs/NaNs to match TS behavior (divide by zero = 0 ChgRatio)
        chg_ratio = chg_ratio.replace([np.inf, -np.inf], np.nan).fillna(0)
    
    rsi_vals = 50 * (chg_ratio + 1)
    
    # Standardize warmup (RSI is valid from the bar where SMA is first calculated)
    rsi_vals.iloc[:period] = np.nan
    
    return rsi_vals

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Compute Average True Range (ATR) using Wilder's smoothing.
    Note: Standard EL AverageTrueRange(Len) uses SMA, but ATR(Len) uses Wilder.
    """
    if close is None or len(close) == 0:
        return pd.Series(index=close.index if close is not None else [], dtype=float).fillna(np.nan)

    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    tr_clean = tr.dropna()
    
    atr_series = _wilder_smoothing(tr_clean, period)
    atr_series = atr_series.reindex(high.index)
    
    return atr_series

def hurst_exponent(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20) -> pd.Series:
    """
    Fast proxy of Hurst exponent from TradeStation.
    Verification against benchmark shows it uses SMA-based ATR (AvgTrueRange).
    H = 100 * ( log(Highest(High, Len) - Lowest(Low, Len)) - log(SMA_ATR(Len)) ) / log(Len)
    """
    if close is None or len(close) == 0:
        return pd.Series(index=close.index if close is not None else [], dtype=float).fillna(np.nan)

    highest_high = high.rolling(window).max()
    lowest_low = low.rolling(window).min()
    range_hl = highest_high - lowest_low

    # Calculate SMA-based ATR for Hurst parity (TradeStation AvgTrueRange built-in)
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    sma_atr = tr.rolling(window).mean()

    # Compute proxy Hurst
    with np.errstate(divide='ignore', invalid='ignore'):
        hurst = 100 * (np.log(range_hl) - np.log(sma_atr)) / np.log(window)
    
    hurst = hurst.replace([np.inf, -np.inf], 0).fillna(0)
    
    # Standardize warmup
    hurst.iloc[:window] = np.nan 
    
    return hurst

def composite_rsi(series: pd.Series, short: int, long: int, w1: float = 0.5, w2: float = 0.5) -> pd.Series:
    """
    Computes a Weighted Composite RSI. Default is 50/50.
    """
    if series is None or len(series) == 0:
        return pd.Series(index=series.index if series is not None else [], dtype=float).fillna(np.nan)
        
    short_rsi = rsi(series, period=short)
    long_rsi = rsi(series, period=long)
    
    return (w1 * short_rsi) + (w2 * long_rsi)
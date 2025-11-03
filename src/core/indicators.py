import pandas as pd

def rsi(series: pd.Series, period: int) -> pd.Series:
    """
    Compute the Relative Strength Index (RSI) over a given window.
    Input:
    series (pd.Series): Price series (typically close prices).
    period (int): Lookback period for RSI calculation.
    Output:
    pd.Series: RSI values in [0, 100].
    """
    pass
def composite_rsi(series: pd.Series, short: int, long: int) -> pd.Series:
    """
    Compute a smoothed version of the short-term RSI using a long-term mean.
    Input:
    series (pd.Series): Price series.
    short (int): Period for short RSI computation.
    long (int): Period for smoothing (e.g. 24 bars).
    Output:
    pd.Series: Composite RSI series (smoothed momentum indicator).
    """
    pass

def hurst_exponent(series: pd.Series, lookback: int) -> float:
    """
    Estimate the Hurst exponent over a rolling window.
    Input:
    series (pd.Series): Price series.
    lookback (int): Number of points for local estimation.
    Output: 
            float: Hurst exponent (H >0.5 indicates persistence)
    """
    pass
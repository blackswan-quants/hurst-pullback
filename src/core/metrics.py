import pandas as pd
import numpy as np


def max_drawdown(equity_curve: pd.Series) -> float:
    """
    Compute the Maximum Drawdown (MDD).

    Parameters
    -----
    equity_curve : pd.Series
        Time series of cumulative portfolio value (or cumulative returns).

    Returns
    -----
    float
        Maximum drawdown as a negative float (peak-to-trough decline).
    """
    cumulative_max = equity_curve.cummax()
    drawdowns = equity_curve / cumulative_max - 1.0
    return drawdowns.min()


def sharpe_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Compute the annualized Sharpe Ratio.

    Parameters
    -----
    returns : pd.Series
        Series of periodic returns.
    periods_per_year : int
        Sampling frequency (252 daily, 52 weekly, 12 monthly).

    Returns
    -----
    float
        Annualized Sharpe Ratio.
    """
    mean_return = returns.mean()
    std_return = returns.std()

    if std_return == 0:
        return np.nan

    sharpe = (mean_return / std_return) * np.sqrt(periods_per_year)
    return sharpe


def cagr(equity_curve: pd.Series, periods_per_year: int = 252) -> float:
    """
    Compute CAGR (Compound Annual Growth Rate).

    Parameters
    -----
    equity_curve : pd.Series
        Series of cumulative portfolio values.
    periods_per_year : int
        Number of periods in one year.

    Returns
    -----
    float
        CAGR value.
    """
    total_periods = len(equity_curve)

    if total_periods == 0:
        return np.nan

    start = equity_curve.iloc[0]
    end = equity_curve.iloc[-1]

    cagr = (end / start) ** (periods_per_year / total_periods) - 1
    return cagr

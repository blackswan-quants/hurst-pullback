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


def expectancy(trade_returns: pd.Series) -> float:
    """
    Calculate expectancy per trade.

    Parameters
    -----
    trade_returns : pd.Series
        Profit/loss of each trade.

    Returns
    -----
    float
        Expectancy value (average profit per trade).
    """
    wins = trade_returns[trade_returns > 0]
    losses = trade_returns[trade_returns < 0]

    if len(trade_returns) == 0:
        return np.nan

    pw = len(wins) / len(trade_returns)
    pl = len(losses) / len(trade_returns)

    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = abs(losses.mean()) if len(losses) > 0 else 0

    return pw * avg_win - pl * avg_loss


def profit_factor(trade_returns: pd.Series) -> float:
    """
    Compute the Profit Factor.

    Parameters
    -----
    trade_returns : pd.Series
        Profit/loss for each trade.

    Returns
    -----
    float
        Profit Factor (gross profit / gross loss).
    """
    gross_profit = trade_returns[trade_returns > 0].sum()
    gross_loss = trade_returns[trade_returns < 0].sum()

    if gross_loss == 0:
        return np.inf

    return gross_profit / abs(gross_loss)


def equity_curve_smoothness(equity_curve: pd.Series) -> float:
    """
    Compute equity curve smoothness as CAGR / volatility of log-returns.

    Parameters
    -----
    equity_curve : pd.Series
        Cumulative portfolio values.

    Returns
    -----
    float
        Smoothness value (higher = smoother equity).
    """
    log_returns = np.log(equity_curve / equity_curve.shift(1)).dropna()

    vol = log_returns.std()
    if vol == 0 or len(log_returns) < 2:
        return np.nan

    cagr_value = (
        equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (252 / len(equity_curve)) - 1

    return cagr_value / vol


def sortino_ratio(returns: pd.Series, periods_per_year: int = 252, risk_free_rate: float = 0.0) -> float:
    """
    Compute the Sortino Ratio.

    Parameters
    -----
    returns : pd.Series
        Asset or strategy periodic returns.
    periods_per_year : int
        Sampling frequency (252 daily, 52 weekly, 12 monthly).
    risk_free_rate : float
        Annual risk-free rate.

    Returns
    -----
    float
        Annualized Sortino Ratio.
    """
    excess_returns = returns - risk_free_rate / periods_per_year

    downside_returns = excess_returns[excess_returns < 0]

    if len(downside_returns) == 0:
        return np.inf

    downside_std = downside_returns.std()
    mean_excess = excess_returns.mean()

    sortino = (mean_excess / downside_std) * np.sqrt(periods_per_year)

    return sortino


def win_rate(returns: pd.Series) -> float:
    """
    Compute the win rate (percentage of positive returns).

    Parameters
    -----
    returns : pd.Series
        Strategy or asset returns.

    Returns
    -----
    float
        Win rate in [0, 1].
    """
    if len(returns) == 0:
        return np.nan

    wins = (returns > 0).sum()
    return wins / len(returns)

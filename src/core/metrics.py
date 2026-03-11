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

    if total_periods <= 1:
        return np.nan

    start = equity_curve.iloc[0]
    end = equity_curve.iloc[-1]

    if start <= 0:
        return np.nan # Cannot calculate CAGR on a portfolio that blows up starting Capital
        
    years = total_periods / periods_per_year
    cagr_value = (end / start) ** (1 / years) - 1
    return cagr_value


def cumulative_return(returns : pd.Series) -> pd.Series:
    """""
    Compute the cumulative return from the series of periodic returns
    
    Parameters
    --------
    returns: pd.Series
    seires of periodic returns

    Output 
    -------
    cum_factors: pd.Series
    series representing the equity curve  
    """""
    cum_factors = [1.0]
    cum_factor = 1.0
    
    for p in returns:
        if p is None or pd.isna(p):
            cum_factors.append(cum_factor)
            continue
        cum_factor *= (1 + p)
        cum_factors.append(cum_factor)

    return pd.Series(cum_factors, index=returns.index.insert(0, returns.index[0] if len(returns) > 0 else 0) if isinstance(returns.index, pd.DatetimeIndex) else None)


def sortino_ratio(returns: pd.Series, periods_per_year: int = 252, target_return: float = 0.0) -> float:
    """
    Compute the annualized Sortino Ratio.

    Parameters
    -----
    returns : pd.Series
        Series of periodic returns.
    periods_per_year : int
        Sampling frequency (252 daily, 52 weekly, 12 monthly).
    target_return : float
        Minimum acceptable return (MAR). Usually set to 0.

    Returns
    -----
    float
        Annualized Sortino Ratio.
    """
    mean_return = returns.mean()
    downside_returns = returns[returns < target_return]
    
    if len(downside_returns) == 0:
        return np.nan # No downside volatility
        
    downside_std = downside_returns.std()
    if downside_std == 0:
        return np.nan
        
    sortino = ((mean_return - target_return) / downside_std) * np.sqrt(periods_per_year)
    return sortino

def calmar_ratio(cagr_val: float, mdd: float) -> float:
    """
    Compute the Calmar Ratio.
    
    Parameters
    -----
    cagr_val: float
        The Compound Annual Growth Rate of the strategy.
    mdd: float
        The Maximum Drawdown (as a negative float).
        
    Returns
    -----
    float
        The Calmar Ratio value.
    """
    if pd.isna(mdd) or mdd == 0:
        return np.nan
    return cagr_val / abs(mdd)


def win_rate(returns: pd.Series) -> float:
    """
    Computes the percentage of winning trades.
    
    Parameters
    -----
    returns: pd.Series
        Series of trade returns (not periodic bar returns, but actual trade profits).
        
    Returns
    -----
    float
        The percentage decimal [0.0, 1.0] representing wins.
    """
    if len(returns) == 0:
        return np.nan
    
    wins = len(returns[returns > 0])
    return wins / len(returns)

def profit_factor(returns: pd.Series) -> float:
    """
    Computes the ratio of gross profit from winning trades to the gross loss of losing trades.
    
    Parameters
    -----
    returns: pd.Series
        Series of trade returns.
        
    Returns
    -----
    float
        The Profit Factor.
    """
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    
    gross_profit = wins.sum()
    gross_loss = abs(losses.sum())
    
    if gross_loss == 0:
        return np.nan if gross_profit == 0 else float('inf')
        
    return gross_profit / gross_loss

def avg_win_avg_loss(returns: pd.Series) -> tuple:
    """
    Computes the average winning trade return and average losing trade return.
    
    Parameters
    -----
    returns: pd.Series
        Series of trade returns.
        
    Returns
    -----
    tuple
        (average_win, average_loss)
    """
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    
    avg_win = wins.mean() if not wins.empty else 0.0
    avg_loss = losses.mean() if not losses.empty else 0.0
    
    return avg_win, avg_loss

def expectancy(returns: pd.Series) -> float:
    """
    Computes the statistical expectancy of a trade.
    Expectancy = (Win % * Average Win) - (Loss % * Average Loss Value (Positive))
    
    Parameters
    -----
    returns: pd.Series
        Series of trade returns.
        
    Returns
    -----
    float
        The expectancy relative unit per trade.
    """
    if len(returns) == 0:
        return np.nan
        
    w_rate = win_rate(returns)
    l_rate = 1.0 - w_rate
    
    avg_w, avg_l = avg_win_avg_loss(returns)
    
    return (w_rate * avg_w) - (l_rate * abs(avg_l))

import pandas as pd
import numpy as np
from src.core import metrics

def vectorized_run(df, params, drag=0.5, start_date=None, end_date=None):
    """
    Centralized high-performance backtest engine.
    Expects df to have: 'rsi', 'hurst', 'composite_rsi'
    Params needs: 'rsi_low', 'rsi_high', 'hurst_threshold', 
                 'max_profitable_closes', 'composite_rsi_threshold', 'max_bars_in_trade'
    """
    rsi_vals = df['rsi'].values
    hurst_vals = df['hurst'].values
    comp_rsi_vals = df['composite_rsi'].values
    closes = df['Close'].values
    opens = df['Open'].values
    
    # Entry: RSI in range AND Hurst > threshold
    # Note: Logic checks previous bar close for current bar open entry
    entry_signal = (rsi_vals >= params['rsi_low']) & (rsi_vals <= params['rsi_high']) & (hurst_vals > params['hurst_threshold'])
    
    # Pre-calculate profitable closes exit condition
    is_prof = (closes > opens).astype(int)
    n_prof = params['max_profitable_closes']
    prof_exit_mask = pd.Series(is_prof).rolling(n_prof).sum() == n_prof
    prof_exit_v = prof_exit_mask.values
    
    # Pre-calculate RSI exit
    rsi_exit_v = (comp_rsi_vals > params['composite_rsi_threshold'])
    
    trades = []
    in_pos = False
    entry_idx = 0
    max_bars = params['max_bars_in_trade']
    
    for i in range(1, len(df)):
        if not in_pos:
            if entry_signal[i-1]:
                in_pos = True
                entry_idx = i
                entry_price = opens[i]
        else:
            bars_in_trade = i - entry_idx + 1
            if bars_in_trade >= max_bars or rsi_exit_v[i] or (bars_in_trade >= n_prof and prof_exit_v[i]):
                exit_idx = i + 1
                if exit_idx < len(df):
                    exit_price = opens[exit_idx]
                else:
                    exit_price = closes[i]
                
                profit = ((exit_price - entry_price) - drag) / entry_price
                trades.append({'profit': profit, 'bars': bars_in_trade})
                in_pos = False
    
    if not trades:
        return {'trades': [], 'sharpe': -10.0, 'profit': 0.0, 'equity': pd.Series([1.0]*len(df))}
    
    t_df = pd.DataFrame(trades)
    eq = metrics.cumulative_return(t_df['profit'])
    sharpe = metrics.sharpe_ratio(t_df['profit'], start_date=start_date, end_date=end_date)
    
    return {
        'trades': trades,
        'sharpe': sharpe if not np.isnan(sharpe) else -10.0,
        'profit': (eq.iloc[-1] - 1.0) * 100,
        'equity': eq
    }

import pandas as pd
from ..strategy.strategy import Strategy
from .indicators import *
import yaml 
from pathlib import Path


def run(df: pd.DataFrame, strategy: Strategy) -> dict:
    """
    Execute a vectorized backtest using the provided strategy object.
    Input:
    df (pd.DataFrame): OHLCV dataset with indicators.
    strategy (Strategy): Instance of Strategy class containing logic.
    Output:
    dict:
    {
    "equity": float, # Final cumulative equity
    "n_trades": int, # Number of completed trades
    "trades": list[float] # Individual trade returns
    }
    """
    # getting strategy settings
    config_path = Path(__file__).parent.parent.parent / "configs" / "base.yaml"
    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
    lookback_rsi = data['indicators']['rsi_period']
    short_composite_rsi = 2  # default value, not in config
    long_composite_rsi = 24  # default value, not in config
    lookback_hurst = data['indicators']['hurst_window']
    ######

    i = 0
    df['rsi'] = 0.0
    df['composite_rsi'] = 0.0
    df['hurst'] = 0.0
    df['open_position'] = False

    all_trades = []
    trade = {
        'open': "",         
        'close': "",       
        'profit': 0.0,      
        'price': 0.0
    }
    signal = 'flat'
    state = {
        'bars': 0,
        'entry_price': 0.0,
        'prof_x': 0
    }

    while i < len(df):
        # indicators calculation 
        rsi_series = rsi(df['close'], lookback_rsi)
        comp_rsi_series = composite_rsi(df['close'], short_composite_rsi, long_composite_rsi)
        hurst_series = hurst_exponent(df['close'], lookback_hurst)
        df.loc[i, 'rsi'] = rsi_series.iloc[i] if i < len(rsi_series) else 0.0
        df.loc[i, 'composite_rsi'] = comp_rsi_series.iloc[i] if i < len(comp_rsi_series) else 0.0
        df.loc[i, 'hurst'] = hurst_series.iloc[i] if i < len(hurst_series) else 0.0
        
        # signal checking
        if signal == 'buy':
            # apriamo la posizione e inizializziamo il trade
            df.loc[i, 'open_position'] = True
            trade['open'] = df.index[i]
            trade['price'] = df.iloc[i]['open'] if 'open' in df.columns else df.iloc[i, 0]
            state['bars'] = 0
            state['entry_price'] = trade['price']
            state['prof_x'] = 0
            signal = 'flat'
        
        elif signal == 'sell':
            # chiudiamo la posizione e calcoliamo il profitto 
            df.loc[i, 'open_position'] = False
            trade['close'] = df.index[i]
            exit_price = df.iloc[i]['close'] if 'close' in df.columns else df.iloc[i, 3]
            trade['profit'] = (exit_price - trade['price']) / trade['price']
            all_trades.append(trade.copy())
            # reset trade and state
            trade = {
                'open': "",         
                'close': "",       
                'profit': 0.0,      
                'price': 0.0
            }
            state['bars'] = 0
            state['entry_price'] = 0.0
            state['prof_x'] = 0
            signal = 'flat'

        else:
            # get current position state
            if i > 0:
                df.loc[i, 'open_position'] = df.loc[i-1, 'open_position']
            else:
                df.loc[i, 'open_position'] = False
            
            if df.loc[i, 'open_position'] == True:
                # update state for position tracking
                state['bars'] += 1
                current_close = df.iloc[i]['close'] if 'close' in df.columns else df.iloc[i, 3]
                if current_close > state['entry_price']:
                    state['prof_x'] += 1
                else:
                    state['prof_x'] = 0
                
                # check exit signal
                should_exit = strategy.exit_signal(df, i, state)
                if should_exit:
                    signal = 'sell'
                else:
                    signal = 'flat'

            elif df.loc[i, 'open_position'] == False:
                # check entry signal
                should_enter = strategy.entry_signal(df, i, state)
                if should_enter:
                    signal = 'buy'
                else:
                    signal = 'flat'

        i = i + 1
    
    # close any open position at the end
    if df.loc[len(df)-1, 'open_position'] == True:
        last_idx = len(df) - 1
        trade['close'] = df.index[last_idx]
        exit_price = df.iloc[last_idx]['close'] if 'close' in df.columns else df.iloc[last_idx, 3]
        trade['profit'] = (exit_price - trade['price']) / trade['price']
        all_trades.append(trade.copy())
    
    # calculate equity and return results
    initial_equity = 1.0
    equity = initial_equity
    trade_returns = []
    for t in all_trades:
        trade_returns.append(t['profit'])
        equity = equity * (1 + t['profit'])
    
    return {
        "equity": equity,
        "n_trades": len(all_trades),
        "trades": trade_returns
    }


# slippage 
# equity allocation 
# fees




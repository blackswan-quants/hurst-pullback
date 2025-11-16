import pandas as pd
from ..strategy.strategy import Strategy
from indicators import *
import yaml 



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
    with open('../../configs/base.yaml' , 'r') as file:
        data = yaml.safe_load(file)
    lookback_rsi = data[]
    short_composite_rsi = data[] 
    long_composite_rsi = data[]
    lookback_hurst = data[]
    ######

    i=0
    df['rsi'] = 0.0
    df['composite_rsi'] = 0.0
    df['hurst'] = 0.0
    df['open_position'] = False


    all_trades = []
    trade = {
        'open': "",         
        'close': "",       
        'profit': 0.0,      
        'price' : 0.0
    }
    signal = 'flat'

    while i<len(df):
        # indicators calculation 
        df.loc[i,'rsi'] = rsi(df['close'] , lookback_rsi)
        df.loc[i,'composite_rsi'] = composite_rsi(df['close'], short_composite_rsi , long_composite_rsi)
        df.loc[i,'hurst'] = hurst_exponent(df['close'] , lookback_hurst)
        #signal checking
        if signal == 'buy':
            #apriamo la posizione e inizializziamo il trade
            df.loc[i,'open_position'] = True
            trade['open'] = df.index[i]
            trade['price'] = df.iloc[i, 'open']
            signal = 'flat'
            
        
        if signal == 'sell':
            #chiudiamo la posizione e calcoliamo il profitto 
            df.loc[i,'open_position'] = False
            trade['close'] = df.iloc[i].index
            trade['profit'] = (df.iloc[i,'open'] - trade['price']) / trade['price']
            signal = 'flat'
            all_trades.append(trade)


        else:
            df.loc[i,'open_position'] = df.loc[i-1, 'open_position']
            if df.loc[i,'open_position'] == True:
                signal = strategy.exit_signal(df, i)

            elif df.loc[i,'open_position']==False:
                signal = strategy.entry_signal(df, i )

        i=i+1
    return


# slippage 
# equity allocation 
# fees




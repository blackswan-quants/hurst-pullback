import pandas as pd
from ..strategy.strategy import Strategy
from .indicators import *
import yaml 

# strategy initialized in run backtest function

def translator(signal : bool, info : str) -> str:
    if not signal:
        return 'flat'
    if info=='exit':
        return 'sell'
    else:
        return 'buy'

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
    # getting strategy settings via strategy object
    cfg = strategy.get_cfg()
    lookback_rsi = cfg['indicators']['rsi_period']
    short_composite_rsi = 2
    long_composite_rsi = 24
    lookback_hurst = cfg['indicators']['hurst_window']
    ######

    i=0
    df['rsi'] = 0.0
    df['composite_rsi'] = 0.0
    df['hurst'] = 0.0
    df['open_position'] = False


    all_trades = []
    trade = {}

    signal = 'flat'
    # Get close column - handle both 'Close' and 'close'
    close_col = 'Close' if 'Close' in df.columns else 'close'
    df['rsi'] = rsi(df[close_col], lookback_rsi)
    df['composite_rsi'] = composite_rsi(df[close_col], short_composite_rsi, long_composite_rsi)
    df['hurst'] = hurst_exponent(df[close_col], lookback_hurst)
    print(df.tail(10))

    while i<len(df):
        print("signal: ", signal)
        # indicators calculation 
        #signal checking
        if signal == 'buy':
            #apriamo la posizione e inizializziamo il trade
            df.loc[i,'open_position'] = True
            trade['open_date'] = df.index[i]
            # Access column by name - try both 'Open' and 'open'
            if 'Open' in df.columns:
                trade['entry_price'] = df.iloc[i]['Open']
            elif 'open' in df.columns:
                trade['entry_price'] = df.iloc[i]['open']
            else:
                trade['entry_price'] = df.iloc[i, 0]  # fallback to first column
            trade['bars']=1
            signal = 'flat'
            
        
        elif signal == 'sell':
            #chiudiamo la posizione e calcoliamo il profitto 
            df.loc[i,'open_position'] = False
            trade['close_date'] = df.index[i]
            # Access column by name - try both 'Open' and 'open'
            if 'Open' in df.columns:
                trade['sell_price'] = df.iloc[i]['Open']
                exit_price = df.iloc[i]['Open']
            elif 'open' in df.columns:
                trade['sell_price'] = df.iloc[i]['open']
                exit_price = df.iloc[i]['open']
            else:
                trade['sell_price'] = df.iloc[i, 0]  # fallback to first column
                exit_price = df.iloc[i, 0]
            trade['profit'] = (exit_price - trade['entry_price']) / trade['entry_price']
            signal = 'flat'
            all_trades.append(trade)
            trade = {}


        else:
            if i!=0:
                df.loc[i,'open_position'] = df.loc[i-1, 'open_position']

            if not trade.get('bars',0)==0:
                trade['bars'] +=1
                
            if df.loc[i,'open_position'] == True:
                signal = strategy.exit_signal(df, i, trade) 
                signal = translator(signal, 'exit')

            elif df.loc[i,'open_position']==False:
                signal = strategy.entry_signal(df, i, trade) # trade non serve
                signal = translator(signal,'entry')

        if i >= len(df):
            break
        i=i+1
    return all_trades





# modificato il dizionario trade per conteggiare anche il numero di barre e modificato i nomi delle chiavi 
# per renderle consistenti con il codice di strategy 

# coddato la funzione run_backtest 

# DOMANDE

# DONE non conviene modificare semplicemente il codice di gabri e restituire flat/buy/sell ?

# rsi e composite rsi dovrebbero restituire un valore unico -> vanno cambiate le funzioni
# inoltre gli errori conviene handlarli dentro quelle funzioni non in engine

# mancano short e long parametri di composite_rsi in configs_yaml 

# DONE funzioni di dimarco completamente sbagliate


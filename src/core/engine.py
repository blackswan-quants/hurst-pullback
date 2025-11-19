import pandas as pd
from ..strategy.strategy import Strategy
from indicators import *
import yaml 

# strategy initialized in run backtest function

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
    lookback_rsi = strategy.get_cfg()['rsi_period']
    short_composite_rsi = strategy.get_cfg()['UNDEFINED']
    long_composite_rsi = strategy.get_cfg()['UNDEFINED']
    lookback_hurst = strategy.get_cfg()['hurst_window']
    ######

    i=0
    df['rsi'] = 0.0
    df['composite_rsi'] = 0.0
    df['hurst'] = 0.0
    df['open_position'] = False


    all_trades = []
    trade = {
        'open_date': "",         
        'close_date': "",       
        'prof_x': 0.0,      
        'entry_price' : 0.0,
        'sell_price': 0.0,
        'profit': 0.0,
        'bars' : 0
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
            trade['open_date'] = df.index[i]
            trade['entry_price'] = df.iloc[i, 'open']
            trade['bars']=1
            trade['prof_x'] = 0
            signal = 'flat'
            
        
        if signal == 'sell':
            #chiudiamo la posizione e calcoliamo il profitto 
            df.loc[i,'open_position'] = False
            trade['close_date'] = df.iloc[i].index
            trade['sell_price'] = df.iloc[i, 'open']
            trade['profit'] = (df.iloc[i,'open'] - trade['entry_price']) / trade['entry_price']
            signal = 'flat'
            all_trades.append(trade)
            trade = {}


        else:
            df.loc[i,'open_position'] = df.loc[i-1, 'open_position']

            if not trade.get('bars',0)==0:
                trade['bars'] +=1
            if trade.get('prof_x'):
                if df.iloc[i,'open'] > trade['entry_price']:
                    trade['prof_x'] +=1
                else:
                    trade['prof_x']=0
                
            if df.loc[i,'open_position'] == True:
                signal = strategy.exit_signal(df, i, trade) #trade non serve

            elif df.loc[i,'open_position']==False:
                signal = strategy.entry_signal(df, i, trade)

        i=i+1
    return all_trades





# modificato il dizionario trade per conteggiare anche il numero di barre e modificato i nomi delle chiavi 
# per renderle consistenti con il codice di strategy 

# coddato la funzione run_backtest 

# DOMANDE

# non conviene modificare semplicemente il codice di gabri e restituire flat/buy/sell ?

# rsi e composite rsi dovrebbero restituire un valore unico -> vanno cambiate le funzioni
# inoltre gli errori conviene handlarli dentro quelle funzioni non in engine

# mancano short e long parametri di composite_rsi in configs_yaml 

# funzioni di dimarco completamente sbagliate

# prof x quindi si intende il numero di giorni consecutivi di profitto ?
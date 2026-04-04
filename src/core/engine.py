import pandas as pd
from ..strategy.strategy import Strategy
from .indicators import *

def translator(signal: bool, info: str) -> str:
    """
    Translate boolean output of entry and exit signal functions into trading signals
    Input:
    signal (bool) : if True it signals to execute the trade (either sell or buy), if False to stay flat
    info (str) : it specifies whether the signal has been returned from the exit function or the entry one
    Output:
    str : either buy , sell or flat
    """
    if not signal:
        return 'flat'
    if info == 'exit':
        return 'sell'
    elif info == 'entry':
        return 'buy'


def run(df: pd.DataFrame, strategy: Strategy) -> dict:
    """
    Execute a vectorized backtest using the provided strategy object.

    The function processes the OHLCV (Open, High, Low, Close, Volume) data 
    along with calculated indicators, applies the entry and exit logic defined 
    in the Strategy object, and simulates trades over the entire dataset.

    Input:
    df (pd.DataFrame): The OHLCV dataset.
    strategy (Strategy): An instance of a Strategy class containing the specific 
                         trading logic (entry/exit conditions) and parameters.

    Output:
    list of dictionaries: A list where each dictionary represents a closed trade. 
                          The keys in each trade dictionary include:
        {
        'open_date': The datetime when the trade (purchase) was initiated.
        'close_date': The datetime when the trade (sale) was closed.
        'entry_price': The price at which the asset was bought.
        'sell_price': The price at which the asset was sold.
        'profit': The percentage return on the trade 
                      (e.g., (sell_price / entry_price - 1)).
        'bars': The number of bars each trade was active for.
        }
    """
    try:
        # getting strategy settings via strategy object
        cfg = strategy.get_cfg()
        lookback_rsi = cfg['indicators']['rsi_period']
        short_composite_rsi = cfg['indicators']['short_composite_rsi']
        long_composite_rsi = cfg['indicators']['long_composite_rsi']
        lookback_hurst = cfg['indicators']['hurst_window']
    except Exception as e:
        print(f"Failed to load data from strategy: {e}")
        return {}  # Return empty if config fails

    # dataframe columns initialization and indicator pre-computation
    # Force a copy to avoid SettingWithCopyWarnings from incoming df slices
    df = df.copy()
    
    if 'rsi' not in df.columns:
        df['rsi'] = rsi(df['Close'], lookback_rsi)
        
    if 'composite_rsi' not in df.columns:
        df['composite_rsi'] = composite_rsi(df['Close'], short_composite_rsi, long_composite_rsi)
        
    if 'hurst' not in df.columns:
        df['hurst'] = hurst_exponent(df['High'], df['Low'], df['Close'], lookback_hurst)
        
    df['open_position'] = False

    # while loop parameters initialization
    all_trades = []
    trade = {}
    i = 0
    signal = 'flat'
<<<<<<< HEAD

    # indicator engines initialization
    rsi_engine = RSIIndicator(period=lookback_rsi)
    comp_engine = CompositeRSIIndicator(
        short_period=short_composite_rsi, long_period=long_composite_rsi)

    # computing the indicators on the whole dataset
    '''try:
        df['rsi'] = rsi(df['Close'], lookback_rsi)
        df['composite_rsi'] = composite_rsi(
            df['Close'], short_composite_rsi, long_composite_rsi)
        df['hurst'] = hurst_exponent(df['Close'], lookback_hurst)
    except Exception as ind_err:
        logger.warning(f"Indicator failure: {ind_err}")
        return {}
        '''

    try:
        while i < len(df):
            logger.debug(f'Column number {i}')
            try:
                df.loc[i, 'rsi'] = rsi_engine.compute(df['Close'].iloc[:i+1])
                df.loc[i, 'composite_rsi'] = comp_engine.compute(
                    df['Close'].iloc[:i+1])
                df.loc[i, 'hurst'] = hurst_exponent(
                    df['Close'][:i], lookback_hurst)
            except Exception as e:
                logger.warning(f"Indicator failure : {e}")

=======

    try:
        while i < len(df):
            # Current row label
            idx_label = df.index[i]
            
>>>>>>> origin/main
            # signal checking
            if signal == 'buy':
                # open the position and initialize the trade dictionary
                df.loc[idx_label, 'open_position'] = True
                trade['open_date'] = idx_label
                trade['entry_price'] = df.iloc[i]['Open']
                trade['bars'] = 1
                signal = 'flat'

            elif signal == 'sell':
                # close the position, store the trade and calculate the profit
                df.loc[idx_label, 'open_position'] = False
                trade['close_date'] = idx_label
                trade['sell_price'] = df.iloc[i]['Open']
                
                # Apply Point Drag (Transaction Costs)
                drag = cfg.get('transaction_costs', {}).get('round_trip_point_drag', 0.0)
                net_price_diff = (trade['sell_price'] - trade['entry_price']) - drag
                
                trade['profit'] = net_price_diff / trade['entry_price']
                signal = 'flat'
                all_trades.append(trade)
                trade = {}

            else:
                if i != 0:
                    prev_label = df.index[i-1]
                    df.loc[idx_label, 'open_position'] = df.loc[prev_label, 'open_position']

                if not trade.get('bars', 0) == 0:
                    trade['bars'] += 1

                try:
                    if df.loc[idx_label, 'open_position'] == True:
                        decision, reason = strategy.exit_signal(df, i, trade)
                        trade['exit_reason'] = reason
                        signal = translator(decision, 'exit')

                    elif df.loc[idx_label, 'open_position'] == False:
                        signal = strategy.entry_signal(df, i, trade)
                        signal = translator(signal, 'entry')
                except Exception as sig_err:
                    print(f"Signal evaluation failure at index {i}: {sig_err}")
                    signal = 'flat'  # Default to flat on error
            if i >= len(df):
                break
            i = i+1
    except Exception as e:
        print(f"Engine failure at index {i}: {e}")
        raise e
    
    return all_trades

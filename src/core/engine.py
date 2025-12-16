import pandas as pd
from ..strategy.strategy import Strategy
from .indicators import *
import yaml
import logging

logger = logging.getLogger('engine')


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
        'net_entry_price': The price at which the asset was bought computed with commission.
        'sell_price': The price at which the asset was sold.
        'net_sell_price': The price at which the asset was sold considering also commission.
        'profit': The percentage return on the trade 
                      (e.g., (sell_price / entry_price - 1)).
        'net_profit': The percentage return on the trade considering also commission.
        'bars': The number of bars each trade was active for.
        'commission_cost': The cost paid for each position opened.
        'slippage_cost': The slippage cost when closing position. 
        }
    """
    logger.info(f"Starting backtest on {len(df)} rows.")
    try:
        # getting strategy settings via strategy object
        cfg = strategy.get_cfg()
        lookback_rsi = cfg['indicators']['rsi_period']
        short_composite_rsi = cfg['indicators']['short_composite_rsi']
        long_composite_rsi = cfg['indicators']['long_composite_rsi']
        lookback_hurst = cfg['indicators']['hurst_window']
        commission_per_contract = cfg['transaction_costs']['commission_per_contract']
        contract_size = cfg['transaction_costs']['contract_size']
        slippage_per_contract = cfg['transaction_costs']['slippage_per_contract']
        ######
    except Exception as e:
        logger.error(f"Failed to load data from strategy: {e}")
        return {}  # Return empty if config fails

    # dataframe columns initialization
    df['rsi'] = 0.0
    df['composite_rsi'] = 0.0
    df['hurst'] = 0.0
    df['open_position'] = False

    # while loop parameters initialization
    all_trades = []
    trade = {}
    i = 0
    signal = 'flat'
    avg_loss = -1
    avg_gain = -1
    avg_loss_short = -1
    avg_gain_short = -1
    avg_loss_long = -1
    avg_gain_long = -1

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
                df.loc[i, 'rsi'] , avg_gain , avg_loss = rsi(df['Close'][:i], avg_gain , avg_loss, lookback_rsi)
                df.loc[i, 'composite_rsi'] , avg_gain_short, avg_loss_short , avg_gain_long , avg_loss_long = composite_rsi(df['Close'][:i],avg_gain_short, avg_loss_short , avg_gain_long , avg_loss_long, short_composite_rsi, long_composite_rsi)
                df.loc[i, 'hurst'] = hurst_exponent(df['Close'][:i], lookback_hurst)
            except Exception as e:
                logger.warning(f"Indicator failure : {e}")
        
            # signal checking
            if signal == 'buy':
                # open the position and initialize the trade dictionary
                df.loc[i, 'open_position'] = True
                trade['open_date'] = df.index[i]
                trade['entry_price'] = df.iloc[i]['Open']
                trade['net_entry_price'] = df.iloc[i]['Open'] + (commission_per_contract / contract_size)
                trade['bars'] = 1
                signal = 'flat'
                logger.info(
                    f"OPEN TRADE at {df.index[i]} at price {trade['entry_price']}")

            elif signal == 'sell':
                # close the position, store the trade and calculate the profit
                df.loc[i, 'open_position'] = False
                trade['close_date'] = df.index[i]
                trade['sell_price'] = df.iloc[i]['Open']
                trade['net_sell_price'] = df.iloc[i]['Open'] - (commission_per_contract + slippage_per_contract) / contract_size
                trade['profit'] = (trade['sell_price'] -
                                   trade['entry_price']) / trade['entry_price']
                trade['net_profit'] = (trade['net_sell_price'] -
                                   trade['net_entry_price']) / trade['net_entry_price']
                trade['commission_cost'] = 2 * (commission_per_contract / contract_size)
                trade['slippage_cost'] = (slippage_per_contract / contract_size)
                signal = 'flat'
                all_trades.append(trade)
                logger.info(
                    f"CLOSE TRADE at {df.index[i]} at price {trade['sell_price']}. Profit: {trade['profit']:.4f}")
                trade = {}

            else:
                if i != 0:
                    df.loc[i, 'open_position'] = df.loc[i-1, 'open_position']

                if not trade.get('bars', 0) == 0:
                    trade['bars'] += 1

                try:
                    if df.loc[i, 'open_position'] == True:
                        signal = strategy.exit_signal(df, i, trade)
                        signal = translator(signal, 'exit')

                    elif df.loc[i, 'open_position'] == False:
                        signal = strategy.entry_signal(df, i, trade)
                        signal = translator(signal, 'entry')
                except Exception as sig_err:
                    logger.warning(
                        f"Signal evaluation failure at index {i}: {sig_err}")
                    signal = 'flat'  # Default to flat on error
            if i >= len(df):
                break
            i = i+1
    except Exception as e:
        logger.critical(f"Engine failure at index {i}: {e}", exc_info=True)
        raise e
    logger.info(f"Backtest finished. Total trades: {len(all_trades)}")
    return all_trades

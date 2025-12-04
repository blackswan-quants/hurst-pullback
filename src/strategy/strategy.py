import pandas as pd
from .signals.rsi2 import long_entry
from .signals.hurst_filter import allow
from .exits.time_exit import should_exit
from .exits.profitable_close_exit import should_exit as prof_exit
from .signals.composite_rsi_exit import should_exit as rsi_exit
import logging

logger_entry = logging.getLogger('strategy_entry')
logger_exit = logging.getLogger('strategy_exit')



class Strategy:
    """
    Main orchestrator class that manages entry and exit signals
    according to parameters and ablation settings.
    Attributes:
    cfg (dict): Loaded configuration dictionary.
    """
    __cfg: dict

    def __init__(self, cfg: dict):
        """
        Initialize strategy with configuration parameters.
        """
        # Check for nested config values
        if 'ablation' not in cfg:
            logger_exit.error("Ablation settings absent, check yaml file!")
        else:
            self.ablation = cfg.get('ablation', {})
            if 'use_hurst' not in self.ablation or not self.ablation['use_hurst']:
                logger_exit.info("use_hurst exit logic disabled")
            if 'use_composite_rsi' not in self.ablation or not self.ablation['use_composite_rsi']:
                logger_exit.info("use_composite_rsi exit logic disabled")
            if 'use_time_exit' not in self.ablation or not self.ablation['use_time_exit']:
                logger_exit.info("use_time_exit exit logic disabled")
            if 'use_RSI_exit' not in self.ablation or not self.ablation['use_RSI_exit']:
                logger_exit.info("use_RSI_exit exit logic disabled")
            if 'use_take_profit' not in self.ablation or not self.ablation['use_take_profit']:
                logger_exit.info("use_take_profit exit logic disabled")
            
        if 'exit_thresholds' not in cfg:
            logger_exit.error("Exit thresholds parameters absent, check yaml file!")
        else:
            self.exit_thresholds = cfg.get('exit_thresholds', {})
            if (self.ablation['use_take_profit']) and ('max_profitable_closes' not in self.exit_thresholds or not self.exit_thresholds['max_profitable_closes']):
                logger_exit.error("max_profitable_closes exit logic is absent")
            if (self.ablation['use_time_exit']) and ('max_bars_in_trade' not in self.exit_thresholds or not self.exit_thresholds['max_bars_in_trade']):
                logger_exit.error("max_bars_in_trade exit logic is absent")
            if (self.ablation['use_RSI_exit']) and ('composite_rsi_threshold' not in self.exit_thresholds or not self.exit_thresholds['composite_rsi_threshold']):
                logger_exit.error("composite_rsi_threshold exit logic is absent")

        if 'entry_thresholds' not in cfg:
            logger_exit.error("Entry thresholds parameters absent, check yaml file! ")
        else:
            self.entry_thresholds = cfg.get('entry_thresholds', {})
            if (self.ablation['use_composite_rsi']) and ('rsi_low' not in self.entry_thresholds or not self.entry_thresholds['rsi_low']):
                logger_entry.error("rsi_low entry logic is absent")
            if (self.ablation['use_composite_rsi']) and ('rsi_high' not in self.entry_thresholds or not self.entry_thresholds['rsi_high']):
                logger_entry.error("rsi_high entry logic is absent")
            if (self.ablation['use_hurst']) and ('hurst_threshold' not in self.entry_thresholds or not self.entry_thresholds['hurst_threshold']):
                logger_entry.error("hurst_threshold entry logic is absent")
        self.__cfg = cfg

    def get_cfg(self) -> dict:
        """
        Getter method for configuation parameters.
        Output:
        dict: The configuration parameters.
        """
        return self.__cfg

    def set_cfg(self, new_cfg: dict):
        """
        Setter method for configuration parameters.
        Input:
        new_cfg (dict): new configurations
        """
        self.__cfg = new_cfg

    def entry_signal(self, df: pd.DataFrame, i: int, state: dict) -> bool:
        """
        Evaluate entry conditions for the current bar.
        Input:
        df (pd.DataFrame): DataFrame with indicators.
        i (int): Current bar index.
        state (dict): Position state (flat or long).
        logging_flag (bool): Enable logging.
        Output:
        bool: True if long entry condition is met.
        """
        try:
            if i >= len(df):
                return False

            long_entry_check = True
            # Get entry thresholds config
            entry_cfg = self.entry_thresholds

            # RSI check
            if (self.ablation['use_rsi']) and ('rsi' in df.columns and 'rsi_low' in entry_cfg and 'rsi_high' in entry_cfg):
                if pd.isna(df.iloc[i]['rsi']):
                    logger_entry.warning(
                        f"Signal Invalidated at index {i}: RSI is NaN")
                    return False

                if not long_entry(df, i, entry_cfg):
                    long_entry_check = False
                    logger_entry.info(
                        "NO ENTRY: RSI indicators was NOT between 10 ad 20.")
            elif not (self.ablation['use_rsi']):
                logger_entry.debug('RSI entry signal is disabled')
            elif 'rsi' not in df.columns:
                logger_entry.error('RSI is NOT in the Dataframe!')
                long_entry_check = False
            elif 'rsi_low' not in entry_cfg:
                logger_entry.error(
                    'Parameters dictionary does NOT contain rsi_low! ')
                long_entry_check = False
            elif 'rsi_high' not in entry_cfg:
                logger_entry.error(
                    'Parameters dictionary does NOT contain rsi_high! ')
                long_entry_check = False

            # Hurst check
            if (self.ablation['use_hurst']) and ('hurst' in df.columns and 'hurst_threshold' in entry_cfg):
                if pd.isna(df.iloc[i]['hurst']):
                    logger_entry.warning(
                        f"Signal Invalidated at index {i}: Hurst is NaN")
                    return False

                if long_entry_check and not allow(df, i, entry_cfg):
                    long_entry_check = False
                    logger_entry.info(
                        "NO ENTRY: Hurst filter is NOT above the threshold.")
            elif not self.ablation['use_hurst']:
                logger_entry.debug('Hurst entry signal is disabled')
            elif 'hurst_threshold' not in entry_cfg:
                logger_entry.error(
                    "Parameters dictionary does NOT contain hurst threshold!")
                long_entry_check = False
            elif 'hurst' not in df.columns:
                logger_entry.error('Hurst exponent is NOT in the dataframe!')
                long_entry_check = False

            return long_entry_check

        except Exception as e:
            logger_entry.error(
                f"Strategy Entry Crash at index {i}: {e}", exc_info=True)
            return False

    def exit_signal(self, df: pd.DataFrame, i: int, state: dict) -> bool:
        """
        Evaluate exit conditions for an open trade.
        Input:
        df (pd.DataFrame): DataFrame with indicators.
        i (int): Current bar index.
        state (dict): Dictionary containing current position info.
        logging_flag (bool): Enable logging.
        Output:
        bool: True if exit condition is met.
        """
        try:
            if i >= len(df):
                return False

            exit_position = False
            # Get exit_thresholds config
            exits_cfg = self.exit_thresholds

            # Time exit check
            if 'bars' not in state.keys():
                logger_exit.error("'bars' number is NOT in state dictionary!")
            elif not(self.ablation['use_time_exit']):
                logger_exit.debug('max time exit signal is disabled')
            elif 'max_bars_in_trade' not in exits_cfg:
                logger_exit.error(
                    "The parameters 'max_bars_in_trade' is NOT in the configuration dictionary!")
            elif should_exit(state, exits_cfg):
                exit_position = True
                logger_exit.info(
                    f"EXIT SIGNAL: the maximum bars in trade is reached")

            # profit exit check
            if not exit_position:
                if 'entry_price' not in state.keys():
                    logger_exit.error("'entry_price' is NOT in state dictionary!")
                elif not self.ablation['use_take_profit']:
                    logger_exit.debug('take profit exit signal is disabled')
                elif 'bars' not in state.keys():
                    logger_exit.error("'bars' is NOT in state dictionary!")
                elif 'max_profitable_closes' not in exits_cfg:
                    logger_exit.error(
                        "The parameters 'max_profitable_closes' is NOT in the configuration dictionary!")
                elif prof_exit(df, i, state, exits_cfg):
                    exit_position = True
                    logger_exit.info(
                        f"EXIT SIGNAL: the position was profitable for {exits_cfg['max_profitable_closes']} days.")

            # composite rsi check
            if not exit_position:
                if 'composite_rsi' not in df.columns:
                    logger_exit.error("'composite_rsi' is NOT in the dataframe!")
                elif not(self.ablation['use_composite_rsi']):
                    logger_exit.debug('composite rsi exit signal is disabled')
                elif 'composite_rsi_threshold' not in exits_cfg:
                    logger_exit.error(
                        "The parameters composite_rsi_threshold is NOT in the configuration dictionary!")
                else:
                    if pd.isna(df.iloc[i]['composite_rsi']):
                        logger_exit.warning(
                            f"Exit Signal Ignored at index {i}: Composite RSI is NaN")
                        return False
                    if rsi_exit(df, i, exits_cfg):
                        exit_position = True
                        logger_exit.info(
                            f"EXIT SIGNAL: the composite rsi signal was triggered!")

            return exit_position

        except Exception as e:
            logger_exit.error(f"Exit Signal Crash at index {i}: {e}")
            return False

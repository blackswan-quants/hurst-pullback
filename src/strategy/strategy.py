import pandas as pd
from .signals.rsi2 import long_entry
from .signals.hurst_filter import allow
from .exits.time_exit import should_exit
from .exits.profitable_close_exit import should_exit as prof_exit
from .signals.composite_rsi_exit import should_exit as rsi_exit
import logging

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
        if 'max_bars_in_trade' not in cfg.keys():
            logging.error("The parameters ’max_bars_in_trade’ is NOT in the configuration dictionary!")
        if 'max_profitable_closes' not in cfg.keys():
            logging.error("'max_profitable_closes' is NOT in configuration dictionary!")
        if 'hurst_threshold' not in cfg.keys():
            logging.error("Parameters dictionary does NOT contain hurst threshold!")
        self.__cfg = cfg
    def get_cfg(self) -> dict:
        """
        Getter method for configuation parameters.
        Output:
        dict: The configuration parameters.
        """
        return self.__cfg
    def set_cfg(self, new_cfg:dict):
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
        Output:
        bool: True if long entry condition is met.
        """
        long_entry_check = True
        # RSI check
        if 'rsi' in df.columns:
            if not long_entry(df, i, self.__cfg):
                long_entry_check = False
                logging.info("NO ENTRY: RSI indicators was NOT between 10 ad 20.")
        elif 'rsi' not in df.columns:
            logging.error('Dataframe does NOT have RSI columns!')

        # Hurst check
        if 'hurst' in df.columns and 'hurst_threshold' in self.__cfg.keys():
            if long_entry_check and not allow(df, i, self.__cfg):
                long_entry_check = False
                logging.info("NO ENTRY: Hurst filter is NOT above the threshold.")
        elif 'hurst_threshold' not in self.__cfg.keys():
            logging.error("Parameters dictionary does NOT contain hurst threshold!")
        elif 'hurst' not in df.columns:
            logging.error('Hurst exponent is NOT in the dataframe!')

        return long_entry_check
    def exit_signal(self, df: pd.DataFrame, i: int, state: dict) -> bool:
        """
        Evaluate exit conditions for an open trade.
        Input:
        df (pd.DataFrame): DataFrame with indicators.
        i (int): Current bar index.
        state (dict): Dictionary containing current position info.
        Output:
        bool: True if exit condition is met.
        """
        exit_position = False

        # Time exit check
        if 'bars' not in state.keys():
            logging.error("'bars' number is NOT in state dictionary!")
        elif 'max_bars_in_trade' not in self.__cfg.keys():
            logging.error("The parameters ’max_bars_in_trade’ is NOT in the configuration dictionary!")
        elif should_exit(state, self.__cfg):
            exit_position = True
            logging.info(f"EXIT SIGNAL: the maximum bars in trade is reached")

        # pofit exit check
        if not exit_position:
            if 'entry_price' not in state.keys():
                logging.error("'entry_price' is NOT in state dictionary!")
            elif 'prof_x' not in state.keys():
                logging.error("'prof_x' is NOT in state dictionary!")
            elif 'max_profitable_closes' not in self.__cfg.keys():
                logging.error("'max_profitable_closes' is NOT in configuration dictionary!")
            elif prof_exit(df, i, state, self.__cfg):
                exit_position = True
                logging.info(f"EXIT SIGNAL: the position was profitable for {self.__cfg['max_profitable_closes']} days.")                

        # composite rsi check
        if not exit_position:
            if 'composite_rsi' not in df.colums:
                logging.error("'composite_rsi' is NOT in the dataframe!")
            elif rsi_exit(df, i, self.__cfg):
                exit_position = True
                logging.info(f"EXIT SIGNAL: the composite rsi signal was triggered!")

        return exit_position
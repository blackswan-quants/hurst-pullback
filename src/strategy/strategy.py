import pandas as pd
from .signals.rsi2 import long_entry
from .signals.hurst_filter import allow
from .exits.time_exit import should_exit
from .exits.profitable_close_exit import should_exit as prof_exit
from .signals.composite_rsi_exit import should_exit as rsi_exit
import logging

logger = logging.getLogger(__name__)


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
        if 'exits' not in cfg or 'max_bars_in_trade' not in cfg.get('exits', {}):
            logger.warning(
                "The parameters 'max_bars_in_trade' is NOT in the configuration dictionary!")
        if 'exits' not in cfg or 'max_profitable_closes' not in cfg.get('exits', {}):
            logger.warning(
                "'max_profitable_closes' is NOT in configuration dictionary!")
        if 'entry_thresholds' not in cfg or 'hurst_threshold' not in cfg.get('entry_thresholds', {}):
            logger.warning(
                "Parameters dictionary does NOT contain hurst threshold!")
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
            entry_cfg = self.__cfg.get('entry_thresholds', {})

            # RSI check
            if 'rsi' in df.columns and 'rsi_low' in entry_cfg and 'rsi_high' in entry_cfg:
                if pd.isna(df.iloc[i]['rsi']):
                    logger.warning(
                        f"Signal Invalidated at index {i}: RSI is NaN")
                    return False

                if not long_entry(df, i, entry_cfg):
                    long_entry_check = False
                    logger.info(
                        "NO ENTRY: RSI indicators was NOT between 10 ad 20.")
            elif 'rsi' not in df.columns:
                logger.error('RSI is NOT in the Dataframe!')
                long_entry_check = False
            elif 'rsi_low' not in entry_cfg:
                logger.error(
                    'Parameters dictionary does NOT contain rsi_low! ')
                long_entry_check = False
            elif 'rsi_high' not in entry_cfg:
                logger.error(
                    'Parameters dictionary does NOT contain rsi_high! ')
                long_entry_check = False

            # Hurst check
            if 'hurst' in df.columns and 'hurst_threshold' in entry_cfg:
                if pd.isna(df.iloc[i]['hurst']):
                    logger.warning(
                        f"Signal Invalidated at index {i}: Hurst is NaN")
                    return False

                if long_entry_check and not allow(df, i, entry_cfg):
                    long_entry_check = False
                    logger.info(
                        "NO ENTRY: Hurst filter is NOT above the threshold.")
            elif 'hurst_threshold' not in entry_cfg:
                logger.error(
                    "Parameters dictionary does NOT contain hurst threshold!")
                long_entry_check = False
            elif 'hurst' not in df.columns:
                logger.error('Hurst exponent is NOT in the dataframe!')
                long_entry_check = False

            return long_entry_check

        except Exception as e:
            logger.error(
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
            # Get exits config
            exits_cfg = self.__cfg.get('exits', {})

            # Time exit check
            if 'bars' not in state.keys():
                logger.error("'bars' number is NOT in state dictionary!")
            elif 'max_bars_in_trade' not in exits_cfg:
                logger.error(
                    "The parameters 'max_bars_in_trade' is NOT in the configuration dictionary!")
            elif should_exit(state, exits_cfg):
                exit_position = True
                logger.info(
                    f"EXIT SIGNAL: the maximum bars in trade is reached")

            # profit exit check
            if not exit_position:
                if 'entry_price' not in state.keys():
                    logger.error("'entry_price' is NOT in state dictionary!")
                elif 'bars' not in state.keys():
                    logger.error("'bars' is NOT in state dictionary!")
                elif 'max_profitable_closes' not in exits_cfg:
                    logger.error(
                        "The parameters 'max_profitable_closes' is NOT in the configuration dictionary!")
                elif prof_exit(df, i, state, exits_cfg):
                    exit_position = True
                    logger.info(
                        f"EXIT SIGNAL: the position was profitable for {exits_cfg['max_profitable_closes']} days.")

            # composite rsi check
            if not exit_position:
                if 'composite_rsi' not in df.columns:
                    logger.error("'composite_rsi' is NOT in the dataframe!")
                elif 'composite_rsi_threshold' not in exits_cfg:
                    logger.error(
                        "The parameters composite_rsi_threshold is NOT in the configuration dictionary!")
                else:
                    if pd.isna(df.iloc[i]['composite_rsi']):
                        logger.warning(
                            f"Exit Signal Ignored at index {i}: Composite RSI is NaN")
                        return False
                    if rsi_exit(df, i, exits_cfg):
                        exit_position = True
                        logger.info(
                            f"EXIT SIGNAL: the composite rsi signal was triggered!")

            return exit_position

        except Exception as e:
            logger.error(f"Exit Signal Crash at index {i}: {e}")
            return False

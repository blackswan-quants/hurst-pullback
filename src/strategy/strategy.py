import pandas as pd
from .signals.rsi2 import long_entry
from .signals.hurst_filter import allow
from .exits.time_exit import should_exit
from .exits.profitable_close_exit import should_exit as prof_exit
from .signals.composite_rsi_exit import should_exit as rsi_exit



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
            print("Ablation settings absent, check yaml file!")
        else:
            self.ablation = cfg.get('ablation', {})
            
        if 'exit_thresholds' not in cfg:
            print("Exit thresholds parameters absent, check yaml file!")
        else:
            self.exit_thresholds = cfg.get('exit_thresholds', {})
            if (self.ablation['use_take_profit']) and ('max_profitable_closes' not in self.exit_thresholds or not self.exit_thresholds['max_profitable_closes']):
                print("max_profitable_closes exit logic is absent")
            if (self.ablation['use_time_exit']) and ('max_bars_in_trade' not in self.exit_thresholds or not self.exit_thresholds['max_bars_in_trade']):
                print("max_bars_in_trade exit logic is absent")
            if (self.ablation['use_RSI_exit']) and ('composite_rsi_threshold' not in self.exit_thresholds or not self.exit_thresholds['composite_rsi_threshold']):
                print("composite_rsi_threshold exit logic is absent")

        if 'entry_thresholds' not in cfg:
            print("Entry thresholds parameters absent, check yaml file! ")
        else:
            self.entry_thresholds = cfg.get('entry_thresholds', {})
            if (self.ablation['use_composite_rsi']) and ('rsi_low' not in self.entry_thresholds or not self.entry_thresholds['rsi_low']):
                print("rsi_low entry logic is absent")
            if (self.ablation['use_composite_rsi']) and ('rsi_high' not in self.entry_thresholds or not self.entry_thresholds['rsi_high']):
                print("rsi_high entry logic is absent")
            if (self.ablation['use_hurst']) and ('hurst_threshold' not in self.entry_thresholds or not self.entry_thresholds['hurst_threshold']):
                print("hurst_threshold entry logic is absent")
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
        
        Args:
            df (pd.DataFrame): DataFrame with indicators.
            i (int): Current bar index.
            state (dict): Position state (flat or long).
            
        Returns:
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
                    return False

                if not long_entry(df, i, entry_cfg):
                    long_entry_check = False
            elif 'rsi' not in df.columns:
                print('RSI is NOT in the Dataframe!')
                long_entry_check = False
            elif 'rsi_low' not in entry_cfg:
                print('Parameters dictionary does NOT contain rsi_low! ')
                long_entry_check = False
            elif 'rsi_high' not in entry_cfg:
                print('Parameters dictionary does NOT contain rsi_high! ')
                long_entry_check = False

            # Hurst check
            if (self.ablation['use_hurst']) and ('hurst' in df.columns and 'hurst_threshold' in entry_cfg):
                if pd.isna(df.iloc[i]['hurst']):
                    return False

                if long_entry_check and not allow(df, i, entry_cfg):
                    long_entry_check = False
            elif 'hurst_threshold' not in entry_cfg:
                print("Parameters dictionary does NOT contain hurst threshold!")
                long_entry_check = False
            elif 'hurst' not in df.columns:
                print('Hurst exponent is NOT in the dataframe!')
                long_entry_check = False

            return long_entry_check

        except Exception as e:
            print(f"Strategy Entry Crash at index {i}: {e}")
            return False

    def exit_signal(self, df: pd.DataFrame, i: int, state: dict) -> tuple[bool, str]:
        """
        Evaluate exit conditions for an open trade.
        
        Args:
            df (pd.DataFrame): DataFrame with indicators.
            i (int): Current bar index.
            state (dict): Dictionary containing current position info.
            
        Returns:
            tuple[bool, str]: (Decision (True/False), Reason for exit).
        """
        try:
            if i >= len(df):
                return False, ""

            # Get exit_thresholds config
            exits_cfg = self.exit_thresholds

            # Time exit check
            if 'bars' not in state:
                print("'bars' number is NOT in state dictionary!")
            elif 'max_bars_in_trade' not in exits_cfg:
                print("The parameters 'max_bars_in_trade' is NOT in the configuration dictionary!")
            elif self.ablation['use_time_exit'] and should_exit(state, exits_cfg):
                return True, "Time Exit"

            # profit exit check
            if 'entry_price' not in state:
                print("'entry_price' is NOT in state dictionary!")
            elif 'bars' not in state:
                # redundant but keeping for safety
                pass 
            elif 'max_profitable_closes' not in exits_cfg:
                print("The parameters 'max_profitable_closes' is NOT in the configuration dictionary!")
            elif self.ablation['use_take_profit'] and prof_exit(df, i, state, exits_cfg):
                return True, "Take Profit"

            # composite rsi check
            if 'composite_rsi' not in df.columns:
                print("'composite_rsi' is NOT in the dataframe!")
            elif 'composite_rsi_threshold' not in exits_cfg:
                print("The parameters composite_rsi_threshold is NOT in the configuration dictionary!")
            elif self.ablation['use_composite_rsi']:
                if pd.isna(df.iloc[i]['composite_rsi']):
                    return False, ""
                if rsi_exit(df, i, exits_cfg):
                    return True, "Composite RSI"

            return False, ""

        except Exception as e:
            print(f"Exit Signal Crash at index {i}: {e}")
            return False, "Error"

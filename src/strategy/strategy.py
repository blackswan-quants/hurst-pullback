import pandas as pd

class Strategy:
    """
    Main orchestrator class that manages entry and exit signals
    according to parameters and ablation settings.
    Attributes:
    cfg (dict): Loaded configuration dictionary.
    """

    def __init__(self, cfg: dict):
        """
        Initialize strategy with configuration parameters.
        """
        pass
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
        pass
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
        pass
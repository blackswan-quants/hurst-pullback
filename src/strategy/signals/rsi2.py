import pandas as pd

def long_entry(df: pd.DataFrame, i: int, params: dict) -> bool:
    """
    Return True if RSI(2) lies within oversold range [10, 20].
    Input:
    df (pd.DataFrame): DataFrame with ’rsi’ column.
    i (int): Current bar index.
    params (dict): Parameter dictionary.
    Output:
    bool: True if entry condition satisfied.
    """
    pass
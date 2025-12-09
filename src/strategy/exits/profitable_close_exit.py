from ntpath import join
import pandas as pd

def should_exit(df: pd.DataFrame, i: int, state: dict, params: dict) -> bool:
    """
    Exit when the number of consecutive profitable closes
    exceeds a defined threshold.
    Input:
    df (pd.DataFrame): DataFrame with price data.
    i (int): Current bar index.
    state (dict): Position state including ’entry_price’ and ’prof_x’.
    params (dict): Contains ’max_profitable_closes’.
    Output:
    bool: True if profit-close condition is satisfied.
    """

    bars = state['bars']
    max_profitable_closes = params['max_profitable_closes']

    if bars < max_profitable_closes:
        return False

    for j in range(max_profitable_closes):
        if df.loc[i-j, 'Close'] < df.loc[i-j, 'Open']:
            return False
        else:
            continue
    return True


import pandas as pd

def should_exit(df: pd.DataFrame, i: int, params: dict) -> bool:
    """
    Trigger exit when Composite RSI crosses above 50
    following a local high reversal pattern.
    Input:
    df (pd.DataFrame): DataFrame with ’composite_rsi’ column.
    i (int): Current bar index.
    params (dict): Parameter dictionary.
    Output:
    bool: True if signal-based exit is detected.
    """
    comp_rsi_thresh = params['exits']["composite_rsi_threshold"]
    curr_comp_rsi = df.loc[i, "composite_rsi"]

    if(pd.isna(curr_comp_rsi)):
        return False
    
    return curr_comp_rsi > comp_rsi_thresh
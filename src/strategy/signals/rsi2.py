import pandas as pd

def long_entry(df: pd.DataFrame, i: int, params: dict) -> bool: 
    """ 
    Return True if RSI(2) lies within oversold range [10, 20]. 
    Input: df (pd.DataFrame): DataFrame with ’rsi’ column. 
    i (int): Current bar index. 
    params (dict): Parameter dictionary. 
    Output: bool: True if entry condition satisfied.

    """ 
    curr_rsi = df.loc[i, "rsi"]

    rsi_low = params["entry_thresholds"]['rsi_low']
    rsi_high = params["entry_thresholds"]['rsi_high']
 
    if(rsi_low is None or pd.isna(rsi_low) or 
       rsi_high is None or pd.isna(rsi_high) or 
       curr_rsi is None or pd.isna(curr_rsi)
    ):
        return False

    return rsi_low <= curr_rsi <= rsi_high

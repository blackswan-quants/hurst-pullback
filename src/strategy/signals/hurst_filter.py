import pandas as pd

def allow(df: pd.DataFrame, i: int, params: dict) -> bool:
    """
    Validate trade based on Hurst regime.
    Input:
    df (pd.DataFrame): DataFrame with ’hurst’ column.
    i (int): Current bar index.
    params (dict): Parameter dictionary with ’hurst_threshold’.
    Output:
    bool: True if Hurst exponent > threshold.
    """
    curr_hurst = df.loc[i, "hurst"]
    hurst_tresh = params.get("hurst_treshold")

    if(pd.isna(curr_hurst)):
        return False
    
    return curr_hurst > hurst_tresh

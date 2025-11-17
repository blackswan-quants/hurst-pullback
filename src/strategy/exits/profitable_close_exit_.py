import pandas as pd 
import numpy as np 

def profitable_close(entry_index: int , df):

    """
    Finds the exit point after 5 consecutive profitable closes following the entry index.
    
    A profitable close is defined as a close price higher than the previous bar's close.
    The function scans forward from the entry bar to find the first occurrence of 
    5 consecutive profitable closes and returns the corresponding exit point.
    
    Parameters:
    -----------
    entry_index : int
        Index of the bar where the position was opened
    df : pandas.DataFrame
        DataFrame containing market data with 'Close' column
        
    Returns:
    --------
    pandas.DataFrame or None
        DataFrame slice from entry bar to exit bar (inclusive) if 5 consecutive 
        profitable closes are found, otherwise None
        
    Example:
    --------
    >>> trade_data = profitable_close(150, df)
    >>> if trade_data is not None:
    >>>     print(f"Trade duration: {len(trade_data)} bars")
    >>>     print(f"Exit price: {trade_data['Close'].iloc[-1]}")
    
    Notes:
    ------
    - The function modifies the input DataFrame by adding a 'profitable' column
    - Scanning starts from the bar immediately after the entry bar (entry_index + 1)
    - Consecutive profitable closes must be exactly 5 in a row without interruptions
    - If no streak is found, returns None and prints a warning message
    - The returned slice includes both entry and exit bars
    """

    df['profitable'] = df['Close'] > df['Close'].shift(1)
    
    start_idx = entry_index + 1
    consecutive = 0
    exit_idx = None
    for i in range(start_idx, len(df)):
        if df['profitable'].iloc[i]:
            consecutive += 1
            if consecutive == 5:
                exit_idx = i
                print(f"Exit at the bar {i} after 5 consecutive profitable closes")
                break
        else:
            consecutive = 0
    if exit_idx:
        return df.iloc[entry_index:exit_idx + 1]
    else:
        print("No sequence of 5 consecutive profitable closes found.")
        return None
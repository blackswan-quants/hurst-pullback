import pandas as pd 
import numpy as np 

def time_exit_11_bar(entry_index: int, df):

    """
    Closes a position after exactly 11 bars from entry.
    
    The function calculates the exit index by adding 11 bars to the entry index
    and automatically handles cases where the exit would exceed DataFrame boundaries.
    
    Parameters:
    -----------
    entry_index : int
        Index of the bar where the position was opened
    df : pandas.DataFrame
        DataFrame containing market data
        
    Returns:
    --------
    tuple (exit_index, exit_row)
        exit_index : int
            Index of the exit bar
        exit_row : pandas.Series
            DataFrame row corresponding to the exit bar
            
    Example:
    --------
    >>> exit_idx, exit_data = time_exit_11_bar(100, df)
    >>> print(f"Exit at bar {exit_idx}")
    Exit at bar 111
    
    Notes:
    ------
    - If entry_index + 11 exceeds DataFrame length, exits at the last available bar
    - Uses zero-based indexing
    - The 11-bar count includes the entry bar as bar 0
    """
    
    exit_index = entry_index + 11


    if exit_index >= len(df):
        exit_index = len(df) - 1
    

    exit_row = df.iloc[exit_index]
    return exit_index, exit_row
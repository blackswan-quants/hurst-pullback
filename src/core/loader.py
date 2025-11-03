import pandas as pd

def load_data(path: str) -> pd.DataFrame:
    """
    Load a CSV file containing OHLCV market data.
    Input:
    path (str): File path to the CSV dataset.
    Output:
    pd.DataFrame: Cleaned DataFrame with lowercase columns
    [’open’, ’high’, ’low’, ’close’, ’volume’] and no NaN values.
    """
    pass
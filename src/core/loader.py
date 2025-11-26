import pandas as pd
import numpy as np
import warnings
from pathlib import Path

def load_data(raw_dir="data/raw", clean_dir="data/clean"):
    """
    Load and combine data from raw and clean directories.
    Returns a DataFrame with sorted UTC DatetimeIndex.

    Parameters
    ----------
    raw_dir : str, optional
        Directory path for raw data files. Default is 'data/raw'.
    clean_dir : str, optional
        Directory path for clean data files. Default is 'data/clean'.

    Processing Steps
    ----------------
    - Loads all CSV files from raw and clean directories.
    - Parses datetime columns and sets them as index.
    - Combines all DataFrames into a single dataset.
    - Removes duplicate indices keeping first occurrence.
    - Sorts the DataFrame chronologically.
    - Handles missing values using forward and backward fill.
    - Converts index timezone to UTC.

    Returns
    -------
    pandas.DataFrame
        Cleaned and combined DataFrame with UTC DatetimeIndex.

    Example
    -------
    >>> df = load_data('data/raw', 'data/processed')
    """
    raw_path = Path(raw_dir)
    clean_path = Path(clean_dir)
    
    
    raw_data = []
    for file in raw_path.glob("*.csv"):
        df = pd.read_csv(file, parse_dates=['datetime'], index_col='datetime')
        raw_data.append(df)
    
    
    clean_data = []
    for file in clean_path.glob("*.csv"):
        df = pd.read_csv(file, parse_dates=['datetime'], index_col='datetime')
        clean_data.append(df)
    
    
    combined_df = pd.concat(raw_data + clean_data, axis=0)
    
    
    combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
    combined_df = combined_df.sort_index()
    
    
    combined_df = combined_df.ffill().bfill()
    
    
    combined_df.index = pd.to_datetime(combined_df.index).tz_convert('UTC')
    
    return combined_df

def error_handling(df):
    """
    Handle errors and anomalous values in the DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame to be cleaned.

    Processing Steps
    ----------------
    - Replaces infinite values with NaN.
    - Removes rows with any NaN values.
    - Identifies and removes outliers using 3 standard deviations rule
      for all numeric columns.

    Returns
    -------
    pandas.DataFrame
        Cleaned DataFrame with outliers and invalid values removed.

    Example
    -------
    >>> clean_df = error_handling(raw_df)
    """
    
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        mean = df[col].mean()
        std = df[col].std()
        df = df[(df[col] <= mean + 3*std) & (df[col] >= mean - 3*std)]
    
    return df

def check_time_gaps(df, freq='1H'):
    """
    Check for time gaps in the DataFrame index and raise warning if gaps are detected.

    Parameters
    ----------
    df : pandas.DataFrame
        The input DataFrame with DatetimeIndex.
    freq : str, optional
        The expected frequency of the time series. Default is '1H' (hourly).

    Processing Steps
    ----------------
    - Generates an expected date range from min to max index with specified frequency.
    - Compares expected range with actual index to identify gaps.
    - Emits a warning if any gaps are detected in the time series.

    Returns
    -------
    pandas.DatetimeIndex
        DatetimeIndex containing all missing timestamps (gaps).

    Warnings
    --------
    UserWarning
        If time gaps are detected between expected and actual indices.

    Example
    -------
    >>> gaps = check_time_gaps(df, freq='1H')
    """
    
    expected_index = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq=freq,
        tz='UTC'
    )
    
    
    gaps = expected_index.difference(df.index)
    
    
    if not gaps.empty:
        warnings.warn(
            f"Found {len(gaps)} time gaps in the DataFrame",
            UserWarning
        )
    
    return gaps

def validate_indicator_alignment(clean_dir="data/clean"):
    """
    Validate temporal alignment of indicators in the clean directory.

    Parameters
    ----------
    clean_dir : str, optional
        Directory path containing cleaned indicator files. Default is 'data/clean'.

    Processing Steps
    ----------------
    - Loads all CSV files from the clean directory.
    - Converts datetime columns to UTC timezone-aware indices.
    - Validates that all DataFrames have identical indices.
    - Checks for null values in any indicator.
    - Raises ValueError if misalignment or null values are detected.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If indicators have misaligned temporal indices or contain null values.

    Example
    -------
    >>> validate_indicator_alignment('data/processed')
    """
    clean_path = Path(clean_dir)
    dataframes = []
    
    
    for file in clean_path.glob("*.csv"):
        df = pd.read_csv(file, parse_dates=['datetime'], index_col='datetime')
        df.index = pd.to_datetime(df.index).tz_convert('UTC')
        dataframes.append((file.stem, df))
    
    if not dataframes:
        raise ValueError("No indicator files found in the clean directory")
    
    
    reference_index = dataframes[0][1].index
    for name, df in dataframes[1:]:
        if not df.index.equals(reference_index):
            raise ValueError(f"Indicator {name} has misaligned temporal index")
    

    for name, df in dataframes:
        if df.isnull().any().any():
            raise ValueError(f"Found null values in indicator {name}")
    
    print("Validation completed: all indicators are temporally aligned")
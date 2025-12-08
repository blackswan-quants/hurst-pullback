import pandas as pd
import numpy as np
import warnings
from pathlib import Path


import pandas as pd
import numpy as np
import warnings
from datetime import datetime

import pandas as pd
import numpy as np
import warnings

# src/loader.py
import pandas as pd
import numpy as np
import warnings

def load_data(file_path, dedup=True, sort=True, handle_missing=True):
    """Load and clean CSV data with datetime index"""
    df = pd.read_csv(file_path)
    
    # Cerca colonna timestamp
    timestamp_col = None
    for col in ['timestamp', 'date', 'Date', 'datetime', 'Datetime']:
        if col in df.columns:
            timestamp_col = col
            break
    
    if timestamp_col:
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        df.set_index(timestamp_col, inplace=True)
    else:
        print(f"⚠️ Warning: No timestamp column found in {file_path}")
        return df
    
    # Gestione timezone (solo per DatetimeIndex)
    if isinstance(df.index, pd.DatetimeIndex):
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')
    
    # Deduplicazione
    if dedup and isinstance(df.index, pd.DatetimeIndex):
        df = df[~df.index.duplicated(keep='first')]
    
    # Sort
    if sort and isinstance(df.index, pd.DatetimeIndex):
        df = df.sort_index()
    
    # Gestione missing values
    if handle_missing:
        original_len = len(df)
        df = df.dropna()
        removed = original_len - len(df)
        if removed > 0:
            print(f"✓ Removed {removed} rows with missing values")
    
    return df


def Error_handling(df):
    """Handle errors while preserving DatetimeIndex"""
    df_fixed = df.copy()
    
    # Dropna but preserve the index structure
    df_fixed = df_fixed.dropna()
    
    # Index should already be DatetimeIndex with UTC tz
    if not isinstance(df_fixed.index, pd.DatetimeIndex):
        df_fixed = df_fixed.reset_index()
        if 'timestamp' in df_fixed.columns:
            df_fixed['timestamp'] = pd.to_datetime(df_fixed['timestamp'])
            df_fixed.set_index('timestamp', inplace=True)
        # Ensure UTC timezone
        if df_fixed.index.tz is None:
            df_fixed.index = df_fixed.index.tz_localize('UTC')
        else:
            df_fixed.index = df_fixed.index.tz_convert('UTC')
    
    return df_fixed


def check_time_gaps(df, expected_freq=None):
    """Check for time gaps in DatetimeIndex"""
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have DatetimeIndex")
    
    gaps = []
    total_gap_duration = pd.Timedelta(0)
    
    # Convert expected_freq to timedelta properly
    if expected_freq:
        if isinstance(expected_freq, str):
            # Handle string frequencies like '1D', 'D', '1H', etc.
            if expected_freq == 'D':
                expected_timedelta = pd.Timedelta(days=1)
            elif expected_freq.endswith('D'):
                days = int(expected_freq[:-1]) if expected_freq[:-1] else 1
                expected_timedelta = pd.Timedelta(days=days)
            else:
                expected_timedelta = pd.to_timedelta(expected_freq)
        else:
            expected_timedelta = expected_freq
    else:
        expected_timedelta = None
    
    for i in range(1, len(df.index)):
        time_diff = df.index[i] - df.index[i-1]
        
        if expected_timedelta and time_diff > expected_timedelta:
            gap_duration = time_diff - expected_timedelta
            gaps.append({
                'start': df.index[i-1],
                'end': df.index[i],
                'duration': gap_duration
            })
            total_gap_duration += gap_duration
            
            warnings.warn(
                f"Time gap detected: {df.index[i-1]} to {df.index[i]} "
                f"(duration: {gap_duration})",
                UserWarning,
                stacklevel=2
            )
    
    return {
        'gap_intervals': gaps,
        'total_gap_duration': total_gap_duration,
        'n_gaps': len(gaps)
    }




'''def load_data(raw_dir="data/raw", clean_dir="data/clean"):
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
    
    # Load raw data files
    raw_data = []
    for file in raw_path.glob("*.csv"):
        df = pd.read_csv(file, parse_dates=['datetime'], index_col='datetime')
        raw_data.append(df)
    
    # Load existing clean data files
    clean_data = []
    for file in clean_path.glob("*.csv"):
        df = pd.read_csv(file, parse_dates=['datetime'], index_col='datetime')
        clean_data.append(df)
    
    # Combine all datasets
    combined_df = pd.concat(raw_data + clean_data, axis=0)
    
    # Remove duplicate indices and sort chronologically
    combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
    combined_df = combined_df.sort_index()
    
    
    combined_df = combined_df.ffill().bfill()
    
    # Convert index to UTC timezone
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
    # Replace infinite values with NaN and drop rows with missing values
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    
    # Identify and remove outliers
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
    # Generate expected continuous index
    expected_index = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq=freq,
        tz='UTC'
    )
    
    # Identify gaps by comparing expected vs actual index
    gaps = expected_index.difference(df.index)
    
    # Raise warning if gaps are found
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
    
    # Load all indicator files from clean directory
    for file in clean_path.glob("*.csv"):
        df = pd.read_csv(file, parse_dates=['datetime'], index_col='datetime')
        df.index = pd.to_datetime(df.index).tz_convert('UTC')
        dataframes.append((file.stem, df))
    
    if not dataframes:
        raise ValueError("No indicator files found in the clean directory")
    
    # Validate temporal index alignment across all indicators
    reference_index = dataframes[0][1].index
    for name, df in dataframes[1:]:
        if not df.index.equals(reference_index):
            raise ValueError(f"Indicator {name} has misaligned temporal index")
    
    # Check for null values in any indicator
    for name, df in dataframes:
        if df.isnull().any().any():
            raise ValueError(f"Found null values in indicator {name}")
    
    print("Validation completed: all indicators are temporally aligned")

'''
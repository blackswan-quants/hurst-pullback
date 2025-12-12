import pandas as pd
import numpy as np
import os
import warnings
import logging
from typing import List, Optional

logger = logging.getLogger('loader')


def error_handling(path: str, target_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Load a CSV file and check schema validity, raising clear exceptions for missing files or malformed columns.

    Parameters
    ----------
    path : str
        Path to the CSV file to load.
    target_columns : list of str, optional
        List of expected columns in the loaded DataFrame. If not specified,
        defaults to ['date', 'open', 'high', 'low', 'close', 'volume'].

    Processing Steps
    ----------------
    - Checks if the file at `path` exists and raises a FileNotFoundError if not.
    - Loads data from the file into a pandas DataFrame.
    - Normalizes column names to lowercase.
    - Checks for any missing or malformed columns; raises ValueError if any are found.

    Returns
    -------
    pandas.DataFrame
        The loaded DataFrame with validated columns and lowercase column names.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    ValueError
        If one or more of the required columns are missing or malformed.

    Example
    -------
    >>> df = Error_handling("ohlc.csv")
    >>> print(df.head())
    """
    if target_columns is None:
        target_columns = ["date", "open", "high", "low", "close", "vol"]

    if not os.path.exists(path):
        logger.error(f"Validation failed. File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")

    try:
        df = pd.read_csv(path)
        df.columns = [c.lower() for c in df.columns]

        missing = [c for c in target_columns if c not in df.columns]
        if missing:
            logger.error("Missing columns: %s", missing)
            raise ValueError(f"Missing columns: {missing}")
        return df

    except Exception as e:
        if not isinstance(e, ValueError):
            logger.error(f"Error_handling check failed: {e}")
        raise e


def check_time_gaps(df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
    """
    Check for time gaps greater than one day in a DataFrame and raise a warning if gaps are detected.

    Parameters
    ----------
    df : pandas.DataFrame
        The input DataFrame containing a datetime column.
    date_column : str, optional
        The column name containing dates. Default is 'date'.

    Processing Steps
    ----------------
    - Converts the specified date column to timezone-aware datetime objects.
    - Sorts the DataFrame by date.
    - Calculates the difference between consecutive dates in the sequence.
    - Emits a warning if any interval greater than one day is detected.

    Returns
    -------
    None

    Warnings
    --------
    UserWarning
        If time intervals greater than 1 day are found between adjacent records.

    Example
    -------
    >>> check_time_gaps(df, date_column='timestamp')
    """
    try:
        if date_column not in df.columns:
            return df

        # Ensure datetime format for calculation
        temp_dates = pd.to_datetime(df[date_column], errors="coerce")
        if temp_dates.isna().any():
            logger.warning(
                "Values found not in time format in date column during gap check")
        gaps = temp_dates.sort_values().diff()
        if (gaps > pd.Timedelta(days=1)).any():
            warnings.warn(
                "Intervals > 1 day between adjacent records were found")
            logger.warning(
                "Intervals > 1 day between adjacent records were found")
        return df
    except Exception as e:
        logger.warning("Could not check time gaps: %s", e)
        return df

def load_data(path: str) -> pd.DataFrame:
    """
    Load a CSV file, standardize columns, and preprocess date/time features.

    Parameters
    ----------
    path : str
        The path to the CSV file to load.

    Processing Steps
    ----------------
    - Reads the specified CSV as a pandas DataFrame.
    - Standardizes column names: 'Date', 'Open', 'High', 'Low', 'Close', 'Volume' (makes lowercase).
    - Converts the 'date' column to timezone-aware datetime64[ns, UTC] format as 'datetime'.
    - Sorts the DataFrame by the 'date' column.
    - Sorts the DataFrame index.
    - Removes duplicate rows and those with missing values.

    Returns
    -------
    pandas.DataFrame
        The cleaned and preprocessed DataFrame, ready for subsequent analysis.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist at the specified path.
    ValueError
        If required columns are missing or 'date' conversion fails.

    Example
    -------
    >>> df = load_data("dataset.csv")
    >>> print(df.head())
    """
    if not os.path.exists(path):
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")

    try:
        error_handling(path)
        df = pd.read_csv(path)

        if df.empty:
            logger.error("The loaded CSV is empty")
            raise ValueError("The loaded CSV is empty")
        
        
        df.columns = [c.lower() for c in df.columns]

        if "date" in df.columns:
            df["datetime"] = pd.to_datetime(
                df['date'], utc=True, format='%Y-%m-%d', errors='coerce')
            if df['datetime'].isna().all():
                raise ValueError("Date parsing failed. All values are NaT.")
            df['datetime'] = df['datetime'].dt.tz_localize(None)
            df = df.sort_values('datetime').reset_index(drop=True)
        else:
            logger.warning("'Date' column missing")

        # Drop exact duplicate rows but preserve rows with missing indicator values for later handling
        df.set_index('datetime', inplace=True)
        df.drop_duplicates(inplace=True)
        df.dropna(inplace=True)
        logger.info(f"Successfully loaded {len(df)} rows")
        check_time_gaps(df)
        return df

    except Exception as e:
        logger.critical(f"Failed to load data: {e}", exc_info=True)
        raise e
    
def save_clean_data(df: pd.DataFrame, path: str) -> None:
    """
    Save a cleaned DataFrame to a specified CSV file path.

    Parameters
    ----------
    df : pandas.DataFrame
        The cleaned DataFrame to save.
    path : str
        Destination path where the CSV file will be written.

    Raises
    ------
    ValueError
        If the DataFrame is empty.
    IOError
        If the file cannot be written.

    Example
    -------
    >>> save_clean_data(df, "data/clean/my_new_dataset.csv")
    """
    if df is None or df.empty:
        logger.error("Attempted to save an empty DataFrame.")
        raise ValueError("Cannot save an empty DataFrame.")

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=True, encoding="utf-8")
        logger.info(f"Clean dataset successfully saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save cleaned dataset to {path}: {e}")
        raise IOError(f"Failed to save cleaned dataset to {path}: {e}")

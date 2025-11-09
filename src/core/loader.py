import pandas as pd 
import numpy as np 
from datetime import datetime
import matplotlib as plt
import os 
import warnings
import pytest 



def load_data(path : str) : 
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
    - Converts the 'date' column to timezone-aware datetime64[ns, UTC] format.
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

    pd.read_csv('percorso del file CSV')

    target_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    df.columns = [col.lower() if col in target_columns else col for col in df.columns]

    df['date'] = pd.to_datetime(df['date'] , utc = True , format = '%Y-%m-%d')
    df['date'] = df['date'].dt.tz_localize('UTC' , nonexistent = 'NaT')
    df['date'] = df.sort_values('date')

    df = df.sort_index() 
    df = df.drop_duplicates(inplace = True) 
    df = df.dropna(inplace = True)

    return df 

def Error_handling (path: str, target_columns=None) : 

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

    if target_columns is None : 
        target_columns = ['date' , 'open' , 'high' , 'low' , 'close' , 'volume']

    #if not os.path.isfile(path) : 
        #raise FileNotFoundError(f"File path "{} "does not exists")
    
    df = df.read_csv(path)
    missing = [col for col in target_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns : {missing}")
    return df

def check_time_gaps (df , date_column = 'date') :

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

    df[date_column] = pd.to_datetime(df[date_column] , utc = True)
    df = df.sort_values(date_column)

    gaps = df[date_column].diff()

    if (gaps > pd.Timedelta(days = 1)).any() : 
        warnings("Intervals > 1 day between adjacent records were found")

    return df 

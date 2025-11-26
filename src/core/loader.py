import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib as plt
import os
import warnings
import pytest
import logging
import os
import warnings
from typing import List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def load_data(path: str) -> pd.DataFrame:
    """Load a CSV file and perform light preprocessing.

    - Raises FileNotFoundError when file missing.
    - Normalizes column names to lowercase.
    - Parses a ``date`` column (if present) and sets it as the index.

    Parameters
    ----------
    path : str
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame.
    """
    if not os.path.exists(path):
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")

    try:
        df = pd.read_csv(path)

        if df.empty:
            logger.error("The loaded CSV is empty")
            raise ValueError("The loaded CSV is empty")

        df.columns = [c.lower() for c in df.columns]

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.sort_values("date").reset_index(drop=True)
        else:
            logger.warning("'date' column missing")

        # Drop exact duplicate rows but preserve rows with missing indicator values for later handling
        df = df.drop_duplicates()
        logger.info(f"Successfully loaded {len(df)} rows")
        return df

    except Exception as e:
        logger.critical(f"Failed to load data: {e}", exc_info=True)
        raise e


def Error_handling(path: str, target_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Load CSV and validate required columns.

    Parameters
    ----------
    path : str
        Path to CSV file.
    target_columns : list[str], optional
        Expected lower-case column names. Defaults to
        ['date','open','high','low','close','volume'].

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame with validated columns.

    Raises
    ------
    FileNotFoundError
    ValueError
    """
    if target_columns is None:
        target_columns = ["date", "open", "high", "low", "close", "volume"]

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
    """Check for gaps greater than one day and warn.

    Returns the dataframe (possibly unchanged).
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

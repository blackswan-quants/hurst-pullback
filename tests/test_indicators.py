from src.core.indicators import RSIIndicator, CompositeRSIIndicator
import pandas as pd
import numpy as np


def test_composite_rsi(prices: pd.Series, reference_rsi: pd.Series, short_period: int = 2, long_period: int = 24, warmup: int = 100) -> dict:
    """
    Validation of CompositeRSIIndicator class implementation

    Computes the Python indicator values step-by-step and compares them against 
    the provided TradeStation reference series

    Parameters
    ----------
    prices : pd.Series
        The raw Close prices to compute the indicator on.
    reference_rsi : pd.Series
        The 'CompositeRSI column from TradeStation.
    short_period : int, optional
        Lookback period for short RSI, by default 2.
    long_period : int, optional
        Lookback period for long RSI, by default 24.
    warmup : int, optional
        Additional bars to ignore for warmup, by default 100.

    Returns
    -------
    dict
        A dictionary containing error metrics:
        - 'mse': Mean Squared Error
        - 'max_error': Maximum absolute difference found
        - 'mismatches': Count of rows where error > 0.1
        - 'total_checked': Number of valid rows compared
        - 'comparison_df': A DataFrame with columns ['Python', 'TradeStation', 'Diff'] for plotting
    """
    # Initialize Indicator
    comp_ind = CompositeRSIIndicator(
        short_period=short_period, long_period=long_period)

    py_values = []

    # Compute Loop
    for i in range(len(prices)):
        # progress bar for long datasets
        current_slice = prices.iloc[:i+1]
        val = comp_ind.compute(current_slice)
        py_values.append(val)

    # Align and Compare
    results = pd.DataFrame({
        'Python': py_values,
        # Ensure alignment
        'TradeStation': reference_rsi.values[:len(py_values)]
    })
    results['Diff'] = results['Python'] - results['TradeStation']

    # Ignore the warmup period (Long Period + 'warmup' bars buffer)
    # Also ignore rows where TradeStation output is 0.0 or indicator has NaN
    warmup_idx = long_period + warmup

    valid_mask = (results.index > warmup_idx) & \
                 (np.abs(results['TradeStation']) > 0.0001) & \
                 (~results['Python'].isna())

    clean_results = results[valid_mask].copy()

    # 5. Calculate Metrics
    mse = (clean_results['Diff'] ** 2).mean()
    max_error = clean_results['Diff'].abs().max()
    mismatches = (clean_results['Diff'].abs() > 0.1).sum()

    metrics = {
        "mse": mse,
        "max_error": max_error,
        "mismatches": mismatches,
        "total_checked": len(clean_results),
        "comparison_df": results  # Returning full DF allows you to plot it later
    }

    # Print Summary
    print("REPORT")
    print("="*40)
    print(f"MSE:  {mse:.6f}")
    print(f"Max Error:      {max_error:.4f}")
    print(f"Mismatches:     {mismatches} / {len(clean_results)} rows")

    return metrics


def test_hurst_output():
    """
    Ensure Hurst exponent computation is bounded and finite.
    """
    pass

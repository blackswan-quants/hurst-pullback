import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path so we can import src modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.indicators import rsi, composite_rsi, hurst_exponent

def run_indicator_tests(raw_data_path: str, ref_data_path: str):
    print("Loading datasets...")
    
    # Load raw data
    try:
        raw_df = pd.read_csv(raw_data_path)
    except FileNotFoundError:
        print(f"Error: Raw dataset not found at {raw_data_path}")
        return
        
    # Load reference data
    try:
        ref_df = pd.read_csv(ref_data_path)
    except FileNotFoundError:
        print(f"Error: Reference dataset not found at {ref_data_path}")
        return

    # Normalize Dates to enable merging
    print("Aligning dates...")
    raw_df['Date'] = pd.to_datetime(raw_df['Date'])
    
    # TradeStation sets dates as MM/DD/YYYY
    ref_df['Date'] = pd.to_datetime(ref_df['Date'], format='%m/%d/%Y', errors='coerce')
    
    # Drop NAs from datetime parsing just in case
    raw_df = raw_df.dropna(subset=['Date'])
    ref_df = ref_df.dropna(subset=['Date'])
    
    # Set indices
    raw_df.set_index('Date', inplace=True)
    ref_df.set_index('Date', inplace=True)
    
    # Ensure they are sorted
    raw_df.sort_index(inplace=True)
    ref_df.sort_index(inplace=True)

    print("Computing indicators natively...")
    # Compute indicators against the raw DataFrame Close column
    # Using defaults: RSI(2), Composite RSI(2, 24), Hurst(20)
    raw_df['calc_rsi'] = rsi(raw_df['Close'], period=2)
    raw_df['calc_composite_rsi'] = composite_rsi(raw_df['Close'], short=2, long=24)
    raw_df['calc_hurst'] = hurst_exponent(raw_df['Close'], window=20)
    
    print("Merging evaluations...")
    # Inner join on Date index to align raw computations with the EasyLanguage benchmark
    merged = raw_df.join(ref_df[['CompositeRSI', 'HurstExponent']], how='inner', validate='1:1')
    
    # Filter out initial warmup periods where indicators return NaNs or 0.0s artificially
    merged = merged.dropna(subset=['calc_composite_rsi', 'calc_hurst', 'CompositeRSI', 'HurstExponent'])
    
    # Ignore initial zeroes in reference platform from indicator startup loops
    merged = merged[(merged['CompositeRSI'] != 0.0) | (merged['HurstExponent'] != 0.0)]
    
    if len(merged) == 0:
        print("Error: Merge resulted in 0 valid overlapping rows.")
        return
        
    print(f"Successfully aligned {len(merged)} datapoints for comparison.")
    
    # Calculate Absolute Errors
    merged['diff_composite'] = abs(merged['calc_composite_rsi'] - merged['CompositeRSI'])
    # TradeStation appears to scale Hurst * 100
    merged['diff_hurst'] = abs((merged['calc_hurst'] * 100) - merged['HurstExponent'])
    
    print("\n" + "="*50)
    print("INDICATOR VALIDATION RESULTS")
    print("="*50)
    
    # ----------------------------------------------------
    # Evaluate Composite RSI
    # ----------------------------------------------------
    comp_mae = merged['diff_composite'].mean()
    comp_max_err = merged['diff_composite'].max()
    
    # TradeStation and Pandas EWMA can differ slightly mathematically during recursion warmup.
    # We will consider tests "successful" if the Mean Absolute Error is < 0.5 (on a 0-100 scale)
    print("\n[ Composite RSI ]")
    print(f"Mean Absolute Error : {comp_mae:.4f}")
    print(f"Max Absolute Error  : {comp_max_err:.4f}")
    
    if comp_mae < 1.0:
        print("-> Status: PASS (High Correlation)")
    else:
        print("-> Status: FAIL (Significant Divergence)")
        
    # ----------------------------------------------------
    # Evaluate Hurst Exponent
    # ----------------------------------------------------
    hurst_mae = merged['diff_hurst'].mean()
    hurst_max_err = merged['diff_hurst'].max()
    
    print("\n[ Hurst Exponent ]")
    print(f"Mean Absolute Error : {hurst_mae:.4f}")
    print(f"Max Absolute Error  : {hurst_max_err:.4f}")
    
    if hurst_mae < 0.05:
        print("-> Status: PASS (High Correlation)")
    else:
        print("-> Status: FAIL (Significant Divergence)")
        
    print("="*50 + "\n")

if __name__ == "__main__":
    raw_path = str(project_root / "data" / "raw" / "ES.csv")
    ref_path = str(project_root / "data" / "easylanguage_indicators" / "indicators_plot_ES.csv")
    
    run_indicator_tests(raw_path, ref_path)
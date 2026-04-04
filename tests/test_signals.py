import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path so we can import src modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategy.signals.rsi2 import long_entry
from src.strategy.signals.hurst_filter import allow
from src.strategy.signals.composite_rsi_exit import should_exit
from src.core.indicators import rsi

def compute_errors(dataset_path: str):
    print(f"Loading dataset: {dataset_path}")
    try:
        # Load the CSV
        df = pd.read_csv(dataset_path)
    except FileNotFoundError:
        print(f"Error: Dataset not found at {dataset_path}")
        return

    # Map column names to what the signal functions expect
    df = df.rename(columns={
        "CompositeRSI": "composite_rsi",
        "HurstExponent": "hurst"
    })

    # The dataset doesn't have an explicit 'rsi' column. 
    # We will initialize it. The tests will focus on checking if the logic in the signal files matches the expected outcomes.
    # The actual RSI calculation is tested separately. However, to evaluate rsi2.py we need some values.
    # We will compute the wilder smoothing RSI(2) on the 'Close' column.
    print("Computing RSI(2)...")
    # Compute RSI(2) over the Close prices directly to feed the rsi2.py signal logic
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    # Use exponential moving average as per Wilder smoothing
    ema_up = up.ewm(com=2-1, adjust=False).mean()
    ema_down = down.ewm(com=2-1, adjust=False).mean()
    
    rs = ema_up / ema_down
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Define parameters based on base.yaml defaults
    params = {
        'rsi_low': 10.0,
        'rsi_high': 20.0,
        'hurst_threshold': 0.5,
        'composite_rsi_threshold': 0.5
    }

    print("Evaluating signals...")
    
    rsi2_errors = 0
    hurst_errors = 0
    comp_rsi_errors = 0
    
    rsi2_count = 0
    hurst_count = 0
    comp_rsi_count = 0

    # Start loop from where we have some data
    for i in range(2, len(df)):
        # --- Evaluate RSI2 Signal ---
        if 'rsi' in df.columns and pd.notna(df.loc[i, 'rsi']):
            expected_rsi_signal = params['rsi_low'] <= df.loc[i, 'rsi'] <= params['rsi_high']
            try:
                actual_rsi_signal = long_entry(df, i, params)
                if expected_rsi_signal != actual_rsi_signal:
                    rsi2_errors += 1
                rsi2_count += 1
            except Exception as e:
                print(f"Error evaluating rsi2 at index {i}: {e}")

        # --- Evaluate Hurst Filter Signal ---
        if 'hurst' in df.columns and pd.notna(df.loc[i, 'hurst']):
            expected_hurst_signal = df.loc[i, 'hurst'] > params['hurst_threshold']
            try:
                actual_hurst_signal = allow(df, i, params)
                if expected_hurst_signal != actual_hurst_signal:
                    hurst_errors += 1
                hurst_count += 1
            except Exception as e:
                print(f"Error evaluating hurst_filter at index {i}: {e}")

        # --- Evaluate Composite RSI Exit Signal ---
        if 'composite_rsi' in df.columns and pd.notna(df.loc[i, 'composite_rsi']):
            expected_comp_rsi_signal = df.loc[i, 'composite_rsi'] > params['composite_rsi_threshold']
            try:
                actual_comp_rsi_signal = should_exit(df, i, params)
                if expected_comp_rsi_signal != actual_comp_rsi_signal:
                    comp_rsi_errors += 1
                comp_rsi_count += 1
            except Exception as e:
                print(f"Error evaluating composite_rsi_exit at index {i}: {e}")

    print("\n--- Evaluation Results ---")
    
    if rsi2_count > 0:
        rsi2_accuracy = 100 - (rsi2_errors / rsi2_count) * 100
        print(f"RSI(2) Signal: {rsi2_errors} errors out of {rsi2_count} evaluations. Accuracy: {rsi2_accuracy:.2f}%")
    else:
        print("RSI(2) Signal: No evaluations performed.")

    if hurst_count > 0:
        hurst_accuracy = 100 - (hurst_errors / hurst_count) * 100
        print(f"Hurst Filter Signal: {hurst_errors} errors out of {hurst_count} evaluations. Accuracy: {hurst_accuracy:.2f}%")
    else:
        print("Hurst Filter Signal: No evaluations performed.")

    if comp_rsi_count > 0:
        comp_rsi_accuracy = 100 - (comp_rsi_errors / comp_rsi_count) * 100
        print(f"Composite RSI Exit Signal: {comp_rsi_errors} errors out of {comp_rsi_count} evaluations. Accuracy: {comp_rsi_accuracy:.2f}%")
    else:
        print("Composite RSI Exit Signal: No evaluations performed.")

if __name__ == "__main__":
    dataset_path = str(project_root / "data" / "easylanguage_indicators" / "indicators_plot_ES.csv")
    compute_errors(dataset_path)

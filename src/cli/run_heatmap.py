import os
import sys
import pandas as pd
import numpy as np
import yaml
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Handle both module and direct execution
try:
    from src.core import indicators as ind
    from src.core.fast_engine import vectorized_run
except ImportError:
    # If running directly, add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.core import indicators as ind
    from src.core.fast_engine import vectorized_run

def main():
    project_root = Path(__file__).parent.parent.parent
    
    # 1. Config & Data loading
    config_path = project_root / "configs" / "base.yaml"
    with open(config_path, 'r') as f:
        base_config = yaml.safe_load(f)
        
    data_path = project_root / "data" / "raw" / "ES.csv"
    df = pd.read_csv(data_path)
    
    # Pre-calculate base indicators
    df['rsi'] = ind.rsi(df['Close'], 2)
    df['composite_rsi'] = ind.composite_rsi(df['Close'], 2, 24)
    # Hurst needs to be calculated per window in the loop if we optimize it, 
    # but for a stability heatmap let's optimize RSI High vs RSI Low for a fixed Hurst Window.
    df['hurst'] = ind.hurst_exponent(df['High'], df['Low'], df['Close'], 20)
    
    # 2. Define Grid
    # Stability of RSI Thresholds
    rsi_low_range = np.arange(5, 21, 2)
    rsi_high_range = np.arange(15, 31, 2)
    
    results = np.zeros((len(rsi_low_range), len(rsi_high_range)))
    
    print(f"Generating heatmap for RSI Low vs RSI High...")
    
    params = {
        'hurst_threshold': base_config['entry_thresholds']['hurst_threshold'],
        'max_profitable_closes': base_config['exit_thresholds']['max_profitable_closes'],
        'composite_rsi_threshold': base_config['exit_thresholds']['composite_rsi_threshold'],
        'max_bars_in_trade': base_config['exit_thresholds']['max_bars_in_trade']
    }
    
    for i, r_low in enumerate(rsi_low_range):
        for j, r_high in enumerate(rsi_high_range):
            if r_high <= r_low:
                results[i, j] = np.nan
                continue
                
            test_params = params.copy()
            test_params['rsi_low'] = r_low
            test_params['rsi_high'] = r_high
            
            res = vectorized_run(df, test_params)
            results[i, j] = res['sharpe']
            
    # 3. Plotting
    plt.style.use('dark_background')
    plt.figure(figsize=(10, 8))
    
    df_heatmap = pd.DataFrame(results, index=rsi_low_range, columns=rsi_high_range)
    sns.heatmap(df_heatmap, annot=True, fmt=".2f", cmap="RdYlGn", center=0)
    
    plt.title("Parameter Stability: RSI Low vs RSI High (Sharpe Ratio)", fontweight='bold')
    plt.xlabel("RSI High Threshold")
    plt.ylabel("RSI Low Threshold")
    
    plot_dir = project_root / "reports" / "plots"
    os.makedirs(plot_dir, exist_ok=True)
    plt.savefig(plot_dir / "heatmap_rsi_stability.png")
    print(f"Heatmap saved to {plot_dir / 'heatmap_rsi_stability.png'}")
    plt.show()

if __name__ == "__main__":
    main()

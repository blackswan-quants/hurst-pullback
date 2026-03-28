import os
import sys
import pandas as pd
import numpy as np
import yaml
import matplotlib.pyplot as plt
from pathlib import Path

# Handle both module and direct execution
try:
    from src.core import indicators as ind
    from src.core.fast_engine import vectorized_run
    from src.core import metrics
except ImportError:
    # If running directly, add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.core import indicators as ind
    from src.core.fast_engine import vectorized_run
    from src.core import metrics

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
    df['hurst'] = ind.hurst_exponent(df['High'], df['Low'], df['Close'], 20)
    
    # 2. Define Building Steps
    # Step 1: Hurst Filter Only (Relax RSI to 0-100)
    step1_params = {
        'rsi_low': 0, 'rsi_high': 100, 
        'hurst_threshold': 50,
        'max_profitable_closes': 999, # Disable prof exit
        'composite_rsi_threshold': 100, # Disable RSI exit
        'max_bars_in_trade': 11
    }
    # Step 2: Hurst + RSI Entry
    step2_params = step1_params.copy()
    step2_params.update({'rsi_low': 10, 'rsi_high': 20})
    
    # Step 3: Hurst + RSI + Composite RSI Exit
    step3_params = step2_params.copy()
    step3_params.update({'composite_rsi_threshold': 50})
    
    # Step 4: Full Strategy (including Profitable Closes)
    step4_params = step3_params.copy()
    step4_params.update({'max_profitable_closes': 5})
    
    steps = [
        ("Hurst Only", step1_params),
        ("Hurst + RSI(2) Entry", step2_params),
        ("Hurst + RSI + CompRSI Exit", step3_params),
        ("Full Strategy", step4_params)
    ]
    
    # 3. Running and Plotting
    plt.style.use('dark_background')
    fig, axes = plt.subplots(4, 1, figsize=(14, 16), sharex=True)
    
    for i, (label, params) in enumerate(steps):
        res = vectorized_run(df, params)
        eq_pct = (res['equity'] - 1.0) * 100
        
        axes[i].plot(eq_pct.values, color='#10b981', linewidth=1.5)
        axes[i].set_title(f"Step {i+1}: {label} (Sharpe: {res['sharpe']:.2f})", loc='left', fontweight='bold')
        axes[i].set_ylabel("Profit %")
        axes[i].grid(True, alpha=0.1)
        axes[i].axhline(0, color='white', alpha=0.2)
        
    plt.xlabel("Cumulative Trades")
    plt.tight_layout()
    
    plot_dir = project_root / "reports" / "plots"
    os.makedirs(plot_dir, exist_ok=True)
    plt.savefig(plot_dir / "strategy_building_steps.png")
    print(f"Building steps plot saved to {plot_dir / 'strategy_building_steps.png'}")
    plt.show()

if __name__ == "__main__":
    main()

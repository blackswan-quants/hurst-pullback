import os
import sys
import pandas as pd
import numpy as np
import yaml
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
    
    # 1. Config & Assets discovery
    config_path = project_root / "configs" / "base.yaml"
    with open(config_path, 'r') as f:
        base_config = yaml.safe_load(f)
        
    data_dir = project_root / "data" / "raw"
    assets = ["ES", "NQ", "YM", "EMD"]
    
    params = {
        'rsi_low': base_config['entry_thresholds']['rsi_low'],
        'rsi_high': base_config['entry_thresholds']['rsi_high'],
        'hurst_threshold': base_config['entry_thresholds']['hurst_threshold'],
        'max_profitable_closes': base_config['exit_thresholds']['max_profitable_closes'],
        'composite_rsi_threshold': base_config['exit_thresholds']['composite_rsi_threshold'],
        'max_bars_in_trade': base_config['exit_thresholds']['max_bars_in_trade']
    }
    
    summary_results = []
    
    print(f"Starting Cross-Asset Comparison...")
    print(f"{'Asset':<10} | {'Trades':>6} | {'Profit%':>10} | {'Sharpe':>8} | {'Win%':>8} | {'Expectancy':>10}")
    print("-" * 65)
    
    for ticker in assets:
        data_path = data_dir / f"{ticker}.csv"
        if not data_path.exists():
            print(f"Asset {ticker} not found at {data_path}")
            continue
            
        df = pd.read_csv(data_path)
        
        # Pre-calculate indicators
        df['rsi'] = ind.rsi(df['Close'], 2)
        df['composite_rsi'] = ind.composite_rsi(df['Close'], 2, 24)
        df['hurst'] = ind.hurst_exponent(df['High'], df['Low'], df['Close'], 20)
        
        res = vectorized_run(df, params)
        
        if res['trades']:
            t_df = pd.DataFrame(res['trades'])
            win_r = metrics.win_rate(t_df['profit']) * 100
            exp = metrics.expectancy(t_df['profit'])
            
            print(f"{ticker:<10} | {len(res['trades']):>6} | {res['profit']:>9.2f}% | {res['sharpe']:>8.2f} | {win_r:>7.1f}% | {exp:>9.4f}")
            
            summary_results.append({
                'Asset': ticker,
                'Trades': len(res['trades']),
                'Profit%': res['profit'],
                'Sharpe': res['sharpe'],
                'Win%': win_r,
                'Expectancy': exp
            })
        else:
            print(f"{ticker:<10} | {'No Trades':^43}")
            
    # Save results to a CSV for report inclusion
    summary_df = pd.DataFrame(summary_results)
    report_dir = project_root / "reports"
    os.makedirs(report_dir, exist_ok=True)
    summary_df.to_csv(report_dir / "cross_asset_comparison.csv", index=False)
    print(f"\nSummary saved to {report_dir / 'cross_asset_comparison.csv'}")

if __name__ == "__main__":
    main()

import yaml
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Handle both module and direct execution
try:
    from ..strategy.strategy import Strategy
    from ..core.engine import run
    from ..core import metrics
except ImportError:
    # If running directly, add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.strategy.strategy import Strategy
    from src.core.engine import run
    from src.core import metrics

# Default optimization parameters
DEFAULT_PARAM = "rsi_period"
DEFAULT_RANGE = "2:1:10"
DEFAULT_SPLIT = "70 30 1"

def get_optimizable_params(config: dict, parent_key: str = "") -> list:
    """
    Recursively find all numeric parameters in the config.
    """
    params = []
    for k, v in config.items():
        if isinstance(v, dict):
            params.extend(get_optimizable_params(v, k))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            params.append(k)
    return params

def update_nested_config(config: dict, key_to_find: str, new_value: any) -> bool:
    """
    Recursively find a key in a nested dict and update its value.
    """
    for key, value in config.items():
        if key == key_to_find:
            config[key] = new_value
            return True
        elif isinstance(value, dict):
            if update_nested_config(value, key_to_find, new_value):
                return True
    return False

def plot_unified_equity(windows_data: list, title: str):
    """
    Display a unified equity curve for multiple Walk Forward windows.
    windows_data: list of dicts {'is_eq': pd.Series, 'oos_eq': pd.Series}
    """
    plt.style.use('dark_background')
    plt.figure(figsize=(14, 7))
    
    current_offset = 0
    cumulative_multiplier = 1.0
    
    is_color = '#10b981' # Emerald
    oos_color = '#3b82f6' # Blue
    
    all_is_segments = []
    all_oos_segments = []
    split_lines = []

    for i, window in enumerate(windows_data):
        is_eq = window['is_eq']
        oos_eq = window['oos_eq']
        best_p = window['param']
        
        # IIS Plot
        is_len = len(is_eq)
        is_range = range(current_offset, current_offset + is_len)
        is_vals = (is_eq * cumulative_multiplier - 1.0) * 100
        plt.plot(is_range, is_vals, color=is_color, linewidth=2, 
                 label='In-Sample (IIS)' if i == 0 else "")
        
        # Parameter Annotation inside IIS portion
        # Place it near the top of the segment for visibility
        y_text = is_vals.max()
        plt.text(current_offset + is_len/2, y_text, f"P={best_p}", 
                 color='#ffffff', fontsize=10, fontweight='bold', 
                 ha='center', va='bottom', bbox=dict(facecolor=is_color, alpha=0.4, edgecolor='none'))
        
        current_offset += is_len - 1
        cumulative_multiplier *= is_eq.iloc[-1]
        
        # Split vertical line
        plt.axvline(x=current_offset, color='#f8fafc', linestyle=':', alpha=0.3, linewidth=1)
        split_lines.append(current_offset)
        
        # OOS Plot
        oos_len = len(oos_eq)
        oos_range = range(current_offset, current_offset + oos_len)
        oos_vals = (oos_eq * cumulative_multiplier - 1.0) * 100
        plt.plot(oos_range, oos_vals, color=oos_color, linewidth=2, 
                 label='Out-of-Sample (OOS)' if i == 0 else "")
        
        current_offset += oos_len - 1
        cumulative_multiplier *= oos_eq.iloc[-1]
        
        # End of Window vertical line (if not last)
        if i < len(windows_data) - 1:
            plt.axvline(x=current_offset, color='#ef4444', linestyle='--', alpha=0.4, linewidth=1.5)

    plt.title(title, loc='left', fontsize=14, fontweight='bold', color='#f8fafc', pad=20)
    plt.xlabel('Cumulative Trades', fontweight='bold', color='#94a3b8')
    plt.ylabel('Cumulative Return %', fontweight='bold', color='#94a3b8')
    
    plt.grid(True, linestyle='--', alpha=0.1, color='#475569')
    plt.axhline(0, color='#f8fafc', linewidth=1, alpha=0.2)
    plt.legend(frameon=False, loc='upper left')
    
    plt.tight_layout()
    plt.show()

def get_performance_summary(all_trades: list, returns_sr: pd.Series, eq_curve: pd.Series, start_date=None, end_date=None) -> dict:
    """
    Calculate a set of summary metrics for a backtest run.
    """
    if not all_trades:
        return {
            'Profit %': 0.0,
            'Sharpe': 0.0,
            'Win Rate': 0.0,
            'Expectancy': 0.0,
            'Trades': 0,
            'Returns': pd.Series(dtype=float)
        }
    
    total_return = (eq_curve.iloc[-1] - 1.0) * 100
    sharpe = metrics.sharpe_ratio(returns_sr, 252, start_date=start_date, end_date=end_date)
    win_r = metrics.win_rate(returns_sr) * 100
    exp = metrics.expectancy(returns_sr)
    
    return {
        'Profit %': total_return,
        'Sharpe': sharpe,
        'Win Rate': win_r,
        'Expectancy': exp,
        'Trades': len(all_trades),
        'Returns': returns_sr
    }

def main():
    # 0. Setup and Config Loading
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "configs" / "base.yaml"
    with open(config_path, 'r') as file:
        base_config = yaml.safe_load(file)

    print("="*50)
    print("      WALK FORWARD STRATEGY OPTIMIZER")
    print("="*50)
    
    # Extract and show available parameters
    all_params = get_optimizable_params(base_config)
    print("\nAVAILABLE PARAMETERS TO OPTIMIZE:")
    print("-" * 50)
    for p in sorted(all_params):
        highlight = " <-- [DEFAULT]" if p == DEFAULT_PARAM else ""
        bullet = ">" if p == DEFAULT_PARAM else " "
        print(f" {bullet} {p}{highlight}")
    print("-" * 50)

    # 1. Inputs
    p_input = input(f"\nSelect parameter name [{DEFAULT_PARAM}]: ").strip()
    param_name = p_input if p_input else DEFAULT_PARAM
    
    print("\nEXAMPLE RANGES:")
    print(f" - rsi_period: 2:1:10 (start from 2, step 1, end at 10)")
    r_input = input(f"Enter range (start:step:end) [{DEFAULT_RANGE}]: ").strip()
    range_str = r_input if r_input else DEFAULT_RANGE
    
    print("\nEXAMPLE SPLITS:")
    print(f" - 70 30 1: One window (70% IS, 30% OOS)")
    print(f" - 70 30 2: Two windows (each has 35% IS, 15% OOS segment)")
    s_input = input(f"Enter split (IS_PCT OOS_PCT NUM_WINDOWS) [{DEFAULT_SPLIT}]: ").strip()
    split_str = s_input if s_input else DEFAULT_SPLIT
    
    try:
        start, step, end = map(float, range_str.split(':'))
        param_values = np.arange(start, end + (step/10), step)
        
        parts = split_str.split()
        is_pct, oos_pct = float(parts[0]), float(parts[1])
        num_windows = int(parts[2]) if len(parts) > 2 else 1
    except Exception as e:
        print(f"Error parsing inputs: {e}")
        return

    # 2. Data Loading
    data_path = project_root / "data" / "raw" / "NQ.csv"
    try:
        df_full = pd.read_csv(data_path)
    except Exception as e:
        print(f"Failed to load data: {e}")
        return

    # 3. Walk Forward Execution
    windows_results = []
    total_len = len(df_full)
    window_total_pct = is_pct + oos_pct
    points_per_window = total_len // num_windows
    
    print(f"\nExecuting {num_windows} Walk Forward Windows...")
    print("-" * 50)

    for w in range(num_windows):
        start_idx = w * points_per_window
        end_idx = (w + 1) * points_per_window if w < num_windows - 1 else total_len
        
        window_df = df_full.iloc[start_idx:end_idx]
        split_idx = int(len(window_df) * (is_pct / window_total_pct))
        
        df_is = window_df.iloc[:split_idx].copy().reset_index(drop=True)
        df_oos = window_df.iloc[split_idx:].copy().reset_index(drop=True)
        
        # Determine window dates for real duration scaling
        try:
            if 'Date' in window_df.columns and 'Time' in window_df.columns:
                is_start = pd.to_datetime(df_is.iloc[0]['Date'] + ' ' + df_is.iloc[0]['Time'])
                is_end = pd.to_datetime(df_is.iloc[-1]['Date'] + ' ' + df_is.iloc[-1]['Time'])
                oos_start = pd.to_datetime(df_oos.iloc[0]['Date'] + ' ' + df_oos.iloc[0]['Time'])
                oos_end = pd.to_datetime(df_oos.iloc[-1]['Date'] + ' ' + df_oos.iloc[-1]['Time'])
            elif 'date' in window_df.columns:
                is_start = pd.to_datetime(df_is.iloc[0]['date'])
                is_end = pd.to_datetime(df_is.iloc[-1]['date'])
                oos_start = pd.to_datetime(df_oos.iloc[0]['date'])
                oos_end = pd.to_datetime(df_oos.iloc[-1]['date'])
            else:
                is_start, is_end, oos_start, oos_end = None, None, None, None
        except Exception:
            is_start, is_end, oos_start, oos_end = None, None, None, None

        print(f"\nWINDOW {w+1}/{num_windows}: IS {len(df_is)} bars, OOS {len(df_oos)} bars")
        print(f"{'Value':>8} | {'Profit %':>10} | {'Sharpe':>8} | {'Win%':>8} | {'Trades':>6}")
        print("-" * 50)
        
        # Optimize IS
        best_val = None
        best_is_perf = None
        best_is_eq = None
        max_profit = -float('inf')
        
        for val in param_values:
            actual_val = int(val) if val == int(val) else val
            run_cfg = yaml.safe_load(yaml.dump(base_config))
            update_nested_config(run_cfg, param_name, actual_val)
            
            strategy = Strategy(run_cfg)
            trades = run(df_is, strategy)
            
            if trades:
                t_df = pd.DataFrame(trades)
                eq = metrics.cumulative_return(t_df['profit'])
                perf = get_performance_summary(trades, t_df['profit'], eq, start_date=is_start, end_date=is_end)
                
                print(f"{actual_val:>8} | {perf['Profit %']:>10.2f}% | {perf['Sharpe']:>8.2f} | {perf['Win Rate']:>7.1f}% | {perf['Trades']:>6}")
                
                if perf['Profit %'] > max_profit:
                    max_profit = perf['Profit %']
                    best_val = actual_val
                    best_is_perf = perf
                    best_is_eq = eq
            else:
                print(f"{actual_val:>8} | {'No Trades':^37}")
        
        if best_val is None:
            print(f" [!] No trades found in In-Sample Window {w+1}")
            continue
            
        # Validate OOS
        oos_cfg = yaml.safe_load(yaml.dump(base_config))
        update_nested_config(oos_cfg, param_name, best_val)
        oos_strategy = Strategy(oos_cfg)
        oos_trades = run(df_oos, oos_strategy)
        
        if oos_trades:
            o_df = pd.DataFrame(oos_trades)
            o_eq = metrics.cumulative_return(o_df['profit'])
            oos_perf = get_performance_summary(oos_trades, o_df['profit'], o_eq, start_date=oos_start, end_date=oos_end)
            
            windows_results.append({
                'window': w+1,
                'param': best_val,
                'is_perf': best_is_perf,
                'oos_perf': oos_perf,
                'is_eq': best_is_eq,
                'oos_eq': o_eq
            })
            print(f" Best Param: {best_val} | IS Profit: {best_is_perf['Profit %']:.2f}% | OOS Profit: {oos_perf['Profit %']:.2f}%")
        else:
            print(f" Best Param: {best_val} | IS Profit: {best_is_perf['Profit %']:.2f}% | OOS: No Trades")

    if not windows_results:
        print("\nNo WFO results generated.")
        return

    # 4. Final Aggregated Reporting
    print("\n" + "="*60)
    print(f"{'WALK FORWARD AGGREGATED RESULTS':^60}")
    print("="*60)
    print(f"{'Win#':<4} | {'Param':>6} | {'IIS Profit':>10} | {'OOS Profit':>10} | {'OOS Trades':>6}")
    print("-" * 60)
    
    all_is_returns = []
    all_oos_returns = []
    
    for res in windows_results:
        print(f"{res['window']:<4} | {res['param']:>6} | {res['is_perf']['Profit %']:>9.2f}% | {res['oos_perf']['Profit %']:>9.2f}% | {res['oos_perf']['Trades']:>10}")
        all_is_returns.append(res['is_perf']['Returns'])
        all_oos_returns.append(res['oos_perf']['Returns'])
    
    # Simple aggregations
    avg_is_profit = sum(r['is_perf']['Profit %'] for r in windows_results) / len(windows_results)
    avg_oos_profit = sum(r['oos_perf']['Profit %'] for r in windows_results) / len(windows_results)
    
    print("-" * 60)
    print(f"{'AVG':<4} | {'-':>6} | {avg_is_profit:>9.2f}% | {avg_oos_profit:>9.2f}% | {'-':>10}")
    print("="*60)

    # 5. Final Unified Plot
    plot_unified_equity(windows_results, f"WALK FORWARD PERFORMANCE: {param_name} ({num_windows} Windows)")

if __name__ == "__main__":
    main()

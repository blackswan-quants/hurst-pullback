import yaml
import sys
from pathlib import Path
import pandas as pd 
import copy

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

def main() -> None:
    """
    Execute ablation study to determine the contribution of each strategy component.
    
    The study performs:
    1. A 'Baseline' run with all components enabled.
    2. 'Ablation' runs where one component is disabled at a time.
    3. Performance comparison and contribution report generation.
    """
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "configs" / "base.yaml"
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Use the synchronized raw data for ES
    data_path = project_root / "data" / "raw" / "ES.csv"
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # All ablation toggles to test
    ablation_flags = [
        'use_rsi', 
        'use_hurst', 
        'use_composite_rsi', 
        'use_time_exit', 
        'use_RSI_exit', 
        'use_take_profit'
    ]

    results = []

    # Extract dates for scaling
    try:
        if 'Date' in df.columns and 'Time' in df.columns:
            start_date = pd.to_datetime(df.iloc[0]['Date'] + ' ' + df.iloc[0]['Time'])
            end_date = pd.to_datetime(df.iloc[-1]['Date'] + ' ' + df.iloc[-1]['Time'])
        elif 'date' in df.columns:
            start_date = pd.to_datetime(df.iloc[0]['date'])
            end_date = pd.to_datetime(df.iloc[-1]['date'])
        else:
            start_date, end_date = None, None
    except Exception:
        start_date, end_date = None, None

    # 1. Baseline Run (Full Strategy)
    print("Running Baseline (Full Strategy)...")
    baseline_config = copy.deepcopy(config)
    # Ensure all are TRUE for baseline
    for flag in ablation_flags:
        baseline_config['ablation'][flag] = True
    
    baseline_strategy = Strategy(baseline_config)
    baseline_trades = run(df, baseline_strategy)
    baseline_metrics = calculate_metrics(baseline_trades, start_date=start_date, end_date=end_date)
    results.append({
        "component": "FULL_STRATEGY",
        "metrics": baseline_metrics,
        "impact": "N/A"
    })

    # 2. Ablation Runs
    for flag in ablation_flags:
        print(f"Ablating {flag}...")
        test_config = copy.deepcopy(baseline_config)
        test_config['ablation'][flag] = False
        
        test_strategy = Strategy(test_config)
        test_trades = run(df, test_strategy)
        test_metrics = calculate_metrics(test_trades, start_date=start_date, end_date=end_date)
        
        # Calculate impact (Impact = Baseline - Restricted)
        # Positive impact means the component adds value.
        cagr_diff = baseline_metrics['cagr'] - test_metrics['cagr']
        sharpe_diff = baseline_metrics['sharpe'] - test_metrics['sharpe']
        
        results.append({
            "component": flag,
            "metrics": test_metrics,
            "impact_cagr": cagr_diff,
            "impact_sharpe": sharpe_diff
        })

    # 3. Print Report
    print_report(results)

def calculate_metrics(trades: list, start_date=None, end_date=None) -> dict:
    """Helper to calculate consistent metrics for a trade list."""
    if not trades:
        return {
            "count": 0, "win_rate": 0, "profit_factor": 0,
            "return": 0, "mdd": 0, "cagr": 0, "sharpe": 0
        }
    
    returns_sr = pd.Series([t['profit'] for t in trades])
    eq_curve = metrics.cumulative_return(returns_sr)
    
    cagr_v = metrics.cagr(eq_curve, 252, start_date=start_date, end_date=end_date)
    mdd_v = metrics.max_drawdown(eq_curve)
    sharpe_v = metrics.sharpe_ratio(returns_sr, 252, start_date=start_date, end_date=end_date)
    
    return {
        "count": len(trades),
        "win_rate": metrics.win_rate(returns_sr),
        "profit_factor": metrics.profit_factor(returns_sr),
        "return": (eq_curve.iloc[-1] - 1.0),
        "mdd": mdd_v,
        "cagr": cagr_v,
        "sharpe": sharpe_v
    }

def print_report(results: list) -> None:
    """Generate a clean CLI report for the ablation study."""
    print("\n" + "="*80)
    print(f"{'COMPONENT ABLATION STUDY':^80}")
    print("="*80)
    print(f"{'Feature Disabled':<20} | {'Trades':<6} | {'Win%':<6} | {'CAGR':<8} | {'MDD':<8} | {'Sharpe':<6} | {'Impact'}")
    print("-" * 80)
    
    baseline = results[0]['metrics']
    
    for res in results:
        m = res['metrics']
        comp = res['component']
        
        if comp == "FULL_STRATEGY":
            impact_str = "[BASELINE]"
            name = "FULL STRATEGY"
        else:
            # Impact is how much value this component ADDS to the strategy
            impact_val = res['impact_cagr'] * 100
            impact_str = f"{impact_val:+.2f}% CAGR"
            name = comp.replace('use_', '')

        print(f"{name:<20} | {m['count']:<6} | {m['win_rate']*100:>5.1f}% | {m['cagr']*100:>7.2f}% | {m['mdd']*100:>7.2f}% | {m['sharpe']:>6.2f} | {impact_str}")

    print("="*80)
    print("\nNOTE: 'Impact' measures how much CAGR is LOST when the component is disabled.")
    print("Positive Impact indicates the component significantly improves performance.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
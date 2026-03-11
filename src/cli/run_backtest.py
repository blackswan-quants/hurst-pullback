import yaml 
import sys
from pathlib import Path
import pandas as pd

# Handle both module and direct execution
try:
    from ..strategy.strategy import Strategy
    from ..core.engine import run
except ImportError:
    # If running directly, add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.strategy.strategy import Strategy
    from src.core.engine import run

def main() -> None:
    """
    Main entrypoint for executing a single backtest.
    Steps:
    1. Load YAML configuration.
    2. Load and clean data.
    3. Initialize Strategy instance.
    4. Run backtest through engine.
    5. Print resulting equity and metrics.
    """
    # Get project root directory
    project_root = Path(__file__).parent.parent.parent
    
    config_path = project_root / "configs" / "base.yaml"
    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
    
    #### dataframe loading ####
    data_path = project_root / "data" / "clean" / "ES_clean.csv"
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f'File not found: {data_path}. Cannot load the dataframe.')
        return
    except Exception as e:
        print(f'An unexpected error occurred during file loading: {e}')
        return
    
    #### backtest running ####
    strategy = Strategy(data)
    all_trades = run(df[:200], strategy)
    print(f"Completed {len(all_trades)} trades")
    
    if len(all_trades) == 0:
        print("No trades executed. Cannot calculate metrics.")
        return

    # Generate metrics dataframes
    from src.core import metrics
    trades_df = pd.DataFrame(all_trades)
    
    if 'profit' not in trades_df.columns:
        print("Error: 'profit' not tracked correctly in all_trades output.")
        return

    returns_sr = trades_df['profit']
    eq_curve = metrics.cumulative_return(returns_sr)
    
    # Calculate Ratios
    win_r = metrics.win_rate(returns_sr)
    prof_fact = metrics.profit_factor(returns_sr)
    expectancy = metrics.expectancy(returns_sr)
    avg_w, avg_l = metrics.avg_win_avg_loss(returns_sr)
    
    # Core Ratios (assuming these returns act as periodic events; typical logic maps these against timestamps)
    # Using 252 for daily equivalent but scaling might vary if trades aren't 1-per-day
    cagr_v = metrics.cagr(eq_curve, 252)
    mdd_v = metrics.max_drawdown(eq_curve)
    sharpe_v = metrics.sharpe_ratio(returns_sr, 252)
    sortino_v = metrics.sortino_ratio(returns_sr, 252)
    calmar_v = metrics.calmar_ratio(cagr_v, mdd_v)

    # Output Formatting Block
    print("\n" + "="*45)
    print("BACKTEST PERFORMANCE METRICS SUMMARY")
    print("="*45)
    print(f"Total Trades        : {len(all_trades)}")
    print(f"Win Rate            : {win_r * 100:.2f}%")
    print(f"Expectancy          : {expectancy:.4f}")
    if prof_fact == float('inf'):
        print(f"Profit Factor       : INF (No Losses)")
    else:
        print(f"Profit Factor       : {prof_fact:.4f}")
    print(f"Average Win         : {avg_w:.4f}")
    print(f"Average Loss        : {avg_l:.4f}")
    print("-" * 45)
    print(f"Cumulative Return   : {(eq_curve.iloc[-1] - 1.0) * 100:.2f}%")
    print(f"Max Drawdown        : {mdd_v * 100:.2f}%")
    print(f"CAGR                : {cagr_v * 100:.2f}%")
    print("-" * 45)
    print(f"Sharpe Ratio        : {sharpe_v:.2f}")
    print(f"Sortino Ratio       : {sortino_v:.2f}")
    print(f"Calmar Ratio        : {calmar_v:.2f}")
    print("="*45 + "\n")

if __name__ == "__main__":
    main()



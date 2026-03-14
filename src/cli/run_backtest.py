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

import matplotlib.pyplot as plt
import os

def plot_performance(trades_df: pd.DataFrame, eq_curve: pd.Series, project_root: Path, ticker: str = "Strategy") -> None:
    """
    Generate and save performance plots with a professional Dark Mode aesthetic.
    """
    # Create directory if not exists
    report_dir = project_root / "reports" / "plots"
    os.makedirs(report_dir, exist_ok=True)
    
    ticker_upper = ticker.upper()
    
    # --- GLOBAL STYLING ---
    plt.rcParams.update({
        'figure.facecolor': '#0f172a',
        'axes.facecolor': '#0f172a',
        'axes.edgecolor': '#334155',
        'axes.labelcolor': '#94a3b8',
        'text.color': '#f8fafc',
        'xtick.color': '#64748b',
        'ytick.color': '#64748b',
        'grid.color': '#1e293b',
        'font.family': 'sans-serif',
        'font.size': 10
    })
    
    # 1. Equity & Drawdown (Professional Combined Chart)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # Equity Curve
    eq_curve_pct = (eq_curve - 1.0) * 100
    ax1.plot(eq_curve_pct.values, label='Cumulative Profit %', color='#10b981', linewidth=2.5, alpha=0.9)
    ax1.fill_between(range(len(eq_curve_pct)), eq_curve_pct.values, 0, color='#10b981', alpha=0.1)
    
    ax1.set_title(f'{ticker_upper} - STRATEGY EQUITY PERFORMANCE', loc='left', fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel('Return (%)', fontweight='bold')
    ax1.legend(loc='upper left', frameon=False)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Drawdown Curve
    cumulative_max = eq_curve.cummax()
    drawdown = (eq_curve / cumulative_max - 1.0) * 100
    ax2.fill_between(range(len(drawdown)), drawdown.values, 0, color='#ef4444', alpha=0.3, label='Drawdown')
    ax2.plot(drawdown.values, color='#ef4444', linewidth=1, alpha=0.6)
    
    ax2.set_title('UNDERWATER DRAWDOWN (%)', loc='left', fontsize=12, fontweight='bold', pad=10)
    ax2.set_ylabel('DD %', fontweight='bold')
    ax2.set_xlabel('Trade Index', fontweight='bold')
    ax2.set_ylim(None, 0.5) # Focus on the depth
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout(pad=3.0)
    plt.savefig(report_dir / f"{ticker.lower()}_equity_drawdown.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    # 2. Trade Distribution (histogram)
    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    returns_pct = trades_df['profit'] * 100
    
    # Histogram with emerald/rose split
    n, bins, patches = plt.hist(returns_pct, bins=40, edgecolor='#0f172a', linewidth=1, alpha=0.8)
    for c, p in zip(bins, patches):
        if c < 0:
            p.set_facecolor('#ef4444')
        else:
            p.set_facecolor('#10b981')
            
    plt.axvline(returns_pct.mean(), color='#facc15', linestyle='--', linewidth=2, label=f'Avg Trade: {returns_pct.mean():.2f}%')
    plt.axvline(0, color='#f8fafc', linewidth=1.5, alpha=0.8)
    
    plt.title(f'{ticker_upper} - DISTRIBUTION OF TRADE RETURNS (%)', loc='left', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Individual Trade Return %', fontweight='bold')
    plt.ylabel('Frequency', fontweight='bold')
    plt.legend(frameon=False)
    plt.grid(True, linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(report_dir / f"{ticker.lower()}_trade_distribution.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n[SUCCESS] {ticker_upper} professional charts saved to: {report_dir}")

import argparse

def main() -> None:
    """
    Main entrypoint for executing a single backtest.
    Steps:
    1. Load YAML configuration.
    2. Load and clean data based on CLI asset input.
    3. Initialize Strategy instance.
    4. Run backtest through engine.
    5. Print resulting equity and metrics.
    6. Generate visualization plots.
    """
    # Get project root directory
    project_root = Path(__file__).parent.parent.parent
    
    # 1. Discover available assets
    data_dir = project_root / "data" / "raw"
    available_assets = [f.stem for f in data_dir.glob("*.csv")]
    
    # 2. CLI Argument Parsing
    parser = argparse.ArgumentParser(description="Run Hurst Pullback Backtest on a specific asset.")
    parser.add_argument(
        "--asset", "-a", 
        type=str, 
        default="ES", 
        help=f"Ticker symbol to backtest. Available: {', '.join(available_assets)}"
    )
    args = parser.parse_args()
    
    ticker = args.asset.upper()
    
    if ticker not in available_assets:
        print(f"\n[ERROR] Asset '{ticker}' not found in {data_dir}")
        print(f"Available assets: {', '.join(available_assets)}")
        return

    config_path = project_root / "configs" / "base.yaml"
    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
    
    #### dataframe loading ####
    data_path = data_dir / f"{ticker}.csv"
    
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        print(f'An unexpected error occurred during file loading: {e}')
        return
    
    #### backtest running ####
    strategy = Strategy(data)
    all_trades = run(df, strategy)
    print(f"Completed {len(all_trades)} trades for {ticker}")
    
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
    
    # Calculate Statistics
    cagr_v = metrics.cagr(eq_curve, 252)
    mdd_v = metrics.max_drawdown(eq_curve)
    sharpe_v = metrics.sharpe_ratio(returns_sr, 252)
    sortino_v = metrics.sortino_ratio(returns_sr, 252)
    calmar_v = metrics.calmar_ratio(cagr_v, mdd_v)
    
    # New Stats
    avg_dur, max_dur, min_dur = metrics.trade_duration_stats(trades_df['bars'])
    max_w_p, max_l_p = metrics.extreme_trades(returns_sr)

    # Output Formatting Block
    print("\n" + "="*45)
    print(f"{f'BACKTEST PERFORMANCE: {ticker}':^45}")
    print("="*45)
    print(f"{'OVERALL PERFORMANCE':^45}")
    print("-" * 45)
    print(f"Cumulative Return   : {(eq_curve.iloc[-1] - 1.0) * 100:.2f}%")
    print(f"CAGR                : {cagr_v * 100:.2f}%")
    print(f"Max Drawdown        : {mdd_v * 100:.2f}%")
    print(f"Sharpe Ratio        : {sharpe_v:.2f}")
    print(f"Sortino Ratio       : {sortino_v:.2f}")
    print(f"Calmar Ratio        : {calmar_v:.2f}")
    print("-" * 45)
    
    print(f"{'TRADE STATISTICS':^45}")
    print("-" * 45)
    print(f"Total Trades        : {len(all_trades)}")
    print(f"Win Rate            : {win_r * 100:.2f}%")
    print(f"Expectancy          : {expectancy:.4f}")
    if prof_fact == float('inf'):
        print(f"Profit Factor       : INF (No Losses)")
    else:
        print(f"Profit Factor       : {prof_fact:.4f}")
    print(f"Average Win         : {avg_w * 100:.2f}%")
    print(f"Average Loss        : {avg_l * 100:.2f}%")
    print(f"Max Win             : {max_w_p * 100:.2f}%")
    print(f"Max Loss            : {max_l_p * 100:.2f}%")
    print("-" * 45)
    
    print(f"{'DURATION STATISTICS (Bars)':^45}")
    print("-" * 45)
    print(f"Average Duration    : {avg_dur:.1f}")
    print(f"Max Duration        : {max_dur}")
    print(f"Min Duration        : {min_dur}")
    print("-" * 45)
    
    # Exit Reason Breakdown
    print(f"{'EXIT REASON BREAKDOWN':^45}")
    if 'exit_reason' in trades_df.columns:
        reasons = trades_df['exit_reason'].value_counts()
        for reason, count in reasons.items():
            pct = (count / len(all_trades)) * 100
            print(f"{reason:<20}: {count:>3} ({pct:>5.1f}%)")
    else:
        print("Exit reasons not available.")
    print("-" * 45)

    # Transaction Cost Impact
    print(f"{'TRANSACTION COST IMPACT':^45}")
    cost_cfg = data.get('transaction_costs', {})
    drag_per_trade = cost_cfg.get('round_trip_point_drag', 0.0)
    total_drag = drag_per_trade * len(all_trades)
    
    print(f"Drag Per Trade (Pts) : {drag_per_trade:.4f}")
    print(f"Total Points Lost    : {total_drag:.2f}")
    print("="*45 + "\n")

    # Generate Visualization
    plot_performance(trades_df, eq_curve, project_root, ticker)

if __name__ == "__main__":
    main()



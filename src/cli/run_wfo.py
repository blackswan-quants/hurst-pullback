import os
import sys
import pandas as pd
import numpy as np
import yaml
import itertools
import matplotlib.pyplot as plt
from pathlib import Path

# Handle both module and direct execution
try:
    from src.core import indicators as ind
    from src.core import metrics
except ImportError:
    # If running directly, add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.core import indicators as ind
    from src.core import metrics

def make_folds(data, is_bars, oos_bars, anchored=False):
    """Step 2 - Partition the data into folds (sliding window)"""
    folds = []
    start = 0
    while True:
        is_end = start + is_bars
        oos_end = is_end + oos_bars
        if oos_end > len(data):
            break
        is_start = 0 if anchored else start
        folds.append({
            "is": data.iloc[is_start : is_end].copy().reset_index(drop=True),
            "oos": data.iloc[is_end : oos_end].copy().reset_index(drop=True),
            "start_idx": is_start,
            "split_idx": is_end,
            "end_idx": oos_end
        })
        start += oos_bars   # step forward by exactly one OOS block
    return folds

def vectorized_run(df, params, drag=0.5):
    """
    Lightweight backtest engine for optimization speed.
    Processes a dataframe with pre-calculated indicators.
    """
    # 1. Logic signals (computed once)
    rsi_vals = df['rsi']
    hurst_vals = df['hurst']
    comp_rsi_vals = df['composite_rsi']
    closes = df['Close'].values
    opens = df['Open'].values
    
    # Entry: RSI in range AND Hurst > threshold
    entry_signal = (rsi_vals >= params['rsi_low']) & (rsi_vals <= params['rsi_high']) & (hurst_vals > params['hurst_threshold'])
    
    # Pre-calculate profitable closes exit condition
    # is_prof: Close > Open
    is_prof = (closes > opens).astype(int)
    # rolling sum of 5
    n_prof = params['max_profitable_closes']
    prof_exit_mask = pd.Series(is_prof).rolling(n_prof).sum() == n_prof
    
    # Pre-calculate RSI exit
    rsi_exit_mask = comp_rsi_vals > params['composite_rsi_threshold']
    
    trades = []
    in_pos = False
    entry_idx = 0
    
    # Loop over bars (still a loop, but interior is very lean)
    # Using raw numpy arrays for speed
    entry_sig_v = entry_signal.values
    rsi_exit_v = rsi_exit_mask.values
    prof_exit_v = prof_exit_mask.values
    max_bars = params['max_bars_in_trade']
    
    for i in range(1, len(df)):
        if not in_pos:
            # Check entry on previous bar close, execute on current open
            if entry_sig_v[i-1]:
                in_pos = True
                entry_idx = i
                entry_price = opens[i]
        else:
            # Check exit conditions
            bars_in_trade = i - entry_idx + 1
            
            # 1. Time Exit
            time_exit = bars_in_trade >= max_bars
            # 2. RSI Exit
            rsi_exit = rsi_exit_v[i]
            # 3. Profitable Closes Exit
            # (only if we have enough bars to check)
            p_exit = prof_exit_v[i] if bars_in_trade >= n_prof else False
            
            if time_exit or rsi_exit or p_exit:
                exit_price = opens[i+1] if i+1 < len(df) else closes[i] # ideally open of next bar
                # Actually following strategy.py logic: exit is triggered by current bar, 
                # translator in engine.py sets signal='sell', 
                # then engine loop next i: trade['sell_price'] = df.iloc[i]['Open']
                # So it's the open of the bar FOLLOWING the signal trigger.
                
                # To match exactly: if signal on bar i, exit on bar i+1 open
                if i+1 < len(df):
                    exit_price = opens[i+1]
                else:
                    exit_price = closes[i] # last bar fallback
                
                profit = ((exit_price - entry_price) - drag) / entry_price
                trades.append({
                    'profit': profit,
                    'bars': bars_in_trade,
                    'entry_idx': entry_idx,
                    'exit_idx': i+1
                })
                in_pos = False
    
    if not trades:
        return {'trades': [], 'sharpe': -10, 'profit': 0, 'equity': pd.Series([1.0]*len(df))}
    
    t_df = pd.DataFrame(trades)
    eq = metrics.cumulative_return(t_df['profit'])
    # Sharpe needs periodic returns, but for optimization we can use Sharpe of trade returns 
    # as a proxy or interpolate back to daily. For speed, just use trade Sharpe.
    sharpe = metrics.sharpe_ratio(t_df['profit'])
    
    # Return full result for OOS stitching
    return {
        'trades': trades,
        'sharpe': sharpe if not np.isnan(sharpe) else -10,
        'profit': (eq.iloc[-1] - 1.0) * 100,
        'equity': eq
    }

def optimize_on_is(is_data, param_grid, objective="sharpe"):
    """Step 3 - The inner loop: optimize on IS"""
    best_params, best_score = None, -np.inf
    
    # Pre-calculate all Indicators for this IS fold once
    # This saves massive time vs calculating inside the grid loop
    is_data = is_data.copy()
    # Note: Using hardcoded common windows to avoid recalculating per grid point
    # but since hurst_window varies in user's grid, we might need to handle it.
    
    # For simplicity in this implementation, we pre-calculate indicators that depend
    # on parameters inside the loop ONLY if they change.
    # Actually, rsi_period is usually 2 (fixed in grid?), hurst_window varies.
    
    # Let's see the user's grid example:
    # hurst_window: [15, 20, 25, 30]
    # rsi_low, rsi_high, max_bars, max_prof : these DON'T affect indicator values
    
    # So we can cache indicators by their window/period
    cache_rsi = {}
    cache_hurst = {}
    cache_comp = {}
    
    for params in param_grid:
        p_rsi = 2 # hardcoded in strategy logic usually
        p_hurst = params['hurst_window']
        p_comp_s = 2
        p_comp_l = 24
        
        if p_rsi not in cache_rsi:
            cache_rsi[p_rsi] = ind.rsi(is_data['Close'], p_rsi)
        if p_hurst not in cache_hurst:
            cache_hurst[p_hurst] = ind.hurst_exponent(is_data['High'], is_data['Low'], is_data['Close'], p_hurst)
        if (p_comp_s, p_comp_l) not in cache_comp:
            cache_comp[(p_comp_s, p_comp_l)] = ind.composite_rsi(is_data['Close'], p_comp_s, p_comp_l)
            
        is_data['rsi'] = cache_rsi[p_rsi]
        is_data['hurst'] = cache_hurst[p_hurst]
        is_data['composite_rsi'] = cache_comp[(p_comp_s, p_comp_l)]
        
        # Fast backtest
        result = vectorized_run(is_data, params)
        score = result[objective]
        
        if score > best_score:
            best_score = score
            best_params = params
            
    return best_params, best_score

def main():
    # Step 1 - Define your parameter grid
    param_grid_raw = {
        "hurst_window":         [15, 20, 25, 30],
        "rsi_low":              [5, 10, 15],
        "rsi_high":             [15, 20, 25],
        "max_bars_in_trade":    [7, 11, 15],
        "max_profitable_closes":[3, 5, 7],
    }
    
    # itertools.product to build combinations
    keys, values = zip(*param_grid_raw.items())
    param_grid = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    # Load Data
    project_root = Path(__file__).parent.parent.parent
    data_path = project_root / "data" / "raw" / "ES.csv"
    df_full = pd.read_csv(data_path)
    
    # Load Config for default thresholds
    config_path = project_root / "configs" / "base.yaml"
    with open(config_path, 'r') as f:
        base_config = yaml.safe_load(f)
    
    # Extract fixed thresholds
    fixed_params = {
        "hurst_threshold": base_config['entry_thresholds']['hurst_threshold'],
        "composite_rsi_threshold": base_config['exit_thresholds']['composite_rsi_threshold']
    }
    
    # Step 2 - Partition the data into folds
    # IS = 500 bars, OOS = 126 bars (roughly 2 years IS, 6 months OOS for daily)
    folds = make_folds(df_full, is_bars=500, oos_bars=126, anchored=False)
    print(f"Generated {len(folds)} folds.")

    # Step 4 - The outer loop: evaluate on OOS
    oos_results = []
    
    for i, fold in enumerate(folds):
        print(f"Processing Fold {i+1}/{len(folds)}...")
        # Merge fixed params into each grid combination for the optimizer
        full_grid = []
        for p in param_grid:
            combo = p.copy()
            combo.update(fixed_params)
            full_grid.append(combo)
            
        best_params, is_score = optimize_on_is(fold["is"], full_grid)
        
        # Evaluate Best Params on OOS
        # Must recalculate indicators for OOS fold
        oos_data = fold["oos"].copy()
        oos_data['rsi'] = ind.rsi(oos_data['Close'], 2)
        oos_data['hurst'] = ind.hurst_exponent(oos_data['High'], oos_data['Low'], oos_data['Close'], best_params['hurst_window'])
        oos_data['composite_rsi'] = ind.composite_rsi(oos_data['Close'], 2, 24)
        
        oos_result = vectorized_run(oos_data, best_params)
        
        oos_results.append({
            "fold": i + 1,
            "params": best_params,
            "is_score": is_score,
            "oos_score": oos_result["sharpe"],
            "oos_profit": oos_result["profit"],
            "oos_trades": oos_result["trades"],
            "oos_equity": oos_result["equity"],
        })
        print(f"  Best Params: {best_params}")
        print(f"  IS Sharpe: {is_score:.2f} | OOS Sharpe: {oos_result['sharpe']:.2f} ({len(oos_result['trades'])} trades)")

    # Step 5 - Stitch the OOS equity curve
    # Need to handle cumulative multiplier for stitching
    stitched_returns = []
    for r in oos_results:
        # Extract trade profits
        trade_profits = [t['profit'] for t in r['oos_trades']]
        stitched_returns.extend(trade_profits)
    
    wf_equity_series = pd.Series(stitched_returns)
    wf_equity = metrics.cumulative_return(wf_equity_series)

    # Step 6 - Stability diagnostics
    print("\n" + "="*50)
    print("WALK FORWARD STABILITY DIAGNOSTICS")
    print("="*50)
    
    # IS vs OOS efficiency ratio
    # Add small epsilon to avoid div by zero
    efficiencies = [r["oos_score"] / (r["is_score"] if r["is_score"] != 0 else 0.0001) for r in oos_results]
    avg_efficiency = np.mean(efficiencies)
    print(f"Average Efficiency Ratio (OOS/IS): {avg_efficiency:.2f}")
    
    # Parameter stability
    param_df = pd.DataFrame([r["params"] for r in oos_results])
    print("\nParameter Stability across folds:")
    print(param_df.describe().loc[['mean', 'std']])

    # Final Plotting
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # 1. Walk Forward Equity Curve
    equity_vals = (wf_equity - 1.0) * 100
    ax1.plot(equity_vals, color='#3b82f6', linewidth=2)
    ax1.set_title("Walk-Forward OOS Equity Curve (%)", fontweight='bold')
    ax1.grid(True, alpha=0.1)
    
    # 2. IS vs OOS Sharpe comparison
    is_sharpes = [r["is_score"] for r in oos_results]
    oos_sharpes = [r["oos_score"] for r in oos_results]
    x = np.arange(len(folds))
    width = 0.35
    ax2.bar(x - width/2, is_sharpes, width, label='IS Sharpe', color='#10b981', alpha=0.7)
    ax2.bar(x + width/2, oos_sharpes, width, label='OOS Sharpe', color='#ef4444', alpha=0.7)
    ax2.set_title("IS vs OOS Sharpe per Fold")
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"F{i+1}" for i in x])
    ax2.legend()
    ax2.grid(True, alpha=0.1)

    plt.tight_layout()
    plot_path = project_root / "reports" / "plots" / "wfo_results.png"
    plt.savefig(plot_path)
    print(f"\nPlot saved to {plot_path}")
    plt.show()

if __name__ == "__main__":
    main()

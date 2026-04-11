import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from src.core import metrics

def test_metrics_fix():
    print("Testing Metrics Fix Verification...")
    print("-" * 40)
    
    # Simulate an equity curve from 10 trades over 2 years
    # Each trade is 1% profit
    returns = pd.Series([0.01] * 10)
    eq_curve = metrics.cumulative_return(returns)
    
    # Real Dates: 2 years apart
    start_date = pd.Timestamp('2020-01-01')
    end_date = pd.Timestamp('2022-01-01')
    
    # 1. Test CAGR
    # Total return is (1.01^10) - 1 = ~10.46%
    # Over 2 years, CAGR should be (1.1046^(1/2)) - 1 = ~5.1%
    cagr_real = metrics.cagr(eq_curve, start_date=start_date, end_date=end_date)
    cagr_old = metrics.cagr(eq_curve, periods_per_year=252) # The old default way
    
    print(f"Total Trades: {len(returns)}")
    print(f"Start Date  : {start_date}")
    print(f"End Date    : {end_date}")
    print(f"Years       : {(end_date - start_date).days / 365.25:.2f}")
    print(f"Eq Start    : {eq_curve.iloc[0]}")
    print(f"Eq End      : {eq_curve.iloc[-1]}")
    print(f"Calculated Years in metrics: {metrics._get_years(len(returns), 252, start_date, end_date)}")
    print("-" * 40)
    print(f"CAGR (Real Period): {cagr_real*100:.2f}%")
    print(f"CAGR (Old Way)    : {cagr_old*100:.4f}%  <-- Extremely high because it thinks it's 10 days")
    
    # 2. Test Sharpe Ratio
    # Annualized Sharpe = (Mean / Std) * sqrt(Trades_Per_Year)
    # Trades Per Year = 10 / 2 = 5
    sharpe_real = metrics.sharpe_ratio(returns, start_date=start_date, end_date=end_date)
    sharpe_old = metrics.sharpe_ratio(returns, periods_per_year=252)
    
    print("-" * 40)
    print(f"Sharpe (Real Period): {sharpe_real:.2f}")
    print(f"Sharpe (Old Way)    : {sharpe_old:.2f}  <-- Extremely high because it thinks there are 252 trades/year")
    
    assert cagr_real < 1.0 # Should be realistic
    assert cagr_real > 0.05 and cagr_real < 0.052
    
    print("-" * 40)
    print("VERIFICATION SUCCESSFUL")

if __name__ == "__main__":
    test_metrics_fix()

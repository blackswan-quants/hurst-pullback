import yaml
from src.core.loader import load_data
from src.core.engine import run
from src.strategy.strategy import Strategy
import pandas as pd 
import copy
import logging
from src.core.metrics import sharpe_ratio, max_drawdown, cagr, cumulative_return
import numpy as np
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    #filename = 'src/cli/ablation.log'    
)

def run_ablation() -> list:
    """
    Run ablation tests to isolate component contributions.
    Steps:
    1. Iterate over all ablation flags.
    2. Disable one component at a time.
    3. Re-run backtest and log performance differences.
    """
    
    
    
    with open("./configs/base.yaml", "r") as f:
        config = yaml.safe_load(f)

    df = pd.read_csv("./" + config['data']['clean_ES']) 
    #df = load_data(config['data']['clean_ES'])             !!!!! DA SOSTITUIRE

    

    config_opt = ['use_hurst', 'use_RSI_exit', 'use_take_profit']
    output = []

    for opt in config_opt:
        tmp_config = copy.deepcopy(config)
        tmp_config['ablation'][opt] = False
        strategy = Strategy(cfg=tmp_config)

        res = run(df=df, strategy=strategy)


        returns = pd.Series((t["profit"] for t in res)).dropna()

        equity_curve = cumulative_return(returns)

        win_rate = returns.sum() / len(returns)
        
        profit_factor = returns[returns > 0].sum() / abs(returns[returns < 0].sum())

        metrics = {
            "sharpe_ratio": sharpe_ratio(returns),
            "max_drawdown": max_drawdown(equity_curve),
            "cagr": cagr(equity_curve),
            "equity_curve": equity_curve,
            "win_rate": win_rate,
            "profit_factor": profit_factor
        }
        logging.info("-" * 50)
        logging.info("\nDISABLED feature: \t %s", opt)
        out = {
            "disaled_feature": opt,
            "all_trades": res,
            "metrics": metrics
        }
        output.append(out)
        

    return output

#if __name__ == '__main__':
#  main()
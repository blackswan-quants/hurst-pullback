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

logger = logging.getLogger('ablation')

def run_ablation() -> list:
    """
    Run ablation tests to isolate component contributions.
    Steps:
    1. Iterate over all ablation flags.
    2. Disable one component at a time.
    3. Re-run backtest and log performance differences.
    Output:
    list: A list of object:
        {
            'disabled_feature' (string): The control that was disabled
            'all_trades' (dict): All the trades made with this strategy
            'metrics' (dict): A list of metrics (sharpe ratio, max drawdown, cagr, win rate, profit factor)
        }
    """
    
    with open("./configs/base.yaml", "r") as f:
        config = yaml.safe_load(f)

    df = pd.read_csv("./" + config['data']['clean_ES']) 

    config_opt = ['use_hurst', 'use_RSI_exit', 'use_take_profit']
    output = []

    for opt in config_opt:
        tmp_config = copy.deepcopy(config)
        if tmp_config['ablation'][opt]:
            tmp_config['ablation'][opt] = False
        else:
            logging.error(f"The logic {opt} was not found!")
        strategy = Strategy(cfg=tmp_config)

        res = run(df=df, strategy=strategy)

        returns = pd.Series((t["net_profit"] for t in res)).dropna()

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
        logging.info("\tDISABLED feature: \t %s", opt)
        logging.info("-" * 50)
        logging.info(f"\t- sharpe ratio: {metrics['sharpe_ratio']}")
        logging.info(f"\t- max drawdown: {metrics['max_drawdown']}")
        logging.info(f"\t- cagr: {metrics['cagr']}")
        #logging.info(f"\t- equity curve: {metrics['equity_curve']}")
        logging.info(f"\t- win rate: {metrics['win_rate']}")
        logging.info(f"\t- profit factor: {metrics['profit_factor']}")
        logging.info("-" * 50)

        out = {
            "disaled_feature": opt,
            "all_trades": res,
            "metrics": metrics
        }
        output.append(out)
        
    return output
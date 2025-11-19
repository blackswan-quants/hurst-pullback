import yaml 
import logging 
from ..strategy.strategy import Strategy
from ..core.engine import run 
import pandas as pd

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
    with open('../../configs/base.yaml' , 'r') as file:
        data = yaml.safe_load(file)
    
    data_path = 'data/clean/NQ_clean.csv'
    try:
        df = pd.read_csv(data_path)
        # Log success
        logging.info('Successfully loaded the dataframe.')

    except FileNotFoundError:
        logging.error(f'File not found: {data_path}. Cannot load the dataframe.')
    except Exception as e:
        logging.error(f'An unexpected error occurred during file loading: {e}')

    strategy = Strategy(data)
    logging.info(strategy.get_cfg())
    all_trades = run(df , strategy)


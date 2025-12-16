import pytest
from src.core.engine import run
from src.strategy.strategy import Strategy
import yaml 
import logging 
import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).parent.parent
config_path = project_root / "configs" / "base.yaml"

@pytest.fixture
def base_config():
    """
    Configuration function for preparing the environment.
    """
    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
    
    data_path = project_root / "data" / "clean" / "NQ_clean.csv"
    try:
        df = pd.read_csv(data_path)
        logging.info('Successfully loaded the dataframe.')

    except FileNotFoundError:
        logging.error(f'File not found: {data_path}. Cannot load the dataframe.')
        return
    except Exception as e:
        logging.error(f'An unexpected error occurred during file loading: {e}')
        return
    
    strategy = Strategy(data)
    trades = run(df[:300], strategy)

    return trades

def test_commission_cost(base_config):
    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
    commission_cost = data['transaction_costs']['commission_per_contract']
    contract_size = data['transaction_costs']['contract_size']
    slippage_cost = data['transaction_costs']['slippage_per_contract']

    for trade in base_config:
        commission = 2 * (commission_cost / contract_size)
        expected_commission = trade['sell_price'] - trade['entry_price'] - (slippage_cost / contract_size) - (trade['net_sell_price'] - trade['net_entry_price'])

        assert pytest.approx(expected_commission) == commission

def test_slippage_cost(base_config):
    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
    commission_cost = data['transaction_costs']['commission_per_contract']
    contract_size = data['transaction_costs']['contract_size']
    slippage_cost = data['transaction_costs']['slippage_per_contract']

    for trade in base_config:
        slippage = (slippage_cost / contract_size)
        expected_slippage = trade['sell_price'] - trade['entry_price'] -  2 * (commission_cost / contract_size) - (trade['net_sell_price'] - trade['net_entry_price'])

        assert pytest.approx(expected_slippage) == slippage

def test_validate_profit(base_config):
    for trade in base_config:
        assert trade['net_profit'] == trade['profit'] - (trade['commission_cost'] + trade['slippage_cost'])


import yaml 
import logging 
import sys
from pathlib import Path
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from calendar import month_name

# Handle both module and direct execution
try:
    from ..strategy.strategy import Strategy
    from ..core.engine import run
except ImportError:
    # If running directly, add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.strategy.strategy import Strategy
    from src.core.engine import run


def plot_trade_metrics(trades, enable_plots: bool = False) -> None:
    """
    Plot key metrics for completed trades:
    - Density (normalized frequency) of months, years, and weekdays
      when trades were OPENED and CLOSED.

    The function is robust to different column names for timestamps.
    It looks for typical columns like: 'entry_time'/'exit_time',
    'open_time'/'close_time', 'entry_dt'/'exit_dt'.

    Parameters
    ----------
    trades : pd.DataFrame | list[dict] | Any iterable
        Collection of completed trades. Must contain at least entry/exit timestamps.
    enable_plots : bool
        If False, the function returns immediately without plotting.
    """
    if not enable_plots:
        return

    # Convert to DataFrame if needed
    if not isinstance(trades, pd.DataFrame):
        try:
            trades = pd.DataFrame(trades)
        except Exception:
            logging.warning("Could not convert trades to DataFrame; skipping plots.")
            return

    # Detect entry/exit columns
    candidate_entry_cols = ["entry_time", "open_time", "entry_dt", "opened_at", "open_dt", "entry_timestamp"]
    candidate_exit_cols  = ["exit_time", "close_time", "exit_dt", "closed_at", "close_dt", "exit_timestamp"]

    entry_col = next((c for c in candidate_entry_cols if c in trades.columns), None)
    exit_col  = next((c for c in candidate_exit_cols  if c in trades.columns), None)

    if entry_col is None or exit_col is None:
        logging.warning("No compatible timestamp columns found in trades; expected entry/exit columns. Skipping plots.")
        return

    # Coerce to datetime
    for c in [entry_col, exit_col]:
        if not pd.api.types.is_datetime64_any_dtype(trades[c]):
            try:
                trades[c] = pd.to_datetime(trades[c], utc=True, errors="coerce")
            except Exception:
                logging.warning(f"Failed to parse datetime in column '{c}'. Skipping plots.")
                return

    # Helper for categorical density plots
    def _density(ax, series, title, categories_order=None):
        s = series.dropna()
        if categories_order is not None:
            # Ensure all categories appear (even if zero)
            counts = s.value_counts(normalize=True).reindex(categories_order, fill_value=0.0)
            ax.bar(counts.index, counts.values)
            ax.set_xticklabels(counts.index, rotation=45, ha="right")
        else:
            counts = s.value_counts(normalize=True).sort_index()
            ax.bar(counts.index, counts.values)
        ax.yaxis.set_major_formatter(PercentFormatter(1.0))
        ax.set_title(title)
        ax.set_ylabel("Density")
        ax.grid(True, axis="y", alpha=0.3)

    # Derive time components
    opened = trades[entry_col].dt.tz_convert(None) if trades[entry_col].dt.tz is not None else trades[entry_col]
    closed = trades[exit_col].dt.tz_convert(None) if trades[exit_col].dt.tz is not None else trades[exit_col]

    # Build ordered categories
    month_order = [m for m in month_name if m]  # ['January', ..., 'December']
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    opened_month = opened.dt.month.apply(lambda m: month_order[m-1])
    closed_month = closed.dt.month.apply(lambda m: month_order[m-1])
    opened_year  = opened.dt.year.astype(str)
    closed_year  = closed.dt.year.astype(str)
    opened_wday  = opened.dt.day_name()
    closed_wday  = closed.dt.day_name()

    # Create subplots: 2 rows (opened/closed) x 3 columns (month/year/weekday)
    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(16, 9))
    fig.suptitle("Trade Timing Density — Opened vs Closed", fontsize=14)

    _density(axes[0, 0], opened_month, "Opened — by Month", categories_order=month_order)
    _density(axes[0, 1], opened_year,  "Opened — by Year")
    _density(axes[0, 2], opened_wday,  "Opened — by Weekday", categories_order=weekday_order)

    _density(axes[1, 0], closed_month, "Closed — by Month", categories_order=month_order)
    _density(axes[1, 1], closed_year,  "Closed — by Year")
    _density(axes[1, 2], closed_wday,  "Closed — by Weekday", categories_order=weekday_order)

    plt.tight_layout()
    plt.show()


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
    
    ###### logging setup ########
    logger_config = data.get('logger', {})
    DEFAULT_LEVEL = 'INFO'
    DEFAULT_FALLBACK = logging.DEBUG # What to set if the level is invalid
    LOGGER_MAP = {
        'engine': 'engine_level',
        'strategy_entry': 'strategy_entry_level',
        'strategy_exit': 'strategy_exit_level',
        'indicators': 'indicators_level',
        'ablation': 'ablation_level',
        'loader' : 'loader_level'
    }

    print("\n--- Starting Logger Configuration ---") # Used for visibility during runtime

    for logger_name, config_key in LOGGER_MAP.items():
        
        level_str = logger_config.get(config_key, DEFAULT_LEVEL)
        
        logger_instance = logging.getLogger(logger_name)
        try:
            level_enum = getattr(logging, level_str.upper())
            logger_instance.setLevel(level_enum)
        
            logging.info(f"Logger '{logger_name}' set to level: {level_str.upper()}")
            
        except AttributeError:
            logger_instance.setLevel(DEFAULT_FALLBACK)
            logging.warning(f"Level '{level_str}' in YAML for '{config_key}' is not valid. Falling back to {DEFAULT_FALLBACK.name}.")

    print("--- Logger Configuration Complete ---\n")

    #### end logging setup ####

    #### dataframe loading ####
    data_path = project_root / "data" / "clean" / "NQ_clean.csv"
    try:
        df = pd.read_csv(data_path)
        # Log success
        logging.info('Successfully loaded the dataframe.')

    except FileNotFoundError:
        logging.error(f'File not found: {data_path}. Cannot load the dataframe.')
        return
    except Exception as e:
        logging.error(f'An unexpected error occurred during file loading: {e}')
        return
    
    #### backtest running ####
    strategy = Strategy(data)
    logging.info(strategy.get_cfg())
    all_trades = run(df[:200], strategy)
    print(f"Completed {len(all_trades)} trades")
    print(all_trades)

    # Toggle from YAML 
    plot_cfg = data.get("plots", {})
    plot_trade_metrics_flag = bool(plot_cfg.get("trade_metrics", False))
    plot_trade_metrics(all_trades, enable_plots=plot_trade_metrics_flag)


if __name__ == "__main__":
    main()


## cambia gli indicatori e aggiungi opzione per plottare dal main
# cambia file clean 
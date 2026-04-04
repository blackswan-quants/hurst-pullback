import pandas as pd
from pathlib import Path
import os

def sync_data():
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    benchmark_dir = project_root / "data" / "easylanguage_indicators"
    raw_dir = project_root / "data" / "raw"
    
    # Ensure raw directory exists
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Mapping of benchmark files to target raw files
    # indicators_plot_ES.csv -> ES.csv
    file_mapping = {
        "indicators_plot_ES.csv": "ES.csv",
        "indicators_plot_NQ.csv": "NQ.csv",
        "indicators_plot_YM.csv": "YM.csv",
        "indicators_plot_EMD.csv": "EMD.csv"
    }
    
    print(f"Starting data synchronization...")
    
    for bench_file, raw_file in file_mapping.items():
        bench_path = benchmark_dir / bench_file
        raw_path = raw_dir / raw_file
        
        if not bench_path.exists():
            print(f"Warning: Benchmark file {bench_file} not found at {bench_path}")
            continue
            
        print(f"Processing {bench_file} -> {raw_file}...")
        
        # Load benchmark data
        try:
            df = pd.read_csv(bench_path)
            
            required_cols = ["Date", "Time", "Open", "High", "Low", "Close", "Vol", "OI"]
            
            # Filter columns that exist
            cols_to_extract = [col for col in required_cols if col in df.columns]
            
            sync_df = df[cols_to_extract].copy()
            
            # Save to raw folder
            sync_df.to_csv(raw_path, index=False)
            print(f"Successfully synchronized {raw_file}")
            
        except Exception as e:
            print(f"Error processing {bench_file}: {e}")

if __name__ == "__main__":
    sync_data()

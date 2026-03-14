import unittest
import pandas as pd
import numpy as np
from src.strategy.exits.time_exit import should_exit as time_exit
from src.strategy.exits.profitable_close_exit import should_exit as prof_exit
from src.strategy.signals.composite_rsi_exit import should_exit as rsi_exit

class TestExits(unittest.TestCase):
    def test_time_exit(self):
        # Case 1: Under limit
        state = {'bars': 5}
        params = {'max_bars_in_trade': 10}
        self.assertFalse(time_exit(state, params))
        
        # Case 2: At limit
        state = {'bars': 10}
        self.assertTrue(time_exit(state, params))
        
        # Case 3: Over limit
        state = {'bars': 11}
        self.assertTrue(time_exit(state, params))

    def test_profitable_close_exit(self):
        # Create a mock dataframe
        # High-Close relations: 
        # i=0: Close < Open (Down)
        # i=1: Close > Open (Up)
        # i=2: Close > Open (Up)
        data = {
            'Open':  [100, 100, 100],
            'Close': [90, 110, 110]
        }
        df = pd.DataFrame(data)
        params = {'max_profitable_closes': 2}
        
        # At i=2, with bars=2, we have 2 Up bars (i=1, i=2)
        state = {'bars': 2}
        self.assertTrue(prof_exit(df, 2, state, params))
        
        # At i=2, if bars=1, it should still check the last 2 bars (because of params)
        # but the check loop iterates range(max_profitable_closes)
        # So it checks i=2 and i=1. Both are UP.
        self.assertTrue(prof_exit(df, 2, state, params))
        
        # Case where it fails (one down bar)
        state = {'bars': 3}
        # Checks i=2, i=1, i=0. i=0 is Down.
        params = {'max_profitable_closes': 3}
        self.assertFalse(prof_exit(df, 2, state, params))

    def test_composite_rsi_exit(self):
        data = {'composite_rsi': [40, 60]}
        df = pd.DataFrame(data)
        params = {'composite_rsi_threshold': 50}
        
        # Case 1: Under threshold
        self.assertFalse(rsi_exit(df, 0, params))
        
        # Case 2: Above threshold
        self.assertTrue(rsi_exit(df, 1, params))
        
        # Case 3: NaN
        data_nan = {'composite_rsi': [np.nan]}
        df_nan = pd.DataFrame(data_nan)
        self.assertFalse(rsi_exit(df_nan, 0, params))

if __name__ == '__main__':
    unittest.main()

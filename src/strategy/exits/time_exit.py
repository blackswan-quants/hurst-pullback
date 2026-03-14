def should_exit(state: dict, params: dict) -> bool:
    """
    Exit when the number of bars in position exceeds the maximum allowed.
    
    Args:
        state (dict): Contains 'bars' counter since entry.
        params (dict): Parameters including 'max_bars_in_trade'.
        
    Returns:
        bool: True if max duration is reached.
    """

    bars = state['bars']
    max_bars = params['max_bars_in_trade']

    if bars >= max_bars:
        return True
    else:
        return False
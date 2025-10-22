def assign_pin_sides(df, use_four_sided):
    df = df.copy()
    if 'Side' not in df.columns:
        df['Side'] = None
    df = df.sort_values(by='Pin Designator', ascending=True).reset_index(drop=True)
    n = len(df)

    if use_four_sided:
        # Split into 4 nearly equal parts and assign sides
        quarters = [n // 4 + (1 if x < n % 4 else 0) for x in range(4)]
        # quarters is a list with how many rows in each quarter, spread fairly
        side_labels = ['Left', 'Bottom', 'Right', 'Top']
        start = 0
        for count, label in zip(quarters, side_labels):
            df.loc[start:start+count-1, 'Side'] = label
            start += count
    else:
        half = n // 2
        # Odd count: assign extra to Left
        df.loc[:half-1, 'Side'] = 'Left'
        df.loc[half:, 'Side'] = 'Right'
    return df

def default_four_sided_toggle(df):
    """
    Returns True if number of rows > 32 (default ON for 4-sided), else False.
    """
    return len(df) > 32

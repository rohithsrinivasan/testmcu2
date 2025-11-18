import re


def assign_pin_sides(df, use_four_sided=True):
    import pandas as pd
    df = df.copy()
    if 'Side' not in df.columns:
        df['Side'] = None

    # Step 1: Count rows
    total_pins = len(df)
    print(f"Total pins before filtering: {total_pins}")

    # Step 2: Identify EPAD pins (case-insensitive)
    epad_mask = df['Pin Display Name'].str.contains('epad', case=False, na=False)
    epad_pins = df[epad_mask]
    non_epad_df = df[~epad_mask]

    print(f"Found {len(epad_pins)} EPAD pins. These will be assigned to the Top side.")

    # Step 3: Work with remaining pins (non-EPAD)
    #non_epad_df = non_epad_df.sort_values(by='Pin Designator', ascending=True).reset_index(drop=True) 
    non_epad_df = non_epad_df.sort_values(by='Pin Designator', key=lambda col: col.map(natural_sort_key)).reset_index(drop=True)
    #print(f" non_epad_df  : {non_epad_df}")
    n = len(non_epad_df)
    print(f"Pins after removing EPAD: {n}")

    # Step 4: Determine how many per side
    if use_four_sided:
        # Find base per side (8, 16, 32, etc.)
        #base_per_side = max(8, (n // 4 if n % 4 == 0 else (n // 4) + 1))
        base_per_side = n // 4 if n % 4 == 0 else (n // 4) + 1
        print(f"Base pins per side: {base_per_side}")

        side_labels = ['Left', 'Bottom', 'Right', 'Top']
        start = 0
        for label in side_labels:
            end = min(start + base_per_side, n)
            non_epad_df.loc[start:end-1, 'Side'] = label
            print(f"Assigned {end - start} pins to {label} side (rows {start} to {end - 1})")
            start = end

        # Step 5: Add EPAD pins to the Top side
        if not epad_pins.empty:
            epad_pins.loc[:, 'Side'] = 'Top'
            df = pd.concat([non_epad_df, epad_pins]).reset_index(drop=True)
        else:
            df = non_epad_df

    else:
        # Two-sided logic — divide non-EPAD pins in half
        half = n // 2
        non_epad_df.loc[:half-1, 'Side'] = 'Left'
        non_epad_df.loc[half:, 'Side'] = 'Right'

        # Add EPAD pins on Right side in 2-side mode
        if not epad_pins.empty:
            epad_pins.loc[:, 'Side'] = 'Right'
            df = pd.concat([non_epad_df, epad_pins]).reset_index(drop=True)
        else:
            df = non_epad_df

    print(f"Final pin distribution by side:\n{df['Side'].value_counts()}")
    return df

def natural_sort_key(s):
    if not isinstance(s, str):
        # Convert non-strings (including NaN, None) to a string safely
        s = str(s) if s is not None else ''
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def default_four_sided_toggle(df):
    """
    Returns True if number of rows > 32 (default ON for 4-sided), else False.
    """
    return len(df) > 32


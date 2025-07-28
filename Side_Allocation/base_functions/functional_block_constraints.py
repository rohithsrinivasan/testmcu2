import pandas as pd
from . import general_constraints

def test_one_GPIOcase(unfilled_df, df):
    print("Test One - Seeing if there are more pins that are GPIO")

    gpio_mask = unfilled_df['Priority'].str.contains('GPIO_Pins', na=False)
    gpio_df = unfilled_df[gpio_mask]

    if gpio_df.empty:
        print("No GPIO Pins found — passing for now.")
        return []

    gpio_count = len(gpio_df)
    print(f"Found {gpio_count} GPIO Pins")

    other_unnamed_df = unfilled_df[~unfilled_df.index.isin(gpio_df.index)]        
    combined_df = pd.concat([gpio_df, other_unnamed_df], ignore_index=True)

    if 40 < len(gpio_df) < 80:
        port_df_side_added = general_constraints.side_for_one_symbol(gpio_df)
        df.loc[gpio_df.index, 'Side'] = port_df_side_added['Side'].values
        return [port_df_side_added]

    else:
        # Calculate number of parts needed
        n_parts_needed = (len(combined_df) + 79) // 80  # Ceiling division
        gpio_parts = general_constraints.split_into_n_parts(combined_df, n_parts_needed, max_rows=80,Strict_Population=False,Balanced_Assignment=False)
        return gpio_parts
    

def test_two_SRDBcase(unfilled_df, df):
    """
    Handles SDRB_Pins from the Priority column - mirrors the GPIO logic
    """
    print("Test Two - Seeing if there are more pins that are SDRB")

    sdrb_mask = unfilled_df['Priority'].str.contains('SDRB_Pins', na=False)
    sdrb_df = unfilled_df[sdrb_mask]

    if sdrb_df.empty:
        print("No SDRB Pins found — passing for now.")
        return []

    sdrb_count = len(sdrb_df)
    print(f"Found {sdrb_count} SDRB Pins")

    other_unnamed_df = unfilled_df[~unfilled_df.index.isin(sdrb_df.index)]        
    combined_df = pd.concat([sdrb_df, other_unnamed_df], ignore_index=True)

    if 40 < len(sdrb_df) < 80:
        port_df_side_added = general_constraints.side_for_one_symbol(sdrb_df)
        df.loc[sdrb_df.index, 'Side'] = port_df_side_added['Side'].values
        return [port_df_side_added]

    else:
        # Calculate number of parts needed
        n_parts_needed = (len(combined_df) + 79) // 80  # Ceiling division
        sdrb_parts = general_constraints.split_into_n_parts(combined_df, n_parts_needed, max_rows=80, Strict_Population=False,Balanced_Assignment=False)
        return sdrb_parts
    

def test_three_DDRcase(unfilled_df, df):
    """
    Handles DDR_Pins from the Priority column - mirrors the SDRB logic
    """
    print("Test Three - Checking for DDR Pins")

    ddr_mask = unfilled_df['Priority'].str.contains('DDR_Pins', na=False)
    ddr_df = unfilled_df[ddr_mask]

    if ddr_df.empty:
        print("No DDR Pins found — skipping.")
        return []

    ddr_count = len(ddr_df)
    print(f"Found {ddr_count} DDR Pins")

    other_unnamed_df = unfilled_df[~unfilled_df.index.isin(ddr_df.index)]
    combined_df = pd.concat([ddr_df, other_unnamed_df], ignore_index=True)

    if 40 < len(ddr_df) < 80:
        port_df_side_added = general_constraints.side_for_one_symbol(ddr_df)
        df.loc[ddr_df.index, 'Side'] = port_df_side_added['Side'].values
        return [port_df_side_added]
    else:
        n_parts_needed = (len(combined_df) + 79) // 80  # Ceiling division
        ddr_parts = general_constraints.split_into_n_parts(
            combined_df, 
            n_parts_needed, 
            max_rows=80, 
            Strict_Population=False, 
            Balanced_Assignment=False
        )
        return ddr_parts

    

def remove_duplicates_from_others_table(df_dict):
    """
    Remove any rows from 'Others Table' that appear in any other table
    """
    if 'Others Table' not in df_dict or df_dict['Others Table'].empty:
        return df_dict
    
    others_df = df_dict['Others Table'].copy()
    
    # Get all other tables (exclude 'Others Table')
    other_tables = {key: df for key, df in df_dict.items() if key != 'Others Table' and not df.empty}
    
    if not other_tables:
        return df_dict
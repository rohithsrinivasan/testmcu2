import pandas as pd

from . import side
from .base_functions import power_pins_constaints
from .base_functions import functional_block_constraints
from .base_functions import general_constraints
from .base_functions import single80pin_constraints



def partitioning(df_last, Strict_Population):
    """
    Partitioning function with improved debugging and GPIO/SDRB separation
    Enhanced with power pin splitting capability and Others Table splitting
    """
    print("=== PARTITIONING START ===")
    
    # Step 1: Filter and sort by priority
    df = single80pin_constraints.filter_and_sort_by_priority(df_last)
    print(f"Step 1: Filtered and sorted DataFrame - {len(df)} rows")

    # Step 2: Apply filter for power pins and update the 'Side' column
    df['Side'] = df.apply(power_pins_constaints.filter_out_power_pins, args=(df,), axis=1)
    power_df = df[df['Side'].isin(['Left', 'Right'])]
    df.loc[power_df.index, 'Side'] = power_df['Side']
    print(f"Step 2: Power pins processed - {len(power_df)} power pins found")

    # NEW FEATURE: Handle power pin splitting if > 80 pins
    power_parts = []
    if len(power_df) > 80:
        print(f">>> Power pins > 80 ({len(power_df)}): Creating separate Power tables")
        power_parts = power_pins_constaints.split_power_pins_by_priority(power_df, Strict_Population)
        print(f">>> Power separated: {len(power_parts)} Power parts created")
    else:
        # Keep original power_df if <= 80 pins
        if not power_df.empty:
            power_parts = [power_df]

    # Step 3: Handle unfilled rows
    unfilled_df = df[df['Side'].isna()]
    number_of_rows_left = len(unfilled_df)
    print(f"Step 3: Unfilled rows - {number_of_rows_left} rows remaining")

    # NEW FEATURE: Check for GPIO and SDRB pins that need separate handling
    gpio_pins = unfilled_df[unfilled_df['Priority'].str.contains('GPIO_Pins', na=False)]
    sdrb_pins = unfilled_df[unfilled_df['Priority'].str.contains('SDRB_Pins', na=False)]
    
    print(f"GPIO pins found: {len(gpio_pins)}")
    print(f"SDRB pins found: {len(sdrb_pins)}")
    
    # Separate GPIO/SDRB if they exceed 40 pins
    gpio_parts = []
    sdrb_parts = []
    
    if len(gpio_pins) > 40:
        print(">>> GPIO pins > 40: Creating separate GPIO tables")
        gpio_parts = functional_block_constraints.test_one_GPIOcase(unfilled_df, df)
        # Remove GPIO pins from unfilled_df for main processing
        unfilled_df = unfilled_df[~unfilled_df['Priority'].str.contains('GPIO_Pins', na=False)]
        print(f">>> GPIO separated: {len(gpio_parts)} GPIO parts created")
    
    if len(sdrb_pins) > 40:
        print(">>> SDRB pins > 40: Creating separate SDRB tables")
        sdrb_parts = functional_block_constraints.test_two_SRDBcase(unfilled_df, df)
        # Remove SDRB pins from unfilled_df for main processing
        unfilled_df = unfilled_df[~unfilled_df['Priority'].str.contains('SDRB_Pins', na=False)]
        print(f">>> SDRB separated: {len(sdrb_parts)} SDRB parts created")
    
    # Update the count after removing GPIO/SDRB
    number_of_rows_left = len(unfilled_df)
    print(f"Remaining unfilled rows after GPIO/SDRB separation: {number_of_rows_left}")

    # Initialize result DataFrames
    df_Part_A = pd.DataFrame()
    port_df_side_added = pd.DataFrame()
    Port_Balance_1 = pd.DataFrame()
    Port_Balance_2 = pd.DataFrame()
    Port_Part_1 = pd.DataFrame()
    additional_port_parts = []

    # MAIN LOGIC: Handle remaining unfilled rows (same as your original working logic)
    if number_of_rows_left <= 80:
        print(">>> CASE 1: Only one extra Part (≤80 rows)")
        df_Part_A = general_constraints.side_for_one_symbol(df_Part_A)

        # Update unfilled rows in the original DataFrame
        df.loc[unfilled_df.index, 'Side'] = df_Part_A['Side'].values

        # Recheck unfilled rows
        number_of_rows_left = df['Side'].isna().sum()
        print(f"After Part A processing: {number_of_rows_left} unfilled rows")

        if number_of_rows_left == 0:
            print("✅ All bins are filled.")
        else:
            print("❌ Something is wrong")
            print(f"Unfilled DataFrame: {df[df['Side'].isna()]}")
    
    elif number_of_rows_left > 80 and any(unfilled_df['Priority'].str.startswith('P_Port')):
        print(">>> CASE 2: Port-based splitting (>80 rows with P_Port)")
        
        port_df = unfilled_df[unfilled_df['Priority'].str.startswith('P_Port')]
        other_unnamed_df = unfilled_df[~unfilled_df.index.isin(port_df.index)]

        print(f"Port df length: {len(port_df)}")
        print(f"Other unnamed df length: {len(other_unnamed_df)}")
        
        combined_df = pd.concat([port_df, other_unnamed_df], ignore_index=True)
        overall_length = len(combined_df)
        print(f"Overall length of combined DataFrame: {overall_length}")
        
        if len(port_df) < 80:
            print(">>> Port pins < 80: Single port table")
            port_df_side_added = general_constraints.side_for_one_symbol(port_df)
            df.loc[port_df.index, 'Side'] = port_df_side_added['Side'].values
        else:
            print(">>> Port pins ≥ 80: Multiple port tables")
            # Calculate number of parts needed
            n_parts_needed = (len(combined_df) + 79) // 80  # Ceiling division
            print(f"Creating {n_parts_needed} port parts")
            
            port_parts = general_constraints.split_into_n_parts(combined_df, n_parts_needed, max_rows=80, Strict_Population=Strict_Population,Balanced_Assignment=False)
            
            # Assign to variables for backward compatibility
            Port_Part_1 = port_parts[0] if len(port_parts) > 0 else pd.DataFrame()
            Port_Balance_1 = port_parts[1] if len(port_parts) > 1 else pd.DataFrame()
            Port_Balance_2 = port_parts[2] if len(port_parts) > 2 else pd.DataFrame()
            
            # Store additional parts if any
            additional_port_parts = port_parts[3:] if len(port_parts) > 3 else []
            print(f"Port parts created: Main={len(Port_Part_1)}, Balance1={len(Port_Balance_1)}, Balance2={len(Port_Balance_2)}, Additional={len(additional_port_parts)}")
    
    else:
        print(">>> CASE 3: Other cases - creating more parts")
        # Handle any remaining GPIO/SDRB that wasn't caught above
        if len(gpio_pins) <= 40 and len(gpio_pins) > 0:
            print(">>> Processing remaining GPIO pins (≤40)")
            gpio_parts = functional_block_constraints.test_one_GPIOcase(unfilled_df, df)
        
        if len(sdrb_pins) <= 40 and len(sdrb_pins) > 0:
            print(">>> Processing remaining SDRB pins (≤40)")
            sdrb_parts = functional_block_constraints.test_two_SRDBcase(unfilled_df, df)

    # Step 4: Construct the dictionary of DataFrames
    print("=== BUILDING RESULT DICTIONARY ===")
    
    df_dict = {
        'Part A Table': df_Part_A,
        'Port Table': port_df_side_added,
        'Others Table': df[df['Side'].isna()],
        'Port Table - 1': Port_Part_1,
        'Port Table - 2': Port_Balance_1,
        'Port Table - 3': Port_Balance_2,
    }

    # Add Power tables dynamically (UPDATED LOGIC)
    for i, part in enumerate(power_parts, start=1):
        if not part.empty:
            if len(power_parts) == 1:
                # Single power table (original behavior for <= 80 pins)
                df_dict['Power Table'] = part
                print(f"Added Power Table: {len(part)} rows")
            else:
                # Multiple power tables (new behavior for > 80 pins)
                df_dict[f'Power Table - {i}'] = part
                print(f"Added Power Table - {i}: {len(part)} rows")

    # Add additional port parts dynamically
    for i, part in enumerate(additional_port_parts, start=4):
        if not part.empty:
            df_dict[f'Port Table - {i}'] = part
            print(f"Added Port Table - {i}: {len(part)} rows")

    # Add GPIO tables dynamically
    for i, part in enumerate(gpio_parts, start=1):
        if not part.empty:
            df_dict[f'GPIO Table - {i}'] = part
            print(f"Added GPIO Table - {i}: {len(part)} rows")

    # Add SDRB tables dynamically  
    for i, part in enumerate(sdrb_parts, start=1):
        if not part.empty:
            df_dict[f'SDRB Table - {i}'] = part
            print(f"Added SDRB Table - {i}: {len(part)} rows")

    # Clean up the dictionary by removing empty DataFrames
    df_dict = {key: value for key, value in df_dict.items() if not value.empty}
    print(f"Final dictionary has {len(df_dict)} non-empty tables")

    # DEDUPLICATION: Remove duplicates from Others Table
    df_dict = functional_block_constraints.remove_duplicates_from_others_table(df_dict)

    # NEW FEATURE: Handle Others Table splitting if > 80 pins
    others_parts = []
    if df_dict is None:
        df_dict = {}

    if 'Others Table' in df_dict and len(df_dict['Others Table']) > 80:
        others_table = df_dict['Others Table']
        others_count = len(others_table)
        print(f"\n>>> Others Table > 80 pins ({others_count}): Splitting into multiple tables")
        
        # Calculate number of parts needed (max 80 per part)
        n_others_parts = (others_count + 79) // 80  # Ceiling division
        print(f">>> Creating {n_others_parts} Others Table parts")
        
        # Split the Others Table using the same strategy as port splitting
        others_parts = general_constraints.split_into_n_parts(others_table, n_others_parts, max_rows=80, Strict_Population=Strict_Population,Balanced_Assignment=False)
        
        # Remove the original Others Table from dict
        del df_dict['Others Table']
        
        # Add the split Others Tables
        for i, part in enumerate(others_parts, start=1):
            if not part.empty:
                df_dict[f'Others Table - {i}'] = part
                print(f"Added Others Table - {i}: {len(part)} rows")
        
        print(f">>> Others Table split complete: {len(others_parts)} parts created")

    # Final validation of splitting logic
    total_rows_processed = sum(len(table) for table in df_dict.values())
    print(f"=== VALIDATION ===")
    print(f"Original rows: {len(df)}")
    print(f"Total rows processed: {total_rows_processed}")
    
    if total_rows_processed != len(df):
        print("❗ WARNING: Row count mismatch!")
        print("Table breakdown:")
        for key, table in df_dict.items():
            print(f"  {key}: {len(table)} rows")
    else:
        print("✅ All rows processed correctly")

    print("=== PARTITIONING END ===")
    return df_dict

def partitioning(df_last, Strict_Population):
    """
    Enhanced partitioning with comprehensive debugging
    """
    print("🚀 === PARTITIONING START ===")
    
    try:
        # Step 1: Filter and sort by priority
        print("📋 Step 1: Filtering and sorting by priority...")
        df = single80pin_constraints.filter_and_sort_by_priority(df_last)
        print(f"✅ Step 1 Complete: {len(df)} rows after filtering")
        print(f"🔍 DataFrame indices range: {df.index.min()} to {df.index.max()}")
        print(f"🔍 DataFrame columns: {list(df.columns)}")

    except Exception as e:
        print(f"❌ Step 1 FAILED: {e}")
        raise

    try:
        # Step 2: Process power pins
        print("⚡ Step 2: Processing power pins...")
        df['Side'] = df.apply(power_pins_constaints.filter_out_power_pins, args=(df,), axis=1)
        power_df = df[df['Side'].isin(['Left', 'Right'])].copy()
        print(f"✅ Step 2 Complete: {len(power_df)} power pins identified")
        if not power_df.empty:
            print(f"🔍 Power pins indices: {list(power_df.index)}")

    except Exception as e:
        print(f"❌ Step 2 FAILED: {e}")
        raise

    try:
        # Step 3: Get unfilled pins
        print("📊 Step 3: Identifying unfilled pins...")
        unfilled_df = df[df['Side'].isna()].copy()
        print(f"✅ Step 3 Complete: {len(unfilled_df)} unfilled pins")
        if not unfilled_df.empty:
            print(f"🔍 Unfilled pins indices range: {unfilled_df.index.min()} to {unfilled_df.index.max()}")
            print(f"🔍 Sample unfilled priorities: {unfilled_df['Priority'].head().tolist()}")

    except Exception as e:
        print(f"❌ Step 3 FAILED: {e}")
        raise

    # Step 4: Handle power pin splitting
    power_parts = []
    try:
        print("⚡ Step 4: Handling power pin splitting...")
        if len(power_df) > 80:
            print(f"🔄 Splitting {len(power_df)} power pins (>80)")
            power_parts = power_pins_constaints.split_power_pins_by_priority(power_df, Strict_Population)
            print(f"✅ Power splitting complete: {len(power_parts)} parts created")
        elif not power_df.empty:
            print(f"📦 Single power part: {len(power_df)} pins")
            power_parts = [power_df]
        else:
            print("📦 No power pins to process")
        
        for i, part in enumerate(power_parts):
            print(f"🔍 Power part {i+1}: {len(part)} rows, indices: {list(part.index) if len(part) <= 10 else f'{part.index.min()}-{part.index.max()}'}")

    except Exception as e:
        print(f"❌ Step 4 FAILED: {e}")
        raise

    # Step 5: Handle GPIO/SDRB separation
    gpio_parts = []
    sdrb_parts = []
    try:
        print("🎯 Step 5: Handling GPIO/SDRB separation...")
        
        gpio_pins = unfilled_df[unfilled_df['Priority'].str.contains('GPIO_Pins', na=False)]
        sdrb_pins = unfilled_df[unfilled_df['Priority'].str.contains('SDRB_Pins', na=False)]
        
        print(f"🔍 GPIO pins found: {len(gpio_pins)}")
        print(f"🔍 SDRB pins found: {len(sdrb_pins)}")
        
        if len(gpio_pins) > 40:
            print(f"🔄 Separating {len(gpio_pins)} GPIO pins (>40)")
            gpio_parts = functional_block_constraints.test_one_GPIOcase(unfilled_df, df)
            unfilled_df = unfilled_df[~unfilled_df['Priority'].str.contains('GPIO_Pins', na=False)]
            print(f"✅ GPIO separation complete: {len(gpio_parts)} parts")
        
        if len(sdrb_pins) > 40:
            print(f"🔄 Separating {len(sdrb_pins)} SDRB pins (>40)")
            sdrb_parts = functional_block_constraints.test_two_SRDBcase(unfilled_df, df)
            unfilled_df = unfilled_df[~unfilled_df['Priority'].str.contains('SDRB_Pins', na=False)]
            print(f"✅ SDRB separation complete: {len(sdrb_parts)} parts")
        
        print(f"✅ Step 5 Complete: {len(unfilled_df)} pins remaining for main processing")

    except Exception as e:
        print(f"❌ Step 5 FAILED: {e}")
        raise

    # Step 6: Split remaining pins and assign sides
    main_parts = []
    try:
        print("🎲 Step 6: Processing main parts...")
        
        if len(unfilled_df) == 0:
            print("📦 No unfilled pins to process")
        elif len(unfilled_df) <= 80:
            print(f"📦 Single main part: {len(unfilled_df)} pins")
            print(f"🔍 Pre-assignment indices: {list(unfilled_df.index) if len(unfilled_df) <= 10 else f'{unfilled_df.index.min()}-{unfilled_df.index.max()}'}")
            
            print("🎯 Applying side assignment to single part...")
            part_with_sides = general_constraints.side_for_one_symbol(unfilled_df)
            print(f"✅ Side assignment complete: {len(part_with_sides)} rows")
            print(f"🔍 Post-assignment indices: {list(part_with_sides.index) if len(part_with_sides) <= 10 else f'{part_with_sides.index.min()}-{part_with_sides.index.max()}'}")
            
            main_parts = [part_with_sides]
        else:
            print(f"🔄 Multiple parts needed for {len(unfilled_df)} pins")
            n_parts = (len(unfilled_df) + 79) // 80
            print(f"🔢 Creating {n_parts} main parts (max 80 rows each)")
            
            print("✂️ Splitting into parts...")
            print(f"🔍 Input to split_into_n_parts: {len(unfilled_df)} rows, indices: {unfilled_df.index.min()}-{unfilled_df.index.max()}")

            unfilled_df = unfilled_df.reset_index(drop=True)
            split_parts = general_constraints.split_into_n_parts(unfilled_df, n_parts, max_rows=80, Strict_Population=Strict_Population,Balanced_Assignment=False)
            print(f"✅ Splitting complete: {len(split_parts)} parts returned")
            
            for i, part in enumerate(split_parts):
                print(f"🔍 Split part {i+1}: {len(part)} rows, empty: {part.empty}")
                if not part.empty:
                    print(f"🔍 Split part {i+1} indices: {list(part.index) if len(part) <= 10 else f'{part.index.min()}-{part.index.max()}'}")
                    print(f"🔍 Split part {i+1} columns: {list(part.columns)}")
                    
                    print(f"🎯 Applying side assignment to part {i+1}...")
                    try:
                        part_with_sides = general_constraints.side_for_one_symbol(part)
                        print(f"✅ Side assignment complete for part {i+1}: {len(part_with_sides)} rows")
                        print(f"🔍 Part {i+1} post-assignment indices: {list(part_with_sides.index) if len(part_with_sides) <= 10 else f'{part_with_sides.index.min()}-{part_with_sides.index.max()}'}")
                        main_parts.append(part_with_sides)
                    except Exception as side_error:
                        print(f"❌ Side assignment FAILED for part {i+1}: {side_error}")
                        print(f"🔍 Part {i+1} problematic data:")
                        print(f"   - Shape: {part.shape}")
                        print(f"   - Index: {part.index}")
                        print(f"   - Columns: {part.columns}")
                        print(f"   - Sample data: {part.head(2).to_dict() if not part.empty else 'Empty'}")
                        raise
        
        print(f"✅ Step 6 Complete: {len(main_parts)} main parts created")

    except Exception as e:
        print(f"❌ Step 6 FAILED: {e}")
        print(f"🔍 Error details: {type(e).__name__}: {str(e)}")
        raise

    # Step 7: Build final dictionary
    try:
        print("🏗️ Step 7: Building result dictionary...")
        df_dict = {}
        
        # Add power tables
        for i, power_part in enumerate(power_parts):
            if not power_part.empty:
                if len(power_parts) == 1:
                    df_dict['Power Table'] = power_part
                    print(f"📦 Added Power Table: {len(power_part)} rows")
                else:
                    df_dict[f'Power Table - {i+1}'] = power_part
                    print(f"📦 Added Power Table - {i+1}: {len(power_part)} rows")
        
        # Add main parts
        for i, main_part in enumerate(main_parts):
            if not main_part.empty:
                if any(main_part['Priority'].str.startswith('P_Port', na=False)):
                    df_dict[f'Port Table - {i+1}'] = main_part
                    print(f"📦 Added Port Table - {i+1}: {len(main_part)} rows")
                else:
                    df_dict[f'Part Table - {i+1}'] = main_part
                    print(f"📦 Added Part Table - {i+1}: {len(main_part)} rows")
        
        # Add GPIO tables
        for i, gpio_part in enumerate(gpio_parts):
            if not gpio_part.empty:
                df_dict[f'GPIO Table - {i+1}'] = gpio_part
                print(f"📦 Added GPIO Table - {i+1}: {len(gpio_part)} rows")
        
        # Add SDRB tables
        for i, sdrb_part in enumerate(sdrb_parts):
            if not sdrb_part.empty:
                df_dict[f'SDRB Table - {i+1}'] = sdrb_part
                print(f"📦 Added SDRB Table - {i+1}: {len(sdrb_part)} rows")
        
        print(f"✅ Step 7 Complete: {len(df_dict)} tables in final dictionary")

    except Exception as e:
        print(f"❌ Step 7 FAILED: {e}")
        raise

    # Step 8: Validation
    try:
        print("🔍 Step 8: Final validation...")
        total_rows_processed = sum(len(table) for table in df_dict.values())
        
        print(f"📊 Original rows: {len(df)}")
        print(f"📊 Total rows processed: {total_rows_processed}")
        
        if total_rows_processed != len(df):
            print("⚠️ WARNING: Row count mismatch!")
            print("📋 Table breakdown:")
            for key, table in df_dict.items():
                print(f"   {key}: {len(table)} rows")
        else:
            print("✅ All rows processed correctly")

    except Exception as e:
        print(f"❌ Step 8 FAILED: {e}")
        raise

    print("🏁 === PARTITIONING END ===")
    return df_dict
from . import single80pin_constraints
from . import power_pins_constaints
from . import functional_block_constraints
from . import general_constraints


def filter_and_prepare_dataframe(df_last):
    """
    Step 1: Filter and sort by priority
    """
    print("📋 Step 1: Filtering and sorting by priority...")
    try:
        df = single80pin_constraints.filter_and_sort_by_priority(df_last)
        print(f"✅ Step 1 Complete: {len(df)} rows after filtering")
        print(f"🔍 DataFrame indices range: {df.index.min()} to {df.index.max()}")
        print(f"🔍 DataFrame columns: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"❌ Step 1 FAILED: {e}")
        raise


def process_power_pins(df, Strict_Population):
    """
    Step 2: Process power pins and handle splitting if > 80 pins
    """
    print("⚡ Step 2: Processing power pins...")
    try:
        df['Side'] = df.apply(power_pins_constaints.filter_out_power_pins, args=(df,), axis=1)
        power_df = df[df['Side'].isin(['Left', 'Right'])].copy()
        print(f"✅ Step 2 Complete: {len(power_df)} power pins identified")
        if not power_df.empty:
            print(f"🔍 Power pins indices: {list(power_df.index)}")
    except Exception as e:
        print(f"❌ Step 2 FAILED: {e}")
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
        
        return power_parts
    except Exception as e:
        print(f"❌ Step 4 FAILED: {e}")
        raise


def identify_unfilled_pins(df):
    """
    Step 3: Identify unfilled pins
    """
    print("📊 Step 3: Identifying unfilled pins...")
    try:
        unfilled_df = df[df['Side'].isna()].copy()
        print(f"✅ Step 3 Complete: {len(unfilled_df)} unfilled pins")
        if not unfilled_df.empty:
            print(f"🔍 Unfilled pins indices range: {unfilled_df.index.min()} to {unfilled_df.index.max()}")
            print(f"🔍 Sample unfilled priorities: {unfilled_df['Priority'].head().tolist()}")
        return unfilled_df
    except Exception as e:
        print(f"❌ Step 3 FAILED: {e}")
        raise


def handle_special_pin_separation(unfilled_df, df):
    """
    Step 5: Handle GPIO/SDRB/DDR separation
    """
    gpio_parts = []
    sdrb_parts = []
    ddr_parts = []

    try:
        print("🎯 Step 5: Handling GPIO/SDRB/DDR separation...")

        gpio_pins = unfilled_df[unfilled_df['Priority'].str.contains('GPIO_Pins', na=False)]
        sdrb_pins = unfilled_df[unfilled_df['Priority'].str.contains('SDRB_Pins', na=False)]
        ddr_pins  = unfilled_df[unfilled_df['Priority'].str.contains('DDR_Pins', na=False)]

        print(f"🔍 GPIO pins found: {len(gpio_pins)}")
        print(f"🔍 SDRB pins found: {len(sdrb_pins)}")
        print(f"🔍 DDR pins found: {len(ddr_pins)}")

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

        if len(ddr_pins) > 40:
            print(f"🔄 Separating {len(ddr_pins)} DDR pins (>40)")
            ddr_parts = functional_block_constraints.test_three_DDRcase(unfilled_df, df)
            unfilled_df = unfilled_df[~unfilled_df['Priority'].str.contains('DDR_Pins', na=False)]
            print(f"✅ DDR separation complete: {len(ddr_parts)} parts")

        print(f"✅ Step 5 Complete: {len(unfilled_df)} pins remaining for main processing")
        return unfilled_df, gpio_parts, sdrb_parts, ddr_parts

    except Exception as e:
        print(f"❌ Step 5 FAILED: {e}")
        raise
        
'''

def handle_special_pin_separation(unfilled_df, df, functional_separation=False):
    """
    Step 5: Handle special pin separations, flexible for interface types
    """
    print("🎯 Step 5: Handling Special Interface Separations...")

    # List all interface types needing splitting
    interface_types = [
        ('GPIO_Pins', functional_block_constraints.test_one_GPIOcase),
        ('SDRB_Pins', functional_block_constraints.test_two_SRDBcase),
        ('DDR_Pins', functional_block_constraints.test_three_DDRcase),
    ]
    # Add dynamically if functional separation is enabled
    if functional_separation:
        interface_types += [
            ('CSI_Interface', functional_block_constraints.generic_handler_function),
            ('LVDS_Interface', functional_block_constraints.generic_handler_function),
            ('Display_Unit', functional_block_constraints.generic_handler_function),
            ('QSPI', functional_block_constraints.generic_handler_function),  # Use 'QSPI' to match any QSPI*
        ]
    # Results for each group, dictionary for clarity
    results = {name: [] for name, _ in interface_types}

    try:
        lower_threshold = 10

        for interface_name, handler_func in interface_types:
            # For QSPI wildcard, match all QSPI*
            if interface_name == 'QSPI':
                mask = unfilled_df['Priority'].str.match(r'QSPI', na=False)
            else:
                mask = unfilled_df['Priority'].str.contains(interface_name, na=False)

            pins_df = unfilled_df[mask]
            print(f"🔍 {interface_name} pins found: {len(pins_df)}")

            if len(pins_df) > lower_threshold:
                print(f"🔄 Separating {len(pins_df)} {interface_name} pins")
                # Call the specialized or generic handler
                part_list = handler_func(unfilled_df, df, interface_name)
                results[interface_name] = part_list
                # Remove these pins from unfilled as they are now handled
                unfilled_df = unfilled_df[~mask]
                print(f"✅ {interface_name} separation complete: {len(part_list)} parts")
        print(f"✅ Step 5 Complete: {len(unfilled_df)} pins remaining for main processing")
        # You can return the dict, or unpack for backwards compatibility
        return (unfilled_df,) + tuple(results[name] for name, _ in interface_types)
    except Exception as e:
        print(f"❌ Step 5 FAILED: {e}")
        raise


def process_main_parts(unfilled_df, Strict_Population):
    """
    Step 6: Split remaining pins and assign sides
    """
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
            split_parts = general_constraints.split_into_n_parts(unfilled_df, n_parts, max_rows=80, Strict_Population=Strict_Population, Balanced_Assignment=False)
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
        return main_parts

    except Exception as e:
        print(f"❌ Step 6 FAILED: {e}")
        print(f"🔍 Error details: {type(e).__name__}: {str(e)}")
        raise


def build_result_dictionary(power_parts, main_parts, gpio_parts, sdrb_parts, ddr_parts):
    """
    Step 7: Build final dictionary
    """
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

        # Add DDR tables
        for i, ddr_part in enumerate(ddr_parts):
            if not ddr_part.empty:
                df_dict[f'DDR Table - {i+1}'] = ddr_part
                print(f"📦 Added DDR Table - {i+1}: {len(ddr_part)} rows")
        
        print(f"✅ Step 7 Complete: {len(df_dict)} tables in final dictionary")
        return df_dict

    except Exception as e:
        print(f"❌ Step 7 FAILED: {e}")
        raise


def validate_final_results(df_dict, original_df):
    """
    Step 8: Final validation
    """
    try:
        print("🔍 Step 8: Final validation...")
        total_rows_processed = sum(len(table) for table in df_dict.values())
        
        print(f"📊 Original rows: {len(original_df)}")
        print(f"📊 Total rows processed: {total_rows_processed}")
        
        if total_rows_processed != len(original_df):
            print("⚠️ WARNING: Row count mismatch!")
            print("📋 Table breakdown:")
            for key, table in df_dict.items():
                print(f"   {key}: {len(table)} rows")
        else:
            print("✅ All rows processed correctly")

    except Exception as e:
        print(f"❌ Step 8 FAILED: {e}")
        raise


def partitioning(df_last, Strict_Population):
    """
    Main partitioning function - orchestrates the entire process
    """
    print("🚀 === PARTITIONING START ===")
    
    # Step 1: Filter and prepare DataFrame
    df = filter_and_prepare_dataframe(df_last)
    
    # Step 2: Process power pins
    power_parts = process_power_pins(df, Strict_Population)
    
    # Step 3: Identify unfilled pins
    unfilled_df = identify_unfilled_pins(df)
    
    # Step 5: Handle special pin separation (GPIO/SDRB/DDR)
    unfilled_df, gpio_parts, sdrb_parts, ddr_parts = handle_special_pin_separation(unfilled_df, df)
    
    # Step 6: Process main parts
    main_parts = process_main_parts(unfilled_df, Strict_Population)
    
    # Step 7: Build result dictionary
    df_dict = build_result_dictionary(power_parts, main_parts, gpio_parts, sdrb_parts, ddr_parts)
    
    # Step 8: Validate results
    validate_final_results(df_dict, df)
    
    print("🏁 === PARTITIONING END ===")
    return df_dict
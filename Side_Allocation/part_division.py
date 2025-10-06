from .base_functions import single80pin_constraints
from .base_functions import power_pins_constaints
from .base_functions import functional_block_constraints
from .base_functions import general_constraints


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


'''
def handle_special_pin_separation(unfilled_df, df):
    """
    Step 5: Handle GPIO/SDRB/DDR separation
    """
    gpio_parts = []
    sdrb_parts = []
    ddr_parts = []

    lower_threshold = 10

    try:
        print("🎯 Step 5: Handling GPIO/SDRB/DDR separation...")

        gpio_pins = unfilled_df[unfilled_df['Priority'].str.contains('GPIO_Pins', na=False)]
        sdrb_pins = unfilled_df[unfilled_df['Priority'].str.contains('SDRB_Pins', na=False)]
        ddr_pins  = unfilled_df[unfilled_df['Priority'].str.contains('DDR_Pins', na=False)]

        print(f"🔍 GPIO pins found: {len(gpio_pins)}")
        print(f"🔍 SDRB pins found: {len(sdrb_pins)}")
        print(f"🔍 DDR pins found: {len(ddr_pins)}")

        if len(gpio_pins) > lower_threshold:
            print(f"🔄 Separating {len(gpio_pins)} GPIO pins (>40)")
            gpio_parts = functional_block_constraints.test_one_GPIOcase(unfilled_df, df)
            unfilled_df = unfilled_df[~unfilled_df['Priority'].str.contains('GPIO_Pins', na=False)]
            print(f"✅ GPIO separation complete: {len(gpio_parts)} parts")

        if len(sdrb_pins) > lower_threshold:
            print(f"🔄 Separating {len(sdrb_pins)} SDRB pins (>40)")
            sdrb_parts = functional_block_constraints.test_two_SRDBcase(unfilled_df, df)
            unfilled_df = unfilled_df[~unfilled_df['Priority'].str.contains('SDRB_Pins', na=False)]
            print(f"✅ SDRB separation complete: {len(sdrb_parts)} parts")

        if len(ddr_pins) > lower_threshold:
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

def handle_special_pin_separation(
    unfilled_df,
    df,
    functional_separation=False,
    lower_threshold=8
):
    """
    Step 5: Handle special pin separations.
    Always returns a fixed 6-tuple in this exact order:
        (unfilled_df, gpio_parts, sdrb_parts, ddr_parts, csi_interface_parts, lvds_interface_parts)

    Notes:
    - gpio/sdrb/ddr behavior preserved.
    - When functional_separation is True, also process CSI_Interface and LVDS_Interface.
    - When functional_separation is False, csi_interface_parts and lvds_interface_parts are empty lists, preserving arity.
    """
    gpio_parts = []
    sdrb_parts = []
    ddr_parts = []
    csi_interface_parts = []
    lvds_interface_parts = []

    try:
        print("🎯 Step 5: Handling GPIO/SDRB/DDR separation...")

        # Core masks
        gpio_mask = unfilled_df['Priority'].str.contains('GPIO_Pins', na=False)
        sdrb_mask = unfilled_df['Priority'].str.contains('SDRB_Pins', na=False)
        ddr_mask  = unfilled_df['Priority'].str.contains('DDR_Pins',  na=False)

        gpio_pins = unfilled_df[gpio_mask]
        sdrb_pins = unfilled_df[sdrb_mask]
        ddr_pins  = unfilled_df[ddr_mask]

        print(f"🔍 GPIO_Pins pins found: {len(gpio_pins)}")
        print(f"🔍 SDRB_Pins pins found: {len(sdrb_pins)}")
        print(f"🔍 DDR_Pins pins found: {len(ddr_pins)}")

        if len(gpio_pins) > lower_threshold:
            print(f"🔄 Separating {len(gpio_pins)} GPIO pins")
            gpio_parts = functional_block_constraints.test_one_GPIOcase(unfilled_df, df)
            unfilled_df = unfilled_df[~gpio_mask]
            print(f"✅ GPIO separation complete: {len(gpio_parts)} parts")

        if len(sdrb_pins) > lower_threshold:
            print(f"🔄 Separating {len(sdrb_pins)} SDRB pins")
            sdrb_parts = functional_block_constraints.test_two_SRDBcase(unfilled_df, df)
            unfilled_df = unfilled_df[~sdrb_mask]
            print(f"✅ SDRB separation complete: {len(sdrb_parts)} parts")

        if len(ddr_pins) > lower_threshold:
            print(f"🔄 Separating {len(ddr_pins)} DDR pins")
            ddr_parts = functional_block_constraints.test_three_DDRcase(unfilled_df, df)
            unfilled_df = unfilled_df[~ddr_mask]
            print(f"✅ DDR separation complete: {len(ddr_parts)} parts")

        # Optional functional separation
        if functional_separation:
            #print(f"🎯 Step 5a: {unfilled_df['Priority'].unique()}")

            # CSI_Interface
            csi_mask = unfilled_df['Priority'].str.contains('CSI Interface', na=False)
            csi_pins = unfilled_df[csi_mask]
            print(f"🔍 CSI Interface pins found: {len(csi_pins)}")
            if len(csi_pins) > lower_threshold:
                print(f"🔄 Separating {len(csi_pins)} CSI Interface pins")
                csi_interface_parts = _generic_interface_handler(unfilled_df, df, csi_mask, "CSI Interface")
                unfilled_df = unfilled_df[~csi_mask]
                print(f"✅ CSI Interface separation complete: {len(csi_interface_parts)} parts")

            # LVDS_Interface
            lvds_mask = unfilled_df['Priority'].str.contains('LVDS Interface', na=False)
            lvds_pins = unfilled_df[lvds_mask]
            print(f"🔍 LVDS Interface pins found: {len(lvds_pins)}")
            if len(lvds_pins) > lower_threshold:
                print(f"🔄 Separating {len(lvds_pins)} LVDS Interface pins")
                lvds_interface_parts = _generic_interface_handler(unfilled_df, df, lvds_mask, "LVDS Interface")
                unfilled_df = unfilled_df[~lvds_mask]
                print(f"✅ LVDS Interface separation complete: {len(lvds_interface_parts)} parts")

        print(f"✅ Step 5 Complete: {len(unfilled_df)} pins remaining for main processing")
        # Fixed 6-tuple to avoid unpacking errors regardless of flag settings
        return (
            unfilled_df,
            gpio_parts,
            sdrb_parts,
            ddr_parts,
            csi_interface_parts,
            lvds_interface_parts,
        )

    except Exception as e:
        print(f"❌ Step 5 FAILED: {e}")
        raise


def _generic_interface_handler(unfilled_df, df, mask, interface_name):
    """
    Generic handler that mirrors 40<cnt<80 side assignment else split into parts.
    """
    pins_df = unfilled_df[mask]
    if pins_df.empty:
        print(f"No {interface_name} pins found — passing for now.")
        return []

    count = len(pins_df)
    print(f"Found {count} {interface_name} pins")

    if 40 < count < 80:
        port_df_side_added = general_constraints.side_for_one_symbol(pins_df)
        df.loc[pins_df.index, 'Side'] = port_df_side_added['Side'].values
        return [port_df_side_added]
    else:
        n_parts_needed = (len(pins_df) + 79) // 80  # ceiling for 80 rows
        parts = general_constraints.split_into_n_parts(
            pins_df,
            n_parts_needed,
            max_rows=80,
            Strict_Population=False,
            Balanced_Assignment=False
        )
        return parts


def process_main_parts(unfilled_df, Strict_Population, Balanced_Assignment):
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
            split_parts = general_constraints.split_into_n_parts(unfilled_df, n_parts, max_rows=80, Strict_Population=Strict_Population, Balanced_Assignment=Balanced_Assignment)
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


'''def build_result_dictionary(power_parts, main_parts, gpio_parts, sdrb_parts, ddr_parts):
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
        raise'''


def build_result_dictionary(
    power_parts,
    main_parts,
    gpio_parts,
    sdrb_parts,
    ddr_parts,
    csi_interface_parts=None,
    lvds_interface_parts=None,
):
    """
    Step 7: Build final dictionary.

    Accepts additional optional parts for CSI_Interface and LVDS_Interface.
    If those are None, they are treated as empty lists.
    """
    try:
        print("🏗️ Step 7: Building result dictionary...")
        df_dict = {}

        # Normalize optional lists
        csi_interface_parts = csi_interface_parts or []
        lvds_interface_parts = lvds_interface_parts or []

        # Helper to add a list of DataFrames under a base label
        def _add_parts(parts_list, base_label):
            for i, part in enumerate(parts_list):
                if hasattr(part, "empty") and not part.empty:
                    key = f"{base_label} - {i+1}" if len(parts_list) > 1 else base_label
                    df_dict[key] = part
                    print(f"📦 Added {key}: {len(part)} rows")

        # Power tables
        _add_parts(power_parts, "Power Table")

        # Main parts: decide Port Table vs Part Table by Priority prefix
        for i, main_part in enumerate(main_parts):
            if hasattr(main_part, "empty") and not main_part.empty:
                if any(main_part['Priority'].str.startswith('P_Port', na=False)):
                    key = f"Port Table - {i+1}"
                    df_dict[key] = main_part
                    print(f"📦 Added {key}: {len(main_part)} rows")
                else:
                    key = f"Part Table - {i+1}"
                    df_dict[key] = main_part
                    print(f"📦 Added {key}: {len(main_part)} rows")

        # GPIO / SDRB / DDR
        _add_parts(gpio_parts, "GPIO Table")
        _add_parts(sdrb_parts, "SDRB Table")
        _add_parts(ddr_parts, "DDR Table")

        # New: CSI / LVDS
        _add_parts(csi_interface_parts, "CSI Interface Table")
        _add_parts(lvds_interface_parts, "LVDS Interface Table")

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


def partitioning(df_last, Strict_Population,Balanced_Assignment):
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
    #unfilled_df, gpio_parts, sdrb_parts, ddr_parts = handle_special_pin_separation(unfilled_df, df)

    unfilled_df, gpio_parts, sdrb_parts, ddr_parts, csi_interface_parts, lvds_interface_parts = handle_special_pin_separation(
        unfilled_df, df, functional_separation=True
    )


    # Step 6: Process main parts
    main_parts = process_main_parts(unfilled_df, Strict_Population,Balanced_Assignment)
    
    # Step 7: Build result dictionary
    df_dict = build_result_dictionary(power_parts, main_parts, gpio_parts, sdrb_parts, ddr_parts, csi_interface_parts, lvds_interface_parts)
    
    # Step 8: Validate results
    validate_final_results(df_dict, df)
    
    print("🏁 === PARTITIONING END ===")
    return df_dict
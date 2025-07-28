import json


def assigning_priority(df,priority_mapping_json):
    df_copy = df.copy()  
    df_copy['Priority'] = df_copy.apply(lambda row: priority_order(row, df_copy,priority_mapping_json), axis=1)
    return df_copy


def priority_order(row, df, priority_mapping_json):
    with open(priority_mapping_json, 'r') as file:
        mappings = json.load(file)

    value = str(row.get('Grouping', '')).strip()  # Ensure value is a string, avoid None
    index = row.name
    value_alternative = str(row.get('Pin Alternate Name', ''))
    pin_display_name = str(row.get('Pin Display Name', ''))
    electrical_type = str(row.get('Electrical Type', ''))

    # 1. Highest priority: Direct mapping
    if value in mappings.get('priority_map', {}):
        return mappings['priority_map'][value]

    # 2. Input + Port check 
    is_input_or_io_or_output = electrical_type in ['Input', 'I/O','Output']
    is_port = value.startswith("Port")
    
    if is_input_or_io_or_output and is_port:
        # 2A. Mixed port assignment
        port_assignment = handle_mixed_port_assignment(pin_display_name, value, df)
        if port_assignment:
            print(f"Step 2A: Mixed port assignment returned: {port_assignment}")
            return port_assignment

        # 2B. Swap conditions
        pin_names = [name.strip() for name in value_alternative.split('/')]
        for alt_name, priority in mappings.get('swap_conditions', {}).items():
            if alt_name in pin_names:
                print(f"Swap match: '{alt_name}' found in '{value_alternative}' → Priority: {priority}")
                swap_pins_for_that_row(df, index, mappings['swap_conditions'])
                return priority

        return f"P_{value}"

    # 3. Generic Port handling
    if is_port:
        parts = value.split()

        if len(parts) >= 2:
            # Example: "P 10"
            try:
                port_number = int(parts[1])
                return f"P_Port_{port_number:02d}"
            except ValueError:
                return f"P_Port_{parts[1]}"

        elif len(parts) == 1:
            # Example: "Port_00"
            sub_parts = parts[0].split("_")
            if len(sub_parts) == 2 and sub_parts[1].isdigit():
                port_number = int(sub_parts[1])
                return f"P_Port_{port_number:02d}"


    # 4. Prefix-based mapping fallback
    for key, prefix in mappings.get('priority_map', {}).items():
        if value.startswith(key):
            return f"{prefix}_{value}"

    # 5. Final fallback
    return f"ZZ_{value}"

def swap_pins_for_that_row(df, index, swap_conditions):
    print(f"🔍 Processing row: {index}")
    
    current_display = df.loc[index, 'Pin Display Name']
    current_alternate = df.loc[index, 'Pin Alternate Name']
    
    # Split alternate names into list
    pin_names = [name.strip() for name in current_alternate.split('/')]

    matched = False
    
    # Check swap conditions
    for key, details in swap_conditions.items():      
        
        if key in pin_names or key == current_display:
            matched_part = key
            matched = True
            print(f"✅Swap Match Found: {matched_part}")
            
            # Replace in alternate if match found there
            if key in pin_names:
                new_alternate = current_alternate.replace(matched_part, current_display)
                print(f"♻️ Swapping in Alternate: {current_alternate} ➡️ {new_alternate}")
            else:
                new_alternate = current_alternate
                print(f"⚠️ No swap in Alternate (key not found there)")
            
            new_display = matched_part
            print(f"🆕 New Display: {new_display}")
            
            # Apply updates to DataFrame
            df.loc[index, 'Pin Display Name'] = new_display
            df.loc[index, 'Pin Alternate Name'] = new_alternate
            
            # If electrical type change exists
            if 'type' in details:
                old_type = df.loc[index, 'Electrical Type']
                df.loc[index, 'Electrical Type'] = details['type']
                print(f"🔌 Electrical Type changed: {old_type} ➡️ {details['type']}")
            
            print(f"✅ Row Updated Successfully!\n")
            return
    
    if not matched:
        print(f"❌ No match found for row {index}\n")


def handle_mixed_port_assignment(pin_display_name, grouping_value, df):
    """
    Handles special case where a port group contains both PXX and PXXX pins.
    Only shows debug output when mixed pins are found.
    """
    # Get all pins in the current group
    group_pins = df[df['Grouping'] == grouping_value]['Pin Display Name'].tolist()
    
    # Check if group has both PXX (3 chars) and PXXX (4 chars)
    has_pxx = any(len(pin) == 3 and pin.startswith('P') and pin[1:].isdigit() for pin in group_pins)
    has_pxxx = any(len(pin) == 4 and pin.startswith('P') and pin[1:].isdigit() for pin in group_pins)
    
    if has_pxx and has_pxxx:
        print(f"\n=== MIXED PORT GROUP DETECTED ===")
        print(f"Group: {grouping_value}")
        print(f"All pins: {group_pins}")
        print(f"Current pin: {pin_display_name}")
        
        pin = pin_display_name
        if len(pin) == 3 and pin.startswith('P'):  # PXX case
            port_num = int(pin[1])  # Take first digit after P
            print(f"Assigning {pin} to P_Port {port_num:02d} (PXX rule: first digit)")
            return f"P_Port_{port_num:02d}"
        elif len(pin) == 4 and pin.startswith('P'):  # PXXX case
            port_num = int(pin[1:3])  # Take first two digits after P
            print(f"Assigning {pin} to P_Port {port_num:02d} (PXXX rule: first two digits)")
            return f"P_Port_{port_num:02d}"
    
    return None
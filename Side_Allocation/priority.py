import json


def assigning_priority(df,priority_mapping_json):
    df_copy = df.copy()  
    df_copy['Priority'] = df_copy.apply(lambda row: priority_order(row, df_copy,priority_mapping_json), axis=1)
    return df_copy


def priority_order(row, df, priority_mapping_json):
    with open(priority_mapping_json, 'r') as file:
        mappings = json.load(file)

    value = row['Grouping']
    index = row.name
    value_alternative = row['Pin Alternate Name']
    pin_display_name = row['Pin Display Name']

    # print(f"\n--- DEBUG: Processing {pin_display_name} ---")
    # print(f"Grouping: '{value}'")
    # print(f"Electrical Type: '{row['Electrical Type']}'")
    # print(f"Pin Alternate Name: '{value_alternative}'")

    # 1. Highest priority: Direct mapping
    if value in mappings['priority_map']:
        #print(f"Step 1: Direct mapping found - returning {mappings['priority_map'][value]}")
        return mappings['priority_map'][value]
    #else:
    #    print("Step 1: No direct mapping found")
    
    # 2. Clock-related cases
    # clock_found = False
    # for clock_type, priority in mappings['clock_map'].items():
    #     if clock_type in value:
    #         print(f"Step 2: Clock mapping found - returning {priority}")
    #         return priority
    #print("Step 2: No clock mapping found")
    
    # 3. Input + Port check 
    input_port_condition = (row['Electrical Type'] == 'Input' or row['Electrical Type'] == 'I/O') and value.strip().startswith("Port")
    #print(f"Step 3: Input/IO + Port condition: {input_port_condition}")
    #print(f"  - Electrical Type check: {row['Electrical Type'] == 'Input' or row['Electrical Type'] == 'I/O'}")
    #print(f"  - Port check: {value.strip().startswith('Port')}")
    
    if input_port_condition:
        #print("Step 3: Entering Input/IO + Port handling")
        
        # 3A. FIRST: Check for mixed port assignment (PXX vs PXXX)
        #print("Step 3A: Checking for mixed port assignment before swap conditions")
        port_assignment = handle_mixed_port_assignment(pin_display_name, value, df)
        if port_assignment:
            print(f"Step 3A: Mixed port assignment returned: {port_assignment}")
            return port_assignment
        
        # 3B. THEN: Check swap conditions
        for alt_name, priority in mappings['swap_conditions'].items():
            pin_names = str(value_alternative).split('/')
            if alt_name in pin_names:
                print(f"EXACT MATCH FOUND! '{alt_name}' found in '{value_alternative}' with priority {priority}")
                swap_pins_for_that_row(df, index, mappings['swap_conditions'])
                return priority
        
        #print(f"Step 3: No swap conditions met, returning P_{value}")
        return f"P_{value}"
  
    # 4B. Generic Port handling 
    generic_port_condition = value.strip().startswith("Port")
    #print(f"Step 4B: Generic port condition: {generic_port_condition}")
    
    if generic_port_condition:
        try:
            port_number = int(value.split(' ')[1])
            result = f"P_Port {port_number:02d}"
            #print(f"Step 4B: Generic port handling - returning {result}")
            return result
        except ValueError:
            result = f"P_Port {value.split(' ')[1]}"
            #print(f"Step 4B: Generic port handling (ValueError) - returning {result}")
            return result
    
    # 5. Default case
    #print("Step 5: Returning None (default case)")
    #return None

    # 5. Fallback: Check for prefix-based mapping
    for key, prefix in mappings.get("priority_map", {}).items():
        if value.startswith(key):
            return f"{prefix}_{value}"

    # 6. Final fallback
    return f"ZZ_{value}"

def swap_pins_for_that_row(df, index, swap_conditions):
    current_display = df.loc[index, 'Pin Display Name']
    current_alternate = df.loc[index, 'Pin Alternate Name']
    
    # Find which swap_condition key is present in the alternate name as a separate pin
    for key in swap_conditions.keys():
        # Split by '/' to get individual pin names and check if key matches exactly
        pin_names = current_alternate.split('/')
        if key in pin_names:
            # Extract the matching part (e.g., "X1" from "P121/X1/INTP1")
            matched_part = key
            
            # Swap ONLY the matched part with display name
            new_alternate = current_alternate.replace(matched_part, current_display)
            new_display = matched_part
            
            df.loc[index, 'Pin Display Name'] = new_display
            df.loc[index, 'Pin Alternate Name'] = new_alternate
            
            # Update Electrical Type based on matched part
            if matched_part in ["X1", "X2", "XT1", "XT2", "MD", "NMI", "//RESET", "RESET"]:
                df.loc[index, 'Electrical Type'] = 'Input'
            elif matched_part == "RESOUT":
                df.loc[index, 'Electrical Type'] = 'Output'
            elif matched_part in ["VREF", "VRFF"]:
                df.loc[index, 'Electrical Type'] = 'Power'
            # Else keep electrical type as it is (no change needed)
            
            return

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
            return f"P_Port {port_num:02d}"
        elif len(pin) == 4 and pin.startswith('P'):  # PXXX case
            port_num = int(pin[1:3])  # Take first two digits after P
            print(f"Assigning {pin} to P_Port {port_num:02d} (PXXX rule: first two digits)")
            return f"P_Port {port_num:02d}"
    
    return None
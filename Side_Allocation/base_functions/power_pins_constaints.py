import pandas as pd 
from . import general_constraints

def filter_out_power_pins(row, df):
    # Fill NaN values in Priority column
    priority_value = str(row['Priority']) if pd.notna(row['Priority']) else ''

    # Check for left power pins (starting with 'A')
    if priority_value.startswith('A'):
        return 'Left'
    # Check for right power pins (starting with 'Z' or 'Y')  
    elif priority_value.startswith(('Z', 'Y')):
        return 'Right'
    else:
        return None
    
def split_power_pins_by_priority(power_df, Strict_Population, max_rows=80):
    """
    Split power pins into multiple DataFrames based on priority grouping constraints
    """

    print(f"\n=== SPLITTING POWER PINS ({len(power_df)} total) ===")

    if power_df.empty:
        print("  [DEBUG] Input power_df is empty. Returning empty list.")
        return []

    # Print initial column info and sample
    print(f"  [DEBUG] Input DataFrame columns: {power_df.columns.tolist()}")
    print(f"  [DEBUG] Sample rows:\n{power_df.head(3)}")

    # Sort by priority to maintain order
    power_df_sorted = power_df.sort_values('Priority', na_position='last').reset_index(drop=True)
    print(f"  [DEBUG] Sorted power_df by Priority. First 3 priorities: {power_df_sorted['Priority'].head(3).tolist()}")

    # Group pins by priority prefix
    priority_groups = {
        'A_group': power_df_sorted[power_df_sorted['Priority'].astype(str).str.startswith('A')],
        'Z_Y_group': power_df_sorted[power_df_sorted['Priority'].astype(str).str.startswith(('Z', 'Y'))],
        'Other_group': power_df_sorted[~power_df_sorted['Priority'].astype(str).str.startswith(('A', 'Z', 'Y'))]
    }

    print("Priority grouping:")
    for name, group in priority_groups.items():
        print(f"  [DEBUG] {name}: {len(group)} pins")

    power_parts = []

    # Process each group
    for group_name, group_df in priority_groups.items():
        if group_df.empty:
            print(f"  [DEBUG] Skipping {group_name} - empty group.")
            continue

        print(f"\nProcessing {group_name}: {len(group_df)} pins")

        if len(group_df) <= max_rows:
            print(f"  [DEBUG] Group fits within {max_rows} rows.")
            try:
                group_df_processed = general_constraints.side_for_one_symbol(group_df)
                power_parts.append(group_df_processed)
                print(f"  -> Created single part with {len(group_df_processed)} pins")
            except Exception as e:
                print(f"  [ERROR] Failed to assign side for {group_name}: {e}")
        else:
            print(f"  [DEBUG] Group exceeds {max_rows} rows, needs splitting.")
            try:
                group_parts = split_large_power_group(group_df, max_rows)
                print(f"  [DEBUG] Split into {len(group_parts)} parts.")
                for idx, part in enumerate(group_parts):
                    print(f"    Part {idx + 1}: {len(part)} pins")
                power_parts.extend(group_parts)
            except Exception as e:
                print(f"  [ERROR] Failed to split {group_name}: {e}")

    # Final merge for small parts
    try:
        original_count = len(power_parts)
        power_parts = merge_small_power_parts(power_parts, max_rows)
        print(f"\n[DEBUG] Merged small power parts. Before: {original_count}, After: {len(power_parts)}")
    except Exception as e:
        print(f"  [ERROR] Failed during merging small parts: {e}")

    print(f"\nFinal power parts: {len(power_parts)} DataFrames")
    for i, part in enumerate(power_parts, 1):
        print(f"  Power part {i}: {len(part)} pins")

    return power_parts


def split_large_power_group(group_df, max_rows):
    """
    Split a large power group into multiple parts of max_rows each
    """
    parts = []
    
    for i in range(0, len(group_df), max_rows):
        part = group_df.iloc[i:i + max_rows].copy()
        part_processed = general_constraints.side_for_one_symbol(part)
        parts.append(part_processed)
    
    return parts


def merge_small_power_parts(power_parts, max_rows):
    """
    Try to merge small power parts together to optimize DataFrame count
    while respecting the max_rows constraint
    """
    if len(power_parts) <= 1:
        return power_parts
    
    merged_parts = []
    current_merge = pd.DataFrame()
    
    for part in power_parts:
        # Check if we can merge this part with current_merge
        if len(current_merge) + len(part) <= max_rows:
            # Merge is possible
            if current_merge.empty:
                current_merge = part.copy()
            else:
                current_merge = pd.concat([current_merge, part], ignore_index=True)
        else:
            # Can't merge, finalize current_merge and start new one
            if not current_merge.empty:
                merged_parts.append(current_merge)
            current_merge = part.copy()
    
    # Add the last merge
    if not current_merge.empty:
        merged_parts.append(current_merge)
    
    return merged_parts
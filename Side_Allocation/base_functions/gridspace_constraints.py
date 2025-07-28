from . import single80pin_constraints
import pandas as pd

def split_large_identical_groups(df, current_unused_grids):
    """
    Split large groups where all pins have identical names into smaller subgroups
    to minimize unused grids. Only called when unused grids > 30.
    """
    print(f"\n=== Splitting large groups to reduce unused grids ({current_unused_grids}) ===")
    
    # Create a copy to avoid modifying original during iteration
    df_modified = df.copy()
    
    # Find the largest group with identical pin names
    largest_group = None
    largest_size = 0
    largest_priority = None
    
    for priority, group in df.groupby('Priority'):
        group_size = len(group)
        unique_names = group['Pin Display Name'].nunique()
        
        if unique_names == 1 and group_size > largest_size:  # All pins have identical names
            largest_group = group
            largest_size = group_size
            largest_priority = priority
    
    if largest_group is None:
        print("No large groups with identical pin names found for splitting")
        return df_modified
    
    pin_name = largest_group['Pin Display Name'].iloc[0]
    print(f"Found largest group '{largest_priority}' with {largest_size} identical pins ('{pin_name}')")
    
    # Calculate current grid distribution
    group_sizes = df.groupby('Priority').size()
    group_sides = df.groupby('Priority')['Side'].first()
    
    left_groups = group_sides[group_sides == 'Left'].index.tolist()
    right_groups = group_sides[group_sides == 'Right'].index.tolist()
    
    current_left_grids = sum(group_sizes[group_sides == 'Left']) + max(0, len(left_groups) - 1)
    current_right_grids = sum(group_sizes[group_sides == 'Right']) + max(0, len(right_groups) - 1)
    
    print(f"Current: Left={current_left_grids}, Right={current_right_grids}, Unused={current_unused_grids}")
    
    # Try different split sizes to find the one that minimizes unused grids
    best_split = None
    best_unused_grids = current_unused_grids
    
    # Try splitting the largest group into 2 parts with different ratios
    for split_ratio in [0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7]:
        group1_size = int(largest_size * split_ratio)
        group2_size = largest_size - group1_size
        
        if group1_size == 0 or group2_size == 0:
            continue
            
        # Calculate what happens if we put group1 on left and group2 on right
        # (or vice versa depending on which side the original group was on)
        original_side = group_sides[largest_priority]
        
        if original_side == 'Left':
            # Remove original group from left, add split groups to both sides
            new_left_grids = current_left_grids - largest_size + group1_size
            new_right_grids = current_right_grids + group2_size + (1 if len(right_groups) > 0 else 0)
        else:
            # Remove original group from right, add split groups to both sides
            new_left_grids = current_left_grids + group1_size + (1 if len(left_groups) > 0 else 0)
            new_right_grids = current_right_grids - largest_size + group2_size
        
        new_unused_grids = abs(new_left_grids - new_right_grids)
        
        print(f"  Split ratio {split_ratio:.2f}: {group1_size}/{group2_size} pins → Unused grids: {new_unused_grids}")
        
        if new_unused_grids < best_unused_grids:
            best_unused_grids = new_unused_grids
            best_split = (group1_size, group2_size, split_ratio)
    
    if best_split is None:
        print("No beneficial split found")
        return df_modified
    
    group1_size, group2_size, split_ratio = best_split
    print(f"  → Best split: {group1_size} + {group2_size} pins (ratio {split_ratio:.2f})")
    print(f"  → Unused grids will reduce from {current_unused_grids} to {best_unused_grids}")
    
    # Apply the best split
    group_sorted = largest_group.sort_values('Pin Designator')
    
    # Split into two groups
    group1_indices = group_sorted.iloc[:group1_size].index
    group2_indices = group_sorted.iloc[group1_size:].index
    
    # Create new priority names
    new_priority1 = f"{largest_priority}_1"
    new_priority2 = f"{largest_priority}_2"
    
    # Update priorities
    df_modified.loc[group1_indices, 'Priority'] = new_priority1
    df_modified.loc[group2_indices, 'Priority'] = new_priority2
    
    # Assign sides to minimize unused grids
    original_side = group_sides[largest_priority]
    if original_side == 'Left':
        df_modified.loc[group1_indices, 'Side'] = 'Left'
        df_modified.loc[group2_indices, 'Side'] = 'Right'
    else:
        df_modified.loc[group1_indices, 'Side'] = 'Left'
        df_modified.loc[group2_indices, 'Side'] = 'Right'
    
    print(f"  → Created: '{new_priority1}' ({group1_size} pins) and '{new_priority2}' ({group2_size} pins)")
    
    return df_modified

def calculate_unused_grids(df):
    """
    Calculate current unused grids based on side assignments.
    """
    # Ensure side assignments exist
    if 'Side' not in df.columns:
        df['Side'] = df.apply(lambda row: single80pin_constraints.allocate_pin_side_by_priority(row, df), axis=1)
    
    # Get group sizes and side assignments
    group_sizes = df.groupby('Priority').size()
    group_sides = df.groupby('Priority')['Side'].first()
    
    left_groups = group_sides[group_sides == 'Left'].index.tolist()
    right_groups = group_sides[group_sides == 'Right'].index.tolist()
    
    left_grids = sum(group_sizes[group_sides == 'Left']) + max(0, len(left_groups) - 1)
    right_grids = sum(group_sizes[group_sides == 'Right']) + max(0, len(right_groups) - 1)
    
    return abs(left_grids - right_grids)

def print_grid_spaces(df):
    # Group pins by Priority
    grouped = df.groupby('Priority')

    # Determine side assignment for each pin using `allocate_pin_side_by_priority`
    df['Side'] = df.apply(lambda row: single80pin_constraints.allocate_pin_side_by_priority(row, df), axis=1)

    # Initialize counters for grid usage
    left_grids = 0
    right_grids = 0

    #print("\nGrid Usage:")
    for priority, group in grouped:
        pins_in_group = len(group)
        side = group['Side'].iloc[0]  # All pins in group are on the same side

        # Each pin takes one grid + 1 separator between groups
        if side == 'Left':
            left_grids += pins_in_group
            if left_grids != pins_in_group:  # Avoid separator before first group
                left_grids += 1
        else:
            right_grids += pins_in_group
            if right_grids != pins_in_group:
                right_grids += 1

        #print(f"Group '{priority}' -> {pins_in_group} pins -> Side: {side}")

    print(f"\nTotal Grid Spaces:")
    print(f"Left: {left_grids} grids")
    print(f"Right: {right_grids} grids")
    print(f"Unused grids : {abs(left_grids - right_grids)}")

def balance_grid_space(df):
    # Calculate initial unused grids
    initial_unused_grids = calculate_unused_grids(df)
    print(f"Initial unused grids: {initial_unused_grids}")

    # Step 1: Optional splitting based on unused grid space
    if initial_unused_grids > 30:
        print("Splitting large identical groups (unused > 30)...")
        df = split_large_identical_groups(df, initial_unused_grids)

    # Step 2: Group and side tracking
    group_sizes = df.groupby('Priority').size()
    group_sides = df.groupby('Priority')['Side'].first()
    left_groups = group_sides[group_sides == 'Left'].index.tolist()
    right_groups = group_sides[group_sides == 'Right'].index.tolist()

    # Step 3: Handle single-sided group imbalance
    if not left_groups or not right_groups:
        dominant_side = 'Left' if left_groups else 'Right'
        print(f"⚠️  All groups on one side ({dominant_side}), rebalancing...")

        all_groups = group_sides.index.tolist()

        if len(all_groups) == 1:
            single_group = all_groups[0]
            group_df = df[df['Priority'] == single_group]
            total_pins = len(group_df)
            print(f"\tSingle group '{single_group}' with {total_pins} pins")

            if total_pins >= 2:
                group_df_sorted = single80pin_constraints.assigning_ascending_order_for_similar_group(group_df, column_name='Pin Display Name')
                half = total_pins // 2
                left_indices = group_df_sorted.iloc[:half].index
                right_indices = group_df_sorted.iloc[half:].index
                df.loc[left_indices, 'Side'] = 'Left'
                df.loc[right_indices, 'Side'] = 'Right'
                print(f"\tSplit: {half} Left / {total_pins - half} Right")
            else:
                print(f"\tOnly one pin. Skipping split.")
                return df
        else:
            half = len(all_groups) // 2
            new_left = all_groups[:half]
            new_right = all_groups[half:]
            print(f"\tReassigned: {len(new_left)} to Left / {len(new_right)} to Right")
            df.loc[df['Priority'].isin(new_left), 'Side'] = 'Left'
            df.loc[df['Priority'].isin(new_right), 'Side'] = 'Right'

        # Recompute after balancing
        group_sizes = df.groupby('Priority').size()
        group_sides = df.groupby('Priority')['Side'].first()
        left_groups = group_sides[group_sides == 'Left'].index.tolist()
        right_groups = group_sides[group_sides == 'Right'].index.tolist()

    # Step 4: Final side rebalance
    if not left_groups or not right_groups:
        print("Still unbalanced after correction. Skipping further balancing.")
        return df

    last_left = left_groups[-1]
    first_right = right_groups[0]

    left_grids = sum(group_sizes[group_sides == 'Left']) + max(0, len(left_groups) - 1)
    right_grids = sum(group_sizes[group_sides == 'Right']) + max(0, len(right_groups) - 1)
    imbalance = abs(left_grids - right_grids)
    print(f"Grid usage - Left: {left_grids}, Right: {right_grids}, Imbalance: {imbalance}")

    if imbalance <= 1:
        print("Imbalance within tolerance. No swap needed.")
        return df

    size_last_left = group_sizes[last_left]
    size_first_right = group_sizes[first_right]

    # Hypothetical moves
    new_imbalance_LtoR = abs((left_grids - size_last_left - 1) - (right_grids + size_last_left + 1))
    new_imbalance_RtoL = abs((left_grids + size_first_right + 1) - (right_grids - size_first_right - 1))

    if new_imbalance_RtoL <= new_imbalance_LtoR and new_imbalance_RtoL < imbalance:
        print(f"✅ Rebalanced: Moved '{first_right}' to Left (Imbalance: {new_imbalance_RtoL})")
        df.loc[df['Priority'] == first_right, 'Side'] = 'Left'
    elif new_imbalance_LtoR < imbalance:
        print(f"✅ Rebalanced: Moved '{last_left}' to Right (Imbalance: {new_imbalance_LtoR})")
        df.loc[df['Priority'] == last_left, 'Side'] = 'Right'
    else:
        print("❌ No improvement from swap. Keeping current balance.")

    return df



def lighthouse_view(parts, n_parts, max_rows):
    """
    Rebalance all parts to make distribution as even as possible,
    keeping groups with the same prefix together.
    """
    all_data = pd.concat(parts)

    # Group by Priority first
    grouped = list(all_data.groupby('Priority'))

    # Determine prefix key for grouping priorities
    def get_prefix(priority):
        if '_' in priority:
            return priority.split('_')[0]  # Take part before first '_'
        return priority[:2]  # If no '_', take first 2 letters as fallback

    # Create prefix-based super-groups
    prefix_groups = {}
    for priority, group in grouped:
        prefix = get_prefix(priority)
        if prefix not in prefix_groups:
            prefix_groups[prefix] = []
        prefix_groups[prefix].append(group)

    # Merge each prefix group into a single DataFrame
    super_groups = []
    for prefix, groups in prefix_groups.items():
        combined_group = pd.concat(groups)
        super_groups.append((prefix, combined_group))

    # Sort super-groups by size (largest first)
    super_groups.sort(key=lambda x: len(x[1]), reverse=True)

    # Re-assign super-groups to parts
    new_parts = [pd.DataFrame() for _ in range(n_parts)]
    part_counts = [0] * n_parts

    for prefix, group in super_groups:
        # Pick the least filled part (ignore max_rows if needed)
        idx = min(range(n_parts), key=lambda i: part_counts[i])
        new_parts[idx] = pd.concat([new_parts[idx], group])
        part_counts[idx] += len(group)

    return new_parts


def distributed_view(parts, n_parts, max_rows):
    """
    Re-distribute into balanced parts while:
    ✅ Preserving order
    ✅ Keeping 'Priority' groups intact
    ✅ Allowing slight imbalance
    """

    all_data = pd.concat(parts, ignore_index=True)

    # ✅ Group by Priority in original order
    grouped = [(priority, group) for priority, group in all_data.groupby('Priority', sort=False)]

    # Calculate target size per part
    total_rows = len(all_data)
    target_size = total_rows // n_parts

    new_parts = []
    current_part = []
    current_count = 0

    for i, (priority, group) in enumerate(grouped):
        group_size = len(group)

        # If adding this group exceeds target size (and not last part) -> cut here
        if current_count + group_size > target_size and len(new_parts) < n_parts - 1:
            new_parts.append(pd.concat(current_part, ignore_index=True))
            current_part = []
            current_count = 0

        current_part.append(group)
        current_count += group_size

    # Append last part
    if current_part:
        new_parts.append(pd.concat(current_part, ignore_index=True))

    # ✅ Debug log
    print(f"🔄 Distributed View (Preserve Order): {total_rows} pins")
    for i, part in enumerate(new_parts, 1):
        print(f"   📦 Part {i}: {len(part)} pins (indices {part.index.min()}-{part.index.max()})")

    return new_parts


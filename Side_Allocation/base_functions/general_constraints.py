import pandas as pd
import re

from . import gridspace_constraints
from . import single80pin_constraints

def side_for_one_symbol(df):

    if df.empty:
        print("Warning: Empty DataFrame passed to side_for_one_symbol")
        return df

    df_copy = df.copy()
    df_new = single80pin_constraints.filter_and_sort_by_priority(df_copy)

    # Assign side
    df_new['Side'] = df_new.apply(lambda row: single80pin_constraints.allocate_pin_side_by_priority(row, df_new), axis=1)
    gridspace_constraints.print_grid_spaces(df_new)
    df_new = gridspace_constraints.balance_grid_space(df_new)

    # Assign order (same logic for both sides)
    df_new = single80pin_constraints.assigning_ascending_order_for_similar_group(df_new)

    return df_new.reset_index(drop=True)


'''def split_into_n_parts(df, n_parts, max_rows=80, Strict_Population=True, Balanced_Assignment=False):
  
    # Step 1: Sort groups by numeric key to ensure ordered processing
    def extract_numeric_key(pin_name):
        """Extract numeric part from pin name for sorting."""
        if '_' in pin_name:
            parts = pin_name.split('_')
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return 999999
        
        match = re.match(r'^([A-Za-z]+)(\d+)$', pin_name)
        if match:
            return int(match.group(2))
        
        return 999999

    grouped_indices = {
        k: v for k, v in sorted(
            df.groupby('Priority').indices.items(),
            key=lambda item: extract_numeric_key(item[0])
        )
    }

    parts = [pd.DataFrame() for _ in range(n_parts)]
    part_row_counts = [0] * n_parts

    if Strict_Population:
        # Original behavior
        for priority, indices in grouped_indices.items():
            group = df.loc[indices]
            if Balanced_Assignment:
                # Find the most balanced part that still has room
                eligible_parts = [
                    (i, part_row_counts[i]) for i in range(n_parts)
                    if part_row_counts[i] + len(group) <= max_rows
                ]

                if eligible_parts:
                    target_idx = min(eligible_parts, key=lambda x: x[1])[0]
                    parts[target_idx] = pd.concat([parts[target_idx], group])
                    part_row_counts[target_idx] += len(group)
                else:
                    # Force append to the last part if no one can hold it
                    parts[-1] = pd.concat([parts[-1], group])
                    part_row_counts[-1] += len(group)
    else:
        # Strict ordered part population (non-balanced)
        current_part = 0
        for priority, indices in grouped_indices.items():
            group = df.loc[indices]

            if part_row_counts[current_part] + len(group) > max_rows:
                current_part += 1
                if current_part >= n_parts:
                    print(f"⚠️ Not enough parts to hold all groups within max_rows limit.")
                    break

            parts[current_part] = pd.concat([parts[current_part], group])
            part_row_counts[current_part] += len(group)

    # ✅ Lighthouse View: Final Rebalancing if Balanced_Assignment=True
    if Balanced_Assignment:
        parts = gridspace_constraints.lighthouse_view(parts, n_parts, max_rows)

    return parts'''

def split_into_n_parts(df, n_parts, max_rows=80, Strict_Population=True, Balanced_Assignment=False):
    """
    Split df into n_parts without breaking Priority groups.
    Maintains original order of df (row order), not sorted by numeric key.
    If a group cannot fit in current part, move to next part (even if overflow occurs).
    """

    # ✅ Group rows by Priority in original order
    grouped = [(priority, group) for priority, group in df.groupby('Priority', sort=True)]

    parts = [pd.DataFrame() for _ in range(n_parts)]
    part_row_counts = [0] * n_parts
    current_part = 0

    for priority, group in grouped:
        group_size = len(group)

        # If adding this group exceeds max_rows AND current part is not empty -> move to next part
        if part_row_counts[current_part] > 0 and part_row_counts[current_part] + group_size > max_rows:
            current_part += 1

        # If we run out of parts, just append to the last part
        if current_part >= n_parts:
            current_part = n_parts - 1

        # Add group to current part
        parts[current_part] = pd.concat([parts[current_part], group])
        part_row_counts[current_part] += group_size

    # ✅ Lighthouse View: Final Rebalancing if Balanced_Assignment=True
    if Balanced_Assignment:
        #parts = gridspace_constraints.lighthouse_view(parts, n_parts, max_rows)
        parts = gridspace_constraints.distributed_view(parts, n_parts, max_rows)

    return parts


def final_filter(df):
    # Step 1: Remove 'Grouping' column if it exists
    if "Grouping" in df.columns:
        df = df.drop(columns=["Grouping"])

    # Step 2: Rename 'Priority' to 'Grouping' if it exists
    if "Priority" in df.columns:
        df = df.rename(columns={"Priority": "Grouping"})

    # Step 3: Replace NaN with empty string
    df = df.fillna("")

    # Step 4: Convert 'Pin Designator' to int if possible BEFORE string cleanup
    if "Pin Designator" in df.columns:
        df["Pin Designator"] = df["Pin Designator"].apply(
            lambda x: int(float(x)) if isinstance(x, (int, float)) or 
                      (isinstance(x, str) and x.replace('.', '', 1).isdigit()) 
                      else x
        )

    # Step 5: Clean string values only in object/string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(lambda x: str(x).strip().replace('  ', ' ')
                                .replace('\n', ' ').replace(' ', '_'))

    return df
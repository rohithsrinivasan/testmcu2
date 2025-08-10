import re
from . import gridspace_constraints

def filter_and_sort_by_priority(df):

    if df.empty:
        print("The DataFrame is empty; skipping sorting.")
        return df  # Return the empty DataFrame as is

    #print(f"Descriptive Columns in DataFrame: {list(df.columns)}")  # Print all column names
    sorted_df = df.sort_values(by='Priority', ascending=True).reset_index(drop=True)
    return sorted_df


def allocate_pin_side_by_priority(row, df):
    """
    Assigns each pin (row) to 'Left' or 'Right' side based on its Priority group,
    ensuring balanced distribution. Prioritizes filling the Left side first and
    avoids splitting Priority groups. Returns an error message if total pins exceed 80.
    """
    total_rows = len(df)

    grouped_indices = df.groupby('Priority').indices
    left, right = [], []
    left_limit = (total_rows + 1) // 2  # ceiling division
    last_side = 'Left'

    for group in list(grouped_indices.values()):
        if last_side == 'Left' and len(left) + len(group) <= left_limit:
            left.extend(group)
        else:
            right.extend(group)
            last_side = 'Right'

    # Optional: diagnostic output
    # print(f"\nPin Distribution:")
    # print(f"Total pins: {total_rows}")
    # print(f"Left side: {len(left)} pins")
    # print(f"Right side: {len(right)} pins")

    return 'Left' if row.name in left else 'Right'

def extract_numeric_key(pin_name):
    """Extract numeric part from pin name for sorting."""
    if '_' in pin_name:
        parts = pin_name.split('_')
        try:
            return int(parts[-1])
        except (ValueError, IndexError):
            return 999999
    
    #match = re.match(r'^([A-Za-z]+)(\d+)$', pin_name)
    match = re.search(r'([A-Za-z]+)(\d+)', pin_name)
    if match:
        return int(match.group(2))
    
    return 999999

def assigning_ascending_order_for_similar_group(df, column_name='Pin Display Name'):
    df = df.copy()
    
    # Extract numeric sorting key
    df['__numeric_key__'] = df[column_name].apply(extract_numeric_key)
    
    # Sort by Priority first, then by numeric key, then by pin name
    sorted_df = df.sort_values(
        by=['Priority', '__numeric_key__', column_name],
        ascending=[True, True, True]
    ).drop(columns=['__numeric_key__'])
    
    return sorted_df.reset_index(drop=True)
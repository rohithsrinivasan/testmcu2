import re
from .base_functions import single80pin_constraints
from .base_functions import gridspace_constraints
from .base_functions import general_constraints


def side_for_singlepart(df):
    """Apply side assignment logic for single symbol DataFrame."""
    side_added = general_constraints.side_for_one_symbol(df)
    return side_added


def side_for_multipart(dataframes_dict):
    if not isinstance(dataframes_dict, dict):
        raise ValueError("Input must be a dictionary")
    
    if not dataframes_dict:
        return {}    
    processed_dfs = {}
    
    for table_name, df in dataframes_dict.items():
        if df is None:
            processed_dfs[table_name] = None
            continue
        df_processed = df.copy(deep=True)
        df_processed = general_constraints.side_for_one_symbol(df_processed)
        processed_dfs[table_name] = df_processed
    
    return processed_dfs

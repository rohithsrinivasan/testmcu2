import re
from .base_functions import single80pin_constraints
from .base_functions import gridspace_constraints
from .base_functions import general_constraints
from .base_functions import power_pins_constaints


def side_for_singlepart(df):
    """Apply side assignment logic for single symbol DataFrame."""
    side_added = general_constraints.side_for_one_symbol(df)
    return side_added


'''def side_for_multipart(dataframes_dict):
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
'''


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

        # ✅ Apply logic based on key name
        if table_name.startswith("Power"):
            # Apply filter_out_power_pins to assign 'Side' column
            df_processed['Side'] = df_processed.apply(lambda row: power_pins_constaints.filter_out_power_pins(row, df_processed), axis=1)
        else:
            # Default logic for non-power tables
            df_processed = general_constraints.side_for_one_symbol(df_processed)
        
        processed_dfs[table_name] = df_processed
    
    return processed_dfs
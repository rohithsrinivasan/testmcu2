import pandas as pd
    

def check_excel_format(df, required_columns, optional_column=None, default_value=' '):
    """
    Universal function to check DataFrame or dict of DataFrames format.
    Adds missing optional column if needed.
    
    Args:
        df: DataFrame or dict of DataFrames
        required_columns: list of required column names
        optional_column: optional column name (added if missing)
        default_value: default value for optional column
    
    Returns:
        tuple: (is_valid, processed_data)
    """

    def _process_dataframe(df, required_columns, optional_column, default_value):
        """Internal function to process a single DataFrame"""
        df_cols = set(df.columns)
        required_set = set(required_columns)
        
        # Perfect match
        if df_cols == required_set:
            return True, df
        
        # Has optional column too
        if optional_column and df_cols == required_set.union({optional_column}):
            return True, df
        
        # Missing only optional column - add it
        if optional_column and df_cols == required_set:
            df_copy = df.copy()
            df_copy[optional_column] = default_value
            return True, df_copy
        
        # Format mismatch
        print(f"Format mismatch. Expected: {required_columns}, Found: {list(df.columns)}")
        return False, df

    try:
        # Handle single DataFrame
        if isinstance(df, pd.DataFrame):
            return _process_dataframe(df, required_columns, optional_column, default_value)
        
        # Handle dictionary of DataFrames
        elif isinstance(df, dict):
            all_valid = True
            processed_dict = {}
            
            for key, dataframe in df.items():
                is_valid, processed_df = _process_dataframe(dataframe, required_columns, optional_column, default_value)
                processed_dict[key] = processed_df
                if not is_valid:
                    all_valid = False
            
            return all_valid, processed_dict
        
        else:
            print("Invalid input: must be DataFrame or dict of DataFrames")
            return False, df
            
    except Exception as e:
        print(f"Error: {e}")
        return False, df


def flatten_label_map(nested_dict, parent_key=""):
    flat_dict = {}
    for k, v in nested_dict.items():
        new_key = f"{parent_key}_{k}" if parent_key else k
        if isinstance(v, dict):
            flat_dict.update(flatten_label_map(v, new_key))
        else:
            flat_dict[new_key] = v
    return flat_dict


def remove_electrical_type(df):
    columns_removed = []
    
    # Remove "Electrical Type" column if it exists
    if "Electrical Type" in df.columns:
        df = df.drop(columns=["Electrical Type"])
        columns_removed.append("Electrical Type")
        print("'Electrical Type' column has been removed.")
    else:
        print("'Electrical Type' column is not present in the DataFrame.")
    
    # Remove "Grouping" column if it exists
    if "Grouping" in df.columns:
        df = df.drop(columns=["Grouping"])
        columns_removed.append("Grouping")
        print("'Grouping' column has been removed.")
    else:
        print("'Grouping' column is not present in the DataFrame.")
    
    # Return the updated DataFrame and a flag indicating if any columns were removed
    return df, False


def remove_description_type(df):
    columns_removed = []
    
    # Remove "Description" column if it exists
    if "Description" in df.columns:
        df = df.drop(columns=["Description"])
        columns_removed.append("Description")
        print("'Description' column has been removed.")
    else:
        print("'Description' column is not present in the DataFrame.")
    
    # Return the updated DataFrame and a flag indicating if any columns were removed
    return df, False

def check_empty_groupings(df):
    empty_groupings = df[df['Grouping'].isna()]
    return empty_groupings


def normalize_string(text):
    """
    Normalize string by converting to uppercase, removing spaces, 
    and removing characters like "(", ")", "[", "]", "."
    """
    if not isinstance(text, str):
        return str(text)
    
    # Convert to uppercase
    normalized = text.upper()
    
    # Remove spaces
    normalized = normalized.replace(" ", "")
    
    # Remove specific characters
    chars_to_remove = ["(", ")", "[", "]", "."]
    for char in chars_to_remove:
        normalized = normalized.replace(char, "")
    
    return normalized
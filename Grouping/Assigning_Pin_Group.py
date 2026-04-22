from .base_functions import general_funct
import json
import re
import difflib
import os
import pandas as pd


def sensitivity_match(name1, name2):
    """
    Normalize and compare two strings by removing special characters and ignoring case.
    """
    def normalize(s):
        return re.sub(r'[\\/_#.\s]', '', s).lower().strip()
    
    return normalize(name1) == normalize(name2)


import difflib

def smart_search_match(name, names, cutoff=0.7):
    """
    Find the closest matching name from a list of names using string similarity.

    Parameters:
        name (str): The input name to match.
        names (list): A list of candidate names to compare against.
        cutoff (float): Similarity threshold (0 to 1), default is 0.7.

    Returns:
        str or None: The closest matching name if found, otherwise None.
    """
    name = name.strip()
    candidates = [item.strip() for item in names]
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def grouping_as_per_database(old_df, json_paths, SENSITIVITY=True, SMARTSEARCH=False, SINGLE_FILE=False):
    df = old_df.copy()
    
    # Initialize the 'Grouping' column here to prevent KeyError, regardless of errors.
    if 'Grouping' not in df.columns:
        df['Grouping'] = None

    json_file_path = None
    label_maps = []

    try:
        # Determine the file path based on the structure of json_paths
        if isinstance(list(json_paths.values())[0], str):
            json_file_path = list(json_paths.values())[0]
        else:
            nested_dict = list(json_paths.values())[0]
            json_file_path = list(nested_dict.values())[0]
        
        print(f"Attempting to load data from: {json_file_path}")

        # Check if the file exists
        if not os.path.exists(json_file_path):
            error_message = f"❌ Error: JSON database file not found at path: '{json_file_path}'."
            print(error_message)
            df['Grouping'] = error_message
            return df

        # Check if the file is empty
        if os.path.getsize(json_file_path) == 0:
            error_message = f"❌ Error: JSON database file is empty at path: '{json_file_path}'."
            print(error_message)
            df['Grouping'] = error_message
            return df
            
        with open(json_file_path, 'r') as f:
            try:
                # Attempt to load the JSON data
                data = json.load(f)
                single_label_map = general_funct.flatten_label_map(data)
                label_maps = [single_label_map]
                print("✅ JSON file loaded and flattened successfully.")
            except json.JSONDecodeError as e:
                # Handle malformed JSON
                error_message = f"❌ Error: Failed to parse JSON file '{json_file_path}'. Details: {e}"
                print(error_message)
                df['Grouping'] = error_message
                return df
    
    except Exception as e:
        # Catch any other unexpected errors during file path handling
        error_message = f"❌ An unexpected error occurred while processing the database paths: {e}"
        print(error_message)
        df['Grouping'] = error_message
        return df

    # Helper function remains the same
    #def get_label(name, maps_to_check):
        # Helper to get label from maps
    def get_label(name, maps_to_check):
        name = name.strip()

        # Try case-sensitive match
        for label_map in maps_to_check:
            for label, names in label_map.items():
                if name in [item.strip() for item in names]:
                    return label

        # Try normalized match if case-insensitive
        if not SENSITIVITY:
            for label_map in maps_to_check:
                for label, names in label_map.items():
                    for item in names:
                        if sensitivity_match(name, item):
                            return label

        if SMARTSEARCH:
            for label_map in maps_to_check:
                for label, names in label_map.items():
                    match = smart_search_match(name, names)
                    if match:
                        return label
        
    # Proceed with grouping only if label_maps were successfully created
    if label_maps:
        for index, row in df.iterrows():
            if pd.isna(df.at[index, 'Grouping']):
                raw_label = get_label(row['Pin Display Name'], label_maps)
                
                if raw_label is not None:
                    # Strip the Side information before assignment
                    # Split the string at the first underscore and take the second part
                    parts = raw_label.split('_', 1)
                    if len(parts) > 1 and (parts[0] == "Left" or parts[0] == "Right"):
                        cleaned_label = parts[1]
                    else:
                        cleaned_label = raw_label
                    
                    df.at[index, 'Grouping'] = cleaned_label

    print("✅ Labels assigned to Grouping column successfully.")
    return df


# Add this function after the imports section
def suggest_power_subcategories(pin_table, json_paths_power):
    """Test all Power subcategories and return suggestions ranked by completeness"""
    suggestions = []
    
    for sub_cat, json_path in json_paths_power.items():
        try:
            test_database = {sub_cat: json_path}
            test_result = grouping_as_per_database(
                pin_table.copy(),
                test_database,
                SENSITIVITY=False,
                SMARTSEARCH=False,
                SINGLE_FILE=True
            )
            
            # Count filled vs empty groupings
            total_pins = len(test_result)
            filled_pins = test_result['Grouping'].notna().sum()
            has_errors = any("❌" in str(val) for val in test_result['Grouping'].values)
            
            if not has_errors:
                match_percentage = (filled_pins / total_pins) * 100
                suggestions.append({
                    'subcategory': sub_cat,
                    'percentage': match_percentage,
                    'filled': filled_pins,
                    'total': total_pins
                })
        except Exception as e:
            continue
    
    # Sort by percentage (descending), then by filled count
    suggestions.sort(key=lambda x: (x['percentage'], x['filled']), reverse=True)
    return suggestions

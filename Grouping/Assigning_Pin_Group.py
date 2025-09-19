from .base_functions import general_funct
import json
import re
import difflib

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


'''
def grouping_as_per_database(old_df, json_paths, SENSITIVITY=True,SMARTSEARCH= False, SINGLE_FILE=False):
    df = old_df.copy()

    try:
        if SINGLE_FILE:
            # Flatten only one single JSON file
            with open(json_paths['Single'], 'r') as f:
                single_label_map = general_funct.flatten_label_map(json.load(f))
            label_maps = [single_label_map]
        else:
            # Flatten all JSON files
            with open(json_paths['Input'], 'r') as f:
                input_label_map = general_funct.flatten_label_map(json.load(f))
            with open(json_paths['Power'], 'r') as f:
                power_label_map = general_funct.flatten_label_map(json.load(f))
            with open(json_paths['Output'], 'r') as f:
                output_label_map = general_funct.flatten_label_map(json.load(f))
            with open(json_paths['I/O'], 'r') as f:
                io_label_map = general_funct.flatten_label_map(json.load(f))
            with open(json_paths['Passive'], 'r') as f:
                passive_label_map = general_funct.flatten_label_map(json.load(f))

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
                for label_map in label_maps:
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


            print(f"Warning: Could not find a matching label for '{name}' in JSON file(s).")
            return None

        # Initialize new column
        df['Grouping'] = None

        # Assign labels
        for index, row in df.iterrows():
            if SINGLE_FILE:
                label = get_label(row['Pin Display Name'], label_maps)
            else:
                if row['Electrical Type'] == "Input":
                    label = get_label(row['Pin Display Name'], [input_label_map, io_label_map, power_label_map, output_label_map, passive_label_map])
                elif row['Electrical Type'] == "Power":
                    label = get_label(row['Pin Display Name'], [power_label_map, io_label_map, input_label_map, output_label_map, passive_label_map])
                elif row['Electrical Type'] == "Output":
                    label = get_label(row['Pin Display Name'], [output_label_map, io_label_map, input_label_map, power_label_map, passive_label_map])
                elif row['Electrical Type'] == "I/O":
                    label = get_label(row['Pin Display Name'], [io_label_map, input_label_map, power_label_map, output_label_map, passive_label_map])
                elif row['Electrical Type'] == "Passive":
                    label = get_label(row['Pin Display Name'], [passive_label_map, io_label_map, input_label_map, power_label_map, output_label_map])
                else:
                    label = None

            if label is not None:
                df.at[index, 'Grouping'] = label

        print("✅ Labels assigned to Grouping column successfully.")

    except Exception as e:
        print(f"❌ Error processing files: {e}")

    return df

'''

def grouping_as_per_database(old_df, json_paths, SENSITIVITY=True, SMARTSEARCH=False, SINGLE_FILE=False):
    df = old_df.copy()

    try:
        # Check if the json_paths object is a simple dictionary or a nested one
        if isinstance(list(json_paths.values())[0], str):
            # This handles the original single file case or the new 'MCU Devices' case.
            # We assume there's only one key whose value is a string.
            json_file_path = list(json_paths.values())[0]
            with open(json_file_path, 'r') as f:
                single_label_map = general_funct.flatten_label_map(json.load(f))
            label_maps = [single_label_map]
        else:
            # This handles the nested 'Power' category case.
            # We assume json_paths contains a single key with a nested dictionary.
            nested_dict = list(json_paths.values())[0]
            json_file_path = list(nested_dict.values())[0]
            with open(json_file_path, 'r') as f:
                single_label_map = general_funct.flatten_label_map(json.load(f))
            label_maps = [single_label_map]

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

            print(f"Warning: Could not find a matching label for '{name}' in JSON file(s).")
            return None

        # Initialize new column
        df['Grouping'] = None

        # Assign labels
        for index, row in df.iterrows():
            # Since we are always passing a single file dictionary now, this simplifies
            # the logic for assigning labels.
            label = get_label(row['Pin Display Name'], label_maps)

            if label is not None:
                df.at[index, 'Grouping'] = label

        print("✅ Labels assigned to Grouping column successfully.")

    except Exception as e:
        print(f"❌ Error processing files: {e}")

    return df


import json
import os
import pandas as pd

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

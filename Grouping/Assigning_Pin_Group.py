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

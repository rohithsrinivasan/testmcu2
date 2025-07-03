import json

def pin_type_as_per_database(old_df, json_paths):
    df = old_df.copy()
    
    # Load all JSON files
    label_maps = {}
    for key, path in json_paths.items():
        with open(path, 'r') as f:
            label_maps[key] = json.load(f)
    
    def get_file_name(pin_name):
        pin_name = pin_name.strip().replace(" ", "_")
        matches = set()
        
        # Search through all JSON files
        for file_name, label_map in label_maps.items():
            for main_category, sub_categories in label_map.items():
                if isinstance(sub_categories, dict):
                    # Handle nested structure: {"Clock": {"A_Main": ["X1", "X2"]}}
                    for sub_category, pin_list in sub_categories.items():
                        if isinstance(pin_list, list) and pin_name in pin_list:
                            matches.add(file_name)
                elif isinstance(sub_categories, list):
                    # Handle direct list: {"Clock": ["X1", "X2"]}
                    if pin_name in sub_categories:
                        matches.add(file_name)
        
        # Return result based on matches found
        if len(matches) > 1:
            print(f"🛑 Conflict: Pin '{pin_name}' found in multiple files: {matches}. Assigning 'NAss'.")
            return "NAss"  # Multiple files contain this pin
        elif len(matches) == 1:
            return matches.pop()  # Found in exactly one file
        else:
            print(f"🛑 Warning: Pin '{pin_name}' not found in any JSON file. Assigning 'NAv'.")
            return "NAv"  # Not found in any file
    
    # Apply the search function to each pin
    df['Electrical Type'] = df['Pin Display Name'].apply(get_file_name)
    print("✅ Pin Type assigned to Electrical Type column successfully.")

    return df

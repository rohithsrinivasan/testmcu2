from .base_functions import general_funct
import json

def grouping_as_per_database(old_df, json_paths):
    df = old_df.copy()
    
    try:
        # Load all JSON files
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

        # Define a generic function to search for a label in all JSON files
        def get_label(name, label_maps):
            name = name.strip()
            for label_map in label_maps:
                for label, names in label_map.items():
                    if name in [item.strip() for item in names]:
                        return label
            print(f"Warning: Could not find a matching label for {name} in any JSON file.")
            return None

        # Apply the correct function based on Electrical Type
        df['Grouping'] = None  # Initialize the Grouping column with None

        for index, row in df.iterrows():
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
                label = None  # Handle unknown Electrical Types

            if label is not None:
                df.at[index, 'Grouping'] = label

        print("✅ Labels assigned to Grouping column successfully.")

    except Exception as e:
        print(f"Error processing files: {e}")

    return df
import json
import pandas as pd

def convert_nested_json_to_excel(json_filepath, excel_filepath):
    """
    Converts a nested JSON file with a specific structure into an Excel file.

    The JSON is expected to have a main key, then sub-keys, and values as a list.
    The Excel file will have three columns: "Main Group", "Subgroup", and "Values".

    Args:
        json_filepath (str): The path to the input JSON file.
        excel_filepath (str): The path where the output Excel file will be saved.
    """
    try:
        with open(json_filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_filepath}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_filepath}. Please check the file format.")
        return

    all_records = []

    for main_group, subgroups_data in data.items():
        if isinstance(subgroups_data, dict):
            for subgroup, values_list in subgroups_data.items():
                if isinstance(values_list, list):
                    for value in values_list:
                        all_records.append({
                            "Main Group": main_group,
                            "Subgroup": subgroup,
                            "Values": value
                        })
                else:
                    # Handle cases where values are not a list but directly a string/number
                    all_records.append({
                        "Main Group": main_group,
                        "Subgroup": subgroup,
                        "Values": values_list
                    })
        else:
            # Handle cases where the main_group directly contains a list or single value
            # This might need adjustment based on your full JSON structure
            print(f"Warning: Unexpected structure for main group '{main_group}'. Skipping or handling as single value.")
            all_records.append({
                "Main Group": main_group,
                "Subgroup": "N/A", # Or some default/empty string
                "Values": subgroups_data
            })


    if not all_records:
        print("No data found to convert. The JSON structure might not match the expected format.")
        return

    df = pd.DataFrame(all_records)

    try:
        df.to_excel(excel_filepath, index=False)
        print(f"Successfully converted '{json_filepath}' to '{excel_filepath}'")
    except Exception as e:
        print(f"An error occurred while writing to Excel: {e}")

# --- Usage Example ---
if __name__ == "__main__":

    json_input_filename = "Grouping\mcu_database\mcu_passive.json"  # <--- CHANGE THIS to your JSON file's name
    output_excel_filename = "mcu_input_data.xlsx"

    # Call the conversion function
    convert_nested_json_to_excel(json_input_filename, output_excel_filename)
import os
import json

# Paths (update these)
json_dir = "Grouping/mcu_database"  # Directory containing 5 JSON files
map_file = "Side_Allocation/priority_map.json"    # Path to map.json

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def get_main_keys(json_obj):
    """Extract top-level keys from a JSON object."""
    if isinstance(json_obj, dict):
        return set(json_obj.keys())
    return set()

def main():
    # Collect all main keys from the 5 JSON files
    main_keys_from_files = set()
    for file_name in os.listdir(json_dir):
        if file_name.endswith(".json") and file_name != "map.json":
            file_path = os.path.join(json_dir, file_name)
            try:
                data = load_json(file_path)
                keys = get_main_keys(data)
                main_keys_from_files.update(keys)
            except Exception as e:
                print(f"Error reading {file_name}: {e}")

    # Load map.json and extract keys under "priority_map"
    map_data = load_json(map_file)
    priority_map = map_data.get("priority_map", {})
    if not isinstance(priority_map, dict):
        print("Error: 'priority_map' not found or invalid in map.json")
        return

    map_keys = set(priority_map.keys())

    # Compare
    missing_in_map = main_keys_from_files - map_keys
    extra_in_map = map_keys - main_keys_from_files

    print("\n=== Comparison Result ===")
    if missing_in_map:
        print(f"Keys present in JSON files but missing in map.json[priority_map]: {missing_in_map}")
    else:
        print("No missing keys in map.json[priority_map].")

    if extra_in_map:
        print(f"Keys present in map.json[priority_map] but not in JSON files: {extra_in_map}")
    else:
        print("No extra keys in map.json[priority_map].")

if __name__ == "__main__":
    main()

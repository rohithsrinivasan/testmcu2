import json

# Path to your JSON file
file_path = "Grouping\shrinidhi_database\combined.json"

# Load the JSON data
with open(file_path, 'r') as f:
    data = json.load(f)

my_list = []

# Navigate to 'Positives' and print first-level subkeys
if "Positive" in data:
    positive = data["Positive"]
    if isinstance(positive, dict):
        print("Subkeys under 'Positive':")
        for key in positive.keys():
            my_list.append(key)
        new_list = sorted(my_list)
        for key in new_list:
            print("-", key)
    else:
        print("'Positive' is not a dictionary.")
else:
    print("'Positive' key not found in the JSON.")

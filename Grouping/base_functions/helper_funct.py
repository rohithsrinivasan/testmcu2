import json
import os
import glob
from fuzzywuzzy import process

def load_json_files(file_paths):
    data = {}
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            data.update(json.load(file))
    return data

def load_json_files_with_type_labels(directory):
    json_data = {}
    json_files = glob.glob(os.path.join(directory, '*.json'))
    for file_path in json_files:
        with open(file_path, 'r') as file:
            data = json.load(file)
            json_data[file_path] = data
    return json_data

def save_json_file(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def get_suggestions(user_input, json_data):

    key_matches = process.extract(user_input, json_data.keys(), limit=5)
    # Step 2: Create a dictionary to store the number of good matches for each key
    key_good_matches = {}
    
    # Step 3: Calculate the number of good matches for each key
    for key, _ in key_matches:
        good_matches = 0
        for value in json_data[key]:
            match_score = process.extractOne(user_input, [value])[1]
            if match_score > 0:  # Count any match (no threshold)
                good_matches += 1
        key_good_matches[key] = good_matches
    
    # Step 4: Sort the keys first by match percentage (descending), then by number of good matches (descending)
    sorted_keys = sorted(key_matches, key=lambda x: (-x[1], -key_good_matches[x[0]]))
    
    limit = 5
    # Step 5: Return the top `limit` suggestions
    return sorted_keys[:limit]
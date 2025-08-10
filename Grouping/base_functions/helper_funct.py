import json
import os
import glob
from fuzzywuzzy import process
import pandas as pd

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



def get_suggestions(user_input, nested_json, top_n=5):
    from difflib import SequenceMatcher
    import re

    def flatten_label_map(nested_dict, parent_key=""):
        flat_dict = {}
        for k, v in nested_dict.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            if isinstance(v, dict):
                flat_dict.update(flatten_label_map(v, new_key))
            else:
                flat_dict[new_key] = v
        return flat_dict

    def extract_port_prefix(pin):
        """Replaces the part after underscore with '_0' for grouping similarity."""
        pin = pin.upper()
        if "_" in pin:
            return re.sub(r'_.+', '_0', pin)
        return pin

    def generate_fallback_pin(pin):
        """Generate fallback pin by replacing suffix with _0."""
        if "_" in pin:
            return re.sub(r'_.+', '_0', pin.upper())
        return pin.upper()

    def is_one_digit_different(s1, s2):
        """True if both strings differ by only one digit at the same position."""
        if len(s1) != len(s2):
            return False
        diffs = 0
        for c1, c2 in zip(s1, s2):
            if c1 != c2:
                if c1.isdigit() and c2.isdigit():
                    diffs += 1
                else:
                    return False
            if diffs > 1:
                return False
        return diffs == 1

    user_input_upper = user_input.upper()
    user_port_prefix = extract_port_prefix(user_input_upper)

    # Flatten the nested JSON
    flat_json = flatten_label_map(nested_json)

    # Build a list of all (pin, group)
    all_pins = []
    for group, pins in flat_json.items():
        for pin in pins:
            all_pins.append((pin.upper(), group))

    # Step 1: Try exact match
    for pin, group in all_pins:
        if pin == user_input_upper:
            return [(pin, 100, group)]

    # Step 2: Try fallback (_0 version)
    fallback_input = generate_fallback_pin(user_input_upper)
    for pin, group in all_pins:
        if pin == fallback_input:
            return [(pin, 95, group)]

    # Step 3: Fuzzy match with bonus logic
    results = []
    for pin, group in all_pins:
        base_score = int(SequenceMatcher(None, user_input_upper, pin).ratio() * 100)

        bonus = 0

        # Strong bonus for port-prefix match
        pin_prefix = extract_port_prefix(pin)
        if user_port_prefix and pin_prefix == user_port_prefix:
            bonus += 40
        elif user_port_prefix and pin_prefix != user_port_prefix:
            bonus -= 20

        # Bonus for only one digit difference (e.g., GETH1VCL vs GETH0VCL)
        if is_one_digit_different(user_input_upper, pin):
            bonus = max(bonus, 20)  # Ensure at least some bonus

        total_score = min(max(base_score + bonus, 0), 100)
        results.append((pin, total_score, group))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def auto_fill_grouping_if_exact_match(df, json_data, match_percentage):
    """
    For each row in the DataFrame, use the 'Pin Display Name' to get suggestions.
    If the top suggestion is a 100% match, fill in the 'Grouping' column with the matched group.
    """

    df = df.copy()

    for index, row in df.iterrows():
        pin_display_name = row.get("Pin Display Name", "")
        current_grouping = row.get("Grouping", "")

        # Handle None values safely
        pin_display_name = pin_display_name.strip() if isinstance(pin_display_name, str) else ""
        current_grouping = current_grouping.strip() if isinstance(current_grouping, str) else ""

        if pin_display_name and (not current_grouping or pd.isna(current_grouping)):
            suggestions = get_suggestions(pin_display_name, json_data, top_n=1)

            if suggestions:
                closest_pin, match_score, matched_group = suggestions[0]

                if match_score > match_percentage:
                    df.at[index, "Grouping"] = matched_group

    return df







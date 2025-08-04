import json

def print_tree(data, indent=""):
    if isinstance(data, dict):
        for i, key in enumerate(data):
            is_last = i == len(data) - 1
            branch = "└── " if is_last else "├── "
            print(indent + branch + str(key))
            extension = "    " if is_last else "│   "
            print_tree(data[key], indent + extension)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            is_last = i == len(data) - 1
            branch = "└── " if is_last else "├── "
            print(indent + branch + f"[{i}]")
            extension = "    " if is_last else "│   "
            print_tree(item, indent + extension)
    else:
        # For terminal values (e.g., strings, numbers)
        print(indent + "└── " + str(data))

def main():
    # === Replace this path with your actual JSON file path
    file_path = r"Grouping\shrinidhi_database\combined.json"

    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    if "Positive" not in json_data:
        print("❌ 'Positive' key not found in the JSON file.")
        return

    print("📂 Tree structure under 'Positive':\n")
    print("Positive")
    print_tree(json_data["Positive"])

if __name__ == "__main__":
    main()

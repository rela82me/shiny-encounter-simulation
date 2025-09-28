import re
import json

# Raw text data from your input
raw_dex_data = 

pokedex_num_to_name = {}

pokedex_num_to_name = {}

for line in raw_dex_data.strip().split('\n'):
    if line.strip().startswith('#') or not line.strip():
        continue

    match = re.match(r'^(.*\S)\s+([\d,]+)$', line.strip())

    if match:
        name = match.group(1).strip()
        number = int(match.group(2).replace(',', ''))

        if number not in pokedex_num_to_name:
            pokedex_num_to_name[number] = name

# --- CREATE THE FINAL DATA STRUCTURES ---

MASTER_DEX_LIST = list(pokedex_num_to_name.values())
NAME_TO_NUMBER_DEX = {name: num for num, name in pokedex_num_to_name.items()}

# This is the dictionary that will be written to the JSON file.
# It contains both your list and your other dictionary.
final_pokedex_data = {
    "master_dex_list": MASTER_DEX_LIST,
    "name_to_number_dex": NAME_TO_NUMBER_DEX
}

# --- NEW OUTPUT SECTION FOR JSON ---

# Open a file named 'pokedex.json' in write mode ('w').
# We still use encoding='utf-8' to handle special characters.
with open('pokedex.json', 'w', encoding='utf-8') as f:
    # json.dump() writes the Python dictionary to the file in JSON format.
    # indent=4 makes the file nicely formatted and easy for a human to read.
    json.dump(final_pokedex_data, f, indent=4)

print("Successfully created the pokedex.json file!")

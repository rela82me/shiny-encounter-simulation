# %%
import random as rand
import pandas as pd
import json

# Open data, with proper encoding for weird text doh.
with open('pokedex.json', 'r', encoding='utf-8') as f:
    pokedex_data = json.load(f)

# Create list & Dictionary
MASTER_DEX_LIST = pokedex_data["master_dex_list"]
NAME_TO_NUMBER_DEX = pokedex_data["name_to_number_dex"]
total_encounter = 0

# Main set that is used to determine unique shiny encounters. Set's only allow unique identifiers,
# so encounters added here will automatically be new.
shiny_dex = set()
normal_dex = set()

# Create the lists ONLY for counting for the report at the end. The set handles the uniqueness and determining if we "got em all"
normal_box_counts = {}
shiny_box_counts = {}


# Variables/Constants
SHINY_RATE = (1 / 4096)

# functions needed: encounter


def encounter():
    global total_encounter
    total_encounter += 1

    # Encounter Logic
    encountered_pokemon = rand.choice(MASTER_DEX_LIST)
    is_shiny = rand.random() < SHINY_RATE

    if is_shiny:
        shiny_dex.add(encountered_pokemon)
        shiny_box_counts[encountered_pokemon] = shiny_box_counts.get(
            encountered_pokemon, 0) + 1
        print(
            f"Caught Shiny: {encountered_pokemon}!!! That's the {shiny_box_counts[encountered_pokemon]} shiny of this species! and the {len(shiny_dex)} shiny overall!")
    else:
        normal_dex.add(encountered_pokemon)
        normal_box_counts[encountered_pokemon] = normal_box_counts.get(
            encountered_pokemon, 0) + 1
        print(f"Caught: {encountered_pokemon} | Encounter: {total_encounter}")


def output_results():
    # output to terminal
    print("Simulation Finished!")
    print(f"Total Encounters: {total_encounter}")
    print(f"Unique Shiny Pokemon: {shiny_box_counts}")
    print(f"Unique Normal Pokemon: {normal_box_counts}")

    # CSV
    normal_df = pd.DataFrame(list(normal_box_counts.items()),
                             columns=['Pokemon', 'Encounters'])
    shiny_df = pd.DataFrame(list(shiny_box_counts.items()),
                            columns=['Pokemon', 'Shiny Encounters'])

    normal_df.to_csv('normal_encounters.csv', index=False)
    shiny_df.to_csv('shiny_encounters.csv', index=False)
    print("Successfully saved reports to /normal_encounters.csv and /shiny_encounters.csv")


# While loop to maintain simulation
# should output in loop which pokemon is being encountered. This will give the user something to look at.
# Start Encounter > Random Pokemon > Is it Shiny? > If yes: Add to shiny box | If no: Add to regular box > New Encounter

while len(shiny_dex) < len(MASTER_DEX_LIST):
    # Encounter Logic/logpoint
    encounter()

output_results()

# %%

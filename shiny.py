# %%
import random as rand
import pandas as pd
import json
import sys
import time

# Open data, with proper encoding for weird text doh.
with open('pokedex.json', 'r', encoding='utf-8') as f:
    pokedex_data = json.load(f)

# Create list & Dictionary
total_encounter = 0

#Setting up the Data Structures

POKEDEX = {}
spawnrate_weights = {
    "Slow": 0.1,
    "Medium Slow": 0.25,
    "Medium Fast": 0.35,
    "Fast": 0.5,
    "Fluctuating": 0.7,
    "Erratic": .9
}
list_of_pokemon = pokedex_data['Pokedex']

#Create the master pokedex in a dictionary with the key of the pokemons name for lookup purposes later. 
for pokemon in list_of_pokemon: 
    pokemon_name = pokemon['name']

    pokemon_stats = {}
    
    pokemon_stats['pokedex number'] = pokemon['pokedex number']
    pokemon_stats['Catch Rate'] = pokemon['Catch Rate']
    pokemon_stats['Experience Type'] = pokemon['Experience Type']
    
    experience_type = pokemon['Experience Type']
    spawn_weight = spawnrate_weights[experience_type]

    pokemon_stats['Spawn Weight'] = spawn_weight
    
    POKEDEX[pokemon_name] = pokemon_stats

#loop through the pokedex to create two lists for the pokemon and spawn weights. 
#This is to feed rand the format of data it needs since they will be in corresponding positions within 

pokemon_for_encountering = []
spawn_weights =[]

for pokemon in POKEDEX:
    pokemon_details = POKEDEX[pokemon]
    pokemon_spawn_weight = pokemon_details['Spawn Weight']
    
    pokemon_for_encountering.append(pokemon)
    spawn_weights.append(pokemon_spawn_weight) 
    
# Main set that is used to determine unique shiny encounters. Set's only allow unique identifiers,
# so encounters added here will automatically be new.
shiny_dex = set()
normal_dex = set()

# Create the lists ONLY for counting for the report at the end. The set handles the uniqueness and determining if we "got em all"
normal_box_counts = {}
shiny_box_counts = {}



# Variables/Constants
SHINY_RATE = (1 / 4096)

# block changed to markdown so simulation doesn't run. 
# functions needed: encounter

def encounter():
    global total_encounter
    total_encounter += 1

    # Encounter Logic
    encountered_pokemon = rand.choices(pokemon_for_encountering, weights=spawn_weights, k=1)[0]
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

start_time = time.time()
print("Starting Shiny Pokemon Encounter Simulation...")
print("Press Ctrl+C to stop the simulation early.")
try:
    while len(shiny_dex) < len(POKEDEX):
        encounter()
        if total_encounter % 1000 == 0:
            percentage_shiny = (len(shiny_dex)/len(POKEDEX)) * 100
            percentage_normal = (len(normal_dex)/len(POKEDEX)) * 100
            print (f"Encounters: {total_encounter:,} | Shinies Caught: {len(shiny_box_counts)}/ {len(POKEDEX)} ({percentage_shiny:.2f}%) | Normals Caught: {len(normal_box_counts)/len(POKEDEX)} ({percentage_normal:.2f}%)", end='\r')
        sys.stdout.flush()
except KeyboardInterrupt:
    print("\nSimulation stopped by user.")

end_time = time.time()

total_seconds = end_time - start_time
total_minutes = total_seconds / 60
print(f"\nTotal Simulation Time: {total_minutes:.2f} minutes")
    
output_results()

# %%
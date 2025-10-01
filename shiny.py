# %%
import random as rand
import pandas as pd
import json
import sys
import time
import os

# Open data, with proper encoding for weird text doh.
with open('pokedex.json', 'r', encoding='utf-8') as f:
    pokedex_data = json.load(f)

# Create list & Dictionary
total_encounter = 0
total_shinies_caught = 0
total_normals_caught = 0

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
shiny_log = []


# Variables/Constants
SHINY_RATE = (1 / 4096)

# block changed to markdown so simulation doesn't run. 
# functions needed: encounter

def attempt_catch(pokemon_name):
    #simulate an attempt to catch a pokemon based on it's rate.
    pokemon_data = POKEDEX[pokemon_name]
    catch_rate = pokemon_data['Catch Rate']

    catch_probability = catch_rate / 255.0

    if rand.random() <= catch_probability:
        return True #Catch Succesful!
    else:
        return False #You lost it you ass


def encounter():
    global total_encounter, total_shinies_caught, total_normals_caught
    total_encounter += 1

    # Encounter Logic
    encountered_pokemon = rand.choices(pokemon_for_encountering, weights=spawn_weights, k=1)[0]
    is_shiny = rand.random() < SHINY_RATE

    if is_shiny:
        #1. Attempt to catch first
        catch_successful = attempt_catch(encountered_pokemon)

        #2. Check for uniqueness after the encounter but before logging. This will tell us if we need a new dex entry. 
        is_new_shiny = encountered_pokemon not in shiny_dex
        
        #3. Create log entry with the complete story of the encounter. 
        log_entry = {
            'Encounter_Number': total_encounter,
            'Pokemon': encountered_pokemon,
            'Catch_Successful': catch_successful,
            'Is_New_Shiny': is_new_shiny
        }
        shiny_log.append(log_entry)

        #4. Update the simulations state and print message only if the catch is new. 

        if catch_successful: 
            shiny_dex.add(encountered_pokemon)
            shiny_box_counts[encountered_pokemon] = shiny_box_counts.get(encountered_pokemon, 0) + 1
            total_shinies_caught += 1
            if is_new_shiny:
                #Print success line/progress updates to the user. 
                catch_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{catch_timestamp} - Gotcha! Shiny ✨{encountered_pokemon}'s✨ been caught!!! Only {len(POKEDEX)-len(shiny_dex)} left to go! ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨ ")

    else:
        total_normals_caught += 1
        normal_dex.add(encountered_pokemon)
        normal_box_counts[encountered_pokemon] = normal_box_counts.get(
            encountered_pokemon, 0) + 1


def output_results():
    # output to terminal
    print("\n\n" + "="*30)
    print("Simulation Finished!")
    print("="*30)
    print(f"Total Encounters: {total_encounter:,}")
    print(f"Unique Shiny Pokemon: {len(shiny_box_counts)}")
    print(f"Unique Normal Pokemon: {len(normal_box_counts)}")

    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")

    output_dir = "reports"

    os.makedirs(output_dir, exist_ok=True)

    normal_filepath = f"{output_dir}/normal_encounters_{timestamp}.csv"
    shiny_filepath = f"{output_dir}/shiny_encounters_{timestamp}.csv"
    analysis_filepath = f"{output_dir}/shiny_analysis_log_{timestamp}.csv"


    # CSV
    normal_df = pd.DataFrame(list(normal_box_counts.items()),
                             columns=['Pokemon', 'Encounters'])
    shiny_df = pd.DataFrame(list(shiny_box_counts.items()),
                            columns=['Pokemon', 'Shiny Encounters'])
    if shiny_log: #makes sure the list isn't empty. 
        analysis_df = pd.DataFrame(shiny_log)
        analysis_df.to_csv(analysis_filepath, index=False)
        print(f"Successfully saved analysis to {analysis_filepath}")

    normal_df.to_csv(normal_filepath, index=False)
    shiny_df.to_csv(shiny_filepath, index=False)
    print(f"Successfully saved reports to {normal_filepath} and {shiny_filepath}")

# While loop to maintain simulation
# should output in loop which pokemon is being encountered. This will give the user something to look at.
# Start Encounter > Random Pokemon > Is it Shiny? > If yes: Add to shiny box | If no: Add to regular box > New Encounter

def save_checkpoint():
    #bundles all critical files into a dictionary and saved to a JSON.
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    state = {
        'total_encounter': total_encounter,
        'total_shinies_caught': total_shinies_caught,
        'total_normals_caught': total_normals_caught,
        'shiny_dex': list(shiny_dex),
        'normal_dex': list(normal_dex),
        'shiny_box_counts': shiny_box_counts,
        'normal_box_counts': normal_box_counts,
        'shiny_log': shiny_log,
        'start_time': start_time,
    }

    with open('checkpoint.json', 'w') as f:
        json.dump(state, f, indent=4)

        print(f"{timestamp} --- 💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾 Checkpoint Saved! 💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾 ---")

def load_checkpoint():
    #Checks for a checkpoint file and loads the simulation state if it already exists.

    global total_encounter, total_shinies_caught, total_normals_caught, shiny_dex, shiny_box_counts, normal_box_counts, shiny_log, start_time

    try:
        with open('checkpoint.json', 'r') as f:
            state = json.load(f)

            total_encounter = state['total_encounter']
            total_shinies_caught = state['total_shinies_caught']
            total_normals_caught = state['total_normals_caught']
            shiny_dex = set(state['shiny_dex'])
            normal_dex = set(state['normal_dex'])
            shiny_box_counts = state['shiny_box_counts']
            normal_box_counts = state['normal_box_counts']
            shiny_log = state['shiny_log']
            start_time = state['start_time']

            print(" --- 💾Checkpoint Loaded! Resuming Simulation💾... ---")

    except FileNotFoundError:
        print("--- No Checkpoint found. Starting a new simulation. ---")


start_time = time.time()

print("Starting Shiny Pokemon Encounter Simulation...")
print("Press Ctrl+C to stop the simulation early.")

load_checkpoint()

try:
    while len(shiny_dex) < len(POKEDEX):
        encounter() # The main encounter function. 

        if total_encounter % 1_000_000 == 0:
            save_checkpoint()

        if total_encounter % 10_000 == 0: #Only display encounter updates every 1000 encounters. 

            current_time = time.time() # Current Date/Time
            elapsed_seconds = current_time - start_time
            current_duration_mins = elapsed_seconds/60 # Time spent in sim. 

            encounters_per_second = total_encounter / elapsed_seconds
            shinies_per_second = total_shinies_caught / elapsed_seconds


            percentage_shiny = (len(shiny_dex)/len(POKEDEX)) * 100 # Catch progress
            percentage_normal = (len(normal_dex)/len(POKEDEX)) * 100 # Catch progress

            

            # the end='\r' keeps the terminal line at the bottom. 
            print (f" Encounters: {total_encounter:,} ({encounters_per_second:.1f} EPS) | Unique Shinies Caught: {len(shiny_dex)} / {len(POKEDEX)} ({percentage_shiny:.2f}%) | Total Shinies: {total_shinies_caught} ({shinies_per_second:.2f} SPS) | Total Normals: {total_normals_caught} | Total Duration (mins): {current_duration_mins:.2f}", end='\r')
        
        sys.stdout.flush() #This sends out the print once total encounters hits 1000 an interval of
except KeyboardInterrupt:
    print("\nSimulation stopped by user.")

end_time = time.time()

total_seconds = end_time - start_time
total_minutes = total_seconds / 60
print(f"\nTotal Simulation Time: {total_minutes:.2f} minutes")
    
output_results()

# %%
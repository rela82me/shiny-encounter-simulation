
'''
This estimate model uses the remaining pokemon from the checkpoint. 
'''
import pandas as pd
import json
import os

# --- FILE PATHS ---
# Path to your main simulation's checkpoint file
CHECKPOINT_PATH = r'C:\Users\rela8\Documents\C VS Code\Project Files\Python Projects\Shiny Encounters\checkpoint.json'
# Path to your Excel data file
EXCEL_PATH = r'C:\Users\rela8\Documents\C VS Code\Project Files\Python Projects\Shiny Encounters\Pokemon Stats.xlsx'


# --- 1. LOAD AND PROCESS POKEMON DATA (Same as before) ---
try:
    pokedex_df = pd.read_excel(EXCEL_PATH, sheet_name='Pokedex')
except FileNotFoundError:
    print(f"FATAL ERROR: Could not find the Excel file at '{EXCEL_PATH}'")
    # Exit if we can't load the main data
    exit()

# --- MATCH YOUR SIMULATION PARAMETERS ---
STABILITY_CONSTANT = 100
RARITY_EXPONENT = 1.8
SHINY_RATE = 1 / 4096

# Calculate probabilities exactly like your simulation
pokedex_df['Spawn Weight'] = 1 / ((pokedex_df['base total'] + STABILITY_CONSTANT) ** RARITY_EXPONENT)
total_spawn_weight = pokedex_df['Spawn Weight'].sum()
pokedex_df['Spawn Probability'] = pokedex_df['Spawn Weight'] / total_spawn_weight
pokedex_df['Catch Probability'] = pokedex_df['Catch Rate'] / 255
pokedex_df['p_i'] = pokedex_df['Spawn Probability'] * pokedex_df['Catch Probability'] * SHINY_RATE


# --- 2. LOAD LIVE DATA FROM CHECKPOINT.JSON ---
current_encounters = 0
shinies_already_caught = set()

try:
    with open(CHECKPOINT_PATH, 'r') as f:
        checkpoint_data = json.load(f)
        current_encounters = checkpoint_data.get('total_encounter', 0)
        # Convert list from JSON to a set for efficient lookups
        shinies_already_caught = set(checkpoint_data.get('shiny_dex', []))
    print("✓ Successfully loaded data from checkpoint.json")
except (FileNotFoundError, json.JSONDecodeError):
    print("⚠ WARNING: Could not load or parse checkpoint.json. Using estimates.")
    # As a fallback, we can estimate progress if the file is missing
    # For now, we'll just start from 0 if the file isn't found
    pass


# --- 3. THE CALCULATION FUNCTION (Same as before) ---
def calculate_expected_encounters(probabilities):
    """Weighted Coupon Collector's Problem formula."""
    remaining_probabilities = sorted(probabilities, reverse=True)
    total_expected_encounters = 0
    
    while remaining_probabilities:
        sum_of_current_probabilities = sum(remaining_probabilities)
        if sum_of_current_probabilities == 0:
            break
        encounters_for_next_unique = 1 / sum_of_current_probabilities
        total_expected_encounters += encounters_for_next_unique
        remaining_probabilities.pop(0)
    
    return total_expected_encounters


# --- 4. CALCULATE AND DISPLAY THE PREDICTION ---

# Filter the DataFrame to get ONLY the shinies you haven't caught yet
remaining_shinies_df = pokedex_df[~pokedex_df['name'].isin(shinies_already_caught)]
remaining_pi_probabilities = remaining_shinies_df['p_i'].tolist()

print("\n" + "=" * 60)
print("REMAINING SHINIES ANALYSIS")
print("=" * 60)
print(f"Total Pokémon in Pokédex: {len(pokedex_df)}")
print(f"Unique Shinies Caught (from checkpoint): {len(shinies_already_caught)}")
print(f"Shinies Remaining to Collect: {len(remaining_pi_probabilities)}")

if not remaining_shinies_df.empty:
    print("\n--- Top 5 Hardest Remaining Shinies (based on your model) ---")
    print(remaining_shinies_df.nsmallest(5, 'p_i')[['name', 'base total', 'p_i']])

# Calculate the expected encounters needed for ONLY the remaining shinies
expected_encounters_remaining = calculate_expected_encounters(remaining_pi_probabilities)

print("\n" + "=" * 60)
print("TIME REMAINING ESTIMATE (FROM CURRENT POSITION)")
print("=" * 60)
print(f"Current Encounters (from checkpoint): {current_encounters:,}")
print(f"Expected ADDITIONAL Encounters Needed: {expected_encounters_remaining:,.0f}")
print(f"Your simulation is expected to finish at ~{current_encounters + expected_encounters_remaining:,.0f} total encounters.")

# Time estimate
EPS = 31736.2  # Your actual Encounters Per Second from the simulation
time_remaining_seconds = expected_encounters_remaining / EPS
time_remaining_hours = time_remaining_seconds / 3600
time_remaining_days = time_remaining_hours / 24

print("\n--- TIME ESTIMATE ---")
print(f"Encounters Per Second: {EPS:,.1f}")
print(f"Estimated Hours Remaining: {time_remaining_hours:.2f}")
if time_remaining_days > 1:
    print(f"Estimated Days Remaining: {time_remaining_days:.2f}")

print("=" * 60)
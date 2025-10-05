import requests
import pandas as pd
from tqdm import tqdm
import time
import re

# The base URL for the PokéAPI
BASE_URL = 'https://pokeapi.co/api/v2/'

def get_all_pokemon_list():
    """Gets the list of all Pokémon from the API."""
    print("Fetching the full list of Pokémon...")
    try:
        response = requests.get(f"{BASE_URL}pokemon?limit=2000") # High limit to get all forms
        response.raise_for_status()
        results = response.json()['results']
        print(f"Found {len(results)} Pokémon entries to process.")
        return results
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Pokémon list: {e}")
        return None

def get_pokemon_details(pokemon_url):
    """Fetches and processes detailed data for a single Pokémon."""
    try:
        response = requests.get(pokemon_url)
        response.raise_for_status()
        data = response.json()

        # --- Basic Info ---
        pokedex_number = data['id']
        name = data['name'].replace('-', ' ').title()
        height = data['height'] / 10  # Convert to metres
        weight = data['weight'] / 10  # Convert to kilograms

        # --- Types ---
        types = [t['type']['name'].capitalize() for t in data['types']]
        type1 = types[0] if types else None
        type2 = types[1] if len(types) > 1 else None

        # --- Abilities ---
        abilities = [a['ability']['name'].replace('-', ' ').title() for a in data['abilities']]

        # --- Stats ---
        stats = {stat['stat']['name']: stat['base_stat'] for stat in data['stats']}

        # --- Species Data (for Pokédex entry, evolution, etc.) ---
        species_response = requests.get(data['species']['url'])
        species_response.raise_for_status()
        species_data = species_response.json()

        # --- Genus/Category ---
        genus = ""
        for g in species_data['genera']:
            if g['language']['name'] == 'en':
                genus = g['genus']
                break
        
        # --- Base Happiness ---
        base_happiness = species_data.get('base_happiness', None)

        # --- Generation ---
        generation = species_data['generation']['name'].replace('generation-', '').upper()

        # --- Evolution ---
        evolves_from = species_data.get('evolves_from_species')
        evolves_from = evolves_from['name'].capitalize() if evolves_from else None

        # --- Find the latest English Pokédex entry ---
        pokedex_entry = "No recent English description found."
        # Prioritize games from newest to oldest
        priority_versions = ['scarlet', 'sword', 'sun', 'x', 'black', 'diamond', 'ruby', 'gold', 'red', 'blue']
        
        all_entries = [entry for entry in species_data['flavor_text_entries'] if entry['language']['name'] == 'en']

        for version in priority_versions:
            found = False
            for entry in all_entries:
                if entry['version']['name'] == version:
                    # Clean up the text: remove newlines, form feeds, etc.
                    cleaned_text = re.sub(r'[\n\f\r]', ' ', entry['flavor_text'])
                    pokedex_entry = cleaned_text
                    found = True
                    break
            if found:
                break

        pokemon_info = {
            'pokedex_number': pokedex_number,
            'name': name,
            'generation': generation,
            'genus': genus,
            'type1': type1,
            'type2': type2,
            'base_happiness': base_happiness,
            'height_m': height,
            'weight_kg': weight,
            'hp': stats.get('hp'),
            'attack': stats.get('attack'),
            'defense': stats.get('defense'),
            'special-attack': stats.get('special-attack'),
            'special-defense': stats.get('special-defense'),
            'speed': stats.get('speed'),
            'abilities': ", ".join(abilities),
            'evolves_from': evolves_from,
            'pokedex_entry': pokedex_entry
        }
        
        return pokemon_info

    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for {pokemon_url}: {e}")
        return None

def main():
    """Main function to run the script."""
    pokemon_list = get_all_pokemon_list()
    if not pokemon_list:
        return

    all_pokemon_data = []
    
    print("Fetching details for each Pokémon...")
    for pokemon in tqdm(pokemon_list, desc="Processing Pokémon"):
        details = get_pokemon_details(pokemon['url'])
        if details:
            all_pokemon_data.append(details)
        time.sleep(0.02) # Be respectful to the API

    if not all_pokemon_data:
        print("No data was fetched. Exiting.")
        return

    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(all_pokemon_data)
    
    # Save the DataFrame to a CSV file
    output_filename = 'pokedex_full_dataset.csv'
    df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    print(f"\nSuccessfully created the dataset!")
    print(f"Data for {len(df)} Pokémon saved to '{output_filename}'.")

if __name__ == "__main__":
    main()
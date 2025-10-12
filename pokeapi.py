import requests
import pandas as pd
import time
from typing import Dict, List, Any
import json

class PokemonDataScraper:
    def __init__(self):
        self.base_url = "https://pokeapi.co/api/v2"
        self.session = requests.Session()
        
    def rate_limit(self, delay=0.1):
        """Be nice to the API"""
        time.sleep(delay)
    
    def get_data(self, url: str) -> Dict:
        """Fetch data with error handling"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return {}
    
    def get_all_pokemon_list(self) -> List[Dict]:
        """Get list of all Pokemon"""
        url = f"{self.base_url}/pokemon?limit=100000"
        data = self.get_data(url)
        return data.get('results', [])
    
    def get_pokemon_games(self, pokemon_data: Dict) -> Dict[str, bool]:
        """Extract game availability from game_indices"""
        games_dict = {
            'in_red': False, 'in_blue': False, 'in_yellow': False,
            'in_gold': False, 'in_silver': False, 'in_crystal': False,
            'in_ruby': False, 'in_sapphire': False, 'in_emerald': False,
            'in_firered': False, 'in_leafgreen': False,
            'in_diamond': False, 'in_pearl': False, 'in_platinum': False,
            'in_heartgold': False, 'in_soulsilver': False,
            'in_black': False, 'in_white': False, 'in_black2': False, 'in_white2': False,
            'in_x': False, 'in_y': False,
            'in_omega_ruby': False, 'in_alpha_sapphire': False,
            'in_sun': False, 'in_moon': False, 'in_ultra_sun': False, 'in_ultra_moon': False,
            'in_lets_go_pikachu': False, 'in_lets_go_eevee': False,
            'in_sword': False, 'in_shield': False,
            'in_brilliant_diamond': False, 'in_shining_pearl': False,
            'in_legends_arceus': False,
            'in_scarlet': False, 'in_violet': False
        }
        
        # Map version IDs to game names (this is a simplified mapping)
        version_map = {
            1: 'red', 2: 'blue', 3: 'yellow',
            4: 'gold', 5: 'silver', 6: 'crystal',
            7: 'ruby', 8: 'sapphire', 9: 'emerald',
            10: 'firered', 11: 'leafgreen',
            12: 'diamond', 13: 'pearl', 14: 'platinum',
            15: 'heartgold', 16: 'soulsilver',
            17: 'black', 18: 'white', 21: 'black2', 22: 'white2',
            23: 'x', 24: 'y',
            25: 'omega_ruby', 26: 'alpha_sapphire',
            27: 'sun', 28: 'moon', 29: 'ultra_sun', 30: 'ultra_moon',
            31: 'lets_go_pikachu', 32: 'lets_go_eevee',
            33: 'sword', 34: 'shield',
            35: 'brilliant_diamond', 36: 'shining_pearl',
            37: 'legends_arceus',
            38: 'scarlet', 39: 'violet'
        }
        
        for game_index in pokemon_data.get('game_indices', []):
            version_id = game_index.get('version', {}).get('url', '').split('/')[-2]
            try:
                version_id = int(version_id)
                if version_id in version_map:
                    game_name = version_map[version_id]
                    games_dict[f'in_{game_name}'] = True
            except:
                continue
                
        return games_dict
    
    def get_complete_pokemon_data(self, pokemon_name: str) -> Dict:
        """Fetch all data for a single Pokemon"""
        print(f"Scraping {pokemon_name}...")
        
        # Get main Pokemon data
        pokemon_url = f"{self.base_url}/pokemon/{pokemon_name}"
        pokemon_data = self.get_data(pokemon_url)
        self.rate_limit()
        
        if not pokemon_data:
            return {}
        
        # Get species data
        species_url = pokemon_data.get('species', {}).get('url', '')
        species_data = self.get_data(species_url) if species_url else {}
        self.rate_limit()
        
        # Get evolution chain
        evolution_url = species_data.get('evolution_chain', {}).get('url', '')
        evolution_data = self.get_data(evolution_url) if evolution_url else {}
        self.rate_limit()
        
        # Build complete data dictionary
        data = {
            # Basic Info
            'id': pokemon_data.get('id'),
            'name': pokemon_data.get('name'),
            'height': pokemon_data.get('height'),  # decimeters
            'weight': pokemon_data.get('weight'),  # hectograms
            'base_experience': pokemon_data.get('base_experience'),
            'order': pokemon_data.get('order'),
            
            # Species Info
            'genus': next((g['genus'] for g in species_data.get('genera', []) if g['language']['name'] == 'en'), None),
            'generation': species_data.get('generation', {}).get('name', '').replace('generation-', '') if species_data.get('generation') else None,
            'is_legendary': species_data.get('is_legendary', False),
            'is_mythical': species_data.get('is_mythical', False),
            'is_baby': species_data.get('is_baby', False),
            'color': species_data.get('color').get('name') if species_data.get('color') else None,
            'shape': species_data.get('shape').get('name') if species_data.get('shape') else None,
            'habitat': species_data.get('habitat').get('name') if species_data.get('habitat') else None,
            'growth_rate': species_data.get('growth_rate').get('name') if species_data.get('growth_rate') else None,
            'capture_rate': species_data.get('capture_rate'),
            'base_happiness': species_data.get('base_happiness'),
            'gender_rate': species_data.get('gender_rate'),  # -1 = genderless, 0 = always male, 8 = always female
            'hatch_counter': species_data.get('hatch_counter'),
            'has_gender_differences': species_data.get('has_gender_differences', False),
            'forms_switchable': species_data.get('forms_switchable', False),
            
            # Types
            'type_1': pokemon_data.get('types', [{}])[0].get('type', {}).get('name') if len(pokemon_data.get('types', [])) > 0 else None,
            'type_2': pokemon_data.get('types', [{}])[1].get('type', {}).get('name') if len(pokemon_data.get('types', [])) > 1 else None,
            
            # Stats
            'stat_hp': next((s['base_stat'] for s in pokemon_data.get('stats', []) if s['stat']['name'] == 'hp'), None),
            'stat_attack': next((s['base_stat'] for s in pokemon_data.get('stats', []) if s['stat']['name'] == 'attack'), None),
            'stat_defense': next((s['base_stat'] for s in pokemon_data.get('stats', []) if s['stat']['name'] == 'defense'), None),
            'stat_special_attack': next((s['base_stat'] for s in pokemon_data.get('stats', []) if s['stat']['name'] == 'special-attack'), None),
            'stat_special_defense': next((s['base_stat'] for s in pokemon_data.get('stats', []) if s['stat']['name'] == 'special-defense'), None),
            'stat_speed': next((s['base_stat'] for s in pokemon_data.get('stats', []) if s['stat']['name'] == 'speed'), None),
            'stat_total': sum(s['base_stat'] for s in pokemon_data.get('stats', [])),
            
            # Abilities
            'ability_1': pokemon_data.get('abilities', [{}])[0].get('ability', {}).get('name') if len(pokemon_data.get('abilities', [])) > 0 else None,
            'ability_2': pokemon_data.get('abilities', [{}])[1].get('ability', {}).get('name') if len(pokemon_data.get('abilities', [])) > 1 else None,
            'ability_hidden': next((a['ability']['name'] for a in pokemon_data.get('abilities', []) if a.get('is_hidden')), None),
            
            # Egg Groups
            'egg_group_1': species_data.get('egg_groups', [{}])[0].get('name') if len(species_data.get('egg_groups', [])) > 0 else None,
            'egg_group_2': species_data.get('egg_groups', [{}])[1].get('name') if len(species_data.get('egg_groups', [])) > 1 else None,
            
            # Evolution Info
            'evolves_from': species_data.get('evolves_from_species').get('name') if species_data.get('evolves_from_species') else None,
            'evolution_chain_id': evolution_data.get('id'),
            
            # Move counts
            'total_moves': len(pokemon_data.get('moves', [])),
            
            # Sprite URLs
            'sprite_front_default': pokemon_data.get('sprites', {}).get('front_default'),
            'sprite_front_shiny': pokemon_data.get('sprites', {}).get('front_shiny'),
            'sprite_official_artwork': pokemon_data.get('sprites', {}).get('other', {}).get('official-artwork', {}).get('front_default'),
        }
        
        # Add game availability
        games_data = self.get_pokemon_games(pokemon_data)
        data.update(games_data)
        
        # Get English flavor text (Pokedex entry)
        flavor_texts = species_data.get('flavor_text_entries', [])
        english_flavor = next((f['flavor_text'].replace('\n', ' ').replace('\f', ' ') 
                              for f in flavor_texts if f['language']['name'] == 'en'), None)
        data['pokedex_entry'] = english_flavor
        
        return data
    
    def scrape_all_pokemon(self, limit: int = None) -> pd.DataFrame:
        """Scrape all Pokemon data"""
        pokemon_list = self.get_all_pokemon_list()
        
        if limit:
            pokemon_list = pokemon_list[:limit]
        
        all_data = []
        total = len(pokemon_list)
        
        for idx, pokemon in enumerate(pokemon_list, 1):
            print(f"Progress: {idx}/{total}")
            data = self.get_complete_pokemon_data(pokemon['name'])
            if data:
                all_data.append(data)
        
        df = pd.DataFrame(all_data)
        return df


# Usage
if __name__ == "__main__":
    scraper = PokemonDataScraper()
    
    # For testing, scrape first 10 Pokemon
    # Remove limit parameter to scrape ALL Pokemon (this will take hours)
    print("Starting Pokemon data scrape...")
    print("This will take a while. Go touch grass or something.")
    
    df = scraper.scrape_all_pokemon()  # Remove limit=10 for full scrape
    
    # Save to CSV
    output_file = 'pokemon_complete_database.csv'
    df.to_csv(output_file, index=False)
    print(f"\nData saved to {output_file}")
    print(f"Total Pokemon scraped: {len(df)}")
    print(f"\nColumns: {list(df.columns)}")
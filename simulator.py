# Required libraries: pip install pandas openpyxl
import random as rand
import pandas as pd
import json
import sys
import time
import os
import csv
import cProfile
import pstats
import argparse

class ShinySimulation:
    """
    A class to encapsulate the shiny Pokémon encounter simulation.
    It manages the simulation's state, data, and core logic in a self-contained object.
    """

    def __init__(self, excel_path='Pokemon Stats.xlsx', sheet_name='Pokedex', reports_dir='reports'):
        # --- Configuration & Tuning ---
        self.SHINY_RATE = 1 / 4096
        self.REPORTS_DIR = reports_dir
        self.CHECKPOINT_FILE = 'checkpoint.json'
        self.BUFFER_SIZE = 1000
        self.PROGRESS_UPDATE_INTERVAL = 100000
        self.CHECKPOINT_INTERVAL = 25_000_000

        # --- Data Loading ---
        self.pokedex = self._load_pokedex_data(excel_path, sheet_name)
        self.total_pokemon = len(self.pokedex)  # Cache this value
        self.pokemon_for_encountering, self.spawn_weights = self._prepare_encounter_lists()

        # --- State Variables ---
        self.total_encounter = 0
        self.total_shinies_caught = 0
        self.total_normals_caught = 0
        self.shiny_dex = set()
        self.normal_dex = set()
        self.shiny_box_counts = {}
        self.normal_box_counts = {}
        self.start_time = time.time()
        self.past_elapsed_seconds = 0
        self.last_checkpoint_time = "Never"
        self.shiny_log_buffer = []
        self._active_writer = None  # Track the active CSV writer

    def _load_pokedex_data(self, excel_path, sheet_name):
        """
        Loads Pokedex data from an Excel file and calculates spawn weights
        based on a power law distribution of base stat totals.
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
        except FileNotFoundError:
            print(f"FATAL ERROR: Could not find the Excel file at '{excel_path}'")
            return {}
        except ValueError as e:
            print(f"FATAL ERROR: Could not find sheet named '{sheet_name}'. Error: {e}")
            return {}

        processed_pokedex = {}
        
        # --- TUNABLE SPAWN PARAMETERS ---
        STABILITY_CONSTANT = 100    # Prevents division by zero, adds baseline
        RARITY_EXPONENT = 1.8       # Higher = more dramatic rarity curve (try 1.5-2.5)
        
        print(f"Loading Pokémon data with spawn parameters:")
        print(f"  - Stability Constant: {STABILITY_CONSTANT}")
        print(f"  - Rarity Exponent: {RARITY_EXPONENT}")

        for index, pokemon in df.iterrows():
            name = pokemon['name']
            base_total = pokemon['base total']
            is_legendary = pokemon.get('is_legendary', False)
            is_mythical = pokemon.get('is_mythical', False)

            # Pure stat-based spawn weight - no special cases
            spawn_weight = 1 / ((base_total + STABILITY_CONSTANT) ** RARITY_EXPONENT)

            processed_pokedex[name] = {
                'pokedex number': pokemon['pokedex number'],
                'Catch Rate': pokemon['Catch Rate'],
                'Spawn Weight': spawn_weight,
                'base_total': base_total,
                'is_legendary': is_legendary,
                'is_mythical': is_mythical
            }
            
        return processed_pokedex

    def _prepare_encounter_lists(self):
        """Prepares parallel lists of Pokémon names and their spawn weights for weighted random selection."""
        if not self.pokedex:
            return [], []
        pokemon_names = list(self.pokedex.keys())
        weights = [self.pokedex[name]['Spawn Weight'] for name in pokemon_names]
        return pokemon_names, weights

    def _attempt_catch(self, pokemon_name):
        """Simulates a catch attempt based on the Pokémon's catch rate."""
        catch_rate = self.pokedex[pokemon_name]['Catch Rate']
        return rand.random() <= (catch_rate / 255.0)

    def _handle_shiny_encounter(self, encountered_pokemon):
        """Handles all logic for a shiny encounter: catch attempt, logging, and state updates."""
        catch_successful = self._attempt_catch(encountered_pokemon)
        is_new_shiny = encountered_pokemon not in self.shiny_dex

        # Buffer the log entry
        self.shiny_log_buffer.append([
            self.total_encounter, 
            encountered_pokemon, 
            catch_successful, 
            is_new_shiny
        ])

        # Flush buffer if it's full
        if len(self.shiny_log_buffer) >= self.BUFFER_SIZE:
            self._flush_shiny_buffer()

        if catch_successful:
            self.total_shinies_caught += 1
            self.shiny_box_counts[encountered_pokemon] = self.shiny_box_counts.get(encountered_pokemon, 0) + 1
            
            if is_new_shiny:
                self.shiny_dex.add(encountered_pokemon)
                catch_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                remaining = self.total_pokemon - len(self.shiny_dex)
                print(f"\r\x1b[K{catch_timestamp} - Gotcha! Shiny ✨ {encountered_pokemon} ✨ has been caught! Only {remaining} left to go!")

    def _handle_normal_encounter(self, encountered_pokemon):
        """Handles all logic for a normal (non-shiny) encounter."""
        self.total_normals_caught += 1
        self.normal_dex.add(encountered_pokemon)
        self.normal_box_counts[encountered_pokemon] = self.normal_box_counts.get(encountered_pokemon, 0) + 1
        
    def _flush_shiny_buffer(self):
        """Writes all buffered shiny encounters to the CSV file."""
        if self._active_writer and self.shiny_log_buffer:
            self._active_writer.writerows(self.shiny_log_buffer)
            self.shiny_log_buffer.clear()

    def run_encounter(self):
        """Executes a single encounter: spawn a Pokémon, check if shiny, handle accordingly."""
        self.total_encounter += 1
        encountered_pokemon = rand.choices(self.pokemon_for_encountering, self.spawn_weights, k=1)[0]
        
        if rand.random() < self.SHINY_RATE:
            self._handle_shiny_encounter(encountered_pokemon)
        else:
            self._handle_normal_encounter(encountered_pokemon)

    def _display_progress(self):
        """Displays real-time progress information in the terminal."""
        current_session_seconds = time.time() - self.start_time
        total_elapsed_seconds = self.past_elapsed_seconds + current_session_seconds
        
        if total_elapsed_seconds < 1:
            return

        enc_per_sec = self.total_encounter / total_elapsed_seconds
        shinies_per_sec = self.total_shinies_caught / total_elapsed_seconds
        percentage_shiny = (len(self.shiny_dex) / self.total_pokemon) * 100
        
        duration_str = f"{(total_elapsed_seconds / 3600):.2f} Hours" if total_elapsed_seconds > 3600 else f"{(total_elapsed_seconds / 60):.2f} Mins"
        
        progress_line = (
            f"\r_Enc: {self.total_encounter:,} ({enc_per_sec:.1f} EPS) | "
            f"Shinies: {self.total_shinies_caught:,} ({shinies_per_sec:.2f} SPS) | "
            f"Unique: {len(self.shiny_dex)}/{self.total_pokemon} ({percentage_shiny:.2f}%) | "
            f"Time: {duration_str}"
        )
        sys.stdout.write(progress_line)
        sys.stdout.flush()

    def save_checkpoint(self):
        """Saves the current state of the simulation to a JSON checkpoint file."""
        # Flush any remaining buffered shinies
        self._flush_shiny_buffer()

        current_session_seconds = time.time() - self.start_time
        total_elapsed_seconds = self.past_elapsed_seconds + current_session_seconds

        self.last_checkpoint_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        state = {
            'total_encounter': self.total_encounter,
            'total_shinies_caught': self.total_shinies_caught,
            'total_normals_caught': self.total_normals_caught,
            'shiny_dex': list(self.shiny_dex),
            'normal_dex': list(self.normal_dex),
            'shiny_box_counts': self.shiny_box_counts,
            'normal_box_counts': self.normal_box_counts,
            'last_checkpoint_time': self.last_checkpoint_time,
            'total_elapsed_seconds': total_elapsed_seconds
        }
        
        with open(self.CHECKPOINT_FILE, 'w') as f:
            json.dump(state, f, indent=4)

    def load_checkpoint(self):
        """Loads the simulation state from a checkpoint file if it exists."""
        try:
            with open(self.CHECKPOINT_FILE, 'r') as f:
                state = json.load(f)
                self.total_encounter = state.get('total_encounter', 0)
                self.total_shinies_caught = state.get('total_shinies_caught', 0)
                self.total_normals_caught = state.get('total_normals_caught', 0)
                self.shiny_dex = set(state.get('shiny_dex', []))
                self.normal_dex = set(state.get('normal_dex', []))
                self.shiny_box_counts = state.get('shiny_box_counts', {})
                self.normal_box_counts = state.get('normal_box_counts', {})
                self.last_checkpoint_time = state.get('last_checkpoint_time', "Loaded")
                self.past_elapsed_seconds = state.get('total_elapsed_seconds', 0)
                self.start_time = time.time()
                
                print("--- Checkpoint successfully loaded. Resuming simulation. ---")
                print(f"    Total Encounters: {self.total_encounter:,}")
                print(f"    Unique Shinies: {len(self.shiny_dex)}/{self.total_pokemon}")
                print(f"    Elapsed Time: {(self.past_elapsed_seconds / 3600):.2f} hours")
                
        except FileNotFoundError:
            print("--- No checkpoint found. Starting a new simulation. ---")
        except json.JSONDecodeError:
            print("--- WARNING: Checkpoint file is corrupted. Starting a new simulation. ---")

    def output_spawn_distribution_analysis(self):
        """Generates a detailed analysis of spawn weights vs actual encounters."""
        spawn_data = []
        
        for name, data in self.pokedex.items():
            actual_encounters = self.normal_box_counts.get(name, 0)
            total_weight = sum(self.spawn_weights)
            expected_proportion = data['Spawn Weight'] / total_weight
            expected_encounters = expected_proportion * self.total_normals_caught
            
            spawn_data.append({
                'Pokemon': name,
                'Pokedex_Number': data['pokedex number'],
                'Base_Total': data['base_total'],
                'Is_Legendary': data.get('is_legendary', False),
                'Is_Mythical': data.get('is_mythical', False),
                'Spawn_Weight': data['Spawn Weight'],
                'Expected_Encounters': int(expected_encounters),
                'Actual_Encounters': actual_encounters,
                'Difference': actual_encounters - int(expected_encounters)
            })
        
        df = pd.DataFrame(spawn_data).sort_values('Base_Total')
        
        timestamp = time.strftime("%Y-%m-%d")
        filepath = os.path.join(self.REPORTS_DIR, f"spawn_distribution_{timestamp}.csv")
        df.to_csv(filepath, index=False)
        
        print(f"Spawn distribution analysis saved to {filepath}")

    def output_final_reports(self):
        """Generates and saves all final summary CSV files."""
        print("\n" + "="*50)
        print("GENERATING FINAL REPORTS")
        print("="*50)
        print(f"Total Encounters: {self.total_encounter:,}")
        print(f"Total Shinies Caught: {self.total_shinies_caught:,}")
        print(f"Unique Shinies Caught: {len(self.shiny_box_counts)}")
        print(f"Unique Normal Pokémon Encountered: {len(self.normal_box_counts)}")

        os.makedirs(self.REPORTS_DIR, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d")
        
        # Normal encounters report
        normal_df = pd.DataFrame(
            list(self.normal_box_counts.items()), 
            columns=['Pokemon', 'Encounters']
        ).sort_values('Encounters', ascending=False)
        normal_filepath = os.path.join(self.REPORTS_DIR, f"normal_encounters_{timestamp}.csv")
        normal_df.to_csv(normal_filepath, index=False)
        print(f"✓ Normal encounters saved to {normal_filepath}")

        # Shiny encounters report
        shiny_df = pd.DataFrame(
            list(self.shiny_box_counts.items()), 
            columns=['Pokemon', 'Shiny_Encounters']
        ).sort_values('Shiny_Encounters', ascending=False)
        shiny_filepath = os.path.join(self.REPORTS_DIR, f"shiny_encounters_{timestamp}.csv")
        shiny_df.to_csv(shiny_filepath, index=False)
        print(f"✓ Shiny encounters saved to {shiny_filepath}")
        
        # Spawn distribution analysis
        self.output_spawn_distribution_analysis()
        
        print("="*50)

    def run(self):
        """The main entry point to start and manage the simulation loop."""
        print("\n" + "="*50)
        print("SHINY POKÉMON ENCOUNTER SIMULATOR")
        print("="*50)
        print("Press Ctrl+C at any time to stop and save progress.\n")
        
        self.load_checkpoint()

        if not self.pokedex:
            print("FATAL ERROR: Pokedex is empty. Cannot start simulation.")
            return

        analysis_filepath = os.path.join(self.REPORTS_DIR, f"shiny_analysis_log.csv")
        
        try:
            os.makedirs(self.REPORTS_DIR, exist_ok=True)
            
            # Open the CSV file and keep it open for the entire simulation
            with open(analysis_filepath, 'a', newline='', encoding='utf-8') as f:
                self._active_writer = csv.writer(f)
                
                # Write header if file is empty
                if f.tell() == 0:
                    self._active_writer.writerow(['Encounter_Number', 'Pokemon', 'Catch_Successful', 'Is_New_Shiny'])
                
                # Check if already completed
                if len(self.shiny_dex) >= self.total_pokemon:
                    print("✓ Simulation already completed based on checkpoint file.")
                    self.output_final_reports()
                    return

                print(f"Starting main encounter loop...")
                print(f"Target: Catch all {self.total_pokemon} unique shiny Pokémon\n")

                # Main simulation loop
                while len(self.shiny_dex) < self.total_pokemon:
                    self.run_encounter()
                    
                    if self.total_encounter % self.PROGRESS_UPDATE_INTERVAL == 0:
                        self._display_progress()
                    
                    if self.total_encounter % self.CHECKPOINT_INTERVAL == 0:
                        self.save_checkpoint()
                
                print("\n\n" + "="*50)
                print("🎉 SIMULATION COMPLETE! 🎉")
                print("="*50)
        
        except KeyboardInterrupt:
            print("\n\n⚠ Simulation interrupted by user.")
        
        finally:
            # Flush any remaining buffered shinies
            print("\nFlushing remaining data and saving final checkpoint...")
            self._flush_shiny_buffer()
            self.save_checkpoint()
            self.output_final_reports()
            
            # Calculate and display final runtime
            current_session_seconds = time.time() - self.start_time
            total_elapsed_seconds = self.past_elapsed_seconds + current_session_seconds
            total_hours = total_elapsed_seconds / 3600
            
            print("\n" + "="*50)
            print("FINAL STATISTICS")
            print("="*50)
            print(f"Total Runtime: {total_hours:.2f} hours ({(total_elapsed_seconds / 60):.2f} minutes)")
            print(f"Average EPS: {(self.total_encounter / total_elapsed_seconds):.1f}")
            print(f"Average SPS: {(self.total_shinies_caught / total_elapsed_seconds):.2f}")
            print("="*50 + "\n")


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description='Shiny Pokémon Encounter Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python shiny.py                    # Run simulation normally
  python shiny.py --profile          # Run with performance profiling enabled
  python shiny.py --excel "data.xlsx" --sheet "Pokemon"  # Use custom data file
        """
    )
    
    parser.add_argument(
        '--profile', 
        action='store_true', 
        help='Enable cProfile performance profiling (adds slight overhead)'
    )
    parser.add_argument(
        '--excel',
        default='Pokemon Stats.xlsx',
        help='Path to Excel file containing Pokémon data (default: Pokemon Stats.xlsx)'
    )
    parser.add_argument(
        '--sheet',
        default='Pokedex',
        help='Sheet name in Excel file (default: Pokedex)'
    )
    
    args = parser.parse_args()
    
    # Initialize profiler if requested
    if args.profile:
        print("⚠ Profiling enabled - this will add slight performance overhead\n")
        profiler = cProfile.Profile()
        profiler.enable()
    
    # Run the simulation
    simulation = ShinySimulation(
        excel_path=args.excel, 
        sheet_name=args.sheet
    )
    simulation.run()
    
    # Output profiling results if enabled
    if args.profile:
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats('cumulative')
        print("\n" + "="*50)
        print("PROFILING RESULTS: TOP 20 TIME CONSUMERS")
        print("="*50)
        stats.print_stats(20)


if __name__ == "__main__":
    main()
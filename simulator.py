# Required libraries: pip install pandas openpyxl
import random as rand
import pandas as pd
import json
import sys
import time
import os
import csv
from datetime import datetime

class ShinySimulation:
    """
    A class to encapsulate the shiny Pokémon encounter simulation.
    Supports custom shiny rates and guaranteed catch modes with live ETA prediction.
    """
    
    # Class-level constants
    RUN_REGISTRY = 'reports/run_registry.json'
    MASTER_RESULTS = 'simulation_results.csv'
    TIMELINE_LOG_INTERVAL = 5000  # Log timeline every 5k encounters

    def __init__(self, excel_path='Pokemon Stats.xlsx', sheet_name='Pokedex', reports_dir='reports'):
        
        self.base_reports_dir = reports_dir
        self.excel_path = excel_path
        self.sheet_name = sheet_name
        
        # --- Interactive Setup ---
        self._setup_simulation()
        
        # --- File Paths ---
        self.REPORTS_DIR = os.path.join(reports_dir, self.run_name)
        self.CHECKPOINT_FILE = os.path.join(self.REPORTS_DIR, 'checkpoint.json')
        
        # --- Configuration ---
        self.BUFFER_SIZE = 1000
        self.PROGRESS_UPDATE_INTERVAL = 100000
        self.CHECKPOINT_INTERVAL = 25_000_000
        self.STABILITY_CONSTANT = 100
        self.RARITY_EXPONENT = 1.8

        # --- Data Loading ---
        self.pokedex = self._load_pokedex_data(excel_path, sheet_name)
        self.total_pokemon = len(self.pokedex)
        self.pokemon_for_encountering, self.spawn_weights = self._prepare_encounter_lists()
        
        # --- Calculate probability table for predictions ---
        self.pokemon_probabilities = self._calculate_pokemon_probabilities()

        # --- State Variables ---
        self.total_encounter = 0
        self.total_shinies_encountered = 0
        self.total_shinies_caught = 0
        self.total_shinies_missed = 0
        self.total_normals_caught = 0
        self.shiny_dex = set()
        self.normal_dex = set()
        self.shiny_box_counts = {}
        self.normal_box_counts = {}
        self.start_time = time.time()
        self.simulation_start_time = time.time()
        self.past_elapsed_seconds = 0
        self.last_checkpoint_time = "Never"
        
        # Prediction tracking
        self.initial_prediction = None
        self.last_eta_update = 0
        self.current_eta_encounters = 0
        self.current_eta_hours = 0
        
        # Buffers
        self.shiny_log_buffer = []
        self.timeline_buffer = []
        
        # File handles
        self._active_shiny_writer = None
        self._active_timeline_writer = None
        self._shiny_file_handle = None
        self._timeline_file_handle = None

    def _calculate_pokemon_probabilities(self):
        """Calculate p_i for each Pokémon for prediction purposes."""
        probabilities = {}
        total_weight = sum(self.spawn_weights)
        
        for name, data in self.pokedex.items():
            spawn_prob = data['Spawn Weight'] / total_weight
            catch_prob = data['Catch Rate'] / 255.0 if not self.guaranteed_catch else 1.0
            p_i = spawn_prob * catch_prob * self.SHINY_RATE
            probabilities[name] = p_i
        
        return probabilities

    def _calculate_expected_encounters_remaining(self, remaining_pokemon=None):
        """
        Calculates expected encounters using Weighted Coupon Collector formula.
        If remaining_pokemon is None, calculates for all Pokémon.
        """
        if remaining_pokemon is None:
            probabilities = list(self.pokemon_probabilities.values())
        else:
            probabilities = [self.pokemon_probabilities[name] for name in remaining_pokemon 
                           if name in self.pokemon_probabilities]
        
        if not probabilities:
            return 0
        
        # Sort descending for efficiency
        probabilities = sorted(probabilities, reverse=True)
        total_expected = 0
        
        while probabilities:
            sum_prob = sum(probabilities)
            if sum_prob == 0:
                break
            total_expected += 1 / sum_prob
            probabilities.pop(0)
        
        return total_expected

    def _display_startup_prediction(self):
        """Display expected completion stats at startup."""
        remaining_pokemon = [name for name in self.pokedex.keys() if name not in self.shiny_dex]
        expected_encounters = self._calculate_expected_encounters_remaining(remaining_pokemon)
        
        # Estimate based on typical EPS (assume 26,000 if starting fresh)
        estimated_eps = 26000
        estimated_hours = expected_encounters / estimated_eps / 3600
        estimated_days = estimated_hours / 24
        
        self.initial_prediction = {
            'expected_total_encounters': self.total_encounter + expected_encounters,
            'expected_additional_encounters': expected_encounters,
            'estimated_hours': estimated_hours,
            'estimated_days': estimated_days
        }
        
        print("\n" + "="*60)
        print("THEORETICAL PREDICTION")
        print("="*60)
        print(f"Shiny Rate: {self.shiny_modifier} ({self.SHINY_RATE:.10f})")
        print(f"Catch Mode: {'Guaranteed' if self.guaranteed_catch else 'Normal'}")
        print(f"Pokémon Remaining: {len(remaining_pokemon)}/{self.total_pokemon}")
        
        if self.total_encounter > 0:
            print(f"\nCurrent Progress: {self.total_encounter:,} encounters")
            print(f"Expected Additional: {expected_encounters:,.0f} encounters")
            print(f"Expected Total at Completion: {self.initial_prediction['expected_total_encounters']:,.0f}")
        else:
            print(f"\nExpected Total Encounters: {expected_encounters:,.0f}")
        
        print(f"\nEstimated Runtime:")
        if estimated_days > 1:
            print(f"  {estimated_hours:.1f} hours ({estimated_days:.2f} days)")
        else:
            print(f"  {estimated_hours:.1f} hours")
        
        print(f"\nNote: This is theoretical. Actual results will vary due to RNG.")
        print("="*60 + "\n")

    def _update_eta(self):
        """Update ETA calculation based on current progress."""
        # Only update ETA every 1M encounters to reduce overhead
        if self.total_encounter - self.last_eta_update < 1_000_000:
            return
        
        self.last_eta_update = self.total_encounter
        
        remaining_pokemon = [name for name in self.pokedex.keys() if name not in self.shiny_dex]
        if not remaining_pokemon:
            self.current_eta_encounters = 0
            self.current_eta_hours = 0
            return
        
        expected_remaining = self._calculate_expected_encounters_remaining(remaining_pokemon)
        
        # Use actual EPS from current session
        elapsed = time.time() - self.simulation_start_time
        if elapsed > 0:
            actual_eps = self.total_encounter / elapsed
            self.current_eta_hours = expected_remaining / actual_eps / 3600
            self.current_eta_encounters = expected_remaining

    # ... (All the registry methods stay the same) ...
    def _load_run_registry(self):
        """Loads the registry of all simulation runs."""
        if os.path.exists(self.RUN_REGISTRY):
            try:
                with open(self.RUN_REGISTRY, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠ Warning: run_registry.json is corrupted. Starting fresh.")
                return {'runs': {}, 'last_active': None}
        return {'runs': {}, 'last_active': None}

    def _save_run_registry(self, registry):
        """Saves the run registry."""
        with open(self.RUN_REGISTRY, 'w') as f:
            json.dump(registry, f, indent=4)

    def _update_run_registry(self):
        """Updates the registry with current run info."""
        registry = self._load_run_registry()
        
        registry['runs'][self.run_name] = {
            'shiny_modifier': self.shiny_modifier,
            'guaranteed_catch': self.guaranteed_catch,
            'last_updated': datetime.now().isoformat(),
            'checkpoint_path': self.CHECKPOINT_FILE,
            'reports_dir': self.REPORTS_DIR
        }
        registry['last_active'] = self.run_name
        
        self._save_run_registry(registry)

    def _list_available_runs(self):
        """Lists all runs with checkpoints."""
        registry = self._load_run_registry()
        available_runs = []
        
        for run_name, info in registry['runs'].items():
            checkpoint_path = info.get('checkpoint_path')
            if checkpoint_path and os.path.exists(checkpoint_path):
                available_runs.append((run_name, info))
        
        return available_runs, registry.get('last_active')

    def _setup_simulation(self):
        """Interactive setup for new or resumed simulation."""
        print("\n" + "="*60)
        print("SHINY POKÉMON ENCOUNTER SIMULATOR")
        print("="*60)
        
        # Check for existing runs
        available_runs, last_active = self._list_available_runs()
        
        if available_runs:
            print(f"\n📁 Found {len(available_runs)} existing run(s) with checkpoints:")
            for i, (run_name, info) in enumerate(available_runs, 1):
                marker = " ⭐ (last active)" if run_name == last_active else ""
                print(f"  {i}. {run_name}{marker}")
                print(f"     - Shiny Rate: {info.get('shiny_modifier', 'unknown')}")
                print(f"     - Catch Mode: {'Guaranteed' if info.get('guaranteed_catch') else 'Normal'}")
                print(f"     - Last Updated: {info.get('last_updated', 'unknown')}")
            
            print(f"  {len(available_runs) + 1}. Start a new simulation")
            
            choice = input(f"\nSelect option (1-{len(available_runs) + 1}): ").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(available_runs):
                    self.run_name, info = available_runs[choice_num - 1]
                    self.shiny_modifier = info.get('shiny_modifier')
                    self.guaranteed_catch = info.get('guaranteed_catch')
                    self.SHINY_RATE = self._get_shiny_rate_from_modifier(self.shiny_modifier)
                    
                    print(f"\n✓ Resuming run: '{self.run_name}'")
                    print(f"  Shiny Rate: {self.shiny_modifier}")
                    print(f"  Catch Mode: {'Guaranteed' if self.guaranteed_catch else 'Normal'}")
                    return
            except ValueError:
                pass
        
        # New simulation setup
        print("\n🆕 Starting new simulation")
        
        # Get run name
        while True:
            self.run_name = input("\nEnter a name for this run (e.g., 'baseline', 'test1'): ").strip()
            if not self.run_name:
                continue
            if not self.run_name.replace('_', '').replace('-', '').isalnum():
                print("❌ Invalid name. Use only letters, numbers, hyphens, and underscores.")
                continue
            
            registry = self._load_run_registry()
            if self.run_name in registry['runs']:
                print(f"⚠ Run name '{self.run_name}' already exists.")
                overwrite = input("Overwrite existing run? (y/n): ").strip().lower()
                if overwrite != 'y':
                    continue
            break
        
        # Get shiny rate
        print("\n--- Shiny Rate Options ---")
        print("1. Standard (1/4096)")
        print("2. Shiny Charm (1/1365)")
        print("3. Masuda Method (1/683)")
        print("4. Charm + Masuda (1/512)")
        
        rate_choice = input("Select option (1-4): ").strip()
        rate_map = {
            '1': ('standard', 1/4096),
            '2': ('charm', 1/1365.3),
            '3': ('masuda', 1/682.7),
            '4': ('both', 1/512.0)
        }
        self.shiny_modifier, self.SHINY_RATE = rate_map.get(rate_choice, ('standard', 1/4096))
        
        # Get catch mode
        print("\n--- Catch Mode Options ---")
        print("1. Normal (catch rate varies by Pokémon)")
        print("2. Guaranteed (100% catch rate)")
        
        catch_choice = input("Select option (1-2): ").strip()
        self.guaranteed_catch = (catch_choice == '2')
        
        print(f"\n✓ Simulation configured:")
        print(f"  Run Name: {self.run_name}")
        print(f"  Shiny Rate: {self.shiny_modifier} ({self.SHINY_RATE:.10f})")
        print(f"  Catch Mode: {'Guaranteed' if self.guaranteed_catch else 'Normal'}")

    def _get_shiny_rate_from_modifier(self, modifier):
        """Converts modifier string to shiny rate."""
        rate_map = {
            'standard': 1/4096,
            'charm': 1/1365.3,
            'masuda': 1/682.7,
            'both': 1/512.0
        }
        return rate_map.get(modifier, 1/4096)

    def _load_pokedex_data(self, excel_path, sheet_name):
        """Loads Pokedex data and calculates spawn weights."""
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
        except FileNotFoundError:
            print(f"FATAL ERROR: Could not find '{excel_path}'")
            return {}
        except ValueError as e:
            print(f"FATAL ERROR: Could not find sheet '{sheet_name}': {e}")
            return {}

        processed_pokedex = {}
        
        print(f"\nLoading Pokémon data...")
        print(f"  Stability Constant: {self.STABILITY_CONSTANT}")
        print(f"  Rarity Exponent: {self.RARITY_EXPONENT}")

        for index, pokemon in df.iterrows():
            name = pokemon['name']
            base_total = pokemon['base total']
            is_legendary = pokemon.get('is_legendary', False)
            is_mythical = pokemon.get('is_mythical', False)

            spawn_weight = 1 / ((base_total + self.STABILITY_CONSTANT) ** self.RARITY_EXPONENT)

            processed_pokedex[name] = {
                'pokedex number': pokemon['pokedex number'],
                'Catch Rate': pokemon['Catch Rate'],
                'Spawn Weight': spawn_weight,
                'base_total': base_total,
                'is_legendary': is_legendary,
                'is_mythical': is_mythical
            }
        
        print(f"✓ Loaded {len(processed_pokedex)} Pokémon")
        return processed_pokedex

    def _prepare_encounter_lists(self):
        """Prepares parallel lists for weighted random selection."""
        if not self.pokedex:
            return [], []
        pokemon_names = list(self.pokedex.keys())
        weights = [self.pokedex[name]['Spawn Weight'] for name in pokemon_names]
        return pokemon_names, weights

    def _attempt_catch(self, pokemon_name):
        """Simulates a catch attempt based on catch rate."""
        if self.guaranteed_catch:
            return True
        
        catch_rate = self.pokedex[pokemon_name]['Catch Rate']
        return rand.random() <= (catch_rate / 255.0)

    def _handle_shiny_encounter(self, encountered_pokemon):
        """Handles all logic for a shiny encounter."""
        self.total_shinies_encountered += 1
        catch_successful = self._attempt_catch(encountered_pokemon)
        is_new_shiny = encountered_pokemon not in self.shiny_dex

        # Buffer the shiny log entry
        self.shiny_log_buffer.append([
            self.total_encounter, 
            encountered_pokemon, 
            catch_successful, 
            is_new_shiny
        ])

        # Flush buffer if full
        if len(self.shiny_log_buffer) >= self.BUFFER_SIZE:
            self._flush_shiny_buffer()

        if catch_successful:
            self.total_shinies_caught += 1
            self.shiny_box_counts[encountered_pokemon] = self.shiny_box_counts.get(encountered_pokemon, 0) + 1
            
            if is_new_shiny:
                self.shiny_dex.add(encountered_pokemon)
                # Update ETA when catching a new unique
                self._update_eta()
                
                catch_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                remaining = self.total_pokemon - len(self.shiny_dex)
                print(f"\r\x1b[K{catch_timestamp} - Gotcha! Shiny ✨ {encountered_pokemon} ✨ has been caught! Only {remaining} left to go!")
        else:
            self.total_shinies_missed += 1

    def _handle_normal_encounter(self, encountered_pokemon):
        """Handles all logic for a normal encounter."""
        self.total_normals_caught += 1
        self.normal_dex.add(encountered_pokemon)
        self.normal_box_counts[encountered_pokemon] = self.normal_box_counts.get(encountered_pokemon, 0) + 1

    def _log_timeline_milestone(self):
        """Logs a timeline milestone for time-series analysis."""
        elapsed = time.time() - self.simulation_start_time
        current_eps = self.total_encounter / elapsed if elapsed > 0 else 0
        current_sps = self.total_shinies_caught / elapsed if elapsed > 0 else 0
        
        self.timeline_buffer.append([
            self.total_encounter,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            self.total_shinies_encountered,
            self.total_shinies_caught,
            self.total_shinies_missed,
            len(self.shiny_dex),
            len(self.normal_dex),
            round(current_eps, 2),
            round(current_sps, 4),
            round(elapsed, 2)
        ])
        
        # Flush timeline buffer periodically
        if len(self.timeline_buffer) >= self.BUFFER_SIZE:
            self._flush_timeline_buffer()
        
    def _flush_shiny_buffer(self):
        """Writes all buffered shiny encounters to CSV."""
        if self._active_shiny_writer and self.shiny_log_buffer:
            try:
                self._active_shiny_writer.writerows(self.shiny_log_buffer)
                self.shiny_log_buffer.clear()
            except (ValueError, AttributeError):
                pass

    def _flush_timeline_buffer(self):
        """Writes all buffered timeline entries to CSV."""
        if self._active_timeline_writer and self.timeline_buffer:
            try:
                self._active_timeline_writer.writerows(self.timeline_buffer)
                self.timeline_buffer.clear()
            except (ValueError, AttributeError):
                pass

    def run_encounter(self):
        """Executes a single encounter."""
        self.total_encounter += 1
        encountered_pokemon = rand.choices(self.pokemon_for_encountering, self.spawn_weights, k=1)[0]
        
        # Log timeline milestone
        if self.total_encounter % self.TIMELINE_LOG_INTERVAL == 0:
            self._log_timeline_milestone()
        
        if rand.random() < self.SHINY_RATE:
            self._handle_shiny_encounter(encountered_pokemon)
        else:
            self._handle_normal_encounter(encountered_pokemon)

    def _display_progress(self):
        """Displays real-time progress in terminal with ETA."""
        current_session_seconds = time.time() - self.start_time
        total_elapsed_seconds = self.past_elapsed_seconds + current_session_seconds
        
        if total_elapsed_seconds < 1:
            return

        enc_per_sec = self.total_encounter / total_elapsed_seconds
        shinies_per_sec = self.total_shinies_caught / total_elapsed_seconds
        percentage_shiny = (len(self.shiny_dex) / self.total_pokemon) * 100
        
        duration_str = f"{(total_elapsed_seconds / 3600):.2f} Hours" if total_elapsed_seconds > 3600 else f"{(total_elapsed_seconds / 60):.2f} Mins"
        
        # Build ETA string
        eta_str = ""
        if self.current_eta_encounters > 0:
            eta_enc_str = f"{self.current_eta_encounters:,.0f}" if self.current_eta_encounters > 1000000 else f"{self.current_eta_encounters/1000:.0f}K"
            if self.current_eta_hours > 24:
                eta_str = f" | ETA: {eta_enc_str} enc (~{self.current_eta_hours/24:.1f}d)"
            elif self.current_eta_hours > 1:
                eta_str = f" | ETA: {eta_enc_str} enc (~{self.current_eta_hours:.1f}h)"
            else:
                eta_str = f" | ETA: {eta_enc_str} enc (~{self.current_eta_hours*60:.0f}m)"
        
        progress_line = (
            f"\r_Enc: {self.total_encounter:,} ({enc_per_sec:.1f} EPS) | "
            f"Shinies: {self.total_shinies_caught:,} ({shinies_per_sec:.2f} SPS) | "
            f"Unique: {len(self.shiny_dex)}/{self.total_pokemon} ({percentage_shiny:.2f}%){eta_str} | "
            f"Time: {duration_str}"
        )
        sys.stdout.write(progress_line)
        sys.stdout.flush()

    def save_checkpoint(self):
        """Saves the current simulation state to JSON."""
        self._flush_shiny_buffer()
        self._flush_timeline_buffer()

        current_session_seconds = time.time() - self.start_time
        total_elapsed_seconds = self.past_elapsed_seconds + current_session_seconds

        self.last_checkpoint_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        os.makedirs(self.REPORTS_DIR, exist_ok=True)
        
        state = {
            'run_name': self.run_name,
            'shiny_modifier': self.shiny_modifier,
            'guaranteed_catch': self.guaranteed_catch,
            'shiny_rate': self.SHINY_RATE,
            'total_encounter': self.total_encounter,
            'total_shinies_encountered': self.total_shinies_encountered,
            'total_shinies_caught': self.total_shinies_caught,
            'total_shinies_missed': self.total_shinies_missed,
            'total_normals_caught': self.total_normals_caught,
            'shiny_dex': list(self.shiny_dex),
            'normal_dex': list(self.normal_dex),
            'shiny_box_counts': self.shiny_box_counts,
            'normal_box_counts': self.normal_box_counts,
            'last_checkpoint_time': self.last_checkpoint_time,
            'total_elapsed_seconds': total_elapsed_seconds,
            'initial_prediction': self.initial_prediction
        }
        
        with open(self.CHECKPOINT_FILE, 'w') as f:
            json.dump(state, f, indent=4)
        
        self._update_run_registry()

    def load_checkpoint(self):
        """Loads simulation state from checkpoint if it exists."""
        try:
            with open(self.CHECKPOINT_FILE, 'r') as f:
                state = json.load(f)
                
                self.total_encounter = state.get('total_encounter', 0)
                self.total_shinies_encountered = state.get('total_shinies_encountered', 0)
                self.total_shinies_caught = state.get('total_shinies_caught', 0)
                self.total_shinies_missed = state.get('total_shinies_missed', 0)
                self.total_normals_caught = state.get('total_normals_caught', 0)
                self.shiny_dex = set(state.get('shiny_dex', []))
                self.normal_dex = set(state.get('normal_dex', []))
                self.shiny_box_counts = state.get('shiny_box_counts', {})
                self.normal_box_counts = state.get('normal_box_counts', {})
                self.last_checkpoint_time = state.get('last_checkpoint_time', "Loaded")
                self.past_elapsed_seconds = state.get('total_elapsed_seconds', 0)
                self.initial_prediction = state.get('initial_prediction')
                self.start_time = time.time()
                
                print(f"\n    Total Encounters: {self.total_encounter:,}")
                print(f"    Unique Shinies: {len(self.shiny_dex)}/{self.total_pokemon}")
                print(f"    Elapsed Time: {(self.past_elapsed_seconds / 3600):.2f} hours\n")
                
        except FileNotFoundError:
            print(f"\n    Starting fresh simulation...\n")

    def _calculate_encounter_summary_stats(self):
        """Calculate comprehensive per-Pokemon statistics from logs."""
        log_path = os.path.join(self.REPORTS_DIR, 'shiny_analysis_log.csv')
        
        pokemon_stats = {}
        
        if os.path.exists(log_path):
            try:
                df = pd.read_csv(log_path)
                for _, row in df.iterrows():
                    pokemon = row['Pokemon']
                    encounter_num = row['Encounter_Number']
                    caught = row['Catch_Successful']
                    
                    if pokemon not in pokemon_stats:
                        pokemon_stats[pokemon] = {
                            'first_encounter': encounter_num,
                            'last_encounter': encounter_num,
                            'first_catch': None,
                            'last_catch': None,
                            'total_encountered': 0,
                            'total_caught': 0,
                            'total_missed': 0
                        }
                    
                    stats = pokemon_stats[pokemon]
                    stats['last_encounter'] = encounter_num
                    stats['total_encountered'] += 1
                    
                    if caught:
                        stats['total_caught'] += 1
                        stats['last_catch'] = encounter_num
                        if stats['first_catch'] is None:
                            stats['first_catch'] = encounter_num
                    else:
                        stats['total_missed'] += 1
                        
            except Exception as e:
                print(f"Warning: Could not read shiny log for detailed stats: {e}")
        
        return pokemon_stats

    def _save_to_master_results(self, final_stats):
        """Appends or updates the master simulation results CSV."""
        if os.path.exists(self.MASTER_RESULTS):
            try:
                df = pd.read_csv(self.MASTER_RESULTS)
                df = df[df['Run_Name'] != self.run_name]
            except:
                df = pd.DataFrame()
        else:
            df = pd.DataFrame()
        
        new_row = pd.DataFrame([final_stats])
        df = pd.concat([df, new_row], ignore_index=True)
        df = df.sort_values('Completion_Date', ascending=False)
        df.to_csv(self.MASTER_RESULTS, index=False)

    def output_final_reports(self):
        """Generates and saves consolidated final reports."""
        print("\n" + "="*60)
        print("GENERATING FINAL REPORTS")
        print("="*60)
        
        # Calculate final statistics
        current_session_seconds = time.time() - self.start_time
        total_elapsed_seconds = self.past_elapsed_seconds + current_session_seconds
        total_hours = total_elapsed_seconds / 3600
        total_days = total_hours / 24
        
        avg_eps = self.total_encounter / total_elapsed_seconds if total_elapsed_seconds > 0 else 0
        avg_sps = self.total_shinies_caught / total_elapsed_seconds if total_elapsed_seconds > 0 else 0
        
        catch_success_rate = (self.total_shinies_caught / self.total_shinies_encountered * 100) if self.total_shinies_encountered > 0 else 0
        actual_shiny_rate = (self.total_shinies_encountered / self.total_encounter) if self.total_encounter > 0 else 0
        expected_shinies = self.total_encounter * self.SHINY_RATE
        shiny_variance = ((self.total_shinies_encountered - expected_shinies) / expected_shinies * 100) if expected_shinies > 0 else 0
        
        # Calculate prediction accuracy
        prediction_accuracy = {}
        if self.initial_prediction:
            predicted_encounters = self.initial_prediction.get('expected_total_encounters', 0)
            if predicted_encounters > 0:
                encounter_diff = self.total_encounter - predicted_encounters
                encounter_diff_pct = (encounter_diff / predicted_encounters * 100)
                prediction_accuracy = {
                    'predicted_encounters': predicted_encounters,
                    'actual_encounters': self.total_encounter,
                    'difference': encounter_diff,
                    'difference_percent': encounter_diff_pct
                }
        
        print(f"Run Name: {self.run_name}")
        print(f"Shiny Rate: {self.shiny_modifier} ({self.SHINY_RATE:.10f})")
        print(f"Catch Mode: {'Guaranteed' if self.guaranteed_catch else 'Normal'}")
        print(f"Total Encounters: {self.total_encounter:,}")
        print(f"Total Shinies Encountered: {self.total_shinies_encountered:,}")
        print(f"Total Shinies Caught: {self.total_shinies_caught:,}")
        print(f"Unique Shinies: {len(self.shiny_box_counts)}/{self.total_pokemon}")
        print(f"Runtime: {total_hours:.2f} hours")
        
        if prediction_accuracy:
            print(f"\n--- Prediction Accuracy ---")
            print(f"Predicted: {prediction_accuracy['predicted_encounters']:,.0f} encounters")
            print(f"Actual: {prediction_accuracy['actual_encounters']:,} encounters")
            print(f"Difference: {prediction_accuracy['difference']:+,.0f} ({prediction_accuracy['difference_percent']:+.2f}%)")

        os.makedirs(self.REPORTS_DIR, exist_ok=True)
        
        # Get detailed per-Pokemon stats
        pokemon_stats = self._calculate_encounter_summary_stats()
        
        # Build comprehensive encounter summary
        summary_data = []
        
        for name, data in self.pokedex.items():
            normal_encounters = self.normal_box_counts.get(name, 0)
            total_weight = sum(self.spawn_weights)
            expected_proportion = data['Spawn Weight'] / total_weight
            expected_normal = expected_proportion * self.total_normals_caught
            
            # Get shiny stats
            stats = pokemon_stats.get(name, {})
            shiny_encountered = stats.get('total_encountered', 0)
            shiny_caught = stats.get('total_caught', 0)
            shiny_missed = stats.get('total_missed', 0)
            
            total_encounters = normal_encounters + shiny_encountered
            
            summary_data.append({
                'Pokemon': name,
                'Pokedex_Number': data['pokedex number'],
                'Base_Total': data['base_total'],
                'Is_Legendary': data.get('is_legendary', False),
                'Is_Mythical': data.get('is_mythical', False),
                'Catch_Rate': data['Catch Rate'],
                'Spawn_Weight': data['Spawn Weight'],
                'Expected_Normal_Encounters': int(expected_normal),
                'Normal_Encounters': normal_encounters,
                'Normal_Encounter_Variance': normal_encounters - int(expected_normal),
                'Shiny_Encounters_Total': shiny_encountered,
                'Shiny_Encounters_Caught': shiny_caught,
                'Shiny_Encounters_Missed': shiny_missed,
                'Total_Encounters': total_encounters,
                'First_Shiny_Encounter': stats.get('first_encounter'),
                'First_Shiny_Catch': stats.get('first_catch'),
                'Last_Shiny_Encounter': stats.get('last_encounter'),
                'Last_Shiny_Catch': stats.get('last_catch')
            })
        
        # Save complete encounter summary
        summary_df = pd.DataFrame(summary_data).sort_values('Pokedex_Number')
        summary_filepath = os.path.join(self.REPORTS_DIR, 'encounter_summary.csv')
        summary_df.to_csv(summary_filepath, index=False)
        print(f"✓ Encounter summary: encounter_summary.csv")
        
        # Save run-specific simulation results
        run_results = {
            'Run_Name': self.run_name,
            'Completion_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Shiny_Modifier': self.shiny_modifier,
            'Shiny_Rate_Decimal': self.SHINY_RATE,
            'Guaranteed_Catch': self.guaranteed_catch,
            'Completion_Status': 'Complete' if len(self.shiny_dex) >= self.total_pokemon else 'Incomplete',
            'Total_Encounters': self.total_encounter,
            'Total_Runtime_Hours': round(total_hours, 2),
            'Total_Runtime_Days': round(total_days, 2),
            'Avg_Encounters_Per_Second': round(avg_eps, 2),
            'Avg_Shinies_Per_Second': round(avg_sps, 4),
            'Total_Shiny_Encounters': self.total_shinies_encountered,
            'Total_Shinies_Caught': self.total_shinies_caught,
            'Total_Shinies_Missed': self.total_shinies_missed,
            'Catch_Success_Rate_Percent': round(catch_success_rate, 2),
            'Unique_Shinies_Caught': len(self.shiny_dex),
            'Unique_Normals_Encountered': len(self.normal_dex),
            'Actual_Shiny_Rate_Decimal': actual_shiny_rate,
            'Expected_Shinies': int(expected_shinies),
            'Shiny_Variance_Percent': round(shiny_variance, 2),
            'Total_Pokemon_In_Dex': self.total_pokemon,
            # Prediction fields
            'Predicted_Total_Encounters': prediction_accuracy.get('predicted_encounters', None),
            'Prediction_Difference': prediction_accuracy.get('difference', None),
            'Prediction_Difference_Percent': round(prediction_accuracy.get('difference_percent', 0), 2) if prediction_accuracy else None
        }
        
        # Save to individual run results
        run_results_filepath = os.path.join(self.REPORTS_DIR, 'simulation_results.csv')
        run_results_df = pd.DataFrame([run_results])
        run_results_df.to_csv(run_results_filepath, index=False)
        print(f"✓ Simulation results: simulation_results.csv")
        
        # Append to master results
        self._save_to_master_results(run_results)
        print(f"✓ Updated master results: {self.MASTER_RESULTS}")
        
        print(f"\n✓ All reports saved to: {self.REPORTS_DIR}/")
        print("="*60)

    def run(self):
        """Main entry point to start and manage the simulation loop."""
        
        self.load_checkpoint()

        if not self.pokedex:
            print("FATAL ERROR: Pokedex is empty.")
            return

        # Display startup prediction
        self._display_startup_prediction()

        shiny_log_path = os.path.join(self.REPORTS_DIR, 'shiny_analysis_log.csv')
        timeline_log_path = os.path.join(self.REPORTS_DIR, 'encounter_timeline.csv')
        
        try:
            os.makedirs(self.REPORTS_DIR, exist_ok=True)
            
            # Open shiny log - append if resuming, write if new
            shiny_file_exists = os.path.exists(shiny_log_path)
            shiny_mode = 'a' if shiny_file_exists else 'w'
            self._shiny_file_handle = open(shiny_log_path, shiny_mode, newline='', encoding='utf-8')
            self._active_shiny_writer = csv.writer(self._shiny_file_handle)
            
            if not shiny_file_exists:
                self._active_shiny_writer.writerow(['Encounter_Number', 'Pokemon', 'Catch_Successful', 'Is_New_Shiny'])
            
            # Open timeline log - append if resuming, write if new
            timeline_file_exists = os.path.exists(timeline_log_path)
            timeline_mode = 'a' if timeline_file_exists else 'w'
            self._timeline_file_handle = open(timeline_log_path, timeline_mode, newline='', encoding='utf-8')
            self._active_timeline_writer = csv.writer(self._timeline_file_handle)
            
            if not timeline_file_exists:
                self._active_timeline_writer.writerow([
                    'Encounter_Milestone',
                    'Timestamp',
                    'Cumulative_Shinies_Encountered',
                    'Cumulative_Shinies_Caught',
                    'Cumulative_Shinies_Missed',
                    'Unique_Shinies_Caught',
                    'Unique_Normals_Encountered',
                    'Current_EPS',
                    'Current_SPS',
                    'Elapsed_Seconds'
                ])
            
            # Check if already completed
            if len(self.shiny_dex) >= self.total_pokemon:
                print("✓ Simulation already completed.")
                self._shiny_file_handle.close()
                self._timeline_file_handle.close()
                self.output_final_reports()
                return

            print(f"Starting encounter loop...")
            print(f"Target: {self.total_pokemon} unique shiny Pokémon")
            print(f"Logging timeline every {self.TIMELINE_LOG_INTERVAL:,} encounters")
            print(f"Press Ctrl+C to pause and save\n")

            # Main simulation loop
            while len(self.shiny_dex) < self.total_pokemon:
                self.run_encounter()
                
                if self.total_encounter % self.PROGRESS_UPDATE_INTERVAL == 0:
                    self._display_progress()
                
                if self.total_encounter % self.CHECKPOINT_INTERVAL == 0:
                    self.save_checkpoint()
            
            print("\n\n" + "="*60)
            print("🎉 SIMULATION COMPLETE! 🎉")
            print("="*60)
            
            # Final flush
            self._flush_shiny_buffer()
            self._flush_timeline_buffer()
            self._shiny_file_handle.close()
            self._timeline_file_handle.close()
        
        except KeyboardInterrupt:
            print("\n\n⚠ Simulation paused by user.")
            if self._shiny_file_handle:
                self._shiny_file_handle.close()
            if self._timeline_file_handle:
                self._timeline_file_handle.close()
        
        finally:
            self._active_shiny_writer = None
            self._active_timeline_writer = None
            
            print("\nSaving checkpoint...")
            self.save_checkpoint()
            self.output_final_reports()
            
            # Final stats display
            current_session_seconds = time.time() - self.start_time
            total_elapsed_seconds = self.past_elapsed_seconds + current_session_seconds
            total_hours = total_elapsed_seconds / 3600
            
            print("\n" + "="*60)
            print("FINAL STATISTICS")
            print("="*60)
            print(f"Total Runtime: {total_hours:.2f} hours")
            print(f"Average EPS: {(self.total_encounter / total_elapsed_seconds):.1f}")
            if self.total_shinies_caught > 0:
                print(f"Average SPS: {(self.total_shinies_caught / total_elapsed_seconds):.4f}")
            print("="*60 + "\n")


if __name__ == "__main__":
    simulation = ShinySimulation()
    simulation.run()
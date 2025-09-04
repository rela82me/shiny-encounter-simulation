# Shiny Pokémon Encounter Simulator

This project is a Python-based command-line application that simulates the experience of hunting for shiny Pokémon. It goes beyond a simple encounter counter by incorporating a detailed rarity system, catch mechanics, resource management, and comprehensive statistical reporting.

## Features

- **Rarity-Based Encounters**: Pokémon don't all appear equally. The simulation uses a weighted system based on defined rarities (`Common`, `Uncommon`, `Rare`, `Very Rare`, `Legendary`) to provide a more realistic distribution of encounters.
- **Dynamic Catch & Run Mechanics**: Finding a shiny is only half the battle! Each shiny encounter initiates a catch sequence. The probability of catching the Pokémon and the chance it will flee after a failed attempt are tied directly to its rarity.
- **Resource Tracking**: The simulation tracks the number of Pokéballs used, adding a layer of resource management to the hunt.
- **Two Simulation Modes**:
  1.  **Fixed Encounters**: Run the simulation for a predetermined number of encounters to see what you can find.
  2.  **Target Hunting**: Set a specific Pokémon as your target, and the simulation will run until that shiny is successfully caught.
- **Detailed Final Report**: At the end of each simulation, a full report is generated, including:
  - Total simulation time.
  - Total encounters and Pokéballs used.
  - A breakdown of shinies found, caught, and those that fled.
  - Calculated metrics like average encounters per shiny and Pokéballs per catch.
  - A log of every shiny Pokémon successfully caught.
- **Data-Driven**: All Pokémon data, including names, Pokédex numbers, and rarities, is loaded from an easily editable `pokedex.json` file.

## How It Works

The simulation is driven by the `shiny.py` script.

1.  **Initialization**: The script loads all Pokémon data and their rarities from `pokedex.json`. It then creates a weighted list of possible encounters.
2.  **Encounter Loop**: The script enters a loop, either for a fixed number of encounters or until a target is caught.
3.  **Spawning**: In each iteration, a Pokémon is randomly chosen from the weighted list.
4.  **Shiny Check**: A random roll is performed against the `SHINY_CHANCE` to determine if the encountered Pokémon is shiny.
5.  **Catch Sequence**: If a shiny appears, the script simulates throwing Pokéballs. Each throw has a chance to succeed or fail based on the Pokémon's rarity. If a throw fails, the Pokémon has a chance to run away.
6.  **Reporting**: Once the simulation's end condition is met, it calculates and prints a final, detailed report of the entire hunt.

## Project Files

- **`shiny.py`**: The main executable script that contains all the simulation logic. Key parameters can be configured at the top of this file.
- **`pokedex.json`**: A JSON database containing all the Pokémon. Each entry includes the Pokémon's ID and its assigned rarity, which dictates its spawn rate and catch difficulty.

## How to Use

### Prerequisites

- Python 3.x

### Running the Simulation

1.  **Clone or download the repository.** Make sure `shiny.py` and `pokedex.json` are in the same directory.

2.  **Configure the Simulation (Optional)**:
    Open `shiny.py` in a text editor and modify the configuration variables at the top of the file to customize your hunt.

    ```python
    # --- CONFIGURATION ---
    POKEDEX_FILE = 'pokedex.json'
    # Set the total number of encounters for the simulation (if not hunting a target)
    SIMULATION_ENCOUNTERS = 100_000
    # Set to a Pokémon name to hunt for it, or None to run for SIMULATION_ENCOUNTERS
    TARGET_POKEMON = "Mewtwo"
    # The base chance of finding a shiny
    SHINY_CHANCE = 1 / 4096
    ```

3.  **Execute the script** from your terminal:

    ```bash
    python shiny.py
    ```

4.  **View the Results**: Watch the live output in your terminal. When a shiny is found, the catch sequence will be printed. The final summary report will be displayed once the simulation is complete.

## Example Output

```
Encounter #8,192: A wild SHINY Eevee appeared! (Rarity: Rare)
   -> Throwing a Pokéball... (Total used: 1)
   Oh no! The Pokémon broke free!
   -> Throwing a Pokéball... (Total used: 2)
   GOTCHA! The shiny Eevee was caught!

========================================
HUNT COMPLETE - FINAL REPORT
========================================
Total Simulation Time: 1.23 seconds
Total Encounters:      8,192
Total Pokéballs Used:  2
----------------------------------------
Shinies Found:   1
Shinies Caught:  1
Shinies Fled:    0
...
```

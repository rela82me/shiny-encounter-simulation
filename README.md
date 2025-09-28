# Shiny Pokémon Encounter Simulator

A command-line Python application that simulates the process of hunting for a complete shiny Pokédex. This script uses weighted encounter and catch rates based on in-game data to provide a more realistic and engaging simulation.

## Features

- **Data-Driven**: All Pokémon data is generated from the `Pokemon Stats.xlsx - Stats.csv` file, making it easy to update and manage.
- **Weighted Encounters**: Pokémon spawn rates are not equal. The simulation uses the "Experience Type" (e.g., Slow, Medium Fast, Fast) to create a weighted probability for each encounter.
- **Catch Mechanics**: When a shiny Pokémon is encountered, the simulation uses its specific "Catch Rate" to determine if the Pokémon is successfully caught or if it flees.
- **Live Progress Tracking**: The terminal displays a clean, single-line progress bar that updates periodically without flooding the screen. It shows total encounters, unique shinies caught, total shinies caught, and the simulation's duration.
- **Unique Shiny Alerts**: The script prints a special, high-visibility message only when a _new, unique_ shiny Pokémon is caught, making each new addition to the Pokédex an exciting event.
- **Automatic Report Generation**: Upon completion or interruption, the script creates a `reports` folder and saves timestamped CSV files (`normal_encounters_{timestamp}.csv` and `shiny_encounters_{timestamp}.csv`) with a full summary of the simulation.

## How It Works

The project is split into two main Python scripts:

1.  **`makelist.py` (Data Preparation)**: This script reads the raw data from `Pokemon Stats.xlsx - Stats.csv`, selects the necessary columns (`name`, `pokedex number`, `Catch Rate`, `Experience Type`), and generates the clean `pokedex.json` file that the main simulator uses.

2.  **`shiny.py` (The Simulator)**:
    - Loads the `pokedex.json` data into a master `POKEDEX` dictionary.
    - Calculates numerical spawn weights for each Pokémon based on their "Experience Type".
    - Prepares two lists: one of all Pokémon names and a corresponding list of their spawn weights for the encounter logic.
    - Enters a loop that runs until one of every Pokémon has been caught as a shiny.
    - Inside the loop, it uses `random.choices()` to simulate a weighted encounter.
    - For each encounter, it rolls for a shiny chance (1 in 4096).
    - If a shiny is found, it then simulates a catch attempt based on that Pokémon's specific catch rate.
    - If the catch is successful, it checks if it's a new shiny and prints the appropriate message.

## How to Run

1.  **Install Dependencies**: Ensure you have the required Python libraries. You can install them using pip:

    ```bash
    pip install pandas
    ```

2.  **Generate Pokémon Data**: If you have made any changes to the `Pokemon Stats.xlsx - Stats.csv` file, you must run the data preparation script first to update the `pokedex.json` file.

    ```bash
    python makelist.py
    ```

3.  **Run the Simulation**: Start the main simulation script from your terminal.

    ```bash
    python shiny.py
    ```

4.  **Stop the Simulation**: To stop the simulation early, press **`Ctrl+C`**. The script is designed to catch this interruption, stop gracefully, and generate the final report based on the progress so far.

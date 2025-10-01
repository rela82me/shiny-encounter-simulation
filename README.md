# Shiny Pokémon Encounter Simulator

A command-line Python application that simulates the long and arduous process of hunting for a complete shiny Pokédex. This project is designed not only to run the simulation but also to generate a rich dataset for analyzing the statistical realities of collecting rare items with weighted probabilities (a variation of the "Coupon Collector's Problem").

The simulation is built to be robust, featuring a checkpoint system that allows it to be stopped and resumed, protecting against interruptions like system restarts.

## Key Features

- **Data-Driven**: All Pokémon stats, including spawn and catch rates, are sourced from an external `.csv` file, processed by `makelist.py`, and loaded from a clean `pokedex.json`.
- **Weighted Encounters**: Pokémon spawn rates are weighted based on their in-game "Experience Type" (e.g., Slow, Fast), ensuring a realistic distribution of common and rare encounters.
- **Catch Mechanics**: Each shiny encounter triggers a catch attempt based on the Pokémon's specific catch rate, adding another layer of probability to the simulation.
- **Robust Checkpointing**: The simulation automatically saves its entire state (all counters, logs, and timers) to a `checkpoint.json` file periodically. If the script is stopped or crashes, it will automatically resume from the last checkpoint on the next run.
- **Detailed Data Logging**: Every single shiny encounter is recorded in a detailed `shiny_analysis_log.csv`, capturing the encounter number, the outcome of the catch attempt, and whether it was a new Pokémon for the Pokédex. This file is specifically designed for in-depth analysis in tools like Power BI.
- **Optimized for Performance**: The main loop is highly optimized, using simple counters instead of expensive calculations to ensure the simulation can run for billions of encounters as efficiently as possible.
- **Live Progress Tracking**: A clean, non-flooding progress bar in the terminal provides real-time updates on total encounters, unique shinies caught, total shinies caught, and performance metrics like encounters per second.

## How It Works

The project is split into two main Python scripts:

1.  **`makelist.py` (Data Preparation)**: This utility reads the raw data from `Pokemon Stats.xlsx - Stats.csv`, processes it, and generates the `pokedex.json` file that acts as the simulation's database.

2.  **`shiny.py` (The Simulator)**:
    - On startup, the script first looks for a `checkpoint.json` file. If found, it loads the entire previous state and seamlessly resumes the simulation.
    - If no checkpoint is found, it initializes all variables and starts a new run.
    - The main loop runs until a shiny version of every Pokémon has been successfully caught.
    - Inside the loop, it simulates a weighted encounter, checks for a shiny, and attempts a catch if a shiny appears.
    - Every shiny encounter is meticulously logged for later analysis.
    - The script saves a checkpoint every 100,000 encounters to prevent data loss.

## How to Run

1.  **Install Dependencies**: Ensure you have the required Python libraries.

    ```bash
    pip install pandas
    ```

2.  **Generate Pokémon Data**: (Only needs to be done once, or after updating the stats CSV)

    ```bash
    python makelist.py
    ```

3.  **Run the Simulation**:

    ```bash
    python shiny.py
    ```

    - If a `checkpoint.json` file exists in the directory, the script will automatically resume.
    - To start a fresh simulation, simply delete the `checkpoint.json` file before running.

4.  **Stop the Simulation**: To stop the simulation early, press **`Ctrl+C`**. The script will catch the interruption, save a final checkpoint, and generate all the report files with the progress so far.

## Generated Files

The script will generate the following files in a `reports` folder:

- **`shiny_analysis_log_{timestamp}.csv`**: The most important file for analysis. Contains a detailed log of every shiny encounter.
- **`shiny_encounters_{timestamp}.csv`**: A summary of how many times each unique shiny species was caught.
- **`normal_encounters_{timestamp}.csv`**: A summary of how many times each normal Pokémon was encountered.
- **`checkpoint.json`**: (In the root directory) The file containing the saved state of the simulation.

# Shiny Pokémon Encounter Simulator

![Main Summary](./Images/Summary.jpg)

A command-line Python application that simulates the long and arduous process of hunting for a complete shiny Pokédex. This project was designed not only to run the simulation but also to generate a rich dataset for analyzing the statistical realities of collecting rare items with weighted probabilities—a variation of the **"Coupon Collector's Problem."**

After a continuous runtime of **72.4 hours**, the simulation successfully completed its goal of catching one of every unique shiny Pokémon, generating a dataset of over 1.6 million shiny encounters.

### **Read the Full Story & See the Interactive Report**

For a detailed breakdown of the project's journey, the key insights from the data, and the story behind the numbers, check out the full blog post:

**[I Simulated 6.7 Billion Pokémon Encounters to Quantify Your Suffering](https://joshualown.org/2025/10/05/i-simulated-6-7-billion-pokemon-encounters-to-quantify-your-suffering/)**

---

## Final Results at a Glance

- **Total Encounters Simulated:** 6,759,893,113
- **Total Simulation Time:** 72.4 Hours
- **Total Shiny Encounters:** 1,652,816
- **Total Shinies Caught:** 664,018
- **Total Shinies Missed:** 988,798
- **Final Unique Shiny Caught:** Arceus-Fairy

![Experience Type Analysis](./Images/Exp%20Type.jpg)

---

## Key Features

- **Interactive Run Management**: On startup, the script lists all previous simulation runs, allowing you to seamlessly resume a paused session or start a new one with a custom name.
- **Live ETA Prediction**: Implements the **Weighted Coupon Collector's Problem** formula to provide a theoretical prediction of the total encounters and runtime before the simulation even begins. This ETA is dynamically updated as the simulation progresses.
- **Configurable Simulation Parameters**: Interactively configure the shiny rate (Standard, Charm, Masuda, or Both) and catch mechanics (Normal or Guaranteed 100% Catch Rate) for each new run.
- **Robust Checkpointing**: Automatically saves progress to a `checkpoint.json` file, ensuring no data is lost. Pausing with `Ctrl+C` will safely save the state before exiting.
- **Detailed, Run-Specific Reporting**: Each simulation run generates its own folder containing detailed logs, including a complete encounter summary, a shiny analysis log, and a timeline log for time-series analysis.
- **Master Results Tracking**: A top-level `simulation_results.csv` file is maintained, allowing for easy comparison of the outcomes of different simulation runs.
- **Weighted Encounters**: Pokémon spawn rates are weighted based on their Base Stat Total, ensuring a more realistic distribution of encounters.
- **Performance Optimized**: The core encounter loop is designed for efficiency, capable of processing tens of thousands of encounters per second.

![Catch Rate Analysis](./Images/Catch%20Rate.jpg)

---

## How It Works

The project is driven by `simulator.py`, the main simulation engine.

1.  **Data Source**: The simulator loads Pokémon data, including Base Stats and Catch Rates, from the `Pokemon Stats.xlsx` file. A utility script, `pokeapi.py`, is also included to generate a more comprehensive dataset from the PokéAPI if needed.

2.  **Interactive Setup**: When you run `simulator.py`, it first checks for a `run_registry.json`.

    - If existing runs are found, it prompts you to either resume a previous run or start a new one.
    - For new runs, it guides you through setting a name, shiny rate, and catch mode.

3.  **Simulation Loop**:
    - The script loads the state from a `checkpoint.json` file if resuming, or starts fresh.
    - It enters a high-speed loop, simulating one encounter at a time based on weighted probabilities.
    - The simulation continues until a shiny version of every Pokémon in the dataset has been successfully caught.

## How to Run

1.  **Install Dependencies**: Ensure you have Pandas and Openpyxl installed.

    ```bash
    pip install pandas openpyxl
    ```

2.  **Prepare Data**: Make sure the `Pokemon Stats.xlsx` file is in the same directory as the script.

3.  **Run the Simulation**:

    ```bash
    python simulator.py
    ```

4.  **Follow the Prompts**: Use the interactive menu to resume a previous run or configure and start a new one.

5.  **Stop the Simulation**: To stop early, press **`Ctrl+C`**. The script will perform a final save of its checkpoint and generate reports with the progress so far.

---

![Fun Stats](./Images/Stats%20for%20Nerds.jpg)

## Generated Files

The scripts will generate the following files and directories:

- **`reports/`**: The main directory for all simulation outputs.
  - **`run_registry.json`**: A master file that keeps track of all simulation runs.
  - **`simulation_results.csv`**: A master CSV comparing the final results of all runs.
  - **`[run_name]/`**: A dedicated directory is created for each simulation run, containing:
    - **`checkpoint.json`**: The saved state of the simulation for this run.
    - **`encounter_summary.csv`**: A detailed, per-Pokémon breakdown of all encounter stats (normal vs. shiny, variance, first/last catch times).
    - **`shiny_analysis_log.csv`**: The raw log of every single shiny encounter, whether it was caught or missed.
    - **`encounter_timeline.csv`**: A log of simulation stats at regular intervals, perfect for time-series analysis.
    - **`simulation_results.csv`**: A summary report specific to this individual run.

---

## Thank You

![Thank You](./Images/Thank%20You.jpg)

Thank you for checking out this project! It was a passion-fueled journey into data simulation, analysis, and storytelling. I hope you found the results as fascinating as I did.

For more projects, simulations, and data-driven descents into madness, feel free to visit my website.

**[joshualown.org](https://joshualown.org)**

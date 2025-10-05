# Shiny Pokémon Encounter Simulator

![Main Summary](https://joshualown.org/wp-content/uploads/2025/10/Main-Summary-1.png)

A command-line Python application that simulates the long and arduous process of hunting for a complete shiny Pokédex. This project was designed not only to run the simulation but also to generate a rich dataset for analyzing the statistical realities of collecting rare items with weighted probabilities—a variation of the **"Coupon Collector's Problem."**

The simulation is built to be robust, featuring a checkpoint system that allows it to be stopped and resumed, protecting against interruptions like system restarts.

After a continuous runtime of **72.4 hours**, the simulation successfully completed its goal of catching one of every unique shiny Pokémon.

### **Read the Full Story**

For a detailed breakdown of the project's journey, the key insights from the data, and the story behind the numbers, check out the full blog post:

**[I Simulated 6.7 Billion Pokémon Encounters to Quantify Your Suffering](https://joshualown.org/2025/10/05/i-simulated-6-7-billion-pokemon-encounters-to-quantify-your-suffering/)**

---

## Final Results at a Glance

- **Total Encounters Simulated:** 6,759,893,105
- **Total Simulation Time:** 72.4 Hours
- **Total Shiny Encounters:** 1,652,816
- **Total Shinies Caught:** 664,018
- **Total Shinies Missed:** 988,798
- **Final Unique Shiny Caught:** Arceus-Fairy

![Experience Type Analysis](https://joshualown.org/wp-content/uploads/2025/10/Experience-Type.png)

---

## Key Features

- **Data-Driven**: All Pokémon stats, including spawn and catch rates, are sourced from an external `.csv` file, processed by `makelist.py`, and loaded from a clean `pokedex.json`.
- **Weighted Encounters**: Pokémon spawn rates are weighted based on their in-game "Experience Type" (e.g., Slow, Fast), ensuring a realistic distribution of common and rare encounters.
- **Catch Mechanics**: Each shiny encounter triggers a catch attempt based on the Pokémon's specific catch rate, adding another layer of probability to the simulation.
- **Robust Checkpointing**: The simulation automatically saves its entire state to a `checkpoint.json` file, allowing it to resume seamlessly after interruptions.
- **Detailed Data Logging**: Every single shiny encounter is recorded in a detailed `shiny_analysis_log.csv`, designed for in-depth analysis in tools like Power BI.
- **Optimized for Performance**: The main loop is highly optimized to ensure the simulation can run for billions of encounters as efficiently as possible.
- **Live Progress Tracking**: A clean, non-flooding progress bar in the terminal provides real-time updates on the simulation's progress.

![Catch Rate Analysis](https://joshualown.org/wp-content/uploads/2025/10/Catch-Rate-1.png)

---

## How It Works

The project is split into two main Python scripts:

1.  **`makelist.py` (Data Preparation)**: This utility reads the raw data from `Pokemon Stats.xlsx - Stats.csv`, processes it, and generates the `pokedex.json` file that acts as the simulation's database.

2.  **`shiny.py` (The Simulator)**:
    - On startup, the script first looks for a `checkpoint.json` file to seamlessly resume a previous simulation.
    - If no checkpoint is found, it initializes all variables for a new run.
    - The main loop runs until a shiny version of every Pokémon has been successfully caught.
    - Inside the loop, it simulates a weighted encounter, checks for a shiny, and attempts a catch if one appears.
    - Every shiny encounter is meticulously logged for later analysis.

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

    - If a `checkpoint.json` file exists, the script will automatically resume.
    - To start a fresh simulation, simply delete the `checkpoint.json` file.

4.  **Stop the Simulation**: To stop the simulation early, press **`Ctrl+C`**. The script will catch the interruption, save a final checkpoint, and generate the report files with the progress so far.

---

![Fun Stats](https://joshualown.org/wp-content/uploads/2025/10/Stats-for-Nerds.png)

## Generated Files

The script will generate the following files in a `reports` folder:

- **`shiny_analysis_log_{timestamp}.csv`**: The most important file for analysis. Contains a detailed log of every shiny encounter.
- **`shiny_encounters_{timestamp}.csv`**: A summary of how many times each unique shiny species was caught.
- **`normal_encounters_{timestamp}.csv`**: A summary of how many times each normal Pokémon was encountered.
- **`checkpoint.json`**: (In the root directory) The file containing the saved state of the simulation.

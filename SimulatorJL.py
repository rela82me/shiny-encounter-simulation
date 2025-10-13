'''
Simulation details: 

Disclaimers:
-All shiny rates are static, while across games they are situational.
-Spawn rates are also conditional per game and will be determined by 
'''

import random as rand
import pandas as pd
import json
import sys
import time
import os
import csv

class ShinySimulation: 
    #Class to encapsulate the shiny pokemon simulator. Manages the state, data, and core logic all in a single object. 

    def __init__(self, excel_path='Pokemon Stats.xlsx', sheet_name='Pokedex' reports_dir='reports'):
        #initialize the simulation by loading data nd setting up the initial state. 

        self.SHINY_RATE = 1/4096
        self.REPORTS_DIR = reports_dir

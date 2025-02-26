"""
Region system for handling descriptive, spawning, and resource regions.
"""
import os

# Base path for region files
REGION_PATH = os.path.dirname(os.path.abspath(__file__))

# Paths to consolidated region definition files (without .json extension)
DESCRIPTIVE_PATH = os.path.join(REGION_PATH, 'descriptive')
SPAWNING_PATH = os.path.join(REGION_PATH, 'spawning') 
RESOURCE_PATH = os.path.join(REGION_PATH, 'resource')
from gurobipy import Model, GRB
import pandas as pd

def read_basic_data():
    # Excel file names
    travel_times = pd.read_excel('a2_part1.xlsx','Travel Times')

    return travel_times

def build_model(travel_times):



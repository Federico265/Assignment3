from gurobipy import Model, GRB, quicksum
import pandas as pd
import numpy as np

def read_basic_data():
    # Excel file names
    travel_times = pd.read_excel('a2_part1.xlsx','Travel Times')
    lines = pd.read_excel('a2_part1.xlsx', 'Lines')

    lines = lines.drop(['Name','Frequency'], axis = 1)
    lines = lines.fillna(0)


    weights = 1 #Each activity has the same importance for us

    # # Create an empty dictionary to store the station counts to generate the weight for each station
    # station_counts = {}
    #
    # # Iterate through the rows of the DataFrame
    # for index, row in lines.iterrows():
    #     # Iterate through columns starting from 'Unnamed: 2'
    #     for col in row.index[2:]:
    #         station = row[col]
    #         if pd.notna(station):
    #             # If the station is not NaN, increment its count in the dictionary
    #             if station in station_counts:
    #                 station_counts[station] += 1
    #             else:
    #                 station_counts[station] = 1
    #
    # activity_running_weights = {}

    return travel_times, lines, weights


def build_model(travel_times, lines, weights):

    # Initialize the Gurobi model
    model = Model("NS_trains")

    line_names = ['800','3000','3100','3500','3900']
    runnning_activites = {}
    dwelling_activities = {}
    transfer_activities = {}
    sync_activities = {}
    headway_activities = {}

    for k in range(5):
        station_names = lines.iloc[k].tolist()  # Extract station names from the first row
        name = line_names[k]

        # Create Gurobi variables for each possible trip between stations
        for i in range(len(station_names) - 1):
            station1 = str(station_names[i])
            station2 = str(station_names[i+1])

            if station1 == '0' or station2 == '0':
                break
            # Create a Gurobi variable for the activity between station1 and station2
            runnning_activites[f'{station1} to {station2} - {name}'] = model.addVar(vtype=GRB.CONTINUOUS,
                                                                        name=f"activity_{station1}_{station2}_{name}")
            runnning_activites[f'{station2} to {station1} - {name}'] = model.addVar(vtype=GRB.CONTINUOUS,
                                                                        name=f"activity_{station2}_{station1}_{name}")

            if i != 0 and i != len(station_names):
                dwelling_activities[f'dwelling at {station1} - {name} forward trip'] = model.addVar(vtype=GRB.CONTINUOUS,
                                                        name=f"activity_dwelling at {station1} - {name} forward trip")
                dwelling_activities[f'dwelling at {station1} - {name} backward trip'] = model.addVar(vtype=GRB.CONTINUOUS,
                                                        name=f"activity_dwelling at {station1} - {name} backward trip")

    print(dwelling_activities)


    # Objective function: Minimize the total weighted travel time
    objective = quicksum(rav * weights for rav in runnning_activites.values())
    model.setObjective(objective, GRB.MINIMIZE)

    model.update()

travel_times, lines, weights = read_basic_data()
print(lines)
build_model(travel_times, lines, weights)


from gurobipy import Model, GRB, quicksum
import pandas as pd

def read_basic_data():
    # Excel file names
    travel_times = pd.read_excel('a2_part1.xlsx','Travel Times')
    lines = pd.read_excel('a2_part1.xlsx', 'Lines')

    lines = lines.drop(['Name','Frequency'], axis = 1)


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

    # Assuming 'lines' is a DataFrame with station names
    station_names = lines.iloc[0].tolist()  # Extract station names from the first row
    runnning_activites = {}  # Dictionary to store Gurobi variables

    model = Model("YourModel")  # Create a Gurobi model

    # Create Gurobi variables for each possible trip between stations
    for i in range(len(station_names)):
        for j in range(i + 1, len(station_names)):
            station1 = station_names[j-1]
            station2 = station_names[j]

            # Create a Gurobi variable for the activity between station1 and station2
            runnning_activites[f'{station1} to {station2}'] = model.addVar(vtype=GRB.CONTINUOUS,
                                                                           name=f"activity_{station1}_{station2}")

    # Objective function: Minimize the total weighted travel time
    objective = quicksum(runnning_activites * weights)
    model.setObjective(objective, GRB.MINIMIZE)

    model.update()

travel_times, lines, weights = read_basic_data()
print(lines)
build_model(travel_times, lines, weights)


from gurobipy import Model, GRB
import pandas as pd

def read_basic_data():
    # Excel file names
    travel_times = pd.read_excel('a2_part1.xlsx','Travel Times')
    lines = pd.read_excel('a2_part1.xlsx', 'Lines')

    # Create an empty dictionary to store the station counts to generate the weight for each station
    station_counts = {}

    # Iterate through the rows of the DataFrame
    for index, row in lines.iterrows():
        # Iterate through columns starting from 'Unnamed: 3'
        for col in row.index[2:]:
            station = row[col]
            if pd.notna(station):
                # If the station is not NaN, increment its count in the dictionary
                if station in station_counts:
                    station_counts[station] += 1
                else:
                    station_counts[station] = 1

    # Convert the dictionary to a pandas Series for a cleaner output
    station_counts_series = pd.Series(station_counts)

    # Print the counts for each station
    print(station_counts_series)

    return travel_times

read_basic_data()

def build_model(travel_times,activity_weights):

    # Initialize the Gurobi model
    model = Model("NS_trains")

    activity_vars = {}
    for index, row in travel_times.iterrows():
        from_station = row['From']
        to_station = row['To']
        # Create a variable for each activity (segment between stations)
        activity_vars[(from_station, to_station)] = model.addVar(vtype=GRB.CONTINUOUS,
                                                                 name=f"activity_{from_station}_{to_station}")

    # Objective function: Minimize the total weighted travel time
    objective = quicksum(activity_vars[activity] * weight for activity, weight in activity_weights.items())
    model.setObjective(objective, GRB.MINIMIZE)

    model.update()


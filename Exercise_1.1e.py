from gurobipy import Model, GRB
import pandas as pd

def read_basic_data():
    # Excel file names
    travel_times = pd.read_excel('a2_part1.xlsx','Travel Times')
    lines = pd.read_excel('a2_part1.xlsx', 'Lines')

    # Drop the 'Name', 'Frequency', and 'Stops' columns as they are not needed for counting stations
    stations_df = lines.drop(['Name', 'Frequency', 'Stops'], axis=1)

    # Use value_counts() to count the occurrences of each station
    station_counts = stations_df.value_counts()

    # Print the counts for each station
    print(station_counts)

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


from gurobipy import Model, GRB, quicksum
import pandas as pd
import numpy as np

def read_basic_data():

    travel_times = pd.read_excel('a2_part1.xlsx', 'Travel Times')

    return travel_times


def build_model(travel_times):

    # Initialize the model
    model = Model("TrainTimetabling")

    # Define all stations and lines, including directions
    all_stations = ['Amr', 'Asd', 'Ut', 'Ehv', 'Std', 'Mt', 'Hdr', 'Nm', 'Shl', 'Vl', 'Hrl']
    lines_stations = {
        '800': ['Amr', 'Asd', 'Ut', 'Ehv', 'Std', 'Mt'],
        '3000': ['Hdr', 'Amr', 'Asd', 'Ut', 'Nm'],
        '3100': ['Shl', 'Ut', 'Nm'],
        '3500': ['Shl', 'Ut', 'Ehv', 'Vl'],
        '3900': ['Ehv', 'Std', 'Hrl'],
    }
    directions = ['forward', 'backward']  # Define directions

    # Define decision variables for arrivals and departures for each station and line
    arrivals = {}
    departures = {}
    for line, stations in lines_stations.items():
        # Define departure variables for all stations except the last one
        for station in stations[:-1]:
            departures[('Departure', station, line)] = model.addVar(vtype=GRB.INTEGER, name=f"dep_{station}_{line}")
        # Define arrival variables for all stations except the first one
        for station in stations[1:]:
            arrivals[('Arrival', station, line)] = model.addVar(vtype=GRB.INTEGER, name=f"arr_{station}_{line}")
        # Define departure variables for the return trip for all stations except the first one
        for station in stations[1:]:
            departures[('Departure', station, line, 'return')] = model.addVar(vtype=GRB.INTEGER, name=f"dep_{station}_{line}_return")
        # Define arrival variables for the return trip for all stations except the last one
        for station in stations[:-1]:
            arrivals[('Arrival', station, line, 'return')] = model.addVar(vtype=GRB.INTEGER, name=f"arr_{station}_{line}_return")

    # Parameters
    T = 30  # The timetable cycle time in minutes

    # Create variables for running and dwelling activities
    running_activities = {}
    dwelling_activities = {}

    for line, stations in lines_stations.items():
        # In the forward direction, we go from the first station to the second-to-last
        for i in range(len(stations) - 1):
            running_activities[(stations[i], stations[i+1], line, 'forward')] = model.addVar(
                vtype=GRB.INTEGER, name=f"run_{stations[i]}_{stations[i+1]}_{line}_forward"
            )
        # In the backward direction, we go from the last station to the second station
        for i in range(len(stations) - 1, 0, -1):
            running_activities[(stations[i], stations[i-1], line, 'backward')] = model.addVar(
                vtype=GRB.INTEGER, name=f"run_{stations[i]}_{stations[i-1]}_{line}_backward"
            )

    for line, stations in lines_stations.items():
        # For the forward direction, exclude the first and last stations
        for i in range(1, len(stations) - 1):
            dwelling_activities[(stations[i], line, 'forward')] = model.addVar(
                vtype=GRB.INTEGER, name=f"dwell_{stations[i]}_{line}_forward"
            )
        # For the backward direction, exclude the first and last stations
        for i in range(len(stations) - 2, 0, -1):
            dwelling_activities[(stations[i], line, 'backward')] = model.addVar(
                vtype=GRB.INTEGER, name=f"dwell_{stations[i]}_{line}_backward"
            )

    # Create variables for p_ij to simulate the modulo operator for periodicity
    p_ij = {}

    # Loop through each line and direction to create p_ij variables for running and dwelling activities
    for line, stations in lines_stations.items():
        # p_ij for running activities in the forward direction
        for i in range(len(stations) - 1):
            p_ij[(stations[i], stations[i+1], line, 'forward')] = model.addVar(
                vtype=GRB.INTEGER, lb=0, name=f"p_run_{stations[i]}_{stations[i+1]}_{line}_forward"
            )
        # p_ij for running activities in the backward direction
        for i in range(len(stations) - 1, 0, -1):
            p_ij[(stations[i], stations[i-1], line, 'backward')] = model.addVar(
                vtype=GRB.INTEGER, lb=0, name=f"p_run_{stations[i]}_{stations[i-1]}_{line}_backward"
            )
        # p_ij for dwelling activities, excluding the first and last stations
        for i in range(1, len(stations) - 1):
            p_ij[(stations[i], line, 'forward')] = model.addVar(
                vtype=GRB.INTEGER, lb=0, name=f"p_dwell_{stations[i]}_{line}_forward"
            )
        for i in range(len(stations) - 2, 0, -1):
            p_ij[(stations[i], line, 'backward')] = model.addVar(
                vtype=GRB.INTEGER, lb=0, name=f"p_dwell_{stations[i]}_{line}_backward"
            )

    headway_vars = {}
    sync_vars = {}
    transfer_vars = {}

    # Define headway variables for the specified connections
    # Forward --> From either Asd or Shl to Ut ; Backward --> From Ut to either Asd or Shl (depends on the line)
    headway_vars['800', '3500', 'forward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_800_3500_forward")
    headway_vars['800', '3100', 'forward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_800_3100_forward")
    headway_vars['3000', '3500', 'forward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_3000_3500_forward")
    headway_vars['3000', '3100', 'forward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_3000_3100_forward")
    headway_vars['800', '3500', 'backward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_800_3500_backward")
    headway_vars['800', '3100', 'backward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_800_3100_backward")
    headway_vars['3000', '3500', 'backward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_3000_3500_backward")
    headway_vars['3000', '3100', 'backward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_3000_3100_backward")

    # Define synchronization variables for the specified line pairs
    sync_pairs = [
        ('800', '3000', 'Amr', 'Asd'),
        ('800', '3000', 'Asd', 'Ut'),
        ('3100', '3500', 'Shl', 'Ut'),
        ('3100', '3000', 'Ut', 'Nm'),
        ('800', '3500', 'Ut', 'Ehv'),
        ('800', '3900', 'Ehv', 'Std'),
    ]
    for line1, line2, station1, station2 in sync_pairs:
        sync_vars[(station1, station2, line1, line2, 'forward')] = model.addVar(vtype=GRB.INTEGER,
                                                                     name="sync_{}_{}_{}_{}".format(station1,
                                                                                                    station2, line1,
                                                                                                    line2))
        sync_vars[(station2, station1, line1, line2,'backward')] = model.addVar(vtype=GRB.INTEGER,
                                                                     name="sync_{}_{}_{}_{}".format(station2,
                                                                                                    station1, line1,
                                                                                                    line2))

    # Define transfer variables for the specified transfers at Ehv station
    # Forward --> Ut to Hrl ; Backward --> Hrl to Ut
    transfer_vars['800', '3900', 'forward'] = model.addVar(vtype=GRB.INTEGER, name=f"transfer_800_3900_forward")
    transfer_vars['3500', '3900', 'forward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_3500_3900_forward")
    transfer_vars['3900', '800', 'backward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_3900_800_backward")
    transfer_vars['3900', '3500', 'backward'] = model.addVar(vtype=GRB.INTEGER, name=f"head_3900_3500_backward")

    transfer_p_vars = {}
    sync_p_vars = {}
    headway_p_vars = {}

    # Add p_ij variables for transfers
    for key in transfer_vars.keys():
        transfer_p_vars[key] = model.addVar(vtype=GRB.INTEGER, name="p_transfer_{}_{}_{}".format(*key))

    # Add p_ij variables for synchronization
    for key in sync_vars.keys():
        sync_p_vars[key] = model.addVar(vtype=GRB.INTEGER, name="p_sync_{}_{}_{}_{}".format(*key))

    # Add p_ij variables for headway
    for key in headway_vars.keys():
        headway_p_vars[key] = model.addVar(vtype=GRB.INTEGER, name="p_headway_{}_{}_{}".format(*key))

    # Objective Function: Minimize the total duration of activities
    model.setObjective(
        quicksum(running_activities[activity] for activity in running_activities) +
        quicksum(dwelling_activities[activity] for activity in dwelling_activities) +
        quicksum(transfer_vars[activity] for activity in transfer_vars) +
        quicksum(headway_vars[activity] for activity in headway_vars) +
        quicksum(sync_vars[activity] for activity in sync_vars),
        GRB.MINIMIZE
    )

    # Constraints for running and dwelling activities
    for line, stations in lines_stations.items():
        for i in range(len(stations)-1):
            # Constraints for forward direction
            if ('Arrival', stations[i+1], line) in arrivals and ('Departure', stations[i], line) in departures:
                model.addConstr(
                    arrivals[('Arrival', stations[i+1], line)] - departures[('Departure', stations[i], line)] ==
                    running_activities[(stations[i], stations[i+1], line, 'forward')] -
                    T * p_ij[(stations[i], stations[i+1], line, 'forward')],
                    name=f"running_time_{stations[i]}_{stations[i+1]}_{line}_forward"
                )
            # Constraints for backward direction
            if ('Arrival', stations[i], line, 'return') in arrivals and ('Departure', stations[i+1], line, 'return') in departures:
                model.addConstr(
                    arrivals[('Arrival', stations[i], line, 'return')] - departures[('Departure', stations[i+1], line, 'return')] ==
                    running_activities[(stations[i+1], stations[i], line, 'backward')] -
                    T * p_ij[(stations[i+1], stations[i], line, 'backward')],
                    name=f"running_time_{stations[i+1]}_{stations[i]}_{line}_backward"
                )
        for i in range(1, len(stations)-1):
            # Constraints for forward direction dwell time
            model.addConstr(
                departures[('Departure', stations[i], line)] - arrivals[('Arrival', stations[i], line)] ==
                dwelling_activities[(stations[i], line, 'forward')] -
                T * p_ij[(stations[i], line, 'forward')],
                name=f"dwelling_time_{stations[i]}_{line}_forward"
            )
            # Constraints for backward direction dwell time
            model.addConstr(
                departures[('Departure', stations[i], line, 'return')] - arrivals[('Arrival', stations[i], line, 'return')] ==
                dwelling_activities[(stations[i], line, 'backward')] -
                T * p_ij[(stations[i], line, 'backward')],
                name=f"dwelling_time_{stations[i]}_{line}_backward"
            )

    # Time constraints for events (pi variables)
    for key, var in arrivals.items():
        model.addConstr(var <= T, name=f"upper_time_bound_arr_{key}")
        model.addConstr(var >= 0, name=f"lower_time_bound_arr_{key}")
    for key, var in departures.items():
        model.addConstr(var <= T, name=f"upper_time_bound_dep_{key}")
        model.addConstr(var >= 0, name=f"lower_time_bound_dep_{key}")

    # Bounds constraints for running activities (using travel times)
    for activity, variable in running_activities.items():
        i, j, line, direction = activity
        travel_time = travel_times.loc[
            (travel_times['From'] == i) & (travel_times['To'] == j), 'Travel Time'
        ].values[0]
        model.addConstr(variable == travel_time, name=f"running_time_{i}_{j}_{line}_{direction}")

    # Lower and upper bounds constraints for dwelling activities
    dwell_time_lower = 2
    dwell_time_upper = 8
    for activity, variable in dwelling_activities.items():
        model.addConstr(variable >= dwell_time_lower, name=f"dwell_time_lower_{activity}")
        model.addConstr(variable <= dwell_time_upper, name=f"dwell_time_upper_{activity}")

    # Constraints for transfer lines
    #for key, transfer_time in transfer_vars.items():
    #    line1, line2, direction = key

    #    if direction == 'forward':
    #        # For transfer from line1 to line2
    #        model.addConstr(
    #            departures[('Departure', 'Ehv', line2)] -
    #            arrivals[('Arrival', 'Ehv', line1)] ==
    #            transfer_time - T * transfer_p_vars[key],
    #            name="transfer_{}_{}_{}_time".format(line1, line2, direction)
    #        )
    #    else:
    #        # For transfer from line2 to line1 (note the reversed order for backward transfers)
    #        model.addConstr(
    #            departures[('Departure', 'Ehv', line2, 'return')] -
    #            arrivals[('Arrival', 'Ehv', line1, 'return')] ==
    #            transfer_time - T * transfer_p_vars[key],
    #            name="transfer_{}_{}_{}_time".format(line1, line2, direction)
    #        )

    # Lower and upper bounds constraints for transfer activities
    #transfer_time_lower = 2
    #transfer_time_upper = 5
    #for activity, variable in transfer_vars.items():
    #    model.addConstr(variable >= transfer_time_lower, name=f"transfer_time_lower_{activity}")
    #    model.addConstr(variable <= transfer_time_upper, name=f"transfer_time_upper_{activity}")


    # Fixed synchronization time (15 minutes)
    sync_time = 15

    for (station1, station2, line1, line2, direction), sync_var in sync_vars.items():
        # Assuming synchronization is based on departure times at station1 for both lines
        if direction == 'forward':
            model.addConstr(
                departures[('Departure', station1, line2)] -
                departures[('Departure', station1, line1)] ==
                sync_var - T * sync_p_vars[(station1, station2, line1, line2, direction)],
                name=f"sync_{line1}_{line2}_{station1}_departure"
            )
        else:
            model.addConstr(
                departures[('Departure', station1, line2, 'return')] -
                departures[('Departure', station1, line1, 'return')] ==
                sync_var - T * sync_p_vars[(station1, station2, line1, line2, direction)],
                name=f"sync_{line1}_{line2}_{station1}_departure"
            )

    # Sync constraints
    for activity, variable in sync_vars.items():
        model.addConstr(variable == sync_time, name=f"sync_time_{activity}")


    # Minimum headway time (3 minutes)
    min_headway_time = 3

    # Adding headway constraints using predefined variables
    for key, headway_var in headway_vars.items():
        line1, line2, direction = key
        # Forward direction: Considering arrivals at 'Ut'
        if direction == 'forward':
            model.addConstr(
                arrivals[('Arrival', 'Ut', line2)] -
                arrivals[('Arrival', 'Ut', line1)] ==
                headway_var - T * headway_p_vars[key],
                name=f"headway_{line1}_{line2}_forward"
            )
        # Backward direction: Considering departures from 'Ut'
        else:  # direction == 'backward'
            model.addConstr(
                departures[('Departure', 'Ut', line2, 'return')] -
                departures[('Departure', 'Ut', line1, 'return')] ==
                headway_var - T * headway_p_vars[key],
                name=f"headway_{line1}_{line2}_backward"
            )

    # Headway constraints
    for activity, variable in headway_vars.items():
        model.addConstr(variable >= min_headway_time, name=f"head_time_{activity}")

    # Set the departure time for the 3500 line at Schiphol to the ninth minute
    departures[('Departure', 'Shl', '3500')].lb = 9  # Lower bound
    departures[('Departure', 'Shl', '3500')].ub = 9  # Upper bound

    # Update model to integrate the new constraints
    model.update()

    print("Constraints:")
    for constr in model.getConstrs():
        print(f"{constr.ConstrName}: {constr.sense} {constr.RHS}")

    return model



def solve_model(model):
    # Optimize the model
    model.optimize()

    # Check the optimization status
    if model.status == GRB.OPTIMAL:
        # Store solutions in a dictionary if the model is solved optimally
        solution_dict = {var.varName: var.X for var in model.getVars()}
        cost = model.objVal
    elif model.status == GRB.INFEASIBLE:
        print("Model is infeasible.")
        model.computeIIS()  # Compute Irreducible Inconsistent Subsystem
        model.write("model.ilp")  # Write IIS to a file
        solution_dict, cost = None, None
    elif model.status == GRB.UNBOUNDED:
        print("Model is unbounded.")
        solution_dict, cost = None, None
    else:
        print(f"Optimization was stopped with status {model.status}")
        solution_dict, cost = None, None

    # Close the Gurobi model
    model.close()

    return solution_dict, cost


def get_station_order_key(row):
    # Define the station order for each line and direction
    station_order = {
        ('3000', 'North'): ['Nm', 'Ut', 'Asd', 'Amr', 'Hdr'],
        ('3000', 'South'): ['Hdr', 'Amr', 'Asd', 'Ut', 'Nm'],
        ('800', 'North'): ['Mt', 'Std', 'Ehv', 'Ut', 'Asd', 'Amr'],
        ('800', 'South'): ['Amr', 'Asd', 'Ut', 'Ehv', 'Std', 'Mt'],
        ('3100', 'North'): ['Nm', 'Ut', 'Shl'],
        ('3100', 'South'): ['Shl', 'Ut', 'Nm'],
        ('3500', 'North'): ['Vl', 'Ehv', 'Ut', 'Shl'],
        ('3500', 'South'): ['Shl', 'Ut', 'Ehv', 'Vl'],
        ('3900', 'North'): ['Hrl', 'Std', 'Ehv'],
        ('3900', 'South'): ['Ehv', 'Std', 'Hrl'],

        # Add other lines and directions as needed
    }

    # Extract the line, direction, and station from the row
    line = row['Line']
    direction = row['Direction']
    station = row['Station']

    # Use the line and direction to find the correct station order
    if (line, direction) in station_order:
        return station_order[(line, direction)].index(station)
    else:
        # If the line-direction pair is not in the station order, return a default value
        return float('inf')

def generate_readable_timetable(solution_dict):
    # Initialize a list to hold the timetable data
    timetable_data = []

    # Iterate over the solution dictionary to process departure and arrival times
    for var_name, time in solution_dict.items():
        parts = var_name.split('_')
        if parts[0] in {'dep', 'arr'}:
            event_type = 'Departure' if parts[0] == 'dep' else 'Arrival'
            station = parts[1]
            line = parts[2]
            direction = 'North' if 'return' in parts else 'South'
            # Append a tuple with the line, direction, station, type, and time
            timetable_data.append((line, direction, station, event_type, time))

    # Convert the list of tuples into a DataFrame
    timetable_df = pd.DataFrame(timetable_data, columns=['Line', 'Direction', 'Station', 'Type', 'Time'])

    # Sort the DataFrame for better readability: by Line, Direction, and Station Order
    timetable_df['StationOrder'] = timetable_df.apply(get_station_order_key, axis=1)
    timetable_df.sort_values(by=['Line', 'Direction', 'StationOrder', 'Type'], ascending=[True, True, True, True],
                             inplace=True)

    # Drop the 'StationOrder' column as it's no longer needed
    timetable_df.drop('StationOrder', axis=1, inplace=True)

    # Reset the index for the sorted DataFrame
    timetable_df.reset_index(drop=True, inplace=True)

    return timetable_df

def print_timetable(timetable_df):
    for line in timetable_df['Line'].unique():
        print(f"Line {line}:")
        for direction in ['North', 'South']:
            print(f"  Direction {direction}:")
            filtered_df = timetable_df[(timetable_df['Line'] == line) & (timetable_df['Direction'] == direction)]
            for index, row in filtered_df.iterrows():
                print(f"    {row['Type']} {row['Station']} at {int(row['Time'])} minutes")
            print()

def runMain_Normal():
    travel_times = read_basic_data()
    model = build_model(travel_times)
    solution_dict, cost = solve_model(model)

    if solution_dict:
        timetable_df = generate_readable_timetable(solution_dict)
        print_timetable(timetable_df)


if __name__ == "__main__":

    runMain_Normal()
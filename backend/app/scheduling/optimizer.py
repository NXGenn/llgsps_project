from ortools.sat.python import cp_model
from app.core.latency import estimate_transfer_time
from datetime import datetime, timedelta

def create_optimized_schedule(all_passes: list, data_demands: list):
    """
    Creates an optimal, conflict-free schedule using a CP-SAT solver.
    """
    model = cp_model.CpModel()

    # --- 1. Pre-computation and Data Structuring ---
    feasible_assignments = []
    for p_idx, p in enumerate(all_passes):
        for d_idx, d in enumerate(data_demands):
            estimation = estimate_transfer_time(p, d['data_mb'])
            if estimation and estimation['is_feasible']:
                feasible_assignments.append({
                    "pass_idx": p_idx,
                    "demand_idx": d_idx,
                    "pass": p,
                    "demand": d,
                    "duration": int(estimation['required_time_seconds'])
                })

    # --- 2. Create Solver Variables ---
    assignments = {}
    for i, a in enumerate(feasible_assignments):
        assignments[i] = model.NewBoolVar(f'assign_{i}')

    # --- 3. Define Constraints ---
    # Constraint 1: Each demand can be scheduled at most once.
    for d_idx in range(len(data_demands)):
        model.AddAtMostOne(
            assignments[i] for i, a in enumerate(feasible_assignments) if a['demand_idx'] == d_idx
        )

    # Constraint 2: The ground station cannot have overlapping contacts.
    intervals = []
    for i, a in enumerate(feasible_assignments):
        start_time = int(datetime.fromisoformat(a['pass']['rise_time']).timestamp())
        end_time = start_time + a['duration']
        
        # ---- THIS IS THE FIX ----
        # Add a unique name as the last argument, like f'interval_{i}'
        intervals.append(model.NewOptionalIntervalVar(
            start_time, a['duration'], end_time, assignments[i], f'interval_{i}'
        ))
        # ---- END OF FIX ----
        
    model.AddNoOverlap(intervals)

    # --- 4. Define the Objective ---
    # We need to handle potential empty lists for the sum
    total_mb_possible = sum(d['data_mb'] for d in data_demands) if data_demands else 0
    total_data_scheduled = model.NewIntVar(0, int(total_mb_possible), 'total_data')
    
    model.Add(total_data_scheduled == sum(
        int(a['demand']['data_mb']) * assignments[i] for i, a in enumerate(feasible_assignments)
    ))
    model.Maximize(total_data_scheduled)

    # --- 5. Solve the Model ---
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # --- 6. Extract the Solution ---
    scheduled_contacts = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        scheduled_demand_indices = set()
        for i, a in enumerate(feasible_assignments):
            if solver.BooleanValue(assignments[i]):
                start_dt = datetime.fromisoformat(a['pass']['rise_time'])
                scheduled_contacts.append({
                    "satellite": a['demand']['satellite'],
                    "ground_station": "ISTRAC Bangalore",
                    "demand_mb": a['demand']['data_mb'],
                    "start_time": a['pass']['rise_time'],
                    "end_time": (start_dt + timedelta(seconds=a['duration'])).isoformat() + "Z",
                    "duration_seconds": a['duration']
                })
                scheduled_demand_indices.add(a['demand_idx'])
    
    unscheduled_demands = [d for idx, d in enumerate(data_demands) if idx not in scheduled_demand_indices]

    return sorted(scheduled_contacts, key=lambda x: x['start_time']), unscheduled_demands
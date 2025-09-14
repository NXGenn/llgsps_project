from ortools.sat.python import cp_model
from app.core.latency import LatencyEstimator, estimate_transfer_time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizationObjective(Enum):
    """Enumeration of available optimization objectives."""
    MAXIMIZE_DATA_THROUGHPUT = "maximize_data"
    MINIMIZE_SCHEDULE_SPAN = "minimize_span"
    MAXIMIZE_PRIORITY_WEIGHTED = "maximize_priority"
    BALANCE_EFFICIENCY_FAIRNESS = "balance_efficiency"

@dataclass
class SchedulingConstraint:
    """Represents a scheduling constraint."""
    constraint_type: str
    parameters: Dict[str, Any]
    weight: float = 1.0
    is_hard_constraint: bool = True

@dataclass
class OptimizationResult:
    """Comprehensive optimization result container."""
    scheduled_contacts: List[Dict]
    unscheduled_demands: List[Dict]
    optimization_status: str
    objective_value: float
    solve_time_seconds: float
    total_data_scheduled: float
    schedule_efficiency: float
    resource_utilization: float
    constraint_violations: List[str]
    solution_quality: str

class AdvancedSchedulingOptimizer:
    """
    Advanced scheduling optimizer with multiple algorithms and objectives.
    Provides comprehensive optimization capabilities for satellite ground station scheduling.
    """
    
    def __init__(self):
        self.latency_estimator = LatencyEstimator()
        self.solver_timeout_seconds = 300  # 5 minutes default
        self.solution_pool_size = 10
        
    def preprocess_scheduling_data(self, passes: List[Dict], demands: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Preprocess and validate scheduling data.
        
        Args:
            passes: List of satellite passes
            demands: List of data demands
            
        Returns:
            Tuple of (feasible_assignments, metadata)
        """
        feasible_assignments = []
        metadata = {
            "total_passes": len(passes),
            "total_demands": len(demands),
            "feasible_combinations": 0,
            "infeasible_combinations": 0
        }
        
        for p_idx, pass_info in enumerate(passes):
            for d_idx, demand in enumerate(demands):
                # Use enhanced latency estimation
                estimation = self.latency_estimator.estimate_transfer_time_detailed(
                    pass_info, demand['data_mb']
                )
                
                if estimation and estimation['is_feasible']:
                    assignment = {
                        "pass_idx": p_idx,
                        "demand_idx": d_idx,
                        "pass": pass_info,
                        "demand": demand,
                        "duration_seconds": int(estimation['total_required_time_seconds']),
                        "data_efficiency": estimation['data_efficiency'],
                        "pass_utilization": estimation['pass_utilization'],
                        "effective_data_rate": estimation['effective_data_rate_mbps'],
                        "priority": demand.get('priority', 1.0),
                        "deadline": demand.get('deadline'),
                        "estimation_details": estimation
                    }
                    feasible_assignments.append(assignment)
                    metadata["feasible_combinations"] += 1
                else:
                    metadata["infeasible_combinations"] += 1
        
        logger.info(f"Preprocessing complete: {metadata['feasible_combinations']} feasible assignments from {metadata['total_passes']} passes and {metadata['total_demands']} demands")
        
        return feasible_assignments, metadata

    def create_cp_sat_model(self, feasible_assignments: List[Dict], 
                           objective: OptimizationObjective = OptimizationObjective.MAXIMIZE_DATA_THROUGHPUT,
                           constraints: List[SchedulingConstraint] = None) -> Tuple[cp_model.CpModel, Dict]:
        """
        Create a CP-SAT optimization model with advanced constraints and objectives.
        
        Args:
            feasible_assignments: List of feasible pass-demand assignments
            objective: Optimization objective
            constraints: Additional scheduling constraints
            
        Returns:
            Tuple of (model, variables_dict)
        """
        model = cp_model.CpModel()
        variables = {}
        
        # Create assignment variables
        assignment_vars = {}
        for i, assignment in enumerate(feasible_assignments):
            var_name = f'assign_{i}'
            assignment_vars[i] = model.NewBoolVar(var_name)
        
        variables['assignments'] = assignment_vars
        
        # Constraint 1: Each demand can be scheduled at most once
        demand_constraints = {}
        for d_idx in set(a['demand_idx'] for a in feasible_assignments):
            relevant_assignments = [
                assignment_vars[i] for i, a in enumerate(feasible_assignments) 
                if a['demand_idx'] == d_idx
            ]
            model.AddAtMostOne(relevant_assignments)
            demand_constraints[d_idx] = relevant_assignments
        
        # Constraint 2: No overlapping contacts (ground station availability)
        intervals = []
        for i, assignment in enumerate(feasible_assignments):
            start_time = int(datetime.fromisoformat(assignment['pass']['rise_time']).timestamp())
            duration = assignment['duration_seconds']
            end_time = start_time + duration
            
            interval = model.NewOptionalIntervalVar(
                start_time, duration, end_time, assignment_vars[i], f'interval_{i}'
            )
            intervals.append(interval)
        
        model.AddNoOverlap(intervals)
        variables['intervals'] = intervals
        
        # Constraint 3: Priority-based scheduling constraints
        if constraints:
            self._add_custom_constraints(model, assignment_vars, feasible_assignments, constraints)
        
        # Constraint 4: Deadline constraints
        self._add_deadline_constraints(model, assignment_vars, feasible_assignments)
        
        # Define objective based on selected strategy
        self._set_optimization_objective(model, assignment_vars, feasible_assignments, objective)
        
        variables['feasible_assignments'] = feasible_assignments
        
        return model, variables

    def _add_custom_constraints(self, model: cp_model.CpModel, assignment_vars: Dict, 
                               feasible_assignments: List[Dict], constraints: List[SchedulingConstraint]):
        """Add custom scheduling constraints to the model."""
        for constraint in constraints:
            if constraint.constraint_type == "minimum_gap":
                # Minimum gap between consecutive contacts
                min_gap_seconds = constraint.parameters.get("gap_seconds", 300)
                # Implementation would add gap constraints between intervals
                
            elif constraint.constraint_type == "maximum_contacts_per_satellite":
                # Limit contacts per satellite
                max_contacts = constraint.parameters.get("max_contacts", 5)
                satellite_groups = {}
                
                for i, assignment in enumerate(feasible_assignments):
                    sat_name = assignment['demand']['satellite']
                    if sat_name not in satellite_groups:
                        satellite_groups[sat_name] = []
                    satellite_groups[sat_name].append(assignment_vars[i])
                
                for sat_name, sat_vars in satellite_groups.items():
                    model.Add(sum(sat_vars) <= max_contacts)
            
            elif constraint.constraint_type == "priority_ordering":
                # Higher priority demands should be scheduled first when possible
                # This is handled in the objective function
                pass

    def _add_deadline_constraints(self, model: cp_model.CpModel, assignment_vars: Dict, 
                                 feasible_assignments: List[Dict]):
        """Add deadline constraints to ensure time-critical demands are met."""
        current_time = datetime.now()
        
        for i, assignment in enumerate(feasible_assignments):
            deadline = assignment['demand'].get('deadline')
            if deadline:
                deadline_dt = datetime.fromisoformat(deadline) if isinstance(deadline, str) else deadline
                pass_time = datetime.fromisoformat(assignment['pass']['rise_time'])
                
                # If pass is after deadline, don't allow this assignment
                if pass_time > deadline_dt:
                    model.Add(assignment_vars[i] == 0)

    def _set_optimization_objective(self, model: cp_model.CpModel, assignment_vars: Dict, 
                                   feasible_assignments: List[Dict], objective: OptimizationObjective):
        """Set the optimization objective based on the selected strategy."""
        
        if objective == OptimizationObjective.MAXIMIZE_DATA_THROUGHPUT:
            # Maximize total data scheduled
            total_data = sum(
                int(assignment['demand']['data_mb']) * assignment_vars[i]
                for i, assignment in enumerate(feasible_assignments)
            )
            model.Maximize(total_data)
            
        elif objective == OptimizationObjective.MAXIMIZE_PRIORITY_WEIGHTED:
            # Maximize priority-weighted data throughput
            weighted_value = sum(
                int(assignment['demand']['data_mb'] * assignment['priority']) * assignment_vars[i]
                for i, assignment in enumerate(feasible_assignments)
            )
            model.Maximize(weighted_value)
            
        elif objective == OptimizationObjective.BALANCE_EFFICIENCY_FAIRNESS:
            # Balance between efficiency and fairness
            efficiency_component = sum(
                int(assignment['data_efficiency'] * 1000) * assignment_vars[i]
                for i, assignment in enumerate(feasible_assignments)
            )
            
            data_component = sum(
                int(assignment['demand']['data_mb']) * assignment_vars[i]
                for i, assignment in enumerate(feasible_assignments)
            )
            
            # Weighted combination
            model.Maximize(efficiency_component + data_component)
            
        else:  # Default to data throughput
            total_data = sum(
                int(assignment['demand']['data_mb']) * assignment_vars[i]
                for i, assignment in enumerate(feasible_assignments)
            )
            model.Maximize(total_data)

    def solve_optimization_model(self, model: cp_model.CpModel, variables: Dict) -> OptimizationResult:
        """
        Solve the optimization model and return comprehensive results.
        
        Args:
            model: The CP-SAT model to solve
            variables: Dictionary containing model variables
            
        Returns:
            OptimizationResult with detailed solution information
        """
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.solver_timeout_seconds
        solver.parameters.num_search_workers = 4  # Parallel solving
        
        start_time = datetime.now()
        status = solver.Solve(model)
        solve_time = (datetime.now() - start_time).total_seconds()
        
        # Extract solution
        scheduled_contacts = []
        scheduled_demand_indices = set()
        total_data_scheduled = 0
        
        assignment_vars = variables['assignments']
        feasible_assignments = variables['feasible_assignments']
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for i, assignment in enumerate(feasible_assignments):
                if solver.BooleanValue(assignment_vars[i]):
                    start_dt = datetime.fromisoformat(assignment['pass']['rise_time'])
                    end_dt = start_dt + timedelta(seconds=assignment['duration_seconds'])
                    
                    contact = {
                        "satellite": assignment['demand']['satellite'],
                        "ground_station": "ISTRAC Bangalore",  # TODO: Make configurable
                        "demand_mb": assignment['demand']['data_mb'],
                        "start_time": assignment['pass']['rise_time'],
                        "end_time": end_dt.isoformat() + "Z",
                        "duration_seconds": assignment['duration_seconds'],
                        "data_efficiency": assignment['data_efficiency'],
                        "pass_utilization": assignment['pass_utilization'],
                        "effective_data_rate_mbps": assignment['effective_data_rate'],
                        "priority": assignment['priority'],
                        "estimation_details": assignment['estimation_details']
                    }
                    
                    scheduled_contacts.append(contact)
                    scheduled_demand_indices.add(assignment['demand_idx'])
                    total_data_scheduled += assignment['demand']['data_mb']
        
        # Identify unscheduled demands
        all_demands = list(set(a['demand'] for a in feasible_assignments))
        unscheduled_demands = [
            demand for i, demand in enumerate(all_demands) 
            if i not in scheduled_demand_indices
        ]
        
        # Calculate metrics
        total_possible_data = sum(d['data_mb'] for d in all_demands)
        schedule_efficiency = total_data_scheduled / total_possible_data if total_possible_data > 0 else 0
        
        # Determine solution quality
        if status == cp_model.OPTIMAL:
            solution_quality = "OPTIMAL"
        elif status == cp_model.FEASIBLE:
            solution_quality = "FEASIBLE"
        else:
            solution_quality = "INFEASIBLE"
        
        return OptimizationResult(
            scheduled_contacts=sorted(scheduled_contacts, key=lambda x: x['start_time']),
            unscheduled_demands=unscheduled_demands,
            optimization_status=solver.StatusName(status),
            objective_value=solver.ObjectiveValue() if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0,
            solve_time_seconds=solve_time,
            total_data_scheduled=total_data_scheduled,
            schedule_efficiency=schedule_efficiency,
            resource_utilization=len(scheduled_contacts) / len(feasible_assignments) if feasible_assignments else 0,
            constraint_violations=[],  # TODO: Implement constraint violation detection
            solution_quality=solution_quality
        )

    def create_advanced_schedule(self, passes: List[Dict], demands: List[Dict],
                               objective: OptimizationObjective = OptimizationObjective.MAXIMIZE_DATA_THROUGHPUT,
                               constraints: List[SchedulingConstraint] = None,
                               solver_timeout: int = None) -> OptimizationResult:
        """
        Create an advanced optimized schedule with comprehensive analysis.
        
        Args:
            passes: List of satellite passes
            demands: List of data demands
            objective: Optimization objective
            constraints: Additional scheduling constraints
            solver_timeout: Solver timeout in seconds
            
        Returns:
            OptimizationResult with detailed scheduling solution
        """
        if solver_timeout:
            self.solver_timeout_seconds = solver_timeout
        
        # Preprocess data
        feasible_assignments, metadata = self.preprocess_scheduling_data(passes, demands)
        
        if not feasible_assignments:
            logger.warning("No feasible assignments found")
            return OptimizationResult(
                scheduled_contacts=[],
                unscheduled_demands=demands,
                optimization_status="NO_FEASIBLE_ASSIGNMENTS",
                objective_value=0,
                solve_time_seconds=0,
                total_data_scheduled=0,
                schedule_efficiency=0,
                resource_utilization=0,
                constraint_violations=[],
                solution_quality="INFEASIBLE"
            )
        
        # Create and solve model
        model, variables = self.create_cp_sat_model(feasible_assignments, objective, constraints)
        result = self.solve_optimization_model(model, variables)
        
        logger.info(f"Optimization complete: {result.solution_quality} solution with {len(result.scheduled_contacts)} contacts")
        logger.info(f"Data scheduled: {result.total_data_scheduled} MB, Efficiency: {result.schedule_efficiency:.2%}")
        
        return result

    def compare_scheduling_strategies(self, passes: List[Dict], demands: List[Dict]) -> Dict[str, OptimizationResult]:
        """
        Compare different scheduling strategies and return results for analysis.
        
        Args:
            passes: List of satellite passes
            demands: List of data demands
            
        Returns:
            Dictionary mapping strategy names to OptimizationResult objects
        """
        strategies = {
            "maximize_data": OptimizationObjective.MAXIMIZE_DATA_THROUGHPUT,
            "priority_weighted": OptimizationObjective.MAXIMIZE_PRIORITY_WEIGHTED,
            "balanced_efficiency": OptimizationObjective.BALANCE_EFFICIENCY_FAIRNESS
        }
        
        results = {}
        for strategy_name, objective in strategies.items():
            logger.info(f"Testing strategy: {strategy_name}")
            result = self.create_advanced_schedule(passes, demands, objective)
            results[strategy_name] = result
        
        return results


# Maintain backward compatibility
def create_optimized_schedule(all_passes: List[Dict], data_demands: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Legacy function for backward compatibility.
    Uses the advanced optimizer with default settings.
    """
    optimizer = AdvancedSchedulingOptimizer()
    result = optimizer.create_advanced_schedule(all_passes, data_demands)
    
    # Convert to legacy format
    scheduled_contacts = []
    for contact in result.scheduled_contacts:
        legacy_contact = {
            "satellite": contact["satellite"],
            "ground_station": contact["ground_station"],
            "demand_mb": contact["demand_mb"],
            "start_time": contact["start_time"],
            "end_time": contact["end_time"],
            "duration_seconds": contact["duration_seconds"]
        }
        scheduled_contacts.append(legacy_contact)
    
    return scheduled_contacts, result.unscheduled_demands


# Create a global instance for easy access
advanced_optimizer = AdvancedSchedulingOptimizer()
#!/usr/bin/env python3
"""
Enhanced demonstration of the LLGSPS Scheduling System.
Showcases advanced optimization capabilities and comprehensive analysis.
"""

from app.core.ground_station import load_ground_stations
from app.core.satellite import find_satellite_passes
from app.scheduling.baseline import create_baseline_schedule
from app.scheduling.optimizer import (
    AdvancedSchedulingOptimizer, 
    OptimizationObjective, 
    SchedulingConstraint
)
from app.core.latency import LatencyEstimator
from datetime import datetime, timedelta
import time
import json

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_section(title):
    """Print a formatted section header."""
    print(f"\n--- {title} ---")

def print_contact_details(contacts, title="Scheduled Contacts"):
    """Print detailed contact information."""
    if not contacts:
        print(f"  No {title.lower()}")
        return
    
    print(f"\n{title}:")
    total_data = 0
    
    for i, contact in enumerate(contacts):
        start_time = datetime.fromisoformat(contact['start_time'].replace('Z', ''))
        duration_min = contact['duration_seconds'] / 60
        total_data += contact['demand_mb']
        
        print(f"  Contact {i+1}:")
        print(f"    Data: {contact['demand_mb']} MB")
        print(f"    Time: {start_time.strftime('%H:%M:%S')} ({duration_min:.1f} min)")
        
        # Enhanced details if available
        if 'data_efficiency' in contact:
            print(f"    Efficiency: {contact['data_efficiency']:.3f}")
        if 'effective_data_rate_mbps' in contact:
            print(f"    Data Rate: {contact['effective_data_rate_mbps']:.1f} Mbps")
        if 'priority' in contact:
            print(f"    Priority: {contact['priority']:.1f}")
    
    print(f"\n  Total Data Scheduled: {total_data} MB")

def demonstrate_latency_analysis():
    """Demonstrate enhanced latency analysis capabilities."""
    print_header("ENHANCED LATENCY ANALYSIS DEMONSTRATION")
    
    estimator = LatencyEstimator()
    
    # Create sample passes with different characteristics
    now = datetime.now()
    passes = [
        {
            'name': 'Short Pass',
            'rise_time': now.isoformat() + 'Z',
            'culmination_time': (now + timedelta(minutes=3)).isoformat() + 'Z',
            'set_time': (now + timedelta(minutes=6)).isoformat() + 'Z'
        },
        {
            'name': 'Medium Pass',
            'rise_time': (now + timedelta(hours=4)).isoformat() + 'Z',
            'culmination_time': (now + timedelta(hours=4, minutes=5)).isoformat() + 'Z',
            'set_time': (now + timedelta(hours=4, minutes=10)).isoformat() + 'Z'
        },
        {
            'name': 'Long Pass',
            'rise_time': (now + timedelta(hours=8)).isoformat() + 'Z',
            'culmination_time': (now + timedelta(hours=8, minutes=7)).isoformat() + 'Z',
            'set_time': (now + timedelta(hours=8, minutes=14)).isoformat() + 'Z'
        }
    ]
    
    data_demand = 750  # MB
    
    print(f"Analyzing passes for {data_demand} MB data transfer:")
    
    for pass_info in passes:
        print(f"\n{pass_info['name']}:")
        
        # Test under different weather conditions
        weather_conditions = ['clear', 'light_clouds', 'rain']
        
        for weather in weather_conditions:
            result = estimator.estimate_transfer_time_detailed(
                pass_info, data_demand, weather_condition=weather
            )
            
            if result:
                status = "✅ FEASIBLE" if result['is_feasible'] else "❌ INFEASIBLE"
                print(f"  {weather.upper():12}: {status} | "
                      f"Rate: {result['effective_data_rate_mbps']:5.1f} Mbps | "
                      f"Time: {result['total_required_time_seconds']:6.1f}s | "
                      f"Efficiency: {result['data_efficiency']:.3f}")
    
    # Demonstrate optimal pass selection
    print_section("Optimal Pass Selection")
    optimal = estimator.get_optimal_pass(passes, data_demand)
    
    if optimal:
        print(f"Best pass for {data_demand} MB:")
        print(f"  Duration: {optimal['pass_duration_seconds']:.0f}s")
        print(f"  Required: {optimal['total_required_time_seconds']:.1f}s")
        print(f"  Efficiency: {optimal['data_efficiency']:.3f}")
        print(f"  Utilization: {optimal['pass_utilization']:.3f}")
    else:
        print(f"No feasible pass found for {data_demand} MB")

def demonstrate_baseline_vs_enhanced():
    """Compare baseline scheduler with enhanced optimization."""
    print_header("BASELINE vs ENHANCED OPTIMIZATION COMPARISON")
    
    # Load real satellite data
    stations = load_ground_stations()
    if not stations:
        print("❌ No ground stations available")
        return
    
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=1)
    
    if not passes:
        print("❌ No satellite passes found")
        return
    
    print(f"Found {len(passes)} ISS passes over the next 24 hours")
    
    # Create challenging demand scenario
    demands = [
        {"satellite": "ISS", "data_mb": 200, "priority": 1.0},
        {"satellite": "ISS", "data_mb": 800, "priority": 3.0},  # Large, high priority
        {"satellite": "ISS", "data_mb": 300, "priority": 1.5},
        {"satellite": "ISS", "data_mb": 600, "priority": 2.0},
        {"satellite": "ISS", "data_mb": 150, "priority": 1.0},
        {"satellite": "ISS", "data_mb": 450, "priority": 2.5},
    ]
    
    total_demand = sum(d['data_mb'] for d in demands)
    print(f"Total data demand: {total_demand} MB across {len(demands)} requests")
    
    # Run baseline scheduler
    print_section("Baseline (Greedy) Scheduler Results")
    start_time = time.time()
    baseline_scheduled, baseline_unscheduled = create_baseline_schedule(passes, demands)
    baseline_time = time.time() - start_time
    
    baseline_data = sum(c['demand_mb'] for c in baseline_scheduled)
    print(f"  Execution Time: {baseline_time:.3f}s")
    print(f"  Contacts Scheduled: {len(baseline_scheduled)}")
    print(f"  Data Scheduled: {baseline_data} MB ({baseline_data/total_demand:.1%})")
    print(f"  Unscheduled Demands: {len(baseline_unscheduled)}")
    
    if baseline_unscheduled:
        unscheduled_data = sum(d['data_mb'] for d in baseline_unscheduled)
        print(f"  Unscheduled Data: {unscheduled_data} MB")
    
    # Run enhanced optimizer
    print_section("Enhanced Optimizer Results")
    optimizer = AdvancedSchedulingOptimizer()
    
    start_time = time.time()
    enhanced_result = optimizer.create_advanced_schedule(
        passes, demands, 
        objective=OptimizationObjective.MAXIMIZE_PRIORITY_WEIGHTED
    )
    enhanced_time = time.time() - start_time
    
    print(f"  Execution Time: {enhanced_time:.3f}s")
    print(f"  Optimization Status: {enhanced_result.optimization_status}")
    print(f"  Solution Quality: {enhanced_result.solution_quality}")
    print(f"  Contacts Scheduled: {len(enhanced_result.scheduled_contacts)}")
    print(f"  Data Scheduled: {enhanced_result.total_data_scheduled} MB "
          f"({enhanced_result.schedule_efficiency:.1%})")
    print(f"  Resource Utilization: {enhanced_result.resource_utilization:.3f}")
    print(f"  Unscheduled Demands: {len(enhanced_result.unscheduled_demands)}")
    
    # Performance comparison
    print_section("Performance Comparison")
    data_improvement = enhanced_result.total_data_scheduled - baseline_data
    contact_improvement = len(enhanced_result.scheduled_contacts) - len(baseline_scheduled)
    
    print(f"  Data Throughput Improvement: {data_improvement:+.0f} MB "
          f"({data_improvement/baseline_data*100:+.1f}%)" if baseline_data > 0 else "N/A")
    print(f"  Contact Count Change: {contact_improvement:+d}")
    print(f"  Execution Time Ratio: {enhanced_time/baseline_time:.1f}x" if baseline_time > 0 else "N/A")
    
    if data_improvement > 0:
        print(f"  ✅ Enhanced optimizer achieved {data_improvement} MB additional throughput!")
    elif data_improvement == 0:
        print(f"  ⚖️  Both schedulers achieved the same throughput")
    else:
        print(f"  ⚠️  Baseline scheduler performed better in this scenario")
    
    # Show detailed schedules
    print_contact_details(baseline_scheduled, "Baseline Schedule")
    print_contact_details(enhanced_result.scheduled_contacts, "Enhanced Schedule")

def demonstrate_advanced_features():
    """Demonstrate advanced optimization features."""
    print_header("ADVANCED OPTIMIZATION FEATURES DEMONSTRATION")
    
    stations = load_ground_stations()
    if not stations: return
    
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=2)
    
    # Create demands with deadlines and priorities
    now = datetime.now()
    demands = [
        {
            "satellite": "ISS", 
            "data_mb": 400, 
            "priority": 3.0,
            "deadline": (now + timedelta(hours=8)).isoformat()
        },
        {
            "satellite": "ISS", 
            "data_mb": 600, 
            "priority": 1.0,
            "deadline": (now + timedelta(hours=24)).isoformat()
        },
        {
            "satellite": "ISS", 
            "data_mb": 300, 
            "priority": 2.0
        },
        {
            "satellite": "ISS", 
            "data_mb": 500, 
            "priority": 2.5,
            "deadline": (now + timedelta(hours=12)).isoformat()
        },
    ]
    
    optimizer = AdvancedSchedulingOptimizer()
    
    # Test multiple optimization objectives
    objectives = [
        (OptimizationObjective.MAXIMIZE_DATA_THROUGHPUT, "Data Throughput"),
        (OptimizationObjective.MAXIMIZE_PRIORITY_WEIGHTED, "Priority Weighted"),
        (OptimizationObjective.BALANCE_EFFICIENCY_FAIRNESS, "Balanced Efficiency"),
    ]
    
    print_section("Multi-Objective Optimization Comparison")
    
    results = {}
    for objective, name in objectives:
        result = optimizer.create_advanced_schedule(passes, demands, objective)
        results[name] = result
        
        avg_priority = 0
        if result.scheduled_contacts:
            avg_priority = sum(c.get('priority', 1.0) for c in result.scheduled_contacts) / len(result.scheduled_contacts)
        
        print(f"\n{name}:")
        print(f"  Data: {result.total_data_scheduled:6.0f} MB")
        print(f"  Contacts: {len(result.scheduled_contacts):2d}")
        print(f"  Efficiency: {result.schedule_efficiency:6.1%}")
        print(f"  Avg Priority: {avg_priority:4.2f}")
        print(f"  Solve Time: {result.solve_time_seconds:6.3f}s")
    
    # Test with constraints
    print_section("Constraint-Based Scheduling")
    
    constraints = [
        SchedulingConstraint("minimum_gap", {"gap_seconds": 600}),  # 10 min gap
        SchedulingConstraint("maximum_contacts_per_satellite", {"max_contacts": 2}),
    ]
    
    constrained_result = optimizer.create_advanced_schedule(
        passes, demands, 
        objective=OptimizationObjective.MAXIMIZE_DATA_THROUGHPUT,
        constraints=constraints
    )
    
    unconstrained_result = results["Data Throughput"]
    
    print(f"Without Constraints: {unconstrained_result.total_data_scheduled:.0f} MB, "
          f"{len(unconstrained_result.scheduled_contacts)} contacts")
    print(f"With Constraints:    {constrained_result.total_data_scheduled:.0f} MB, "
          f"{len(constrained_result.scheduled_contacts)} contacts")
    
    constraint_impact = unconstrained_result.total_data_scheduled - constrained_result.total_data_scheduled
    print(f"Constraint Impact:   -{constraint_impact:.0f} MB reduction")
    
    # Strategy comparison
    print_section("Automated Strategy Comparison")
    comparison = optimizer.compare_scheduling_strategies(passes, demands)
    
    print(f"{'Strategy':<20} {'Data (MB)':<10} {'Contacts':<9} {'Efficiency':<10} {'Time (s)'}")
    print("-" * 70)
    
    best_data = 0
    best_strategy = ""
    
    for strategy_name, result in comparison.items():
        print(f"{strategy_name:<20} {result.total_data_scheduled:<10.0f} "
              f"{len(result.scheduled_contacts):<9} {result.schedule_efficiency:<10.1%} "
              f"{result.solve_time_seconds:<8.3f}")
        
        if result.total_data_scheduled > best_data:
            best_data = result.total_data_scheduled
            best_strategy = strategy_name
    
    print(f"\n🏆 Best Strategy: {best_strategy} ({best_data:.0f} MB)")

def demonstrate_real_world_scenario():
    """Demonstrate a realistic operational scenario."""
    print_header("REAL-WORLD OPERATIONAL SCENARIO")
    
    stations = load_ground_stations()
    if not stations: return
    
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=1)
    
    print("Scenario: Mission Control needs to schedule urgent data downloads")
    print("from the International Space Station over the next 24 hours.")
    
    # Realistic demand scenario
    now = datetime.now()
    demands = [
        {
            "satellite": "ISS",
            "data_mb": 250,
            "priority": 3.0,
            "deadline": (now + timedelta(hours=6)).isoformat(),
            "description": "Critical experiment data"
        },
        {
            "satellite": "ISS",
            "data_mb": 800,
            "priority": 2.0,
            "deadline": (now + timedelta(hours=18)).isoformat(),
            "description": "Earth observation imagery"
        },
        {
            "satellite": "ISS",
            "data_mb": 150,
            "priority": 1.0,
            "description": "Routine telemetry"
        },
        {
            "satellite": "ISS",
            "data_mb": 600,
            "priority": 2.5,
            "deadline": (now + timedelta(hours=12)).isoformat(),
            "description": "Medical research data"
        },
        {
            "satellite": "ISS",
            "data_mb": 300,
            "priority": 1.5,
            "description": "Educational outreach content"
        },
    ]
    
    total_demand = sum(d['data_mb'] for d in demands)
    urgent_demands = [d for d in demands if d.get('deadline')]
    
    print(f"\nDemand Summary:")
    print(f"  Total Data: {total_demand} MB")
    print(f"  Total Requests: {len(demands)}")
    print(f"  Urgent (with deadlines): {len(urgent_demands)}")
    print(f"  Available Passes: {len(passes)}")
    
    # Show demand details
    print(f"\nData Transfer Requests:")
    for i, demand in enumerate(demands):
        deadline_str = ""
        if demand.get('deadline'):
            deadline_dt = datetime.fromisoformat(demand['deadline'])
            hours_until = (deadline_dt - now).total_seconds() / 3600
            deadline_str = f" (deadline in {hours_until:.1f}h)"
        
        print(f"  {i+1}. {demand['description']}: {demand['data_mb']} MB, "
              f"Priority {demand['priority']:.1f}{deadline_str}")
    
    # Run optimization
    optimizer = AdvancedSchedulingOptimizer()
    result = optimizer.create_advanced_schedule(
        passes, demands,
        objective=OptimizationObjective.MAXIMIZE_PRIORITY_WEIGHTED
    )
    
    print_section("Optimization Results")
    print(f"Status: {result.optimization_status}")
    print(f"Solution Quality: {result.solution_quality}")
    print(f"Data Scheduled: {result.total_data_scheduled} MB ({result.schedule_efficiency:.1%})")
    print(f"Contacts: {len(result.scheduled_contacts)}")
    print(f"Solve Time: {result.solve_time_seconds:.3f}s")
    
    # Analyze results
    if result.scheduled_contacts:
        print(f"\n📅 Scheduled Operations:")
        
        for i, contact in enumerate(result.scheduled_contacts):
            start_time = datetime.fromisoformat(contact['start_time'].replace('Z', ''))
            duration_min = contact['duration_seconds'] / 60
            
            # Find original demand for description
            description = "Unknown"
            for demand in demands:
                if demand['data_mb'] == contact['demand_mb']:
                    description = demand.get('description', 'Unknown')
                    break
            
            print(f"  Contact {i+1}: {start_time.strftime('%H:%M')} "
                  f"({duration_min:.1f} min) - {contact['demand_mb']} MB")
            print(f"    {description}")
            print(f"    Priority: {contact.get('priority', 1.0):.1f}, "
                  f"Efficiency: {contact.get('data_efficiency', 0):.3f}")
    
    if result.unscheduled_demands:
        print(f"\n⚠️  Unscheduled Requests ({len(result.unscheduled_demands)}):")
        for demand in result.unscheduled_demands:
            description = demand.get('description', 'Unknown')
            print(f"  - {description}: {demand['data_mb']} MB (Priority {demand['priority']:.1f})")
    
    # Mission success analysis
    urgent_scheduled = 0
    urgent_total = 0
    
    for demand in demands:
        if demand.get('deadline'):
            urgent_total += demand['data_mb']
            # Check if this urgent demand was scheduled
            for contact in result.scheduled_contacts:
                if contact['demand_mb'] == demand['data_mb']:
                    urgent_scheduled += demand['data_mb']
                    break
    
    print_section("Mission Success Analysis")
    print(f"Overall Data Success: {result.schedule_efficiency:.1%}")
    if urgent_total > 0:
        urgent_success = urgent_scheduled / urgent_total
        print(f"Urgent Data Success: {urgent_success:.1%} ({urgent_scheduled}/{urgent_total} MB)")
    
    if result.schedule_efficiency >= 0.8:
        print("🎯 MISSION SUCCESS: High data throughput achieved!")
    elif result.schedule_efficiency >= 0.6:
        print("✅ MISSION ACCEPTABLE: Good data throughput achieved")
    else:
        print("⚠️  MISSION CHALLENGING: Limited data throughput")

def main():
    """Run the enhanced demonstration."""
    print("🛰️  LLGSPS - Low Latency Ground Station Pass Scheduler")
    print("Enhanced Demonstration with Advanced Optimization")
    print(f"Demonstration started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        demonstrate_latency_analysis()
        time.sleep(2)  # Pause for readability
        
        demonstrate_baseline_vs_enhanced()
        time.sleep(2)
        
        demonstrate_advanced_features()
        time.sleep(2)
        
        demonstrate_real_world_scenario()
        
        print_header("DEMONSTRATION COMPLETE")
        print("🎉 All advanced features demonstrated successfully!")
        print("\nKey Capabilities Shown:")
        print("  ✅ Enhanced latency modeling with weather effects")
        print("  ✅ Multi-objective optimization strategies")
        print("  ✅ Constraint-based scheduling")
        print("  ✅ Deadline-aware planning")
        print("  ✅ Priority-weighted optimization")
        print("  ✅ Real-world scenario handling")
        print("  ✅ Comprehensive performance analysis")
        
    except Exception as e:
        print(f"\n❌ DEMONSTRATION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
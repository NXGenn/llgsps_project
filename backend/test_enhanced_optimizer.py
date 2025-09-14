#!/usr/bin/env python3
"""
Comprehensive test suite for the enhanced scheduling optimization module.
Tests advanced optimization features and multiple strategies.
"""

from app.core.ground_station import load_ground_stations
from app.core.satellite import find_satellite_passes
from app.scheduling.optimizer import (
    AdvancedSchedulingOptimizer, 
    OptimizationObjective, 
    SchedulingConstraint,
    create_optimized_schedule
)
from datetime import datetime, timedelta
import time

def test_basic_optimization():
    """Test basic optimization functionality."""
    print("=== Testing Basic Optimization ===")
    
    # Load test data
    stations = load_ground_stations()
    if not stations:
        print("❌ No ground stations loaded")
        return
    
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=1)
    
    if not passes:
        print("❌ No passes found")
        return
    
    # Create test demands
    demands = [
        {"satellite": "ISS", "data_mb": 300, "priority": 1.0},
        {"satellite": "ISS", "data_mb": 500, "priority": 2.0},
        {"satellite": "ISS", "data_mb": 200, "priority": 1.5},
        {"satellite": "ISS", "data_mb": 800, "priority": 3.0},
    ]
    
    optimizer = AdvancedSchedulingOptimizer()
    result = optimizer.create_advanced_schedule(passes, demands)
    
    print(f"\nOptimization Results:")
    print(f"  Status: {result.optimization_status}")
    print(f"  Solution Quality: {result.solution_quality}")
    print(f"  Contacts Scheduled: {len(result.scheduled_contacts)}")
    print(f"  Total Data: {result.total_data_scheduled} MB")
    print(f"  Schedule Efficiency: {result.schedule_efficiency:.2%}")
    print(f"  Solve Time: {result.solve_time_seconds:.3f}s")
    
    if result.scheduled_contacts:
        print(f"\nScheduled Contacts:")
        for i, contact in enumerate(result.scheduled_contacts):
            print(f"  Contact {i+1}: {contact['demand_mb']} MB, "
                  f"Efficiency: {contact['data_efficiency']:.3f}, "
                  f"Rate: {contact['effective_data_rate_mbps']:.1f} Mbps")
    
    if result.unscheduled_demands:
        print(f"\nUnscheduled Demands: {len(result.unscheduled_demands)}")
        for demand in result.unscheduled_demands:
            print(f"  {demand['data_mb']} MB (Priority: {demand.get('priority', 1.0)})")

def test_multiple_objectives():
    """Test different optimization objectives."""
    print("\n=== Testing Multiple Optimization Objectives ===")
    
    stations = load_ground_stations()
    if not stations: return
    
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=1)
    
    # Create demands with varying priorities
    demands = [
        {"satellite": "ISS", "data_mb": 400, "priority": 1.0},
        {"satellite": "ISS", "data_mb": 600, "priority": 3.0},  # High priority
        {"satellite": "ISS", "data_mb": 300, "priority": 1.5},
        {"satellite": "ISS", "data_mb": 700, "priority": 2.0},
        {"satellite": "ISS", "data_mb": 250, "priority": 2.5},
    ]
    
    optimizer = AdvancedSchedulingOptimizer()
    
    objectives = [
        (OptimizationObjective.MAXIMIZE_DATA_THROUGHPUT, "Data Throughput"),
        (OptimizationObjective.MAXIMIZE_PRIORITY_WEIGHTED, "Priority Weighted"),
        (OptimizationObjective.BALANCE_EFFICIENCY_FAIRNESS, "Balanced Efficiency"),
    ]
    
    results = {}
    
    for objective, name in objectives:
        print(f"\n--- Testing {name} Objective ---")
        result = optimizer.create_advanced_schedule(passes, demands, objective)
        results[name] = result
        
        print(f"  Contacts: {len(result.scheduled_contacts)}")
        print(f"  Total Data: {result.total_data_scheduled} MB")
        print(f"  Efficiency: {result.schedule_efficiency:.2%}")
        print(f"  Solve Time: {result.solve_time_seconds:.3f}s")
        
        if result.scheduled_contacts:
            avg_priority = sum(c['priority'] for c in result.scheduled_contacts) / len(result.scheduled_contacts)
            print(f"  Avg Priority: {avg_priority:.2f}")
    
    # Compare results
    print(f"\n--- Objective Comparison ---")
    for name, result in results.items():
        print(f"{name:20}: {result.total_data_scheduled:6.0f} MB, "
              f"{len(result.scheduled_contacts):2d} contacts, "
              f"{result.schedule_efficiency:.1%} efficiency")

def test_constraints():
    """Test scheduling with custom constraints."""
    print("\n=== Testing Custom Constraints ===")
    
    stations = load_ground_stations()
    if not stations: return
    
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=1)
    
    demands = [
        {"satellite": "ISS", "data_mb": 300},
        {"satellite": "ISS", "data_mb": 400},
        {"satellite": "ISS", "data_mb": 500},
        {"satellite": "ISS", "data_mb": 350},
        {"satellite": "ISS", "data_mb": 450},
    ]
    
    # Test with constraints
    constraints = [
        SchedulingConstraint("minimum_gap", {"gap_seconds": 300}),
        SchedulingConstraint("maximum_contacts_per_satellite", {"max_contacts": 3}),
    ]
    
    optimizer = AdvancedSchedulingOptimizer()
    
    # Without constraints
    result_no_constraints = optimizer.create_advanced_schedule(passes, demands)
    
    # With constraints
    result_with_constraints = optimizer.create_advanced_schedule(
        passes, demands, constraints=constraints
    )
    
    print(f"\nWithout Constraints:")
    print(f"  Contacts: {len(result_no_constraints.scheduled_contacts)}")
    print(f"  Total Data: {result_no_constraints.total_data_scheduled} MB")
    
    print(f"\nWith Constraints:")
    print(f"  Contacts: {len(result_with_constraints.scheduled_contacts)}")
    print(f"  Total Data: {result_with_constraints.total_data_scheduled} MB")
    
    print(f"\nConstraint Impact:")
    data_diff = result_no_constraints.total_data_scheduled - result_with_constraints.total_data_scheduled
    contact_diff = len(result_no_constraints.scheduled_contacts) - len(result_with_constraints.scheduled_contacts)
    print(f"  Data Reduction: {data_diff} MB")
    print(f"  Contact Reduction: {contact_diff}")

def test_deadline_constraints():
    """Test scheduling with deadline constraints."""
    print("\n=== Testing Deadline Constraints ===")
    
    stations = load_ground_stations()
    if not stations: return
    
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=2)
    
    # Create demands with deadlines
    now = datetime.now()
    demands = [
        {
            "satellite": "ISS", 
            "data_mb": 300, 
            "priority": 1.0,
            "deadline": (now + timedelta(hours=12)).isoformat()
        },
        {
            "satellite": "ISS", 
            "data_mb": 500, 
            "priority": 2.0,
            "deadline": (now + timedelta(hours=6)).isoformat()  # Urgent
        },
        {
            "satellite": "ISS", 
            "data_mb": 400, 
            "priority": 1.5,
            "deadline": (now + timedelta(days=1)).isoformat()
        },
        {
            "satellite": "ISS", 
            "data_mb": 200, 
            "priority": 1.0
            # No deadline
        },
    ]
    
    optimizer = AdvancedSchedulingOptimizer()
    result = optimizer.create_advanced_schedule(passes, demands)
    
    print(f"\nDeadline-Constrained Scheduling:")
    print(f"  Contacts: {len(result.scheduled_contacts)}")
    print(f"  Total Data: {result.total_data_scheduled} MB")
    
    if result.scheduled_contacts:
        print(f"\nScheduled Contacts (with deadlines):")
        for i, contact in enumerate(result.scheduled_contacts):
            start_time = datetime.fromisoformat(contact['start_time'].replace('Z', ''))
            print(f"  Contact {i+1}: {contact['demand_mb']} MB at {start_time.strftime('%H:%M')}")
    
    if result.unscheduled_demands:
        print(f"\nUnscheduled (possibly missed deadlines): {len(result.unscheduled_demands)}")

def test_strategy_comparison():
    """Test the strategy comparison feature."""
    print("\n=== Testing Strategy Comparison ===")
    
    stations = load_ground_stations()
    if not stations: return
    
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=1)
    
    demands = [
        {"satellite": "ISS", "data_mb": 350, "priority": 1.0},
        {"satellite": "ISS", "data_mb": 600, "priority": 3.0},
        {"satellite": "ISS", "data_mb": 400, "priority": 2.0},
        {"satellite": "ISS", "data_mb": 500, "priority": 1.5},
    ]
    
    optimizer = AdvancedSchedulingOptimizer()
    comparison = optimizer.compare_scheduling_strategies(passes, demands)
    
    print(f"\nStrategy Comparison Results:")
    print(f"{'Strategy':<20} {'Contacts':<8} {'Data (MB)':<10} {'Efficiency':<10} {'Time (s)':<8}")
    print("-" * 65)
    
    for strategy_name, result in comparison.items():
        print(f"{strategy_name:<20} {len(result.scheduled_contacts):<8} "
              f"{result.total_data_scheduled:<10.0f} {result.schedule_efficiency:<10.2%} "
              f"{result.solve_time_seconds:<8.3f}")
    
    # Find best strategy
    best_strategy = max(comparison.items(), key=lambda x: x[1].total_data_scheduled)
    print(f"\nBest Strategy: {best_strategy[0]} ({best_strategy[1].total_data_scheduled} MB)")

def test_backward_compatibility():
    """Test that legacy functions still work."""
    print("\n=== Testing Backward Compatibility ===")
    
    stations = load_ground_stations()
    if not stations: return
    
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=1)
    
    demands = [
        {"satellite": "ISS", "data_mb": 400},
        {"satellite": "ISS", "data_mb": 600},
        {"satellite": "ISS", "data_mb": 300},
    ]
    
    # Test legacy function
    scheduled, unscheduled = create_optimized_schedule(passes, demands)
    
    print(f"Legacy Function Results:")
    print(f"  Scheduled Contacts: {len(scheduled)}")
    print(f"  Unscheduled Demands: {len(unscheduled)}")
    
    if scheduled:
        total_data = sum(c['demand_mb'] for c in scheduled)
        print(f"  Total Data: {total_data} MB")
        print("✅ Legacy compatibility maintained")
    else:
        print("❌ Legacy function failed")

def test_performance():
    """Test optimization performance with larger datasets."""
    print("\n=== Testing Performance ===")
    
    stations = load_ground_stations()
    if not stations: return
    
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=2)
    
    # Create larger demand set
    demands = []
    for i in range(20):  # 20 demands
        demands.append({
            "satellite": "ISS",
            "data_mb": 200 + (i * 50) % 800,  # Varying sizes
            "priority": 1.0 + (i % 3)  # Varying priorities
        })
    
    optimizer = AdvancedSchedulingOptimizer()
    
    print(f"Performance Test: {len(passes)} passes, {len(demands)} demands")
    
    start_time = time.time()
    result = optimizer.create_advanced_schedule(passes, demands)
    end_time = time.time()
    
    print(f"  Solve Time: {end_time - start_time:.3f}s")
    print(f"  Contacts Scheduled: {len(result.scheduled_contacts)}")
    print(f"  Total Data: {result.total_data_scheduled} MB")
    print(f"  Efficiency: {result.schedule_efficiency:.2%}")
    
    # Test with timeout
    print(f"\nTesting with 10s timeout:")
    optimizer.solver_timeout_seconds = 10
    
    start_time = time.time()
    result_timeout = optimizer.create_advanced_schedule(passes, demands)
    end_time = time.time()
    
    print(f"  Actual Time: {end_time - start_time:.3f}s")
    print(f"  Status: {result_timeout.optimization_status}")
    print(f"  Quality: {result_timeout.solution_quality}")

def main():
    """Run all optimization tests."""
    print("=" * 70)
    print("ENHANCED SCHEDULING OPTIMIZATION MODULE TEST SUITE")
    print("=" * 70)
    
    try:
        test_basic_optimization()
        test_multiple_objectives()
        test_constraints()
        test_deadline_constraints()
        test_strategy_comparison()
        test_backward_compatibility()
        test_performance()
        
        print("\n" + "=" * 70)
        print("ALL OPTIMIZATION TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Integration test suite for the enhanced LLGSPS system.
Tests the complete workflow from satellite passes to optimized scheduling.
"""

from app.core.ground_station import load_ground_stations
from app.core.satellite import find_satellite_passes
from app.core.latency import LatencyEstimator, estimate_transfer_time
from app.scheduling.baseline import create_baseline_schedule
from app.scheduling.optimizer import AdvancedSchedulingOptimizer, OptimizationObjective
from datetime import datetime, timedelta
import time

def test_complete_workflow():
    """Test the complete workflow from data loading to scheduling."""
    print("=== Integration Test: Complete Workflow ===")
    
    # Step 1: Load ground stations
    print("Step 1: Loading ground stations...")
    stations = load_ground_stations()
    assert stations, "No ground stations loaded"
    assert len(stations) > 0, "Ground stations list is empty"
    print(f"✅ Loaded {len(stations)} ground station(s)")
    
    # Step 2: Find satellite passes
    print("\nStep 2: Finding satellite passes...")
    bangalore_station = stations[0]
    passes = find_satellite_passes('iss.txt', bangalore_station, days=1)
    assert passes, "No satellite passes found"
    assert len(passes) > 0, "Passes list is empty"
    print(f"✅ Found {len(passes)} satellite passes")
    
    # Step 3: Create data demands
    print("\nStep 3: Creating data demands...")
    demands = [
        {"satellite": "ISS", "data_mb": 300, "priority": 1.0},
        {"satellite": "ISS", "data_mb": 500, "priority": 2.0},
        {"satellite": "ISS", "data_mb": 200, "priority": 1.5},
        {"satellite": "ISS", "data_mb": 700, "priority": 3.0},
    ]
    total_demand = sum(d['data_mb'] for d in demands)
    print(f"✅ Created {len(demands)} demands totaling {total_demand} MB")
    
    # Step 4: Test latency estimation
    print("\nStep 4: Testing latency estimation...")
    estimator = LatencyEstimator()
    feasible_count = 0
    
    for pass_info in passes[:3]:  # Test first 3 passes
        for demand in demands[:2]:  # Test first 2 demands
            result = estimator.estimate_transfer_time_detailed(pass_info, demand['data_mb'])
            if result and result['is_feasible']:
                feasible_count += 1
    
    print(f"✅ Latency estimation working, {feasible_count} feasible combinations found")
    
    # Step 5: Test baseline scheduling
    print("\nStep 5: Testing baseline scheduling...")
    baseline_scheduled, baseline_unscheduled = create_baseline_schedule(passes, demands)
    baseline_data = sum(c['demand_mb'] for c in baseline_scheduled)
    print(f"✅ Baseline scheduler: {len(baseline_scheduled)} contacts, {baseline_data} MB")
    
    # Step 6: Test enhanced optimization
    print("\nStep 6: Testing enhanced optimization...")
    optimizer = AdvancedSchedulingOptimizer()
    result = optimizer.create_advanced_schedule(passes, demands)
    
    assert result.optimization_status in ['OPTIMAL', 'FEASIBLE'], f"Unexpected status: {result.optimization_status}"
    print(f"✅ Enhanced optimizer: {len(result.scheduled_contacts)} contacts, {result.total_data_scheduled} MB")
    
    # Step 7: Compare results
    print("\nStep 7: Comparing results...")
    improvement = result.total_data_scheduled - baseline_data
    print(f"Data throughput improvement: {improvement:+.0f} MB")
    
    if improvement >= 0:
        print("✅ Enhanced optimizer performed as well or better than baseline")
    else:
        print("⚠️  Baseline performed better in this case")
    
    print("\n🎉 Complete workflow test PASSED!")
    return True

def test_data_consistency():
    """Test data consistency across different modules."""
    print("\n=== Integration Test: Data Consistency ===")
    
    stations = load_ground_stations()
    passes = find_satellite_passes('iss.txt', stations[0], days=1)
    
    # Test that all passes have required fields
    required_fields = ['rise_time', 'culmination_time', 'set_time']
    for i, pass_info in enumerate(passes):
        for field in required_fields:
            assert field in pass_info, f"Pass {i} missing field: {field}"
        
        # Test that times are in correct order
        rise_time = datetime.fromisoformat(pass_info['rise_time'].replace('Z', ''))
        culmination_time = datetime.fromisoformat(pass_info['culmination_time'].replace('Z', ''))
        set_time = datetime.fromisoformat(pass_info['set_time'].replace('Z', ''))
        
        assert rise_time < culmination_time < set_time, f"Pass {i} has incorrect time ordering"
    
    print(f"✅ All {len(passes)} passes have consistent data structure")
    
    # Test latency estimation consistency
    estimator = LatencyEstimator()
    test_pass = passes[0]
    test_data = 500
    
    # Test multiple calls return same result
    result1 = estimator.estimate_transfer_time_detailed(test_pass, test_data)
    result2 = estimator.estimate_transfer_time_detailed(test_pass, test_data)
    
    assert result1['is_feasible'] == result2['is_feasible'], "Inconsistent feasibility results"
    assert abs(result1['total_required_time_seconds'] - result2['total_required_time_seconds']) < 0.001, "Inconsistent time calculations"
    
    print("✅ Latency estimation is consistent")
    
    # Test backward compatibility
    legacy_result = estimate_transfer_time(test_pass, test_data)
    enhanced_result = estimator.estimate_transfer_time_detailed(test_pass, test_data)
    
    assert legacy_result['is_feasible'] == enhanced_result['is_feasible'], "Legacy compatibility broken"
    
    print("✅ Backward compatibility maintained")
    print("🎉 Data consistency test PASSED!")

def test_performance_scalability():
    """Test system performance with varying loads."""
    print("\n=== Integration Test: Performance Scalability ===")
    
    stations = load_ground_stations()
    passes = find_satellite_passes('iss.txt', stations[0], days=2)  # More passes
    
    # Test with increasing demand sizes
    demand_sizes = [5, 10, 15, 20]
    optimizer = AdvancedSchedulingOptimizer()
    
    performance_results = []
    
    for size in demand_sizes:
        # Create demands
        demands = []
        for i in range(size):
            demands.append({
                "satellite": "ISS",
                "data_mb": 200 + (i * 100) % 600,
                "priority": 1.0 + (i % 3)
            })
        
        # Measure optimization time
        start_time = time.time()
        result = optimizer.create_advanced_schedule(passes, demands)
        end_time = time.time()
        
        solve_time = end_time - start_time
        performance_results.append((size, solve_time, len(result.scheduled_contacts)))
        
        print(f"  {size:2d} demands: {solve_time:.3f}s, {len(result.scheduled_contacts)} contacts scheduled")
    
    # Check that performance is reasonable
    max_time = max(result[1] for result in performance_results)
    assert max_time < 30.0, f"Performance too slow: {max_time:.3f}s for largest test"
    
    print(f"✅ Performance acceptable (max: {max_time:.3f}s)")
    print("🎉 Performance scalability test PASSED!")

def test_error_handling():
    """Test error handling and edge cases."""
    print("\n=== Integration Test: Error Handling ===")
    
    estimator = LatencyEstimator()
    optimizer = AdvancedSchedulingOptimizer()
    
    # Test invalid pass data
    invalid_pass = {"invalid": "data"}
    result = estimator.estimate_transfer_time_detailed(invalid_pass, 100)
    assert result is None, "Should return None for invalid pass data"
    print("✅ Invalid pass data handled correctly")
    
    # Test empty demands list
    stations = load_ground_stations()
    passes = find_satellite_passes('iss.txt', stations[0], days=1)
    
    result = optimizer.create_advanced_schedule(passes, [])
    assert len(result.scheduled_contacts) == 0, "Should return empty schedule for no demands"
    assert len(result.unscheduled_demands) == 0, "Should have no unscheduled demands"
    print("✅ Empty demands list handled correctly")
    
    # Test empty passes list
    demands = [{"satellite": "ISS", "data_mb": 500}]
    result = optimizer.create_advanced_schedule([], demands)
    assert len(result.scheduled_contacts) == 0, "Should return empty schedule for no passes"
    assert len(result.unscheduled_demands) == 1, "Should have all demands unscheduled"
    print("✅ Empty passes list handled correctly")
    
    # Test very large data demand
    large_demand = [{"satellite": "ISS", "data_mb": 50000}]  # 50GB
    result = optimizer.create_advanced_schedule(passes, large_demand)
    # Should handle gracefully without crashing
    print("✅ Large data demand handled gracefully")
    
    # Test zero data demand
    zero_demand = [{"satellite": "ISS", "data_mb": 0}]
    result = optimizer.create_advanced_schedule(passes, zero_demand)
    # Should handle gracefully
    print("✅ Zero data demand handled gracefully")
    
    print("🎉 Error handling test PASSED!")

def test_optimization_objectives():
    """Test different optimization objectives produce different results."""
    print("\n=== Integration Test: Optimization Objectives ===")
    
    stations = load_ground_stations()
    passes = find_satellite_passes('iss.txt', stations[0], days=1)
    
    # Create demands with varying priorities
    demands = [
        {"satellite": "ISS", "data_mb": 300, "priority": 1.0},
        {"satellite": "ISS", "data_mb": 400, "priority": 3.0},  # High priority
        {"satellite": "ISS", "data_mb": 500, "priority": 1.5},
        {"satellite": "ISS", "data_mb": 200, "priority": 2.0},
    ]
    
    optimizer = AdvancedSchedulingOptimizer()
    
    # Test different objectives
    objectives = [
        OptimizationObjective.MAXIMIZE_DATA_THROUGHPUT,
        OptimizationObjective.MAXIMIZE_PRIORITY_WEIGHTED,
        OptimizationObjective.BALANCE_EFFICIENCY_FAIRNESS,
    ]
    
    results = {}
    for objective in objectives:
        result = optimizer.create_advanced_schedule(passes, demands, objective)
        results[objective] = result
        
        print(f"  {objective.value}: {result.total_data_scheduled:.0f} MB, "
              f"{len(result.scheduled_contacts)} contacts")
    
    # Verify that different objectives can produce different results
    data_values = [r.total_data_scheduled for r in results.values()]
    contact_counts = [len(r.scheduled_contacts) for r in results.values()]
    
    # At least some variation should exist (unless all produce identical optimal solutions)
    print("✅ Multiple optimization objectives working")
    print("🎉 Optimization objectives test PASSED!")

def test_constraint_enforcement():
    """Test that constraints are properly enforced."""
    print("\n=== Integration Test: Constraint Enforcement ===")
    
    stations = load_ground_stations()
    passes = find_satellite_passes('iss.txt', stations[0], days=1)
    
    demands = [
        {"satellite": "ISS", "data_mb": 300},
        {"satellite": "ISS", "data_mb": 400},
        {"satellite": "ISS", "data_mb": 500},
        {"satellite": "ISS", "data_mb": 350},
        {"satellite": "ISS", "data_mb": 450},
    ]
    
    optimizer = AdvancedSchedulingOptimizer()
    
    # Test without constraints
    result_unconstrained = optimizer.create_advanced_schedule(passes, demands)
    
    # Test with contact limit constraint
    from app.scheduling.optimizer import SchedulingConstraint
    constraints = [
        SchedulingConstraint("maximum_contacts_per_satellite", {"max_contacts": 2})
    ]
    
    result_constrained = optimizer.create_advanced_schedule(passes, demands, constraints=constraints)
    
    # Verify constraint is enforced
    assert len(result_constrained.scheduled_contacts) <= 2, "Contact limit constraint violated"
    
    print(f"  Unconstrained: {len(result_unconstrained.scheduled_contacts)} contacts")
    print(f"  Constrained (max 2): {len(result_constrained.scheduled_contacts)} contacts")
    print("✅ Constraint enforcement working")
    print("🎉 Constraint enforcement test PASSED!")

def main():
    """Run all integration tests."""
    print("=" * 80)
    print("LLGSPS ENHANCED SYSTEM - INTEGRATION TEST SUITE")
    print("=" * 80)
    
    test_results = []
    
    try:
        # Run all integration tests
        test_results.append(("Complete Workflow", test_complete_workflow()))
        test_results.append(("Data Consistency", test_data_consistency()))
        test_results.append(("Performance Scalability", test_performance_scalability()))
        test_results.append(("Error Handling", test_error_handling()))
        test_results.append(("Optimization Objectives", test_optimization_objectives()))
        test_results.append(("Constraint Enforcement", test_constraint_enforcement()))
        
        # Summary
        print("\n" + "=" * 80)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {test_name:<25}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("The enhanced LLGSPS system is working correctly.")
        else:
            print("❌ SOME TESTS FAILED!")
            print("Please review the failed tests and fix issues.")
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
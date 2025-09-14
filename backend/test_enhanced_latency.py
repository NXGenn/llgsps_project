#!/usr/bin/env python3
"""
Comprehensive test suite for the enhanced latency estimation module.
Tests all new features and ensures backward compatibility.
"""

from app.core.latency import LatencyEstimator, estimate_transfer_time
from datetime import datetime, timedelta
import json

def test_basic_latency_estimation():
    """Test basic latency estimation functionality."""
    print("=== Testing Basic Latency Estimation ===")
    
    estimator = LatencyEstimator()
    
    # Create a sample pass
    now = datetime.now()
    sample_pass = {
        'rise_time': now.isoformat() + 'Z',
        'culmination_time': (now + timedelta(minutes=5)).isoformat() + 'Z',
        'set_time': (now + timedelta(minutes=10)).isoformat() + 'Z'
    }
    
    # Test different data sizes
    test_cases = [100, 500, 1000, 1500]  # MB
    
    for data_mb in test_cases:
        result = estimator.estimate_transfer_time_detailed(sample_pass, data_mb)
        
        if result:
            print(f"\nData: {data_mb} MB")
            print(f"  Feasible: {result['is_feasible']}")
            print(f"  Total Time: {result['total_required_time_seconds']:.2f}s")
            print(f"  Data Transfer Time: {result['data_transfer_time_seconds']:.2f}s")
            print(f"  Overhead Time: {result['overhead_time_seconds']:.2f}s")
            print(f"  Effective Rate: {result['effective_data_rate_mbps']:.2f} Mbps")
            print(f"  Data Efficiency: {result['data_efficiency']:.3f}")
            print(f"  Pass Utilization: {result['pass_utilization']:.3f}")
        else:
            print(f"Data: {data_mb} MB - ESTIMATION FAILED")

def test_weather_conditions():
    """Test latency estimation under different weather conditions."""
    print("\n=== Testing Weather Condition Effects ===")
    
    estimator = LatencyEstimator()
    
    now = datetime.now()
    sample_pass = {
        'rise_time': now.isoformat() + 'Z',
        'culmination_time': (now + timedelta(minutes=5)).isoformat() + 'Z',
        'set_time': (now + timedelta(minutes=10)).isoformat() + 'Z'
    }
    
    weather_conditions = ['clear', 'light_clouds', 'heavy_clouds', 'rain', 'storm']
    data_mb = 500
    
    print(f"\nTesting {data_mb} MB transfer under different weather conditions:")
    
    for weather in weather_conditions:
        result = estimator.estimate_transfer_time_detailed(
            sample_pass, data_mb, weather_condition=weather
        )
        
        if result:
            print(f"  {weather.upper():12}: {result['effective_data_rate_mbps']:6.2f} Mbps, "
                  f"{result['total_required_time_seconds']:6.2f}s, "
                  f"Feasible: {result['is_feasible']}")

def test_multiple_pass_analysis():
    """Test analysis of multiple passes to find optimal scheduling."""
    print("\n=== Testing Multiple Pass Analysis ===")
    
    estimator = LatencyEstimator()
    
    # Create multiple passes with different durations
    now = datetime.now()
    passes = []
    
    for i in range(5):
        pass_start = now + timedelta(hours=i*4)
        duration_minutes = 8 + (i * 2)  # Varying pass durations
        
        pass_info = {
            'rise_time': pass_start.isoformat() + 'Z',
            'culmination_time': (pass_start + timedelta(minutes=duration_minutes//2)).isoformat() + 'Z',
            'set_time': (pass_start + timedelta(minutes=duration_minutes)).isoformat() + 'Z'
        }
        passes.append(pass_info)
    
    data_mb = 800  # Large data demand
    
    print(f"\nAnalyzing {len(passes)} passes for {data_mb} MB transfer:")
    
    # Test multiple pass estimation
    results = estimator.estimate_multiple_passes(passes, data_mb)
    
    for i, result in enumerate(results):
        print(f"\nPass {i+1}:")
        print(f"  Duration: {result['pass_duration_seconds']:.0f}s")
        print(f"  Required: {result['total_required_time_seconds']:.2f}s")
        print(f"  Feasible: {result['is_feasible']}")
        print(f"  Efficiency: {result['data_efficiency']:.3f}")
        print(f"  Utilization: {result['pass_utilization']:.3f}")
    
    # Find optimal pass
    optimal = estimator.get_optimal_pass(passes, data_mb)
    if optimal:
        print(f"\nOptimal pass found:")
        print(f"  Pass duration: {optimal['pass_duration_seconds']:.0f}s")
        print(f"  Required time: {optimal['total_required_time_seconds']:.2f}s")
        print(f"  Data efficiency: {optimal['data_efficiency']:.3f}")
    else:
        print("\nNo feasible pass found for this data demand.")

def test_signal_propagation():
    """Test signal propagation delay calculations."""
    print("\n=== Testing Signal Propagation Calculations ===")
    
    estimator = LatencyEstimator()
    
    # Test different satellite altitudes and elevation angles
    test_scenarios = [
        (408, 10),   # ISS at low elevation
        (408, 45),   # ISS at medium elevation
        (408, 90),   # ISS directly overhead
        (35786, 45), # Geostationary satellite
        (1200, 30),  # Medium Earth Orbit
    ]
    
    print("\nSignal propagation delays:")
    print("Altitude (km) | Elevation (°) | Delay (ms)")
    print("-" * 45)
    
    for altitude_km, elevation_deg in test_scenarios:
        delay = estimator.calculate_signal_propagation_delay(altitude_km, elevation_deg)
        print(f"{altitude_km:12} | {elevation_deg:11} | {delay*1000:8.2f}")

def test_backward_compatibility():
    """Test that the legacy function still works correctly."""
    print("\n=== Testing Backward Compatibility ===")
    
    now = datetime.now()
    sample_pass = {
        'rise_time': now.isoformat() + 'Z',
        'culmination_time': (now + timedelta(minutes=5)).isoformat() + 'Z',
        'set_time': (now + timedelta(minutes=10)).isoformat() + 'Z'
    }
    
    # Test legacy function
    legacy_result = estimate_transfer_time(sample_pass, 500, 150)
    
    if legacy_result:
        print("Legacy function test:")
        print(f"  Feasible: {legacy_result['is_feasible']}")
        print(f"  Required Time: {legacy_result['required_time_seconds']:.2f}s")
        print(f"  Pass Duration: {legacy_result['pass_duration_seconds']:.2f}s")
        print("✅ Legacy compatibility maintained")
    else:
        print("❌ Legacy function failed")

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n=== Testing Edge Cases ===")
    
    estimator = LatencyEstimator()
    
    # Test with invalid pass data
    invalid_pass = {'invalid': 'data'}
    result = estimator.estimate_transfer_time_detailed(invalid_pass, 100)
    print(f"Invalid pass data: {result is None} (should be True)")
    
    # Test with zero data
    now = datetime.now()
    valid_pass = {
        'rise_time': now.isoformat() + 'Z',
        'culmination_time': (now + timedelta(minutes=5)).isoformat() + 'Z',
        'set_time': (now + timedelta(minutes=10)).isoformat() + 'Z'
    }
    
    result = estimator.estimate_transfer_time_detailed(valid_pass, 0)
    if result:
        print(f"Zero data test: Feasible={result['is_feasible']}, Time={result['total_required_time_seconds']:.2f}s")
    
    # Test with very large data demand
    result = estimator.estimate_transfer_time_detailed(valid_pass, 10000)  # 10GB
    if result:
        print(f"Large data test: Feasible={result['is_feasible']}, Time={result['total_required_time_seconds']:.2f}s")

def main():
    """Run all latency estimation tests."""
    print("=" * 60)
    print("ENHANCED LATENCY ESTIMATION MODULE TEST SUITE")
    print("=" * 60)
    
    try:
        test_basic_latency_estimation()
        test_weather_conditions()
        test_multiple_pass_analysis()
        test_signal_propagation()
        test_backward_compatibility()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
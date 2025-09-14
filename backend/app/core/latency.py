import math
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List

class LatencyEstimator:
    """
    Deterministic latency estimation module for satellite communication systems.
    Provides comprehensive modeling of various latency factors in satellite passes.
    """
    
    def __init__(self):
        # Physical constants
        self.SPEED_OF_LIGHT = 299792458  # m/s
        self.EARTH_RADIUS = 6371000  # meters
        
        # Communication parameters (configurable)
        self.default_data_rate_mbps = 150  # Megabits per second
        self.protocol_overhead = 0.15  # 15% overhead for protocols
        self.handshake_time = 2.0  # seconds for initial handshake
        self.error_correction_overhead = 0.08  # 8% for error correction
        
        # Atmospheric and environmental factors
        self.atmospheric_loss_db = 0.5  # dB loss due to atmosphere
        self.weather_degradation = {
            'clear': 1.0,
            'light_clouds': 0.95,
            'heavy_clouds': 0.85,
            'rain': 0.7,
            'storm': 0.5
        }

    def calculate_signal_propagation_delay(self, satellite_altitude_km: float, 
                                         elevation_angle_deg: float) -> float:
        """
        Calculate the signal propagation delay based on satellite position.
        
        Args:
            satellite_altitude_km: Altitude of satellite in kilometers
            elevation_angle_deg: Elevation angle of satellite from ground station
            
        Returns:
            Propagation delay in seconds
        """
        # Convert to radians and meters
        elevation_rad = math.radians(elevation_angle_deg)
        altitude_m = satellite_altitude_km * 1000
        
        # Calculate slant range using spherical geometry
        # Distance = sqrt((R + h)² - R² * cos²(elevation)) - R * sin(elevation)
        earth_radius = self.EARTH_RADIUS
        satellite_distance = earth_radius + altitude_m
        
        cos_elev = math.cos(elevation_rad)
        sin_elev = math.sin(elevation_rad)
        
        slant_range = math.sqrt(
            satellite_distance**2 - earth_radius**2 * cos_elev**2
        ) - earth_radius * sin_elev
        
        # Round trip delay
        propagation_delay = (2 * slant_range) / self.SPEED_OF_LIGHT
        
        return propagation_delay

    def estimate_data_rate_degradation(self, elevation_angle_deg: float, 
                                     weather_condition: str = 'clear') -> float:
        """
        Estimate data rate degradation based on elevation angle and weather.
        
        Args:
            elevation_angle_deg: Elevation angle of satellite
            weather_condition: Weather condition ('clear', 'light_clouds', etc.)
            
        Returns:
            Effective data rate multiplier (0.0 to 1.0)
        """
        # Lower elevation angles have more atmospheric interference
        elevation_factor = min(1.0, max(0.3, elevation_angle_deg / 90.0))
        
        # Apply weather degradation
        weather_factor = self.weather_degradation.get(weather_condition, 1.0)
        
        # Combine factors
        return elevation_factor * weather_factor

    def calculate_effective_data_rate(self, base_rate_mbps: float, 
                                    elevation_angle_deg: float,
                                    weather_condition: str = 'clear') -> float:
        """
        Calculate the effective data rate considering all degradation factors.
        
        Args:
            base_rate_mbps: Base data rate in Mbps
            elevation_angle_deg: Elevation angle of satellite
            weather_condition: Weather condition
            
        Returns:
            Effective data rate in Mbps
        """
        degradation_factor = self.estimate_data_rate_degradation(
            elevation_angle_deg, weather_condition
        )
        
        # Apply protocol overhead and error correction
        effective_rate = base_rate_mbps * degradation_factor
        effective_rate *= (1 - self.protocol_overhead)
        effective_rate *= (1 - self.error_correction_overhead)
        
        return max(1.0, effective_rate)  # Minimum 1 Mbps

    def estimate_transfer_time_detailed(self, pass_info: Dict, data_demand_mb: float,
                                      base_data_rate_mbps: float = None,
                                      weather_condition: str = 'clear',
                                      satellite_altitude_km: float = 408) -> Optional[Dict]:
        """
        Enhanced transfer time estimation with detailed latency modeling.
        
        Args:
            pass_info: Dictionary containing pass timing information
            data_demand_mb: Data to transfer in Megabytes
            base_data_rate_mbps: Base data rate in Mbps
            weather_condition: Weather condition
            satellite_altitude_km: Satellite altitude in km (default ISS altitude)
            
        Returns:
            Detailed estimation dictionary or None if invalid input
        """
        try:
            # Parse timing information
            rise_time = datetime.fromisoformat(pass_info['rise_time'])
            set_time = datetime.fromisoformat(pass_info['set_time'])
            
            # Calculate pass duration
            pass_duration_seconds = (set_time - rise_time).total_seconds()
            
            # Use default data rate if not provided
            if base_data_rate_mbps is None:
                base_data_rate_mbps = self.default_data_rate_mbps
            
            # Estimate average elevation angle (simplified model)
            # In reality, this would be calculated from orbital mechanics
            avg_elevation_deg = 45.0  # Simplified assumption
            
            # Calculate effective data rate
            effective_rate_mbps = self.calculate_effective_data_rate(
                base_data_rate_mbps, avg_elevation_deg, weather_condition
            )
            
            # Calculate propagation delay
            propagation_delay = self.calculate_signal_propagation_delay(
                satellite_altitude_km, avg_elevation_deg
            )
            
            # Calculate transfer time components
            data_transfer_time = (data_demand_mb * 8) / effective_rate_mbps  # Convert MB to Mb
            total_overhead_time = self.handshake_time + (2 * propagation_delay)
            
            # Total required time
            total_required_time = data_transfer_time + total_overhead_time
            
            # Check feasibility
            is_feasible = pass_duration_seconds >= total_required_time
            
            # Calculate efficiency metrics
            data_efficiency = data_transfer_time / total_required_time if total_required_time > 0 else 0
            pass_utilization = total_required_time / pass_duration_seconds if pass_duration_seconds > 0 else 0
            
            return {
                "is_feasible": is_feasible,
                "total_required_time_seconds": round(total_required_time, 2),
                "data_transfer_time_seconds": round(data_transfer_time, 2),
                "overhead_time_seconds": round(total_overhead_time, 2),
                "pass_duration_seconds": round(pass_duration_seconds, 2),
                "effective_data_rate_mbps": round(effective_rate_mbps, 2),
                "base_data_rate_mbps": base_data_rate_mbps,
                "propagation_delay_seconds": round(propagation_delay, 3),
                "data_efficiency": round(data_efficiency, 3),
                "pass_utilization": round(pass_utilization, 3),
                "weather_condition": weather_condition,
                "estimated_elevation_deg": avg_elevation_deg
            }
            
        except (KeyError, TypeError, ValueError) as e:
            return None

    def estimate_multiple_passes(self, passes: List[Dict], data_demand_mb: float,
                               **kwargs) -> List[Dict]:
        """
        Estimate transfer feasibility for multiple passes.
        
        Args:
            passes: List of pass information dictionaries
            data_demand_mb: Data demand in MB
            **kwargs: Additional parameters for estimation
            
        Returns:
            List of estimation results for each pass
        """
        results = []
        for pass_info in passes:
            estimation = self.estimate_transfer_time_detailed(
                pass_info, data_demand_mb, **kwargs
            )
            if estimation:
                estimation['pass_info'] = pass_info
                results.append(estimation)
        
        # Sort by feasibility and efficiency
        results.sort(key=lambda x: (x['is_feasible'], x['data_efficiency']), reverse=True)
        return results

    def get_optimal_pass(self, passes: List[Dict], data_demand_mb: float,
                        **kwargs) -> Optional[Dict]:
        """
        Find the optimal pass for a given data demand.
        
        Args:
            passes: List of pass information dictionaries
            data_demand_mb: Data demand in MB
            **kwargs: Additional parameters for estimation
            
        Returns:
            Best pass estimation or None if no feasible passes
        """
        estimations = self.estimate_multiple_passes(passes, data_demand_mb, **kwargs)
        
        # Return the best feasible pass
        for estimation in estimations:
            if estimation['is_feasible']:
                return estimation
        
        return None


# Maintain backward compatibility with existing code
def estimate_transfer_time(pass_info: dict, data_demand_mb: float, 
                         data_rate_mbps: float = 150) -> Optional[Dict]:
    """
    Legacy function for backward compatibility.
    Uses the enhanced estimator with simplified parameters.
    """
    estimator = LatencyEstimator()
    
    # Use the detailed estimation but return simplified format
    detailed_result = estimator.estimate_transfer_time_detailed(
        pass_info, data_demand_mb, data_rate_mbps
    )
    
    if detailed_result is None:
        return None
    
    # Return in the original format for compatibility
    return {
        "is_feasible": detailed_result["is_feasible"],
        "required_time_seconds": detailed_result["total_required_time_seconds"],
        "pass_duration_seconds": detailed_result["pass_duration_seconds"]
    }


# Create a global instance for easy access
latency_estimator = LatencyEstimator()
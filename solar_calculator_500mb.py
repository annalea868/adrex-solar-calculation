#!/usr/bin/env python3
"""
Optimized Solar Calculator - 500MB Version
Uses optimized grid for TypeScript applications - interpolation
"""

import os
import pickle
import math
from datetime import datetime
import pandas as pd

class OptimizedSolarCalculator:
    """Solar calculator using optimized 500MB interpolated grid."""
    
    # Default efficiency values - can be overridden with frontend parameters
    DEFAULT_SYSTEM_EFFICIENCY = 0.8  # 80% system efficiency (fallback)
    
    def __init__(self, data_dir="solar_grid_500mb"):
        self.data_dir = data_dir
        self.grid_resolution = 0.75  # 0.75° grid spacing
        
        if not os.path.exists(data_dir):
            print(f"❌ Grid directory '{data_dir}' not found!")
            print("   Run 'python3 grid_downloader_500mb.py' first to download the optimized grid.")
            raise FileNotFoundError(f"Grid directory {data_dir} not found")
        
        # Load available configurations
        self.available_configs = self.load_available_configurations()
        
        # Initialize PV modules database
        self.pv_modules = self.get_pv_modules_database()
        
        # Initialize inverter database  
        self.inverters = self.get_inverters_database()
        
        print(f"✅ Optimized solar calculator ready (500MB version)")
        print(f"   Grid directory: {data_dir}")
        print(f"   Available configurations: {len(self.available_configs)}")
        print(f"   PV modules in database: {len(self.pv_modules)}")
        print(f"   Grid resolution: {self.grid_resolution}° (~{self.grid_resolution*111:.0f}km)")
        print(f"   TypeScript compatible: ✅")
    
    def get_pv_modules_database(self):
        """Database of available PV modules with their specifications."""
        return {
            "winaico_gg_black_450": {
                "name": "Winaico GG Black 450 Wp",
                "power_wp": 450,
                "efficiency": 0.205,  # 20.5%
                "temp_coefficient": -0.0038,  # -0.38%/°C
                "area_m2": 2.196,
                "voltage_mpp": 41.2,
                "current_mpp": 10.93
            },
            "winaico_gg_black_400": {
                "name": "Winaico GG Black 400 Wp", 
                "power_wp": 400,
                "efficiency": 0.195,
                "temp_coefficient": -0.0038,
                "area_m2": 2.054,
                "voltage_mpp": 38.1,
                "current_mpp": 10.50
            },
            "generic_400": {
                "name": "Generic 400 Wp Module",
                "power_wp": 400,
                "efficiency": 0.20,
                "temp_coefficient": -0.004,
                "area_m2": 2.0,
                "voltage_mpp": 40.0,
                "current_mpp": 10.0
            }
        }
    
    def get_inverters_database(self):
        """Database of available inverters with their specifications."""
        return {
            "quality_inverter": {
                "name": "Qualitäts-Wechselrichter",
                "efficiency": 0.96,
                "max_power_kw": 20.0
            },
            "standard_inverter": {
                "name": "Standard-Wechselrichter", 
                "efficiency": 0.94,
                "max_power_kw": 15.0
            },
            "premium_inverter": {
                "name": "Premium-Wechselrichter",
                "efficiency": 0.98,
                "max_power_kw": 30.0
            }
        }

    def load_available_configurations(self):
        """Load all available tilt/azimuth configurations from grid files."""
        configs = set()
        
        try:
            files = [f for f in os.listdir(self.data_dir) if f.startswith('grid_') and f.endswith('.pkl')]
            
            for file in files:
                # Parse filename: grid_lat_lon_tilt_azimuth_year.pkl
                parts = file.replace('grid_', '').replace('.pkl', '').split('_')
                if len(parts) >= 4:
                    try:
                        tilt = int(parts[2])
                        azimuth = int(parts[3])
                        configs.add((tilt, azimuth))
                    except:
                        pass
            
            return sorted(list(configs))
            
        except Exception as e:
            print(f"Error loading configurations: {e}")
            return []
    
    def find_nearest_configuration(self, target_tilt, target_azimuth):
        """
        Find the nearest available configuration with enhanced intelligence.
        Optimized for the 4 configurations in 500MB version.
        """
        if not self.available_configs:
            print("❌ No configurations available in grid")
            return None
        
        # Check for exact match first
        if (target_tilt, target_azimuth) in self.available_configs:
            print(f"✅ Exact configuration match: {target_tilt}°/{target_azimuth}°")
            return (target_tilt, target_azimuth)
        
        # Enhanced matching for optimized grid
        # Available configs should be: (30,0), (30,90), (30,270), (45,0)
        
        # Special case: if user wants 30° tilt, prefer 30° configs
        if target_tilt <= 37:  # Closer to 30°
            if target_azimuth >= -45 and target_azimuth <= 45:
                match = (30, 0)  # South
                print(f"🎯 Smart match: {match[0]}°/{match[1]}° (South-facing)")
                return match
            elif target_azimuth >= 45 and target_azimuth <= 135:
                match = (30, 90)  # West
                print(f"🎯 Smart match: {match[0]}°/{match[1]}° (West-facing)")
                return match
            elif target_azimuth >= 225 and target_azimuth <= 315:
                match = (30, 270)  # East
                print(f"🎯 Smart match: {match[0]}°/{match[1]}° (East-facing)") 
                return match
            else:
                # Default to south for 30° tilt
                match = (30, 0)
                print(f"🎯 Default match: {match[0]}°/{match[1]}° (South default for 30° tilt)")
                return match
        
        # For steeper tilts (>37°), prefer 45° south
        elif target_tilt > 37:
            if target_azimuth >= -45 and target_azimuth <= 45:
                match = (45, 0)  # Steep south
                print(f"🎯 Smart match: {match[0]}°/{match[1]}° (Steep south)")
                return match
            else:
                # For steep non-south, use 30° with appropriate direction
                if target_azimuth >= 45 and target_azimuth <= 135:
                    match = (30, 90)  # West
                elif target_azimuth >= 225 and target_azimuth <= 315:
                    match = (30, 270)  # East
                else:
                    match = (45, 0)  # Default to steep south
                print(f"🎯 Compromise match: {match[0]}°/{match[1]}° (adjusted for steep angle)")
                return match
        
        # Fallback: find truly nearest using Euclidean distance
        min_distance = float('inf')
        nearest_config = None
        
        for tilt, azimuth in self.available_configs:
            # Calculate distance in configuration space
            tilt_diff = abs(target_tilt - tilt)
            
            # Handle azimuth wraparound (0° and 360° are the same)
            azimuth_diff = min(
                abs(target_azimuth - azimuth),
                abs(target_azimuth - azimuth + 360),
                abs(target_azimuth - azimuth - 360)
            )
            
            # Weight tilt more heavily (factor of 2)
            distance = math.sqrt((tilt_diff * 2)**2 + azimuth_diff**2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_config = (tilt, azimuth)
        
        if nearest_config:
            tilt_diff = abs(target_tilt - nearest_config[0])
            azimuth_diff = min(
                abs(target_azimuth - nearest_config[1]),
                abs(target_azimuth - nearest_config[1] + 360),
                abs(target_azimuth - nearest_config[1] - 360)
            )
            
            print(f"📍 Nearest configuration: {nearest_config[0]}°/{nearest_config[1]}°")
            print(f"   Difference: {tilt_diff}° tilt, {azimuth_diff}° azimuth")
            
            if tilt_diff > 15 or azimuth_diff > 90:
                print(f"⚠️  Large configuration difference - results may be less accurate")
            elif tilt_diff > 10 or azimuth_diff > 45:
                print(f"⚠️  Moderate configuration difference - results still good")
        
        return nearest_config
    
    def get_grid_filename(self, lat, lon, tilt, azimuth, year=2023):
        """Generate filename for grid data."""
        return f"grid_{lat:.1f}_{lon:.1f}_{tilt}_{azimuth}_{year}.pkl"
    
    def load_grid_data(self, lat, lon, tilt, azimuth, year=2023):
        """Load data from grid file."""
        filename = self.get_grid_filename(lat, lon, tilt, azimuth, year)
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            return data
        except Exception as e:
            print(f"Error loading grid file {filename}: {e}")
            return None
    
    def find_grid_points(self, latitude, longitude):
        """Find the 4 surrounding grid points for interpolation."""
        # Round to grid boundaries
        lat_lower = math.floor(latitude / self.grid_resolution) * self.grid_resolution
        lat_upper = lat_lower + self.grid_resolution
        lon_lower = math.floor(longitude / self.grid_resolution) * self.grid_resolution
        lon_upper = lon_lower + self.grid_resolution
        
        # Ensure we're within Germany bounds
        lat_lower = max(47.5, lat_lower)
        lat_upper = min(55.0, lat_upper)
        lon_lower = max(6.0, lon_lower)
        lon_upper = min(15.0, lon_upper)
        
        grid_points = [
            (lat_lower, lon_lower),
            (lat_lower, lon_upper),
            (lat_upper, lon_lower),
            (lat_upper, lon_upper)
        ]
        
        return grid_points
    
    def interpolate_radiation(self, latitude, longitude, tilt, azimuth, target_datetime):
        """
        Get radiation value using bilinear interpolation from grid points.
        Optimized for 500MB version with enhanced error handling.
        """
        # Find nearest available configuration
        config = self.find_nearest_configuration(tilt, azimuth)
        if not config:
            return None
        
        actual_tilt, actual_azimuth = config
        
        # Get surrounding grid points
        grid_points = self.find_grid_points(latitude, longitude)
        
        # Load data from grid points
        grid_data = []
        for grid_lat, grid_lon in grid_points:
            data = self.load_grid_data(grid_lat, grid_lon, actual_tilt, actual_azimuth)
            if data is not None:
                radiation = self.extract_radiation_from_data(data, target_datetime)
                grid_data.append({
                    'lat': grid_lat,
                    'lon': grid_lon,
                    'radiation': radiation
                })
        
        if len(grid_data) == 0:
            print("❌ No grid data available for this location")
            return None
        
        # Enhanced fallback for 500MB version
        if len(grid_data) < 4:
            print(f"🔍 Using nearest neighbor (found {len(grid_data)}/4 grid points)")
            # Find closest point
            min_distance = float('inf')
            closest_radiation = None
            
            for point in grid_data:
                distance = math.sqrt((latitude - point['lat'])**2 + (longitude - point['lon'])**2)
                if distance < min_distance and point['radiation'] is not None:
                    min_distance = distance
                    closest_radiation = point['radiation']
            
            if closest_radiation is not None:
                print(f"☀️  Radiation: {closest_radiation:.1f} W/m² (nearest neighbor)")
            return closest_radiation
        
        # Full bilinear interpolation
        try:
            # Sort points for interpolation
            grid_data.sort(key=lambda p: (p['lat'], p['lon']))
            
            if len(grid_data) == 4:
                # Full bilinear interpolation
                x1, y1 = grid_data[0]['lon'], grid_data[0]['lat']  # bottom-left
                x2, y2 = grid_data[3]['lon'], grid_data[3]['lat']  # top-right
                
                # Get radiation values
                r11 = grid_data[0]['radiation']  # bottom-left
                r12 = grid_data[2]['radiation']  # top-left  
                r21 = grid_data[1]['radiation']  # bottom-right
                r22 = grid_data[3]['radiation']  # top-right
                
                # Check for None values
                if any(r is None for r in [r11, r12, r21, r22]):
                    # Fall back to average of available values
                    valid_values = [r for r in [r11, r12, r21, r22] if r is not None]
                    if valid_values:
                        avg_radiation = sum(valid_values) / len(valid_values)
                        print(f"☀️  Radiation: {avg_radiation:.1f} W/m² (averaged from {len(valid_values)} points)")
                        return avg_radiation
                    return None
                
                # Bilinear interpolation formula
                x, y = longitude, latitude
                
                radiation = (
                    r11 * (x2 - x) * (y2 - y) +
                    r21 * (x - x1) * (y2 - y) +
                    r12 * (x2 - x) * (y - y1) +
                    r22 * (x - x1) * (y - y1)
                ) / ((x2 - x1) * (y2 - y1))
                
                print(f"☀️  Radiation: {radiation:.1f} W/m² (interpolated)")
                return radiation
            
        except Exception as e:
            print(f"Error in interpolation: {e}")
        
        # Final fallback to simple average
        valid_radiations = [p['radiation'] for p in grid_data if p['radiation'] is not None]
        if valid_radiations:
            avg_radiation = sum(valid_radiations) / len(valid_radiations)
            print(f"☀️  Radiation: {avg_radiation:.1f} W/m² (average fallback)")
            return avg_radiation
        
        return None
    
    def extract_radiation_from_data(self, data, target_datetime):
        """Extract radiation value for specific datetime from PVGIS data."""
        try:
            # Make target_datetime timezone-aware if needed
            if target_datetime.tzinfo is None:
                import pytz
                target_datetime = pytz.UTC.localize(target_datetime)
            
            # Find closest time match
            closest_time = None
            min_diff = float('inf')
            
            for idx in data.index:
                if idx.tzinfo is None:
                    import pytz
                    idx_aware = pytz.UTC.localize(idx)
                else:
                    idx_aware = idx
                
                time_diff = abs((target_datetime - idx_aware).total_seconds())
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest_time = idx
            
            if closest_time is not None:
                # Calculate total radiation from components
                direct = data.loc[closest_time, 'poa_direct']
                sky_diffuse = data.loc[closest_time, 'poa_sky_diffuse']
                ground_diffuse = data.loc[closest_time, 'poa_ground_diffuse']
                
                total_radiation = direct + sky_diffuse + ground_diffuse
                return total_radiation
            
            return None
            
        except Exception as e:
            print(f"Error extracting radiation: {e}")
            return None
    
    def calculate_energy_for_datetime(self, latitude, longitude, tilt, azimuth, 
                                    target_datetime, N, P_mod, dt):
        """
        Calculate energy generation for specific location and time.
        Optimized for 500MB version with enhanced feedback.
        """
        print(f"🔋 Calculating energy for {latitude:.3f}°N, {longitude:.3f}°E")
        print(f"   Configuration: {tilt}° tilt, {azimuth}° azimuth")
        print(f"   Date/Time: {target_datetime}")
        
        # Get radiation using optimized interpolation
        G = self.interpolate_radiation(latitude, longitude, tilt, azimuth, target_datetime)
        
        if G is None:
            print("❌ Could not determine radiation for this location/configuration")
            return None
        
        # Calculate energy using the standard formula (fallback)
        E = (N * P_mod * (G / 1000) * self.DEFAULT_SYSTEM_EFFICIENCY) * (dt / 3600)
        
        results = {
            'datetime': target_datetime,
            'latitude': latitude,
            'longitude': longitude,
            'tilt': tilt,
            'azimuth': azimuth,
            'radiation_W_per_m2': G,
            'num_modules': N,
            'power_per_module_kWp': P_mod,
            'system_efficiency': self.DEFAULT_SYSTEM_EFFICIENCY, # This was not in the original code, but should be
            'time_period_seconds': dt,
            'energy_kWh': E,
            'energy_Wh': E * 1000,
            'data_source': 'Optimized Local Grid (500MB)',
            'grid_version': '500MB TypeScript Compatible'
        }
        
        return results
    
    def calculate_system_efficiency(self, 
                                   inverter_type: str = "quality_inverter",
                                   dc_losses: float = 0.02,
                                   ac_losses: float = 0.01,
                                   shading_losses: float = 0.0,
                                   soiling_losses: float = 0.02,
                                   mismatch_losses: float = 0.02,
                                   degradation_years: int = 0,
                                   annual_degradation: float = 0.005) -> float:
        """Calculate dynamic system efficiency based on all loss factors."""
        
        # Get inverter efficiency
        if inverter_type in self.inverters:
            inverter_efficiency = self.inverters[inverter_type]['efficiency']
        else:
            inverter_efficiency = 0.96  # Default
        
        # Calculate degradation factor
        degradation_factor = (1 - annual_degradation) ** degradation_years
        
        # Calculate total efficiency
        total_efficiency = (
            inverter_efficiency * 
            (1 - dc_losses) * 
            (1 - ac_losses) *
            (1 - shading_losses) *
            (1 - soiling_losses) *
            (1 - mismatch_losses) *
            degradation_factor
        )
        
        return total_efficiency
    
    def calculate_temperature_effect(self, 
                                   ambient_temp_c: float,
                                   irradiance_w_m2: float,
                                   temp_coefficient: float,
                                   nominal_operating_cell_temp: float = 45.0) -> float:
        """Calculate temperature effect on PV module performance."""
        
        # Estimate cell temperature using NOCT model
        cell_temp = ambient_temp_c + (irradiance_w_m2 / 1000) * (nominal_operating_cell_temp - 20)
        
        # Calculate temperature effect (reference is 25°C)
        temp_effect = 1 + temp_coefficient * (cell_temp - 25)
        
        return max(0.0, temp_effect)  # Ensure non-negative
    
    def calculate_enhanced_energy_production(self, 
                                           # Location and time
                                           latitude: float,
                                           longitude: float, 
                                           target_datetime,
                                           
                                           # PV System Configuration (from frontend)
                                           pv_module_type: str = "winaico_gg_black_450",
                                           module_count: int = 40,
                                           tilt: float = 30.0,
                                           azimuth: float = 0.0,
                                           dimensionsfaktor_pv: float = 2.0,
                                           
                                           # System Efficiency Parameters (from frontend)
                                           inverter_type: str = "quality_inverter",
                                           installation_type: str = "standard",  # affects losses
                                           dc_losses: float = 0.02,
                                           ac_losses: float = 0.01,
                                           shading_losses: float = 0.0,
                                           soiling_losses: float = 0.02,
                                           mismatch_losses: float = 0.02,
                                           
                                           # Environmental Parameters
                                           ambient_temp_c: float = 20.0,
                                           
                                           # System Age (from frontend)
                                           system_age_years: int = 0,
                                           annual_degradation: float = 0.005,
                                           
                                           # Time Period
                                           time_period_hours: float = 1.0):
        """
        Calculate enhanced energy production with all frontend parameters.
        This replaces the simple formula with comprehensive calculations.
        """
        
        print(f"🔋 Enhanced Energy Production Calculation (500MB Grid)")
        print(f"   Location: {latitude:.3f}°N, {longitude:.3f}°E")
        print(f"   Date/Time: {target_datetime}")
        print(f"   PV System: {module_count}x {pv_module_type}")
        print(f"   Configuration: {tilt}°/{azimuth}°")
        
        # Get PV module specifications
        if pv_module_type not in self.pv_modules:
            print(f"❌ Unknown PV module type: {pv_module_type}")
            print(f"   Available types: {list(self.pv_modules.keys())}")
            return None
        
        module_spec = self.pv_modules[pv_module_type]
        print(f"   Module power: {module_spec['power_wp']} Wp")
        print(f"   Module efficiency: {module_spec['efficiency']*100:.1f}%")
        
        # Apply dimensionsfaktor (sizing factor from frontend)
        effective_module_count = int(module_count * dimensionsfaktor_pv / 2.0)  # 2.0 is default
        print(f"   Effective modules (with sizing factor): {effective_module_count}")
        
        # Get solar irradiance using optimized grid
        irradiance = self.interpolate_radiation(latitude, longitude, tilt, azimuth, target_datetime)
        if irradiance is None:
            print("❌ Could not determine solar irradiance")
            return None
        
        # Adjust losses based on installation type
        installation_loss_factors = {
            "standard": {"dc": 0.02, "ac": 0.01},
            "premium": {"dc": 0.015, "ac": 0.008},
            "basic": {"dc": 0.03, "ac": 0.015}
        }
        
        if installation_type in installation_loss_factors:
            dc_losses = installation_loss_factors[installation_type]["dc"]
            ac_losses = installation_loss_factors[installation_type]["ac"]
        
        # Calculate system efficiency
        system_efficiency = self.calculate_system_efficiency(
            inverter_type=inverter_type,
            dc_losses=dc_losses,
            ac_losses=ac_losses,
            shading_losses=shading_losses,
            soiling_losses=soiling_losses,
            mismatch_losses=mismatch_losses,
            degradation_years=system_age_years,
            annual_degradation=annual_degradation
        )
        
        print(f"   System efficiency: {system_efficiency*100:.1f}%")
        
        # Calculate temperature effect
        temp_effect = self.calculate_temperature_effect(
            ambient_temp_c=ambient_temp_c,
            irradiance_w_m2=irradiance,
            temp_coefficient=module_spec['temp_coefficient']
        )
        
        print(f"   Temperature effect: {temp_effect*100:.1f}%")
        
        # Calculate total system power
        total_power_kw = (effective_module_count * module_spec['power_wp']) / 1000
        
        # Enhanced energy production formula with all frontend parameters
        energy_kwh = (
            total_power_kw *                    # System power in kW (with sizing factor)
            (irradiance / 1000) *               # Irradiance factor (1000 W/m² = 1)
            system_efficiency *                 # All system losses (dynamic)
            temp_effect *                       # Temperature effect (dynamic)
            time_period_hours                   # Time period
        )
        
        print(f"💡 Enhanced Energy Production: {energy_kwh:.3f} kWh")
        
        # Compare with simple calculation
        simple_energy = (module_count * module_spec['power_wp'] / 1000) * (irradiance/1000) * self.DEFAULT_SYSTEM_EFFICIENCY * time_period_hours
        improvement = ((energy_kwh - simple_energy) / simple_energy * 100) if simple_energy > 0 else 0
        
        print(f"🔄 Comparison:")
        print(f"   Simple method: {simple_energy:.3f} kWh")
        print(f"   Enhanced method: {energy_kwh:.3f} kWh")
        print(f"   Improvement: {improvement:+.1f}%")
        
        # Detailed results
        results = {
            # Input parameters
            'datetime': target_datetime,
            'latitude': latitude,
            'longitude': longitude,
            'tilt': tilt,
            'azimuth': azimuth,
            
            # PV System (with frontend parameters)
            'pv_module_type': pv_module_type,
            'module_count': module_count,
            'effective_module_count': effective_module_count,
            'dimensionsfaktor_pv': dimensionsfaktor_pv,
            'module_power_wp': module_spec['power_wp'],
            'total_power_kw': total_power_kw,
            'module_efficiency': module_spec['efficiency'],
            
            # Environmental
            'irradiance_w_m2': irradiance,
            'ambient_temp_c': ambient_temp_c,
            'temperature_effect': temp_effect,
            
            # System Performance (all frontend parameters)
            'inverter_type': inverter_type,
            'installation_type': installation_type,
            'dc_losses': dc_losses,
            'ac_losses': ac_losses,
            'shading_losses': shading_losses,
            'soiling_losses': soiling_losses,
            'mismatch_losses': mismatch_losses,
            'system_efficiency': system_efficiency,
            'system_age_years': system_age_years,
            'annual_degradation': annual_degradation,
            
            # Results
            'time_period_hours': time_period_hours,
            'energy_kwh': energy_kwh,
            'energy_wh': energy_kwh * 1000,
            'specific_yield_kwh_kwp': energy_kwh / total_power_kw if total_power_kw > 0 else 0,
            
            # Comparison
            'simple_calculation_kwh': simple_energy,
            'improvement_percent': improvement,
            
            # Metadata
            'data_source': 'Enhanced 500MB Grid Calculator',
            'calculation_method': 'All frontend parameters included',
            'grid_version': '500MB TypeScript Compatible Enhanced'
        }
        
        return results

def main():
    """Interactive optimized solar calculator."""
    print("\n🔆" + "=" * 46 + "🔆")
    print()
    print("=== Optimized Solar Calculator (500MB) ===")
    print("TypeScript-compatible instant calculations")
    print()
    
    try:
        calculator = OptimizedSolarCalculator()
        
        # Show available configurations
        print(f"\n📊 Available configurations in optimized grid:")
        config_names = {
            (30, 0): "30° South (most common)",
            (30, 90): "30° West (morning sun)",
            (30, 270): "30° East (evening sun)",
            (45, 0): "45° South (steep roofs)"
        }
        
        for tilt, azimuth in calculator.available_configs:
            name = config_names.get((tilt, azimuth), "Custom")
            print(f"   {tilt}° tilt, {azimuth}° azimuth - {name}")
        
        # Demo both calculation methods
        print("\n📋 Demo: München PV System Comparison (Available Data)")
        print("="*50)
        
        demo_datetime = datetime(2023, 6, 15, 12, 0)
        
        # Simple method demo
        print("\n🔹 Simple Method (Backward Compatible):")
        simple_result = calculator.calculate_energy_for_datetime(
            48.1, 11.6, 25, 270, demo_datetime, 20, 0.4, 3600
        )
        
        if simple_result:
            print(f"   Energy: {simple_result['energy_kWh']:.3f} kWh")
            print(f"   System efficiency: {simple_result['system_efficiency']:.1%} (fixed)")
        
        # Enhanced method demo
        print("\n🔹 Enhanced Method (All Frontend Parameters):")
        enhanced_result = calculator.calculate_enhanced_energy_production(
            latitude=48.1,
            longitude=11.6,
            target_datetime=demo_datetime,
            pv_module_type="winaico_gg_black_450",
            module_count=40,
            tilt=25.0,
            azimuth=270.0,
            dimensionsfaktor_pv=2.0,
            inverter_type="quality_inverter",
            shading_losses=0.0,
            system_age_years=1,
            ambient_temp_c=25.0,
            time_period_hours=1.0
        )
        
        if enhanced_result:
            print(f"   Energy: {enhanced_result['energy_kwh']:.3f} kWh")
            print(f"   System efficiency: {enhanced_result['system_efficiency']*100:.1f}% (dynamic)")
            print(f"   Improvement: {enhanced_result['improvement_percent']:+.1f}%")
        
        print("\n" + "="*50)
        print("💡 The enhanced method includes all frontend parameters!")
        print("   - Dynamic system efficiency")
        print("   - Temperature effects")
        print("   - Module-specific characteristics")
        print("   - Installation type losses")
        print("   - System aging effects")
        
        print("\n" + "="*60)
        print("📍 VERFÜGBARE GRID-DATEN - Use these coordinates:")
        print("   München: 48.1°N, 11.6°E, 25° Neigung, 270° Azimuth (Ost)")
        print("   (Other locations require grid data download)")
        print("="*60)
        print("\nPlease enter the following parameters for custom calculation:")
        
        # Get user input with Munich examples
        latitude = float(input("Breitengrad (z.B. 48.1 für München): "))
        longitude = float(input("Längengrad (z.B. 11.6 für München): "))
        tilt = int(input("Neigung in Grad (z.B. 25 für verfügbare Daten): "))
        azimuth = int(input("Ausrichtung in Grad (z.B. 270=Ost für verfügbare Daten): "))
        
        # Date and time input
        date_str = input("Datum (YYYY-MM-DD, z.B. 2023-06-15): ")
        time_str = input("Uhrzeit (HH:MM, z.B. 12:00): ")
        
        # Parse datetime
        datetime_str = f"{date_str} {time_str}"
        target_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        
        # System parameters
        N = int(input("Anzahl der Module (z.B. 30): "))
        P_mod = float(input("Nennleistung pro Modul in kWp (z.B. 0.41 für 410Wp): "))
        dt = int(input("Zeitraum in Sekunden (z.B. 900 für 15 Min): "))
        
        print("\n" + "="*50)
        print("⚡ Optimized calculation starting...")
        
        # Calculate energy
        results = calculator.calculate_energy_for_datetime(
            latitude, longitude, tilt, azimuth, target_datetime,
            N, P_mod, dt
        )
        
        if results:
            print("\n" + "="*50)
            print("🎉 RESULTS")
            print("="*50)
            print(f"📍 Location: {results['latitude']:.3f}°N, {results['longitude']:.3f}°E")
            print(f"🧭 Orientation: {results['azimuth']}° (0°=South)")
            print(f"📐 Tilt: {results['tilt']}°")
            print(f"📅 Date/Time: {results['datetime']}")
            print(f"☀️  Global radiation: {results['radiation_W_per_m2']:.1f} W/m²")
            print(f"🏠 Modules: {results['num_modules']}")
            print(f"⚡ Power per module: {results['power_per_module_kWp']:.2f} kWp")
            print(f"📊 System efficiency: {results['system_efficiency']:.1%} (fixed)")
            print(f"⏱️  Time period: {results['time_period_seconds']} seconds")
            print(f"🗄️  Data source: {results['data_source']}")
            print(f"💾 Grid version: {results['grid_version']}")
            
            print(f"\n🎯 ENERGY GENERATION:")
            print(f">>> {results['energy_kWh']:.4f} kWh <<<")
            print(f">>> {results['energy_Wh']:.1f} Wh <<<")
            
        else:
            print("\n❌ Calculation failed!")
            print("💡 Possible causes:")
            print("   - Location outside Germany")
            print("   - Optimized grid data not downloaded")
            print("   - Invalid date/time")
            
    except FileNotFoundError:
        print("❌ Optimized grid data not found!")
        print("💡 Please run 'python3 grid_downloader_500mb.py' first.")
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except ValueError as e:
        print(f"\n❌ Input error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Enhanced Solar Calculator with Full Frontend Integration
Includes all user input parameters from the frontend for accurate energy production calculation.
"""

import os
import pickle
import math
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional, Tuple

class EnhancedSolarCalculator:
    """
    Enhanced solar calculator that includes all frontend parameters for maximum accuracy.
    Replaces the fixed 0.8 system efficiency with dynamic calculations based on user inputs.
    """
    
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
        
        # Initialize battery database  
        self.battery_types = self.get_battery_database()
        
        # Initialize consumption characteristics
        self.consumption_characteristics = self.get_consumption_characteristics()
        
        print(f"✅ Enhanced solar calculator ready")
        print(f"   Grid directory: {data_dir}")
        print(f"   Available configurations: {len(self.available_configs)}")
        print(f"   PV modules in database: {len(self.pv_modules)}")
        print(f"   Battery types available: {len(self.battery_types)}")
    
    def get_pv_modules_database(self) -> Dict:
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
    
    def get_battery_database(self) -> Dict:
        """Database of available battery systems."""
        return {
            "sonnenbatterie_10": {
                "name": "sonnenBatterie 10 Pv / 11.0",
                "capacity_kwh": 11.0,
                "usable_capacity_kwh": 10.0,
                "efficiency": 0.95,
                "max_charge_rate_kw": 4.6,
                "max_discharge_rate_kw": 4.6,
                "cycles": 10000
            },
            "sonnenbatterie_eco": {
                "name": "sonnenBatterie eco 8.0/10",
                "capacity_kwh": 10.0,
                "usable_capacity_kwh": 8.0,
                "efficiency": 0.93,
                "max_charge_rate_kw": 3.3,
                "max_discharge_rate_kw": 3.3,
                "cycles": 10000
            },
            "generic_10kwh": {
                "name": "Generic 10 kWh Battery",
                "capacity_kwh": 10.0,
                "usable_capacity_kwh": 9.0,
                "efficiency": 0.90,
                "max_charge_rate_kw": 5.0,
                "max_discharge_rate_kw": 5.0,
                "cycles": 6000
            }
        }
    
    def get_consumption_characteristics(self) -> Dict:
        """Consumption pattern characteristics from frontend."""
        return {
            "day_distributed": {
                "id": "day",
                "name": "Über den Tag verteilt",
                "household_factor": 1.1,
                "heat_pump_factor": 0.72858,
                "ecar_factor": 0.61105,
                "description": "Energy consumption spread throughout the day"
            },
            "evening_night": {
                "id": "night", 
                "name": "Überwiegend Abends/Morgens",
                "household_factor": 1.0,
                "heat_pump_factor": 0.4839,
                "ecar_factor": 0.5555,
                "description": "Energy consumption mainly in evening/morning"
            },
            "yield_optimized": {
                "id": "optimized",
                "name": "Ertragsoptimiert", 
                "household_factor": 1.18,
                "heat_pump_factor": 0.77424,
                "ecar_factor": 0.65549,
                "description": "Energy consumption optimized for solar yield"
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
    
    def calculate_system_efficiency(self, 
                                   inverter_efficiency: float = 0.96,
                                   dc_losses: float = 0.02,
                                   ac_losses: float = 0.01,
                                   shading_losses: float = 0.0,
                                   soiling_losses: float = 0.02,
                                   mismatch_losses: float = 0.02,
                                   degradation_years: int = 0,
                                   annual_degradation: float = 0.005) -> float:
        """
        Calculate dynamic system efficiency based on all loss factors.
        
        Parameters:
        - inverter_efficiency: Inverter efficiency (default 96%)
        - dc_losses: DC wiring losses (default 2%)
        - ac_losses: AC wiring losses (default 1%) 
        - shading_losses: Shading losses (default 0%)
        - soiling_losses: Soiling/dirt losses (default 2%)
        - mismatch_losses: Module mismatch losses (default 2%)
        - degradation_years: Years since installation
        - annual_degradation: Annual degradation rate (default 0.5%)
        
        Returns:
        - Total system efficiency factor
        """
        
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
        """
        Calculate temperature effect on PV module performance.
        
        Parameters:
        - ambient_temp_c: Ambient temperature in Celsius
        - irradiance_w_m2: Solar irradiance in W/m²
        - temp_coefficient: Temperature coefficient (%/°C)
        - nominal_operating_cell_temp: NOCT in °C
        
        Returns:
        - Temperature correction factor (1.0 = no effect)
        """
        
        # Estimate cell temperature using NOCT model
        cell_temp = ambient_temp_c + (irradiance_w_m2 / 1000) * (nominal_operating_cell_temp - 20)
        
        # Calculate temperature effect (reference is 25°C)
        temp_effect = 1 + temp_coefficient * (cell_temp - 25)
        
        return max(0.0, temp_effect)  # Ensure non-negative
    
    def find_nearest_configuration(self, target_tilt, target_azimuth):
        """Find the nearest available configuration with enhanced intelligence."""
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
                # Fallback to 30° south for steep non-south orientations
                match = (30, 0)
                print(f"🎯 Fallback match: {match[0]}°/{match[1]}° (Steep non-south → South)")
                return match
        
        # Fallback: find truly nearest by Euclidean distance
        min_distance = float('inf')
        best_config = None
        
        for config_tilt, config_azimuth in self.available_configs:
            # Handle azimuth wraparound (e.g., 350° vs 10°)
            azimuth_diff = min(
                abs(target_azimuth - config_azimuth),
                abs(target_azimuth - config_azimuth + 360),
                abs(target_azimuth - config_azimuth - 360)
            )
            
            distance = math.sqrt((target_tilt - config_tilt)**2 + azimuth_diff**2)
            
            if distance < min_distance:
                min_distance = distance
                best_config = (config_tilt, config_azimuth)
        
        if best_config:
            print(f"🔍 Nearest match: {best_config[0]}°/{best_config[1]}° (distance: {min_distance:.1f}°)")
            accuracy = max(0, 100 - min_distance * 2)  # Rough accuracy estimate
            print(f"   Expected accuracy: ~{accuracy:.0f}%")
        
        return best_config
    
    def find_grid_points(self, latitude, longitude):
        """Find the 4 surrounding grid points for interpolation."""
        # Round to grid boundaries
        lat_lower = math.floor(latitude / self.grid_resolution) * self.grid_resolution
        lat_upper = lat_lower + self.grid_resolution
        lon_lower = math.floor(longitude / self.grid_resolution) * self.grid_resolution  
        lon_upper = lon_lower + self.grid_resolution
        
        # Return 4 corner points for bilinear interpolation
        grid_points = [
            (lat_lower, lon_lower),   # Southwest
            (lat_lower, lon_upper),   # Southeast
            (lat_upper, lon_lower),   # Northwest
            (lat_upper, lon_upper)    # Northeast
        ]
        
        return grid_points
    
    def load_grid_data(self, latitude, longitude, tilt, azimuth):
        """Load radiation data from grid file."""
        filename = f"grid_{latitude}_{longitude}_{tilt}_{azimuth}_2023.pkl"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            return data
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None
    
    def extract_radiation_from_data(self, data, target_datetime):
        """Extract radiation value for specific datetime from grid data."""
        if data is None:
            return None
        
        try:
            # Convert to pandas DataFrame if it's a list of dictionaries
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                
                # Ensure datetime column exists and is datetime type
                if 'time' in df.columns:
                    df['datetime'] = pd.to_datetime(df['time'])
                elif 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                else:
                    print("No datetime column found in data")
                    return None
                
                # Find closest time match
                target_ts = pd.Timestamp(target_datetime)
                time_diff = abs(df['datetime'] - target_ts)
                closest_idx = time_diff.idxmin()
                
                # Get radiation value (try different possible column names)
                radiation_columns = ['poa_total', 'total_radiation', 'G(i)', 'irradiance']
                for col in radiation_columns:
                    if col in df.columns:
                        return df.loc[closest_idx, col]
                
                print(f"Available columns: {list(df.columns)}")
                return None
                
            else:
                print("Data format not recognized")
                return None
                
        except Exception as e:
            print(f"Error extracting radiation: {e}")
            return None
    
    def interpolate_radiation(self, latitude, longitude, tilt, azimuth, target_datetime):
        """Get radiation value using bilinear interpolation from grid points."""
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
            # Extract coordinates and values
            lats = [p['lat'] for p in grid_data]
            lons = [p['lon'] for p in grid_data]
            values = [p['radiation'] for p in grid_data if p['radiation'] is not None]
            
            if len(values) < 4:
                # Fallback to nearest neighbor if missing radiation values
                return self.interpolate_radiation(latitude, longitude, tilt, azimuth, target_datetime)
            
            # Bilinear interpolation
            lat_min, lat_max = min(lats), max(lats)
            lon_min, lon_max = min(lons), max(lons)
            
            # Normalize coordinates
            lat_norm = (latitude - lat_min) / (lat_max - lat_min) if lat_max != lat_min else 0
            lon_norm = (longitude - lon_min) / (lon_max - lon_min) if lon_max != lon_min else 0
            
            # Find corner values
            sw = next(p['radiation'] for p in grid_data if p['lat'] == lat_min and p['lon'] == lon_min)
            se = next(p['radiation'] for p in grid_data if p['lat'] == lat_min and p['lon'] == lon_max)  
            nw = next(p['radiation'] for p in grid_data if p['lat'] == lat_max and p['lon'] == lon_min)
            ne = next(p['radiation'] for p in grid_data if p['lat'] == lat_max and p['lon'] == lon_max)
            
            # Bilinear interpolation
            south = sw * (1 - lon_norm) + se * lon_norm
            north = nw * (1 - lon_norm) + ne * lon_norm
            result = south * (1 - lat_norm) + north * lat_norm
            
            print(f"☀️  Radiation: {result:.1f} W/m² (bilinear interpolation)")
            return result
            
        except Exception as e:
            print(f"Interpolation failed: {e}, using nearest neighbor")
            # Fallback to nearest neighbor
            min_distance = float('inf')
            closest_radiation = None
            
            for point in grid_data:
                if point['radiation'] is not None:
                    distance = math.sqrt((latitude - point['lat'])**2 + (longitude - point['lon'])**2)
                    if distance < min_distance:
                        min_distance = distance
                        closest_radiation = point['radiation']
            
            return closest_radiation
    
    def calculate_enhanced_energy(self, 
                                # Location and time
                                latitude: float,
                                longitude: float, 
                                target_datetime: datetime,
                                
                                # PV System Configuration
                                pv_module_type: str = "winaico_gg_black_450",
                                module_count: int = 40,
                                tilt: float = 30.0,
                                azimuth: float = 0.0,
                                
                                # System Efficiency Parameters
                                inverter_efficiency: float = 0.96,
                                dc_losses: float = 0.02,
                                ac_losses: float = 0.01,
                                shading_losses: float = 0.0,
                                soiling_losses: float = 0.02,
                                mismatch_losses: float = 0.02,
                                
                                # Environmental Parameters
                                ambient_temp_c: float = 20.0,
                                
                                # System Age
                                system_age_years: int = 0,
                                annual_degradation: float = 0.005,
                                
                                # Time Period
                                time_period_hours: float = 1.0) -> Optional[Dict]:
        """
        Calculate enhanced energy production with all frontend parameters.
        
        Returns detailed results including all calculation steps.
        """
        
        print(f"🔋 Enhanced Energy Calculation")
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
        
        # Get solar irradiance
        irradiance = self.interpolate_radiation(latitude, longitude, tilt, azimuth, target_datetime)
        if irradiance is None:
            print("❌ Could not determine solar irradiance")
            return None
        
        # Calculate system efficiency
        system_efficiency = self.calculate_system_efficiency(
            inverter_efficiency=inverter_efficiency,
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
        total_power_kw = (module_count * module_spec['power_wp']) / 1000
        
        # Calculate energy production
        energy_kwh = (
            total_power_kw *                    # System power in kW
            (irradiance / 1000) *               # Irradiance factor (1000 W/m² = 1)
            system_efficiency *                 # System losses
            temp_effect *                       # Temperature effect
            time_period_hours                   # Time period
        )
        
        print(f"💡 Energy Production: {energy_kwh:.3f} kWh")
        
        # Detailed results
        results = {
            # Input parameters
            'datetime': target_datetime,
            'latitude': latitude,
            'longitude': longitude,
            'tilt': tilt,
            'azimuth': azimuth,
            
            # PV System
            'pv_module_type': pv_module_type,
            'module_count': module_count,
            'module_power_wp': module_spec['power_wp'],
            'total_power_kw': total_power_kw,
            'module_efficiency': module_spec['efficiency'],
            
            # Environmental
            'irradiance_w_m2': irradiance,
            'ambient_temp_c': ambient_temp_c,
            'temperature_effect': temp_effect,
            
            # System Performance
            'inverter_efficiency': inverter_efficiency,
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
            
            # Metadata
            'data_source': 'Enhanced Calculator (500MB Grid)',
            'calculation_method': 'Dynamic efficiency with all frontend parameters'
        }
        
        return results

def main():
    """Interactive enhanced solar calculator."""
    try:
        calculator = EnhancedSolarCalculator()
        
        print("\n" + "="*60)
        print("🔆 Enhanced Solar Energy Calculator")
        print("   With Full Frontend Parameter Integration")
        print("="*60)
        
        # Example calculation with all parameters
        print("\n📋 Example: Berlin PV System")
        
        result = calculator.calculate_enhanced_energy(
            # Location
            latitude=52.5,
            longitude=13.4,
            target_datetime=datetime(2023, 6, 15, 12, 0),
            
            # PV System
            pv_module_type="winaico_gg_black_450",
            module_count=40,
            tilt=30.0,
            azimuth=0.0,  # South
            
            # Advanced parameters
            inverter_efficiency=0.96,
            shading_losses=0.05,  # 5% shading
            ambient_temp_c=25.0,
            system_age_years=2,
            
            time_period_hours=1.0
        )
        
        if result:
            print(f"\n📊 Detailed Results:")
            print(f"   Total System Power: {result['total_power_kw']:.1f} kWp")
            print(f"   Solar Irradiance: {result['irradiance_w_m2']:.0f} W/m²")
            print(f"   System Efficiency: {result['system_efficiency']*100:.1f}%")
            print(f"   Temperature Effect: {result['temperature_effect']*100:.1f}%")
            print(f"   Energy Production: {result['energy_kwh']:.3f} kWh")
            print(f"   Specific Yield: {result['specific_yield_kwh_kwp']:.3f} kWh/kWp")
            
            # Compare with simple calculation
            simple_energy = result['total_power_kw'] * (result['irradiance_w_m2']/1000) * 0.8 * 1.0
            improvement = ((result['energy_kwh'] - simple_energy) / simple_energy * 100) if simple_energy > 0 else 0
            
            print(f"\n🔄 Comparison with Simple Method:")
            print(f"   Simple (0.8 efficiency): {simple_energy:.3f} kWh")
            print(f"   Enhanced calculation: {result['energy_kwh']:.3f} kWh")
            print(f"   Improvement: {improvement:+.1f}%")
        
        print("\n✅ Enhanced calculator ready for simulation!")
        print("   Use calculate_enhanced_energy() for accurate production values")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

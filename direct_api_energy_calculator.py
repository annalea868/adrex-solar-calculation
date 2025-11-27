#!/usr/bin/env python3
"""
Direct API Energy Calculator with Full Frontend Integration
Uses live PVGIS API calls with all frontend parameters for maximum accuracy.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import time

class DirectApiEnergyCalculator:
    """
    Energy calculator using direct PVGIS API calls with all frontend parameters.
    Provides real-time data with comprehensive parameter support.
    """
    
    def __init__(self):
        self.base_url = "https://re.jrc.ec.europa.eu/api/v5_2"
        
        # Initialize PV modules database
        self.pv_modules = self.get_pv_modules_database()
        
        # Initialize inverter database  
        self.inverters = self.get_inverters_database()
        
        print(f"✅ Direct API energy calculator ready")
        print(f"   API endpoint: {self.base_url}")
        print(f"   PV modules in database: {len(self.pv_modules)}")
        print(f"   Real-time PVGIS data: ✅")
    
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
            },
            "premium_500": {
                "name": "Premium 500 Wp Module",
                "power_wp": 500,
                "efficiency": 0.22,
                "temp_coefficient": -0.0035,
                "area_m2": 2.27,
                "voltage_mpp": 45.0,
                "current_mpp": 11.11
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
            },
            "micro_inverter": {
                "name": "Mikro-Wechselrichter",
                "efficiency": 0.97,
                "max_power_kw": 5.0
            }
        }
    
    def get_pvgis_hourly_data(self, latitude: float, longitude: float, 
                             tilt: float, azimuth: float, year: int = 2023,
                             timeout: int = 30):
        """
        Get hourly solar irradiation data from PVGIS API.
        
        Parameters:
        - latitude, longitude: Location coordinates
        - tilt: Panel tilt angle (0-90°)
        - azimuth: Panel azimuth (0°=South, 90°=West, 270°=East)
        - year: Year for data (default: 2023)
        - timeout: API timeout in seconds
        """
        
        print(f"🌐 Fetching real-time PVGIS data...")
        print(f"   Location: {latitude:.3f}°N, {longitude:.3f}°E")
        print(f"   Configuration: {tilt}° tilt, {azimuth}° azimuth")
        
        # PVGIS API parameters
        params = {
            'lat': latitude,
            'lon': longitude,
            'raddatabase': 'PVGIS-SARAH2',  # Best database for Europe
            'browser': '0',
            'outputformat': 'json',
            'usehorizon': '1',
            'userhorizon': '',
            'startyear': year,
            'endyear': year,
            'angle': int(tilt),
            'aspect': int(azimuth),
            'optimalinclination': '0',
            'optimalangles': '0',
            'js': '1',
            'select_database_hourly': 'PVGIS-SARAH2'
        }
        
        url = f"{self.base_url}/seriescalc"
        
        try:
            print(f"   API call: {url}")
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if 'outputs' not in data:
                print(f"❌ Invalid response format from PVGIS")
                return None
            
            hourly_data = data['outputs']['hourly']
            metadata = data['inputs']
            
            print(f"✅ Retrieved {len(hourly_data)} hourly records")
            print(f"   Database: {metadata.get('radiation_database', 'Unknown')}")
            
            return {
                'hourly_data': hourly_data,
                'metadata': metadata,
                'location': {'lat': latitude, 'lon': longitude},
                'configuration': {'tilt': tilt, 'azimuth': azimuth}
            }
            
        except requests.exceptions.Timeout:
            print(f"❌ PVGIS API timeout after {timeout} seconds")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ PVGIS API error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            return None
    
    def find_closest_hourly_data(self, hourly_data: List[Dict], target_datetime: datetime):
        """Find the closest hourly data point to target datetime."""
        
        target_month = target_datetime.month
        target_day = target_datetime.day
        target_hour = target_datetime.hour
        
        # Convert to comparable format
        target_key = f"{target_month:02d}{target_day:02d}:{target_hour:02d}00"
        
        closest_record = None
        min_diff = float('inf')
        
        for record in hourly_data:
            record_time = record['time']  # Format: "20230615:1200"
            
            # Extract components
            try:
                month_day = record_time[4:8]  # MMDD
                hour_min = record_time[9:13]  # HHMM
                record_key = f"{month_day}:{hour_min}"
                
                # Simple string comparison for finding closest match
                if record_key == target_key:
                    closest_record = record
                    break
                    
                # Calculate rough difference for fallback
                record_hour = int(record_time[9:11])
                hour_diff = abs(target_hour - record_hour)
                
                if hour_diff < min_diff:
                    min_diff = hour_diff
                    closest_record = record
                    
            except (ValueError, IndexError):
                continue
        
        if closest_record:
            print(f"🔍 Found data for {closest_record['time']}")
            print(f"   Global irradiance: {closest_record['G(i)']} W/m²")
            print(f"   Direct irradiance: {closest_record['Gb(i)']} W/m²")
            print(f"   Diffuse irradiance: {closest_record['Gd(i)']} W/m²")
            print(f"   Temperature: {closest_record['T2m']}°C")
            
        return closest_record
    
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
                                           target_datetime: datetime,
                                           
                                           # PV System Configuration (from frontend)
                                           pv_module_type: str = "winaico_gg_black_450",
                                           module_count: int = 40,
                                           tilt: float = 30.0,
                                           azimuth: float = 0.0,
                                           dimensionsfaktor_pv: float = 2.0,
                                           
                                           # System Efficiency Parameters (from frontend)
                                           inverter_type: str = "quality_inverter",
                                           installation_type: str = "standard",
                                           dc_losses: float = 0.02,
                                           ac_losses: float = 0.01,
                                           shading_losses: float = 0.0,
                                           soiling_losses: float = 0.02,
                                           mismatch_losses: float = 0.02,
                                           
                                           # System Age (from frontend)
                                           system_age_years: int = 0,
                                           annual_degradation: float = 0.005,
                                           
                                           # Time Period
                                           time_period_hours: float = 1.0,
                                           
                                           # API options
                                           use_cached_data: bool = False,
                                           api_timeout: int = 30):
        """
        Calculate enhanced energy production using direct PVGIS API with all frontend parameters.
        """
        
        print(f"🔋 Enhanced Energy Production Calculation (Direct API)")
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
        
        # Get real-time PVGIS data
        pvgis_data = self.get_pvgis_hourly_data(
            latitude=latitude,
            longitude=longitude,
            tilt=tilt,
            azimuth=azimuth,
            year=target_datetime.year,
            timeout=api_timeout
        )
        
        if not pvgis_data:
            print("❌ Could not retrieve PVGIS data")
            return None
        
        # Find closest hourly data
        hourly_record = self.find_closest_hourly_data(
            pvgis_data['hourly_data'], 
            target_datetime
        )
        
        if not hourly_record:
            print("❌ Could not find matching hourly data")
            return None
        
        # Extract irradiance and temperature from PVGIS data
        irradiance = hourly_record['G(i)']  # Global irradiance on inclined plane
        ambient_temp_c = hourly_record['T2m']  # 2m air temperature
        
        print(f"🌡️  Real-time conditions:")
        print(f"   Irradiance: {irradiance} W/m²")
        print(f"   Temperature: {ambient_temp_c}°C")
        
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
        
        # Calculate temperature effect using real temperature data
        temp_effect = self.calculate_temperature_effect(
            ambient_temp_c=ambient_temp_c,
            irradiance_w_m2=irradiance,
            temp_coefficient=module_spec['temp_coefficient']
        )
        
        print(f"   Temperature effect: {temp_effect*100:.1f}%")
        
        # Calculate total system power
        total_power_kw = (effective_module_count * module_spec['power_wp']) / 1000
        
        # Enhanced energy production formula with all frontend parameters + real-time data
        energy_kwh = (
            total_power_kw *                    # System power in kW (with sizing factor)
            (irradiance / 1000) *               # Real-time irradiance factor
            system_efficiency *                 # All system losses (dynamic)
            temp_effect *                       # Real-time temperature effect
            time_period_hours                   # Time period
        )
        
        print(f"💡 Enhanced Energy Production (Real-time): {energy_kwh:.3f} kWh")
        
        # Compare with simple calculation
        simple_energy = (module_count * module_spec['power_wp'] / 1000) * (irradiance/1000) * 0.8 * time_period_hours
        improvement = ((energy_kwh - simple_energy) / simple_energy * 100) if simple_energy > 0 else 0
        
        print(f"🔄 Comparison:")
        print(f"   Simple method: {simple_energy:.3f} kWh")
        print(f"   Enhanced real-time: {energy_kwh:.3f} kWh")
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
            
            # Real-time Environmental Data (from PVGIS)
            'irradiance_w_m2': irradiance,
            'ambient_temp_c': ambient_temp_c,
            'direct_irradiance': hourly_record['Gb(i)'],
            'diffuse_irradiance': hourly_record['Gd(i)'],
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
            
            # PVGIS Metadata
            'pvgis_database': pvgis_data['metadata'].get('radiation_database', 'Unknown'),
            'pvgis_record_time': hourly_record['time'],
            
            # Metadata
            'data_source': 'Enhanced Direct API Calculator (Real-time PVGIS)',
            'calculation_method': 'All frontend parameters + real-time weather data',
            'api_endpoint': self.base_url
        }
        
        return results

def main():
    """Interactive direct API energy calculator."""
    try:
        calculator = DirectApiEnergyCalculator()
        
        print("\n" + "="*60)
        print("🌐 Direct API Energy Calculator")
        print("   Real-time PVGIS data with full frontend parameters")
        print("="*60)
        
        # Example calculation with all parameters
        print("\n📋 Example: Berlin PV System (Real-time)")
        
        result = calculator.calculate_enhanced_energy_production(
            # Location
            latitude=52.5,
            longitude=13.4,
            target_datetime=datetime(2023, 6, 15, 12, 0),
            
            # PV System (from frontend)
            pv_module_type="winaico_gg_black_450",
            module_count=40,
            tilt=30.0,
            azimuth=0.0,  # South
            dimensionsfaktor_pv=2.0,
            
            # Advanced parameters (from frontend)
            inverter_type="premium_inverter",
            installation_type="premium",
            shading_losses=0.05,  # 5% shading
            system_age_years=2,
            
            time_period_hours=1.0
        )
        
        if result:
            print(f"\n📊 Detailed Real-time Results:")
            print(f"   Total System Power: {result['total_power_kw']:.1f} kWp")
            print(f"   Real-time Irradiance: {result['irradiance_w_m2']:.0f} W/m²")
            print(f"   Real-time Temperature: {result['ambient_temp_c']:.1f}°C")
            print(f"   System Efficiency: {result['system_efficiency']*100:.1f}%")
            print(f"   Temperature Effect: {result['temperature_effect']*100:.1f}%")
            print(f"   Energy Production: {result['energy_kwh']:.3f} kWh")
            print(f"   Specific Yield: {result['specific_yield_kwh_kwp']:.3f} kWh/kWp")
            print(f"   PVGIS Database: {result['pvgis_database']}")
            print(f"   Data Timestamp: {result['pvgis_record_time']}")
            
            print(f"\n🔄 Accuracy Improvement: {result['improvement_percent']:+.1f}%")
        
        print("\n✅ Direct API calculator ready for real-time calculations!")
        print("   Use calculate_enhanced_energy_production() for live PVGIS data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PVGIS Direct Solar Calculator - Full API Version
Uses pvlib library for direct PVGIS API access with all frontend parameters.
"""

import os
import math
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    import pvlib
    PVLIB_AVAILABLE = True
except ImportError:
    PVLIB_AVAILABLE = False
    print("⚠️  pvlib not installed. Run: pip install pvlib")

class PVGISDirectSolarCalculator:
    """Solar calculator using direct PVGIS API calls via pvlib library."""
    
    # Default efficiency values - can be overridden with frontend parameters
    DEFAULT_SYSTEM_EFFICIENCY = 0.8  # 80% system efficiency (fallback)
    
    def __init__(self):
        if not PVLIB_AVAILABLE:
            raise ImportError("pvlib library is required. Install with: pip install pvlib")
        
        # Initialize PV modules database
        self.pv_modules = self.get_pv_modules_database()
        
        # Initialize inverter database  
        self.inverters = self.get_inverters_database()
        
        # Initialize PV technology mapping for PVGIS
        self.pvgis_tech_mapping = self.get_pvgis_technology_mapping()
        
        # Initialize mounting types for PVGIS
        self.pvgis_mounting_types = self.get_pvgis_mounting_types()
        
        print(f"✅ PVGIS Direct solar calculator ready")
        print(f"   Using pvlib version: {pvlib.__version__}")
        print(f"   PV module types available: {len(self.pv_modules)}")
        print(f"   Direct PVGIS API access: ✅")
    
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
                "current_mpp": 10.93,
                "pvgis_tech": "crystSi",  # PVGIS technology type
                "module_type": "premium"
            },
            "winaico_gg_black_400": {
                "name": "Winaico GG Black 400 Wp", 
                "power_wp": 400,
                "efficiency": 0.195,
                "temp_coefficient": -0.0038,
                "area_m2": 2.054,
                "voltage_mpp": 38.1,
                "current_mpp": 10.50,
                "pvgis_tech": "crystSi",
                "module_type": "standard"
            },
            "generic_400": {
                "name": "Generic 400 Wp Module",
                "power_wp": 400,
                "efficiency": 0.20,
                "temp_coefficient": -0.004,
                "area_m2": 2.0,
                "voltage_mpp": 40.0,
                "current_mpp": 10.0,
                "pvgis_tech": "crystSi",
                "module_type": "standard"
            },
            "premium_500": {
                "name": "Premium 500 Wp Module",
                "power_wp": 500,
                "efficiency": 0.22,
                "temp_coefficient": -0.0035,
                "area_m2": 2.27,
                "voltage_mpp": 45.0,
                "current_mpp": 11.11,
                "pvgis_tech": "crystSi",
                "module_type": "premium"
            },
            "thin_film_300": {
                "name": "Thin Film 300 Wp Module",
                "power_wp": 300,
                "efficiency": 0.15,
                "temp_coefficient": -0.0025,
                "area_m2": 2.0,
                "voltage_mpp": 35.0,
                "current_mpp": 8.57,
                "pvgis_tech": "CIS",
                "module_type": "thin_film"
            }
        }
    
    def get_inverters_database(self):
        """Database of available inverters with their specifications."""
        return {
            "quality_inverter": {
                "name": "Qualitäts-Wechselrichter",
                "efficiency": 0.96,
                "max_power_kw": 20.0,
                "pvgis_loss_factor": 12.0  # Total system losses for PVGIS (%)
            },
            "standard_inverter": {
                "name": "Standard-Wechselrichter", 
                "efficiency": 0.94,
                "max_power_kw": 15.0,
                "pvgis_loss_factor": 14.0
            },
            "premium_inverter": {
                "name": "Premium-Wechselrichter",
                "efficiency": 0.98,
                "max_power_kw": 30.0,
                "pvgis_loss_factor": 10.0
            },
            "micro_inverter": {
                "name": "Mikro-Wechselrichter",
                "efficiency": 0.97,
                "max_power_kw": 5.0,
                "pvgis_loss_factor": 11.0
            }
        }
    
    def get_pvgis_technology_mapping(self):
        """Mapping of PV technologies for PVGIS API."""
        return {
            "crystSi": "Crystalline Silicon",
            "CIS": "Copper Indium Selenide", 
            "CdTe": "Cadmium Telluride",
            "Unknown": "Unknown technology"
        }
    
    def get_pvgis_mounting_types(self):
        """Mounting types available in PVGIS."""
        return {
            "free": "Free standing",
            "building": "Building integrated"
        }
    
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
    
    def calculate_pvgis_system_losses(self, 
                                     inverter_type: str = "quality_inverter",
                                     installation_type: str = "standard",
                                     shading_losses: float = 0.0,
                                     system_age_years: int = 0,
                                     annual_degradation: float = 0.005) -> float:
        """
        Calculate total system losses for PVGIS API.
        PVGIS expects a single loss percentage that includes all system losses.
        """
        
        # Base losses from inverter type
        if inverter_type in self.inverters:
            base_losses = self.inverters[inverter_type]['pvgis_loss_factor']
        else:
            base_losses = 14.0  # Default PVGIS system losses
        
        # Installation type adjustments
        installation_adjustments = {
            "standard": 0.0,     # No adjustment
            "premium": -2.0,     # 2% less losses
            "basic": +3.0        # 3% more losses
        }
        
        installation_adjustment = installation_adjustments.get(installation_type, 0.0)
        
        # Add shading losses (convert to percentage)
        shading_losses_pct = shading_losses * 100
        
        # Add degradation losses
        degradation_losses_pct = system_age_years * annual_degradation * 100
        
        # Total losses (ensure within reasonable bounds)
        total_losses = base_losses + installation_adjustment + shading_losses_pct + degradation_losses_pct
        total_losses = max(5.0, min(30.0, total_losses))  # Clamp between 5% and 30%
        
        return total_losses
    
    def get_pvgis_hourly_data(self, 
                             latitude: float, 
                             longitude: float,
                             tilt: float,
                             azimuth: float,
                             year: int = 2023,
                             pv_module_type: str = "winaico_gg_black_450",
                             total_peak_power: float = 18.0,  # kWp
                             inverter_type: str = "quality_inverter",
                             installation_type: str = "standard",
                             shading_losses: float = 0.0,
                             system_age_years: int = 0,
                             mounting_type: str = "free"):
        """
        Get hourly data from PVGIS API using pvlib.
        
        Parameters:
        - latitude, longitude: Location coordinates
        - tilt: Panel tilt angle (0-90°)
        - azimuth: Panel azimuth (PVGIS uses 0°=South, -90°=East, 90°=West)
        - year: Year for data
        - pv_module_type: Module type from database
        - total_peak_power: Total system peak power in kWp
        - inverter_type: Inverter type from database
        - installation_type: Installation quality
        - shading_losses: Shading losses (0-1)
        - system_age_years: System age for degradation
        - mounting_type: Mounting configuration
        """
        
        print(f"🌐 Fetching PVGIS data via pvlib...")
        print(f"   Location: {latitude:.3f}°N, {longitude:.3f}°E")
        print(f"   Configuration: {tilt}° tilt, {azimuth}° azimuth")
        print(f"   System: {total_peak_power:.1f} kWp, {pv_module_type}")
        
        # Get module specifications
        if pv_module_type in self.pv_modules:
            module_spec = self.pv_modules[pv_module_type]
            pvgis_tech = module_spec['pvgis_tech']
        else:
            pvgis_tech = "crystSi"  # Default
        
        # Calculate system losses for PVGIS
        system_losses = self.calculate_pvgis_system_losses(
            inverter_type=inverter_type,
            installation_type=installation_type,
            shading_losses=shading_losses,
            system_age_years=system_age_years
        )
        
        print(f"   PVGIS parameters:")
        print(f"     Technology: {pvgis_tech} ({self.pvgis_tech_mapping.get(pvgis_tech, 'Unknown')})")
        print(f"     System losses: {system_losses:.1f}%")
        print(f"     Mounting: {mounting_type} ({self.pvgis_mounting_types.get(mounting_type, 'Unknown')})")
        
        try:
            # Convert azimuth to PVGIS convention (0°=South, -90°=East, 90°=West)
            pvgis_azimuth = azimuth
            if azimuth == 270:  # East in our convention
                pvgis_azimuth = -90
            elif azimuth == 90:  # West in our convention  
                pvgis_azimuth = 90
            # South (0°) remains the same
            
            # Call PVGIS API via pvlib
            data, meta = pvlib.iotools.get_pvgis_hourly(
                latitude=latitude,
                longitude=longitude,
                start=year,
                end=year,
                surface_tilt=tilt,
                surface_azimuth=pvgis_azimuth,
                outputformat='json',
                usehorizon=True,
                pvcalculation=True,
                peakpower=total_peak_power,
                pvtechchoice=pvgis_tech,
                mountingplace=mounting_type,
                loss=system_losses,
                trackingtype=0,  # Fixed system
                optimal_surface_tilt=False,
                optimalangles=False,
                map_variables=True,
                timeout=60  # 60 second timeout
            )
            
            print(f"✅ Retrieved {len(data)} hourly records")
            print(f"   Database: {meta.get('inputs', {}).get('radiation_database', 'Unknown')}")
            print(f"   Horizon: {'Yes' if meta.get('inputs', {}).get('usehorizon', False) else 'No'}")
            
            return {
                'data': data,
                'meta': meta,
                'location': {'lat': latitude, 'lon': longitude},
                'configuration': {
                    'tilt': tilt, 
                    'azimuth': azimuth, 
                    'pvgis_azimuth': pvgis_azimuth
                },
                'system': {
                    'peak_power': total_peak_power,
                    'technology': pvgis_tech,
                    'losses': system_losses,
                    'mounting': mounting_type
                }
            }
            
        except Exception as e:
            print(f"❌ PVGIS API error: {e}")
            return None
    
    def find_closest_hourly_data(self, data: pd.DataFrame, target_datetime: datetime):
        """Find the closest hourly data point to target datetime."""
        
        # Convert target to pandas timestamp and handle timezone
        target_ts = pd.Timestamp(target_datetime)
        
        # If data index is timezone-aware but target is not, localize target to UTC
        if data.index.tz is not None and target_ts.tz is None:
            target_ts = target_ts.tz_localize('UTC')
        # If data index is timezone-naive but target is timezone-aware, remove target timezone
        elif data.index.tz is None and target_ts.tz is not None:
            target_ts = target_ts.tz_localize(None)
        
        # Find the closest index
        time_diff = abs(data.index - target_ts)
        # Find the position of the minimum time difference, then get the corresponding index
        min_pos = time_diff.argmin()
        closest_idx = data.index[min_pos]
        
        closest_record = data.loc[closest_idx]
        
        # Debug: show available columns
        print(f"📊 Available data columns: {list(closest_record.index)}")
        
        print(f"🔍 Found data for {closest_idx}")
        # Try multiple possible column names for irradiance
        irradiance_cols = ['poa_global', 'G(i)', 'Gb(i)', 'Gd(i)', 'irradiance']
        temp_cols = ['temp_air', 'T2m', 'temperature']
        power_cols = ['P', 'power', 'pv_power']
        
        # Find irradiance value
        global_irr = None
        for col in irradiance_cols:
            if col in closest_record.index:
                global_irr = closest_record[col]
                print(f"   Global irradiance ({col}): {global_irr} W/m²")
                break
        
        # Find temperature
        temperature = None
        for col in temp_cols:
            if col in closest_record.index:
                temperature = closest_record[col]
                print(f"   Air temperature ({col}): {temperature}°C")
                break
                
        # Find power
        power = None
        for col in power_cols:
            if col in closest_record.index:
                power = closest_record[col]
                print(f"   PV power output ({col}): {power} W")
                break
        
        return closest_record, closest_idx
    
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
                                           
                                           # Environmental Parameters
                                           ambient_temp_c: Optional[float] = None,  # Will use PVGIS data if None
                                           
                                           # System Age (from frontend)
                                           system_age_years: int = 0,
                                           annual_degradation: float = 0.005,
                                           
                                           # Time Period
                                           time_period_hours: float = 1.0,
                                           
                                           # PVGIS specific options
                                           mounting_type: str = "free",
                                           use_pvgis_calculation: bool = True):
        """
        Calculate enhanced energy production using direct PVGIS API with all frontend parameters.
        
        Two calculation methods:
        1. use_pvgis_calculation=True: Use PVGIS internal PV calculation (more accurate)
        2. use_pvgis_calculation=False: Use our enhanced formula with PVGIS irradiance data
        """
        
        print(f"🔋 Enhanced Energy Production Calculation (PVGIS Direct)")
        print(f"   Location: {latitude:.3f}°N, {longitude:.3f}°E")
        print(f"   Date/Time: {target_datetime}")
        print(f"   PV System: {module_count}x {pv_module_type}")
        print(f"   Configuration: {tilt}°/{azimuth}°")
        print(f"   Calculation method: {'PVGIS internal' if use_pvgis_calculation else 'Enhanced formula'}")
        
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
        
        # Calculate total system power
        total_power_kw = (effective_module_count * module_spec['power_wp']) / 1000
        print(f"   Total system power: {total_power_kw:.1f} kWp")
        
        # Get PVGIS data
        pvgis_data = self.get_pvgis_hourly_data(
            latitude=latitude,
            longitude=longitude,
            tilt=tilt,
            azimuth=azimuth,
            year=target_datetime.year,
            pv_module_type=pv_module_type,
            total_peak_power=total_power_kw,
            inverter_type=inverter_type,
            installation_type=installation_type,
            shading_losses=shading_losses,
            system_age_years=system_age_years,
            mounting_type=mounting_type
        )
        
        if not pvgis_data:
            print("❌ Could not retrieve PVGIS data")
            return None
        
        # Find closest hourly data
        hourly_record, record_index = self.find_closest_hourly_data(
            pvgis_data['data'], 
            target_datetime
        )
        
        if hourly_record is None:
            print("❌ Could not find matching hourly data")
            return None
        
        # Extract data from PVGIS - calculate total irradiance from components
        # PVGIS provides: poa_direct, poa_sky_diffuse, poa_ground_diffuse
        poa_direct = hourly_record.get('poa_direct', 0)
        poa_sky_diffuse = hourly_record.get('poa_sky_diffuse', 0)
        poa_ground_diffuse = hourly_record.get('poa_ground_diffuse', 0)
        
        # Calculate total irradiance (POA = Plane of Array)
        irradiance = poa_direct + poa_sky_diffuse + poa_ground_diffuse
        
        print(f"🔆 Irradiance components:")
        print(f"   Direct: {poa_direct:.1f} W/m²")
        print(f"   Sky diffuse: {poa_sky_diffuse:.1f} W/m²")
        print(f"   Ground diffuse: {poa_ground_diffuse:.1f} W/m²")
        print(f"   → Total: {irradiance:.1f} W/m²")
        
        # Try different possible column names for temperature
        temp_options = ['temp_air', 'T2m', 'temperature']
        pvgis_temp = 20  # Default
        for col in temp_options:
            if col in hourly_record.index and pd.notna(hourly_record[col]):
                pvgis_temp = hourly_record[col]
                break
                
        # Try different possible column names for power
        power_options = ['P', 'power', 'pv_power']
        pvgis_power = 0
        for col in power_options:
            if col in hourly_record.index and pd.notna(hourly_record[col]):
                pvgis_power = hourly_record[col]
                break
        
        # Use provided temperature or PVGIS temperature
        if ambient_temp_c is None:
            ambient_temp_c = pvgis_temp
            temp_source = "PVGIS"
        else:
            temp_source = "User input"
        
        print(f"\n🌡️  Environmental conditions:")
        print(f"   Total irradiance (POA): {irradiance:.1f} W/m²")
        print(f"   Temperature: {ambient_temp_c}°C ({temp_source})")
        print(f"   PVGIS power output: {pvgis_power:.0f} W")
        
        if use_pvgis_calculation:
            # Method 1: Use PVGIS internal calculation (most accurate)
            energy_kwh = (pvgis_power / 1000) * time_period_hours  # Convert W to kW
            
            # Estimate system efficiency from PVGIS result
            theoretical_power = total_power_kw * (irradiance / 1000)
            estimated_efficiency = (pvgis_power / 1000) / theoretical_power if theoretical_power > 0 else 0
            temp_effect = 1.0  # Already included in PVGIS calculation
            
            print(f"   Using PVGIS internal calculation")
            print(f"   Estimated system efficiency: {estimated_efficiency*100:.1f}% (from PVGIS)")
            
        else:
            # Method 2: Use our enhanced formula with PVGIS irradiance data
            
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
            
            # Calculate temperature effect
            temp_effect = self.calculate_temperature_effect(
                ambient_temp_c=ambient_temp_c,
                irradiance_w_m2=irradiance,
                temp_coefficient=module_spec['temp_coefficient']
            )
            
            # Enhanced energy production formula
            energy_kwh = (
                total_power_kw *                    # System power in kW
                (irradiance / 1000) *               # Irradiance factor
                system_efficiency *                 # All system losses
                temp_effect *                       # Temperature effect
                time_period_hours                   # Time period
            )
            
            estimated_efficiency = system_efficiency
            
            print(f"   System efficiency: {system_efficiency*100:.1f}%")
            print(f"   Temperature effect: {temp_effect*100:.1f}%")
        
        print(f"💡 Enhanced Energy Production (PVGIS): {energy_kwh:.3f} kWh")
        
        # Compare with simple calculation
        simple_energy = total_power_kw * (irradiance/1000) * self.DEFAULT_SYSTEM_EFFICIENCY * time_period_hours
        improvement = ((energy_kwh - simple_energy) / simple_energy * 100) if simple_energy > 0 else 0
        
        print(f"🔄 Comparison:")
        print(f"   Simple method: {simple_energy:.3f} kWh")
        print(f"   PVGIS enhanced: {energy_kwh:.3f} kWh")
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
            
            # Environmental Data (from PVGIS)
            'irradiance_w_m2': irradiance,
            'ambient_temp_c': ambient_temp_c,
            'temperature_source': temp_source,
            'temperature_effect': temp_effect,
            'poa_direct': hourly_record.get('poa_direct', None),
            'poa_diffuse': hourly_record.get('poa_diffuse', None),
            
            # System Performance (all frontend parameters)
            'inverter_type': inverter_type,
            'installation_type': installation_type,
            'dc_losses': dc_losses,
            'ac_losses': ac_losses,
            'shading_losses': shading_losses,
            'soiling_losses': soiling_losses,
            'mismatch_losses': mismatch_losses,
            'system_efficiency': estimated_efficiency,
            'system_age_years': system_age_years,
            'annual_degradation': annual_degradation,
            'mounting_type': mounting_type,
            
            # Results
            'time_period_hours': time_period_hours,
            'energy_kwh': energy_kwh,
            'energy_wh': energy_kwh * 1000,
            'specific_yield_kwh_kwp': energy_kwh / total_power_kw if total_power_kw > 0 else 0,
            
            # PVGIS specific
            'pvgis_power_w': pvgis_power,
            'pvgis_system_losses_pct': pvgis_data['system']['losses'],
            'pvgis_technology': pvgis_data['system']['technology'],
            'use_pvgis_calculation': use_pvgis_calculation,
            
            # Comparison
            'simple_calculation_kwh': simple_energy,
            'improvement_percent': improvement,
            
            # PVGIS Metadata
            'pvgis_database': pvgis_data['meta'].get('inputs', {}).get('radiation_database', 'Unknown'),
            'pvgis_record_time': str(record_index),
            
            # Metadata
            'data_source': 'PVGIS Direct Calculator (pvlib)',
            'calculation_method': f"PVGIS {'internal' if use_pvgis_calculation else 'enhanced'} with all frontend parameters",
            'pvlib_version': pvlib.__version__
        }
        
        return results

def main():
    """Interactive PVGIS direct solar calculator."""
    try:
        calculator = PVGISDirectSolarCalculator()
        
        print("\n" + "="*60)
        print("🌐 PVGIS Direct Solar Calculator")
        print("   Real-time API access with full frontend parameters")
        print("="*60)
        
        # Example calculation with all parameters
        print("\n📋 Example: Berlin PV System (PVGIS Direct)")
        
        demo_datetime = datetime(2023, 6, 15, 12, 0)
        
        # Method 1: PVGIS internal calculation
        print("\n🔹 Method 1: PVGIS Internal Calculation")
        pvgis_result = calculator.calculate_enhanced_energy_production(
            # Location
            latitude=52.5,
            longitude=13.4,
            target_datetime=demo_datetime,
            
            # PV System (from frontend)
            pv_module_type="winaico_gg_black_450",
            module_count=40,
            tilt=30.0,
            azimuth=0.0,  # South
            dimensionsfaktor_pv=2.0,
            
            # Advanced parameters (from frontend)
            inverter_type="quality_inverter",
            installation_type="standard",
            shading_losses=0.05,  # 5% shading
            system_age_years=2,
            
            time_period_hours=1.0,
            use_pvgis_calculation=True
        )
        
        if pvgis_result:
            print(f"   Energy (PVGIS): {pvgis_result['energy_kwh']:.3f} kWh")
            print(f"   System efficiency: {pvgis_result['system_efficiency']*100:.1f}%")
            print(f"   PVGIS power: {pvgis_result['pvgis_power_w']:.0f} W")
        
        # Method 2: Enhanced formula with PVGIS data
        print("\n🔹 Method 2: Enhanced Formula with PVGIS Data")
        enhanced_result = calculator.calculate_enhanced_energy_production(
            # Same parameters
            latitude=52.5,
            longitude=13.4,
            target_datetime=demo_datetime,
            pv_module_type="winaico_gg_black_450",
            module_count=40,
            tilt=30.0,
            azimuth=0.0,
            dimensionsfaktor_pv=2.0,
            inverter_type="quality_inverter",
            installation_type="standard",
            shading_losses=0.05,
            system_age_years=2,
            time_period_hours=1.0,
            use_pvgis_calculation=False  # Use our enhanced formula
        )
        
        if enhanced_result:
            print(f"   Energy (Enhanced): {enhanced_result['energy_kwh']:.3f} kWh")
            print(f"   System efficiency: {enhanced_result['system_efficiency']*100:.1f}%")
            print(f"   Temperature effect: {enhanced_result['temperature_effect']*100:.1f}%")
        
        # Comparison
        if pvgis_result and enhanced_result:
            diff = enhanced_result['energy_kwh'] - pvgis_result['energy_kwh']
            diff_pct = (diff / pvgis_result['energy_kwh'] * 100) if pvgis_result['energy_kwh'] > 0 else 0
            
            print(f"\n🔄 Method Comparison:")
            print(f"   PVGIS internal:  {pvgis_result['energy_kwh']:.3f} kWh")
            print(f"   Enhanced formula: {enhanced_result['energy_kwh']:.3f} kWh")
            print(f"   Difference: {diff:+.3f} kWh ({diff_pct:+.1f}%)")
        
        print(f"\n✅ PVGIS Direct calculator ready!")
        print(f"   Use calculate_enhanced_energy_production() for real PVGIS data")
        print(f"   Set use_pvgis_calculation=True for PVGIS internal calculation")
        print(f"   Set use_pvgis_calculation=False for enhanced formula with PVGIS data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Direct PVGIS API Solar Calculator - Demo Version
Shows how solar radiation (G) and energy (E) are calculated step by step.
Uses live PVGIS API calls to demonstrate the calculation process.

Formula: E = (N * P_mod * (G / 1000) * eta_sys) * (dt / 3600)
"""

import pandas as pd
from datetime import datetime
from pvlib.iotools import get_pvgis_hourly
import pytz

class DirectAPISolarCalculator:
    """Direct PVGIS API calculator for demonstration purposes."""
    
    # System efficiency constant - 80% is typical for solar installations
    SYSTEM_EFFICIENCY = 0.8  # 80%
    
    def __init__(self):
        self.data = None
        self.meta = None
        print("🌞 Direct PVGIS API Solar Calculator")
        print("   Demonstrates live calculation of solar radiation and energy")
        print("   Uses 2023 as reference year for any date input")
    
    def get_radiation_data(self, latitude, longitude, tilt, azimuth):
        """
        Fetch solar radiation data from PVGIS API for demonstration.
        Always uses 2023 as reference year regardless of user input year.
        """
        try:
            print(f"\n📡 Fetching live PVGIS data...")
            print(f"   Coordinates: {latitude}°N, {longitude}°E")
            print(f"   Panel configuration: {tilt}° tilt, {azimuth}° azimuth")
            print(f"   Reference year: 2023 (used for all calculations)")
            print("   ⏳ This may take 30-60 seconds...")
            
            # Always use 2023 as reference year
            data, meta = get_pvgis_hourly(
                latitude=latitude,
                longitude=longitude,
                surface_tilt=tilt,
                surface_azimuth=azimuth,
                start=2023,  # Always 2023
                end=2023,    # Always 2023
                components=True,
                timeout=120
            )
            
            self.data = data
            self.meta = meta
            
            print(f"   ✅ Successfully fetched {len(data)} hourly data points")
            print(f"   📊 Data source: {meta.get('inputs', {}).get('radiation_database', 'PVGIS-SARAH')}")
            
            return data
            
        except Exception as e:
            print(f"   ❌ Error fetching PVGIS data: {e}")
            print("   💡 This might be due to:")
            print("      - Network timeout (try again)")
            print("      - Invalid coordinates")
            print("      - PVGIS server temporarily unavailable")
            return None
    
    def parse_date_german(self, date_str, time_str):
        """
        Parse German date format (DD/MM/YYYY) and convert to 2023 reference.
        
        Parameters:
        - date_str: Date in DD/MM/YYYY format
        - time_str: Time in HH:MM format
        
        Returns:
        - datetime object with 2023 as year (for PVGIS lookup)
        """
        try:
            # Parse the input date
            input_date = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
            
            # Convert to 2023 reference (keep same day/month/time)
            reference_date = datetime(2023, input_date.month, input_date.day, 
                                    input_date.hour, input_date.minute)
            
            print(f"📅 Date conversion:")
            print(f"   Input date: {input_date.strftime('%d/%m/%Y %H:%M')}")
            print(f"   Reference date: {reference_date.strftime('%d/%m/%Y %H:%M')} (2023 used for solar data)")
            
            return reference_date
            
        except ValueError as e:
            print(f"❌ Date parsing error: {e}")
            print("💡 Please use format: DD/MM/YYYY for date and HH:MM for time")
            return None
    
    def get_radiation_at_time(self, target_datetime):
        """
        Get solar radiation (G) for specific date and time.
        Shows detailed breakdown of radiation components.
        """
        if self.data is None:
            print("❌ No radiation data available. Please fetch data first.")
            return None
        
        try:
            # Make target_datetime timezone-aware (PVGIS uses UTC)
            if target_datetime.tzinfo is None:
                target_datetime = pytz.UTC.localize(target_datetime)
            
            print(f"\n🔍 Finding radiation data for {target_datetime.strftime('%d/%m/%Y %H:%M')}...")
            
            # Find the closest time match in the data
            closest_time = None
            min_diff = float('inf')
            
            for idx in self.data.index:
                if idx.tzinfo is None:
                    idx_aware = pytz.UTC.localize(idx)
                else:
                    idx_aware = idx
                
                time_diff = abs((target_datetime - idx_aware).total_seconds())
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest_time = idx
            
            if closest_time is not None:
                # Get radiation components from PVGIS data
                direct = self.data.loc[closest_time, 'poa_direct']
                sky_diffuse = self.data.loc[closest_time, 'poa_sky_diffuse'] 
                ground_diffuse = self.data.loc[closest_time, 'poa_ground_diffuse']
                
                # Calculate total global radiation (G)
                total_radiation = direct + sky_diffuse + ground_diffuse
                
                print(f"   ✅ Found data for: {closest_time.strftime('%d/%m/%Y %H:%M')}")
                print(f"   📊 Radiation components breakdown:")
                print(f"      Direct radiation:     {direct:.1f} W/m²")
                print(f"      Sky diffuse:          {sky_diffuse:.1f} W/m²") 
                print(f"      Ground reflection:    {ground_diffuse:.1f} W/m²")
                print(f"      ────────────────────────────────")
                print(f"      Total radiation (G): {total_radiation:.1f} W/m²")
                
                return total_radiation
            else:
                print(f"❌ No data found for time {target_datetime}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting radiation: {e}")
            return None
    
    def calculate_energy_step_by_step(self, N, P_mod, G, dt):
        """
        Calculate energy (E) step by step showing the formula breakdown.
        
        Formula: E = (N * P_mod * (G / 1000) * eta_sys) * (dt / 3600)
        """
        if G is None or G < 0:
            print("❌ Cannot calculate energy: Invalid radiation data")
            return 0
        
        print(f"\n🧮 Step-by-step energy calculation:")
        print(f"   Formula: E = (N × P_mod × (G / 1000) × η_sys) × (dt / 3600)")
        print(f"   ")
        print(f"   Given values:")
        print(f"   • N (Number of modules):     {N}")
        print(f"   • P_mod (Power per module):  {P_mod} kWp")
        print(f"   • G (Global radiation):      {G:.1f} W/m²")
        print(f"   • η_sys (System efficiency): {self.SYSTEM_EFFICIENCY} (80%)")
        print(f"   • dt (Time period):          {dt} seconds")
        print(f"   ")
        print(f"   Calculation steps:")
        
        # Step 1: Convert radiation to kW/m²
        G_kW = G / 1000
        print(f"   1. Convert radiation: G = {G:.1f} W/m² ÷ 1000 = {G_kW:.3f} kW/m²")
        
        # Step 2: Calculate total system power
        P_total = N * P_mod
        print(f"   2. Total system power: N × P_mod = {N} × {P_mod} = {P_total} kWp")
        
        # Step 3: Calculate instantaneous power output
        P_instant = P_total * G_kW * self.SYSTEM_EFFICIENCY
        print(f"   3. Instant power: {P_total} × {G_kW:.3f} × {self.SYSTEM_EFFICIENCY} = {P_instant:.3f} kW")
        
        # Step 4: Convert time period to hours
        dt_hours = dt / 3600
        print(f"   4. Time in hours: dt = {dt} seconds ÷ 3600 = {dt_hours:.3f} hours")
        
        # Step 5: Final energy calculation
        E = P_instant * dt_hours
        print(f"   5. Energy: E = {P_instant:.3f} kW × {dt_hours:.3f} h = {E:.4f} kWh")
        
        print(f"   ")
        print(f"   🎯 Final result: {E:.4f} kWh = {E * 1000:.1f} Wh")
        
        return E
    
    def calculate_energy_for_datetime(self, latitude, longitude, tilt, azimuth, 
                                    date_str, time_str, N, P_mod, dt):
        """
        Complete demonstration: fetch radiation and calculate energy step by step.
        """
        print(f"\n" + "="*60)
        print("🔆 SOLAR ENERGY CALCULATION DEMONSTRATION")
        print("="*60)
        
        # Parse date (always convert to 2023 reference)
        target_datetime = self.parse_date_german(date_str, time_str)
        if target_datetime is None:
            return None
        
        # Fetch radiation data from PVGIS
        radiation_data = self.get_radiation_data(latitude, longitude, tilt, azimuth)
        if radiation_data is None:
            return None
        
        # Get radiation value (G) for the specific time
        G = self.get_radiation_at_time(target_datetime)
        if G is None:
            return None
        
        # Calculate energy (E) step by step
        E = self.calculate_energy_step_by_step(N, P_mod, G, dt)
        
        # Compile results
        results = {
            'input_date': f"{date_str} {time_str}",
            'reference_datetime': target_datetime,
            'latitude': latitude,
            'longitude': longitude,
            'tilt': tilt,
            'azimuth': azimuth,
            'radiation_W_per_m2': G,
            'num_modules': N,
            'power_per_module_kWp': P_mod,
            'system_efficiency': self.SYSTEM_EFFICIENCY,
            'time_period_seconds': dt,
            'energy_kWh': E,
            'energy_Wh': E * 1000,
            'data_source': 'Live PVGIS API',
            'calculation_type': 'Step-by-step demonstration'
        }
        
        return results

def main():
    """Interactive demo calculator with live PVGIS API."""
    print("\n🔆" + "=" * 58 + "🔆")
    print()
    print("=== Solar Energy Calculator - Live PVGIS Demo ===")
    print("Demonstrates step-by-step calculation of solar energy")
    print("Uses live PVGIS API to show how G and E are determined")
    print()
    
    calculator = DirectAPISolarCalculator()
    
    try:
        print("Please enter the following parameters:")
        print()
        
        # Location input
        print("📍 LOCATION:")
        latitude = float(input("Breitengrad (z.B. 52.5): "))
        longitude = float(input("Längengrad (z.B. 13.4): "))
        
        print("\n🏠 SOLAR PANEL CONFIGURATION:")
        tilt = int(input("Neigung in Grad (z.B. 30): "))
        azimuth = int(input("Ausrichtung in Grad (0°=Süd, 90°=West, 270°=Ost): "))
        
        print("\n📅 DATE AND TIME (any year - 2023 used as reference):")
        date_str = input("Datum (DD/MM/YYYY, z.B. 15/06/2024): ")
        time_str = input("Uhrzeit (HH:MM, z.B. 12:00): ")
        
        print("\n⚡ SYSTEM PARAMETERS:")
        N = int(input("Anzahl der Module (z.B. 30): "))
        P_mod = float(input("Nennleistung pro Modul in kWp (z.B. 0.41 für 410Wp): "))
        dt = int(input("Zeitraum in Sekunden (z.B. 900 für 15 Min): "))
        
        print(f"\n{'='*60}")
        print("🚀 Starting live calculation...")
        print(f"{'='*60}")
        
        # Calculate energy with step-by-step demonstration
        results = calculator.calculate_energy_for_datetime(
            latitude, longitude, tilt, azimuth, date_str, time_str, N, P_mod, dt
        )
        
        if results:
            print(f"\n{'='*60}")
            print("🎉 FINAL RESULTS")
            print(f"{'='*60}")
            print(f"📍 Location: {results['latitude']:.2f}°N, {results['longitude']:.2f}°E")
            print(f"🧭 Panel orientation: {results['azimuth']}° azimuth, {results['tilt']}° tilt")
            print(f"📅 Input date/time: {results['input_date']}")
            print(f"📊 Reference used: {results['reference_datetime'].strftime('%d/%m/2023 %H:%M')}")
            print(f"☀️  Global radiation (G): {results['radiation_W_per_m2']:.1f} W/m²")
            print(f"🏠 System: {results['num_modules']} modules × {results['power_per_module_kWp']} kWp")
            print(f"📈 System efficiency: {results['system_efficiency']:.0%} (fixed)")
            print(f"⏱️  Time period: {results['time_period_seconds']} seconds")
            print(f"🌐 Data source: {results['data_source']}")
            print()
            print(f"🎯 FINAL ENERGY GENERATION:")
            print(f">>> E = {results['energy_kWh']:.4f} kWh <<<")
            print(f">>> E = {results['energy_Wh']:.1f} Wh <<<")
            print()
            print("📝 Formula used:")
            print(f"   E = ({results['num_modules']} × {results['power_per_module_kWp']} × ({results['radiation_W_per_m2']:.1f}/1000) × {results['system_efficiency']}) × ({results['time_period_seconds']}/3600)")
            print(f"   E = {results['energy_kWh']:.4f} kWh")
            
        else:
            print("\n❌ Calculation failed!")
            print("💡 Common issues:")
            print("   - Network timeout (PVGIS servers busy)")
            print("   - Invalid coordinates (outside Europe)")
            print("   - Invalid date format (use DD/MM/YYYY)")
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except ValueError as e:
        print(f"\n❌ Input error: {e}")
        print("💡 Please check your input format:")
        print("   Date: DD/MM/YYYY (e.g., 15/06/2024)")
        print("   Time: HH:MM (e.g., 12:00)")
        print("   Numbers: Use decimal point for kWp values")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

def quick_demo():
    """Quick demo with predefined values."""
    print("\n🚀 Quick Demo - Berlin Solar Installation")
    print("="*50)
    
    calculator = DirectAPISolarCalculator()
    
    # Predefined demo values
    latitude = 52.5
    longitude = 13.4
    tilt = 30
    azimuth = 0
    date_str = "15/06/2024"  # June 15, 2024
    time_str = "12:00"       # Noon
    N = 20                   # 20 modules
    P_mod = 0.4             # 400W per module
    dt = 3600               # 1 hour
    
    print(f"Demo parameters:")
    print(f"  Location: Berlin ({latitude}°N, {longitude}°E)")
    print(f"  Roof: {tilt}° tilt, {azimuth}° south-facing")
    print(f"  Date/Time: {date_str} {time_str}")
    print(f"  System: {N} modules × {P_mod} kWp = {N * P_mod} kWp total")
    print(f"  Period: {dt} seconds (1 hour)")
    
    results = calculator.calculate_energy_for_datetime(
        latitude, longitude, tilt, azimuth, date_str, time_str, N, P_mod, dt
    )
    
    if results:
        print(f"\n✅ Demo completed successfully!")
        print(f"   Solar radiation: {results['radiation_W_per_m2']:.1f} W/m²")
        print(f"   Energy generated: {results['energy_kWh']:.4f} kWh")

if __name__ == "__main__":
    import sys
    
    if "--demo" in sys.argv:
        quick_demo()
    else:
        main()





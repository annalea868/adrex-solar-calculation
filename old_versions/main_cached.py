#!/usr/bin/env python3
"""
Solar Energy Calculator using PVGIS API with Local Caching
Calculates solar energy generation with fast local data access.

Formula: E = (N * P_mod * (G / 1000) * eta_sys) * (dt / 3600)
Where:
- N: Number of modules
- P_mod: Nominal power per module in kWp
- G: Global radiation on module surface [W/m²]
- eta_sys: System efficiency (fixed at 80%)
- dt: Time period in seconds
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from data_fetcher import PVGISDataManager

class SolarEnergyCalculator:
    """Calculate solar energy generation using cached PVGIS data."""
    
    # System efficiency constant - typical value for most solar installations
    SYSTEM_EFFICIENCY = 0.8  # 80%
    
    def __init__(self):
        self.data = None
        self.meta = None
        self.data_manager = PVGISDataManager()
        self.current_params = None  # Store current data parameters
    
    def get_radiation_data(self, latitude, longitude, tilt, azimuth, year=2023):
        """
        Get radiation data using the cache manager.
        
        Parameters:
        - latitude: Breitengrad (degrees)
        - longitude: Längengrad (degrees) 
        - tilt: Neigung (degrees, 0° = horizontal, 90° = vertical)
        - azimuth: Ausrichtung (degrees, 0° = South, 90° = West, 270° = East, 180° = North)
        - year: Jahr für die Daten (default: 2023)
        
        Returns:
        - DataFrame with hourly radiation data
        """
        try:
            print(f"📊 Getting radiation data for: {latitude}°N, {longitude}°E")
            print(f"   Tilt: {tilt}°, Azimuth: {azimuth}°, Year: {year}")
            
            # Use the cache manager to get data
            data, meta = self.data_manager.get_data(latitude, longitude, tilt, azimuth, year)
            
            if data is not None:
                self.data = data
                self.meta = meta
                self.current_params = (latitude, longitude, tilt, azimuth, year)
                
                print(f"✅ Data ready: {len(data)} hourly data points")
                return data
            else:
                print("❌ Failed to get radiation data")
                return None
                
        except Exception as e:
            print(f"❌ Error getting radiation data: {e}")
            return None
    
    def get_radiation_at_time(self, target_datetime):
        """
        Get radiation value for a specific date and time.
        
        Parameters:
        - target_datetime: datetime object for the desired time
        
        Returns:
        - G: Global radiation in W/m²
        """
        if self.data is None:
            print("No radiation data available. Please fetch data first.")
            return None
        
        try:
            # Make target_datetime timezone-aware if it isn't already
            if target_datetime.tzinfo is None:
                # PVGIS data is typically in UTC
                import pytz
                target_datetime = pytz.UTC.localize(target_datetime)
            
            # Find the closest time match
            closest_time = None
            min_diff = float('inf')
            
            for idx in self.data.index:
                # Calculate time difference in seconds
                if idx.tzinfo is None:
                    # Make index timezone-aware if needed
                    import pytz
                    idx_aware = pytz.UTC.localize(idx)
                else:
                    idx_aware = idx
                
                time_diff = abs((target_datetime - idx_aware).total_seconds())
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest_time = idx
            
            if closest_time is not None:
                # Calculate total irradiance from POA components
                # POA (Plane of Array) = direct + sky diffuse + ground diffuse
                direct = self.data.loc[closest_time, 'poa_direct']
                sky_diffuse = self.data.loc[closest_time, 'poa_sky_diffuse'] 
                ground_diffuse = self.data.loc[closest_time, 'poa_ground_diffuse']
                
                # Total global irradiance on the tilted surface
                radiation = direct + sky_diffuse + ground_diffuse
                
                print(f"🌞 Radiation at {target_datetime}: {radiation:.2f} W/m²")
                print(f"   Direct: {direct:.1f}, Sky diffuse: {sky_diffuse:.1f}, Ground diffuse: {ground_diffuse:.1f}")
                print(f"   Closest data point: {closest_time}")
                return radiation
            else:
                print(f"No data found for time {target_datetime}")
                return None
                
        except Exception as e:
            print(f"Error getting radiation at time: {e}")
            return None
    
    def calculate_energy(self, N, P_mod, G, eta_sys, dt):
        """
        Calculate energy generation using the formula:
        E = (N * P_mod * (G / 1000) * eta_sys) * (dt / 3600)
        
        Parameters:
        - N: Anzahl der Module (number of modules)
        - P_mod: Nennleistung pro Modul in kWp (nominal power per module)
        - G: Globalstrahlung in W/m² (global radiation)
        - eta_sys: Systemwirkungsgrad (system efficiency, e.g., 0.8 for 80%)
        - dt: Zeitraum in Sekunden (time period in seconds)
        
        Returns:
        - E: Energy in kWh
        """
        if G is None or G < 0:
            return 0
        
        E = (N * P_mod * (G / 1000) * eta_sys) * (dt / 3600)
        
        return E
    
    def calculate_energy_for_datetime(self, latitude, longitude, tilt, azimuth, 
                                    target_datetime, N, P_mod, dt, year=None):
        """
        Complete calculation: get radiation data and calculate energy for specific datetime.
        
        Parameters:
        - latitude: Breitengrad
        - longitude: Längengrad  
        - tilt: Neigung
        - azimuth: Ausrichtung
        - target_datetime: datetime object
        - N: Anzahl der Module
        - P_mod: Nennleistung pro Modul in kWp
        - dt: Zeitraum in Sekunden
        - year: Jahr (if None, uses year from target_datetime)
        
        Note: System efficiency is fixed at 80% (0.8)
        
        Returns:
        - dict with results
        """
        if year is None:
            year = target_datetime.year
        
        # Get radiation data (from cache or fetch if needed)
        current_check = (latitude, longitude, tilt, azimuth, year)
        if self.current_params != current_check:
            data = self.get_radiation_data(latitude, longitude, tilt, azimuth, year)
            if data is None:
                return None
        
        # Get radiation for the specific time
        G = self.get_radiation_at_time(target_datetime)
        if G is None:
            return None
        
        # Calculate energy using fixed system efficiency
        E = self.calculate_energy(N, P_mod, G, self.SYSTEM_EFFICIENCY, dt)
        
        results = {
            'datetime': target_datetime,
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
            'data_source': 'PVGIS (cached)' if self.data_manager.has_cached_data(latitude, longitude, tilt, azimuth, year) else 'PVGIS (fresh)'
        }
        
        return results


def main():
    """Main function to demonstrate usage."""
    calculator = SolarEnergyCalculator()
    
    print("\n")
    print("🔆" + "=" * 46 + "🔆")
    print()
    print("=== Solar Energy Calculator (Cached) ===")
    print("Using local PVGIS data cache for fast access")
    print()
    
    try:
        # Get user input
        print("Please enter the following parameters:")
        
        latitude = float(input("Breitengrad (z.B. 52.5): "))
        longitude = float(input("Längengrad (z.B. 13.4): "))
        tilt = float(input("Neigung in Grad (z.B. 30): "))
        azimuth = float(input("Ausrichtung in Grad (0°=Süd, 90°=West, 270°=Ost, 180°=Nord): "))
        
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
        print("Berechnung läuft...")
        
        # Calculate energy
        results = calculator.calculate_energy_for_datetime(
            latitude, longitude, tilt, azimuth, target_datetime,
            N, P_mod, dt
        )
        
        if results:
            print("\n=== ERGEBNISSE ===")
            print(f"Standort: {results['latitude']:.2f}°N, {results['longitude']:.2f}°E")
            print(f"Ausrichtung: {results['azimuth']:.1f}° (0°=Süd)")
            print(f"Neigung: {results['tilt']:.1f}°")
            print(f"Datum/Zeit: {results['datetime']}")
            print(f"Globalstrahlung G: {results['radiation_W_per_m2']:.1f} W/m²")
            print(f"Anzahl Module: {results['num_modules']}")
            print(f"Leistung pro Modul: {results['power_per_module_kWp']:.2f} kWp")
            print(f"Systemwirkungsgrad: {results['system_efficiency']:.1%} (fest)")
            print(f"Zeitraum: {results['time_period_seconds']} Sekunden")
            print(f"Datenquelle: {results['data_source']}")
            print()
            print(f">>> ERZEUGTE ENERGIE: {results['energy_kWh']:.4f} kWh <<<")
            print(f">>> ERZEUGTE ENERGIE: {results['energy_Wh']:.1f} Wh <<<")
            
        else:
            print("Fehler bei der Berechnung!")
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"Fehler: {e}")


if __name__ == "__main__":
    main()

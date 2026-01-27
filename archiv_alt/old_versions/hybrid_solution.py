#!/usr/bin/env python3
"""
Hybrid Solar Calculator - Database + On-Demand PVGIS
Smart solution that uses database when available, PVGIS API when needed.
"""

import os
from datetime import datetime
from supabase_manager import SupabaseSolarManager
from data_fetcher import PVGISDataManager
import math

class HybridSolarCalculator:
    """
    Smart calculator that combines database and live PVGIS data.
    
    Strategy:
    1. Check database first for exact match
    2. Check database for nearby locations (interpolate)
    3. Fall back to PVGIS API with better timeout handling
    4. Cache new data for future use
    """
    
    SYSTEM_EFFICIENCY = 0.8  # 80%
    
    def __init__(self):
        try:
            self.db_manager = SupabaseSolarManager()
            self.pvgis_manager = PVGISDataManager()
            self.db_available = True
            print("✅ Hybrid calculator ready (Database + PVGIS)")
        except Exception as e:
            print(f"⚠️  Database not available, using PVGIS only: {e}")
            self.pvgis_manager = PVGISDataManager()
            self.db_available = False
    
    def find_nearest_database_location(self, latitude, longitude, tilt, azimuth, max_distance=0.5):
        """Find nearest location in database within max_distance degrees."""
        if not self.db_available:
            return None
        
        try:
            # Query for nearby locations
            result = self.db_manager.supabase.table('solar_radiation').select(
                'latitude, longitude, tilt, azimuth'
            ).gte(
                'latitude', latitude - max_distance
            ).lte(
                'latitude', latitude + max_distance
            ).gte(
                'longitude', longitude - max_distance
            ).lte(
                'longitude', longitude + max_distance
            ).eq(
                'tilt', tilt
            ).eq(
                'azimuth', azimuth
            ).limit(10).execute()
            
            if not result.data:
                return None
            
            # Find closest location
            min_distance = float('inf')
            closest_location = None
            
            for location in result.data:
                distance = math.sqrt(
                    (latitude - location['latitude'])**2 + 
                    (longitude - location['longitude'])**2
                )
                
                if distance < min_distance:
                    min_distance = distance
                    closest_location = location
            
            if min_distance <= max_distance:
                print(f"📍 Found nearby data: {closest_location['latitude']:.1f}°N, {closest_location['longitude']:.1f}°E")
                print(f"   Distance: {min_distance * 111:.0f} km")
                return closest_location
            
            return None
            
        except Exception as e:
            print(f"Error finding nearest location: {e}")
            return None
    
    def get_radiation_smart(self, latitude, longitude, tilt, azimuth, target_datetime):
        """
        Smart radiation lookup with multiple fallback strategies.
        """
        print(f"🧠 Smart lookup for {latitude}°N, {longitude}°E...")
        
        # Strategy 1: Try exact database match
        if self.db_available:
            print("   Strategy 1: Exact database match...")
            radiation_data = self.db_manager.get_radiation_for_datetime(
                latitude, longitude, tilt, azimuth, target_datetime
            )
            
            if radiation_data:
                print("   ✅ Found exact match in database!")
                return radiation_data['total_radiation']
        
        # Strategy 2: Try nearest database location
        if self.db_available:
            print("   Strategy 2: Nearest database location...")
            nearest = self.find_nearest_database_location(latitude, longitude, tilt, azimuth)
            
            if nearest:
                radiation_data = self.db_manager.get_radiation_for_datetime(
                    nearest['latitude'], nearest['longitude'], tilt, azimuth, target_datetime
                )
                
                if radiation_data:
                    print("   ✅ Using nearby database location!")
                    return radiation_data['total_radiation']
        
        # Strategy 3: PVGIS API with improved timeout handling
        print("   Strategy 3: PVGIS API (live download)...")
        return self.get_radiation_from_pvgis(latitude, longitude, tilt, azimuth, target_datetime)
    
    def get_radiation_from_pvgis(self, latitude, longitude, tilt, azimuth, target_datetime):
        """
        Get radiation from PVGIS with improved error handling and caching.
        """
        try:
            print("   🌐 Downloading from PVGIS (this may take 30-60 seconds)...")
            
            # Try to get data with longer timeout and retries
            for attempt in range(3):
                try:
                    data, meta = self.pvgis_manager.get_data(latitude, longitude, tilt, azimuth, target_datetime.year)
                    
                    if data is not None:
                        print("   ✅ PVGIS download successful!")
                        
                        # Find radiation for target time
                        radiation = self.find_radiation_in_data(data, target_datetime)
                        
                        # Cache this data in database for future use (if database available)
                        if self.db_available and radiation is not None:
                            print("   💾 Caching data for future use...")
                            self.cache_new_data_async(latitude, longitude, tilt, azimuth, data)
                        
                        return radiation
                    
                except Exception as e:
                    print(f"   ⚠️  PVGIS attempt {attempt + 1}/3 failed: {e}")
                    if attempt < 2:
                        print("   🔄 Retrying in 5 seconds...")
                        import time
                        time.sleep(5)
            
            print("   ❌ All PVGIS attempts failed")
            return None
            
        except Exception as e:
            print(f"   ❌ PVGIS error: {e}")
            return None
    
    def find_radiation_in_data(self, data, target_datetime):
        """Find radiation value for specific datetime in PVGIS data."""
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
                # Calculate total radiation
                direct = data.loc[closest_time, 'poa_direct']
                sky_diffuse = data.loc[closest_time, 'poa_sky_diffuse']
                ground_diffuse = data.loc[closest_time, 'poa_ground_diffuse']
                total_radiation = direct + sky_diffuse + ground_diffuse
                
                print(f"   ☀️  Radiation: {total_radiation:.1f} W/m² (Direct: {direct:.1f}, Diffuse: {sky_diffuse:.1f})")
                return total_radiation
            
            return None
            
        except Exception as e:
            print(f"Error extracting radiation from data: {e}")
            return None
    
    def cache_new_data_async(self, latitude, longitude, tilt, azimuth, data):
        """Cache new PVGIS data in database (non-blocking)."""
        try:
            # Round coordinates for caching
            lat_rounded = round(latitude, 1)
            lon_rounded = round(longitude, 1)
            
            # Check if already exists
            if not self.db_manager.check_data_exists(lat_rounded, lon_rounded, tilt, azimuth, 2023):
                print(f"   💾 Caching {lat_rounded}°N, {lon_rounded}°E for future use...")
                
                # Convert and upload data
                db_records = self.db_manager.convert_to_db_format(data, lat_rounded, lon_rounded, tilt, azimuth, 2023)
                
                # Upload in background (simplified)
                batch_size = 1000
                for i in range(0, len(db_records), batch_size):
                    batch = db_records[i:i + batch_size]
                    self.db_manager.supabase.table('solar_radiation').insert(batch).execute()
                
                print(f"   ✅ Cached {len(db_records)} data points")
            
        except Exception as e:
            print(f"   ⚠️  Caching failed (not critical): {e}")
    
    def calculate_energy_for_datetime(self, latitude, longitude, tilt, azimuth, 
                                    target_datetime, N, P_mod, dt):
        """
        Calculate energy with hybrid approach.
        """
        print(f"🔋 Calculating energy for {latitude}°N, {longitude}°E")
        
        # Get radiation using smart lookup
        G = self.get_radiation_smart(latitude, longitude, tilt, azimuth, target_datetime)
        
        if G is None:
            print("❌ Could not get radiation data")
            return None
        
        # Calculate energy
        E = (N * P_mod * (G / 1000) * self.SYSTEM_EFFICIENCY) * (dt / 3600)
        
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
            'data_source': 'Hybrid (Database + PVGIS)'
        }
        
        return results

def main():
    """Test the hybrid calculator."""
    print("\n🔆" + "=" * 46 + "🔆")
    print()
    print("=== Hybrid Solar Calculator ===")
    print("Smart combination of database + live PVGIS")
    print()
    
    try:
        calculator = HybridSolarCalculator()
        
        # Get user input
        print("Please enter the following parameters:")
        
        latitude = float(input("Breitengrad (z.B. 52.5): "))
        longitude = float(input("Längengrad (z.B. 13.4): "))
        tilt = int(input("Neigung in Grad (z.B. 30): "))
        azimuth = int(input("Ausrichtung in Grad (0°=Süd, 90°=West, 270°=Ost): "))
        
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
        print("🧠 Smart calculation starting...")
        
        # Calculate energy
        results = calculator.calculate_energy_for_datetime(
            latitude, longitude, tilt, azimuth, target_datetime,
            N, P_mod, dt
        )
        
        if results:
            print("\n" + "="*50)
            print("🎉 RESULTS")
            print("="*50)
            print(f"📍 Location: {results['latitude']:.2f}°N, {results['longitude']:.2f}°E")
            print(f"🧭 Orientation: {results['azimuth']}° (0°=South)")
            print(f"📐 Tilt: {results['tilt']}°")
            print(f"📅 Date/Time: {results['datetime']}")
            print(f"☀️  Global radiation: {results['radiation_W_per_m2']:.1f} W/m²")
            print(f"🏠 Modules: {results['num_modules']}")
            print(f"⚡ Power per module: {results['power_per_module_kWp']:.2f} kWp")
            print(f"📊 System efficiency: {results['system_efficiency']:.1%}")
            print(f"⏱️  Time period: {results['time_period_seconds']} seconds")
            print(f"🗄️  Data source: {results['data_source']}")
            
            print(f"\n🎯 ENERGY GENERATION:")
            print(f">>> {results['energy_kWh']:.4f} kWh <<<")
            print(f">>> {results['energy_Wh']:.1f} Wh <<<")
            
        else:
            print("\n❌ Calculation failed!")
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()

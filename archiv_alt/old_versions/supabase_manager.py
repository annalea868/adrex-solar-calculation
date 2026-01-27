#!/usr/bin/env python3
"""
Supabase Solar Data Manager
Handles uploading PVGIS data to Supabase database and querying it.
"""

import os
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from data_fetcher import PVGISDataManager

# Load environment variables
load_dotenv()

class SupabaseSolarManager:
    """Manages solar radiation data in Supabase database."""
    
    def __init__(self):
        # Get Supabase credentials from environment
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("Please set SUPABASE_URL and SUPABASE_KEY in .env file")
        
        self.supabase: Client = create_client(url, key)
        self.pvgis_manager = PVGISDataManager()
        
        print(f"✅ Connected to Supabase: {url}")
    
    def upload_location_data(self, latitude, longitude, tilt, azimuth, year=2023):
        """
        Download PVGIS data and upload to Supabase.
        
        Parameters:
        - latitude: Breitengrad
        - longitude: Längengrad
        - tilt: Neigung in degrees
        - azimuth: Ausrichtung in degrees (0=South, 90=West, 270=East)
        - year: Jahr für die Daten
        """
        try:
            print(f"\n📊 Processing: {latitude}°N, {longitude}°E (Tilt: {tilt}°, Azimuth: {azimuth}°)")
            
            # Check if data already exists
            if self.check_data_exists(latitude, longitude, tilt, azimuth, year):
                print("✅ Data already exists in database, skipping...")
                return True
            
            # Get PVGIS data
            data, meta = self.pvgis_manager.get_data(latitude, longitude, tilt, azimuth, year)
            
            if data is None:
                print("❌ Failed to get PVGIS data")
                return False
            
            # Convert to database format
            db_records = self.convert_to_db_format(data, latitude, longitude, tilt, azimuth, year)
            
            # Upload in batches (Supabase has limits)
            batch_size = 1000
            total_records = len(db_records)
            
            print(f"📤 Uploading {total_records:,} records in batches of {batch_size}...")
            
            for i in range(0, total_records, batch_size):
                batch = db_records[i:i + batch_size]
                
                result = self.supabase.table('solar_radiation').insert(batch).execute()
                
                if hasattr(result, 'error') and result.error:
                    print(f"❌ Error uploading batch {i//batch_size + 1}: {result.error}")
                    return False
                
                progress = min(i + batch_size, total_records)
                print(f"   ✅ Uploaded {progress:,}/{total_records:,} records")
            
            print(f"🎉 Successfully uploaded all data for {latitude}°N, {longitude}°E")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading location data: {e}")
            return False
    
    def convert_to_db_format(self, pvgis_data, latitude, longitude, tilt, azimuth, year):
        """Convert PVGIS data to database format."""
        records = []
        
        for timestamp, row in pvgis_data.iterrows():
            # Calculate total radiation
            total_radiation = (
                row['poa_direct'] + 
                row['poa_sky_diffuse'] + 
                row['poa_ground_diffuse']
            )
            
            record = {
                'latitude': float(latitude),
                'longitude': float(longitude),
                'tilt': int(tilt),
                'azimuth': int(azimuth),
                'year': int(year),
                'month': int(timestamp.month),
                'day': int(timestamp.day),
                'hour': int(timestamp.hour),
                'poa_direct': float(row['poa_direct']),
                'poa_sky_diffuse': float(row['poa_sky_diffuse']),
                'poa_ground_diffuse': float(row['poa_ground_diffuse']),
                'total_radiation': float(total_radiation),
                'temperature': float(row.get('temp_air', 0)) if 'temp_air' in row else None,
                'wind_speed': float(row.get('wind_speed', 0)) if 'wind_speed' in row else None
            }
            
            records.append(record)
        
        return records
    
    def check_data_exists(self, latitude, longitude, tilt, azimuth, year):
        """Check if data already exists for this location/config."""
        try:
            result = self.supabase.table('solar_radiation').select('id').eq(
                'latitude', latitude
            ).eq(
                'longitude', longitude
            ).eq(
                'tilt', tilt
            ).eq(
                'azimuth', azimuth
            ).eq(
                'year', year
            ).limit(1).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error checking existing data: {e}")
            return False
    
    def get_radiation_for_datetime(self, latitude, longitude, tilt, azimuth, target_datetime):
        """
        Get radiation data for specific location and time.
        
        Returns closest available data point.
        """
        try:
            # Round coordinates to nearest grid point
            lat_rounded = round(latitude, 1)
            lon_rounded = round(longitude, 1)
            
            result = self.supabase.table('solar_radiation').select(
                'total_radiation, poa_direct, poa_sky_diffuse, poa_ground_diffuse, temperature'
            ).eq(
                'latitude', lat_rounded
            ).eq(
                'longitude', lon_rounded
            ).eq(
                'tilt', tilt
            ).eq(
                'azimuth', azimuth
            ).eq(
                'month', target_datetime.month
            ).eq(
                'day', target_datetime.day
            ).eq(
                'hour', target_datetime.hour
            ).execute()
            
            if result.data:
                return result.data[0]
            else:
                # Try to find nearest time if exact match not found
                return self.find_nearest_radiation(lat_rounded, lon_rounded, tilt, azimuth, target_datetime)
                
        except Exception as e:
            print(f"Error getting radiation data: {e}")
            return None
    
    def find_nearest_radiation(self, latitude, longitude, tilt, azimuth, target_datetime):
        """Find radiation data for nearest available time."""
        try:
            # Get data for same day, different hours
            result = self.supabase.table('solar_radiation').select(
                'hour, total_radiation, poa_direct, poa_sky_diffuse, poa_ground_diffuse'
            ).eq(
                'latitude', latitude
            ).eq(
                'longitude', longitude
            ).eq(
                'tilt', tilt
            ).eq(
                'azimuth', azimuth
            ).eq(
                'month', target_datetime.month
            ).eq(
                'day', target_datetime.day
            ).execute()
            
            if not result.data:
                return None
            
            # Find closest hour
            target_hour = target_datetime.hour
            closest_data = min(result.data, key=lambda x: abs(x['hour'] - target_hour))
            
            return closest_data
            
        except Exception as e:
            print(f"Error finding nearest radiation: {e}")
            return None
    
    def populate_germany_grid(self):
        """Populate database with optimized Germany grid."""
        print("🇩🇪 Populating Germany Solar Database")
        print("=" * 50)
        
        # Major German cities (fine grid)
        major_cities = [
            ("Berlin", 52.5, 13.4),
            ("München", 48.1, 11.6),
            ("Hamburg", 53.6, 10.0),
            ("Köln", 50.9, 6.9),
            ("Frankfurt", 50.1, 8.7),
            ("Stuttgart", 48.8, 9.2),
            ("Düsseldorf", 51.2, 6.8),
            ("Dortmund", 51.5, 7.5),
            ("Dresden", 51.0, 13.7),
            ("Leipzig", 51.3, 12.4),
            ("Hannover", 52.4, 9.7),
            ("Bremen", 53.1, 8.8),
            ("Nürnberg", 49.5, 11.1),
            ("Mannheim", 49.5, 8.5),
            ("Karlsruhe", 49.0, 8.4)
        ]
        
        # Solar configurations (simplified)
        tilts = [30]  # Most common
        azimuths = [0, 90, 270]  # South, West, East
        
        success_count = 0
        total_locations = 0
        
        # Process major cities with fine grid
        print(f"\n🏙️  Processing {len(major_cities)} major cities...")
        
        for city_name, base_lat, base_lon in major_cities:
            print(f"\n📍 {city_name} ({base_lat}°N, {base_lon}°E)")
            
            # Fine grid around city (±0.5° = ~50km radius)
            for lat_offset in [-0.4, -0.2, 0.0, 0.2, 0.4]:
                for lon_offset in [-0.4, -0.2, 0.0, 0.2, 0.4]:
                    lat = round(base_lat + lat_offset, 1)
                    lon = round(base_lon + lon_offset, 1)
                    
                    for tilt in tilts:
                        for azimuth in azimuths:
                            total_locations += 1
                            
                            if self.upload_location_data(lat, lon, tilt, azimuth, 2023):
                                success_count += 1
        
        # Coarse grid for rest of Germany
        print(f"\n🗺️  Processing coarse grid for rest of Germany...")
        
        # Germany boundaries
        lat_range = (47.5, 55.0)
        lon_range = (6.0, 15.0)
        coarse_resolution = 0.5
        
        lat_current = lat_range[0]
        while lat_current <= lat_range[1]:
            lon_current = lon_range[0]
            while lon_current <= lon_range[1]:
                # Skip if too close to major cities (already covered)
                skip = False
                for _, city_lat, city_lon in major_cities:
                    if abs(lat_current - city_lat) < 0.6 and abs(lon_current - city_lon) < 0.6:
                        skip = True
                        break
                
                if not skip:
                    for tilt in tilts:
                        for azimuth in azimuths:
                            total_locations += 1
                            
                            if self.upload_location_data(lat_current, lon_current, tilt, azimuth, 2023):
                                success_count += 1
                
                lon_current += coarse_resolution
            lat_current += coarse_resolution
        
        print(f"\n🎉 Database Population Complete!")
        print(f"✅ Successfully uploaded: {success_count}/{total_locations} locations")
        print(f"📊 Database ready for production use!")

def main():
    """Interactive menu for database management."""
    try:
        manager = SupabaseSolarManager()
        
        print("\n🗄️  Supabase Solar Database Manager")
        print("=" * 40)
        print("1. Test single location upload")
        print("2. Populate entire Germany grid (SLOW!)")
        print("3. Test radiation lookup")
        print("4. Check database status")
        
        choice = input("\nChoose option (1-4): ").strip()
        
        if choice == "1":
            # Test with Berlin
            print("\n🧪 Testing with Berlin...")
            success = manager.upload_location_data(52.5, 13.4, 30, 0, 2023)
            if success:
                print("✅ Test upload successful!")
            else:
                print("❌ Test upload failed!")
                
        elif choice == "2":
            confirm = input("⚠️  This will take several hours. Continue? (yes/no): ")
            if confirm.lower() in ['yes', 'y']:
                manager.populate_germany_grid()
            else:
                print("Cancelled.")
                
        elif choice == "3":
            # Test lookup
            test_datetime = datetime(2023, 6, 15, 12, 0)
            result = manager.get_radiation_for_datetime(52.5, 13.4, 30, 0, test_datetime)
            if result:
                print(f"✅ Found radiation data: {result['total_radiation']:.1f} W/m²")
            else:
                print("❌ No data found")
                
        elif choice == "4":
            # Check status
            result = manager.supabase.table('solar_radiation').select('id').limit(1).execute()
            if result.data:
                print("✅ Database connection working!")
                
                # Count records
                count_result = manager.supabase.table('solar_radiation').select('id', count='exact').execute()
                print(f"📊 Records in database: {count_result.count:,}")
            else:
                print("❌ Database empty or connection issue")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("1. Created .env file with SUPABASE_URL and SUPABASE_KEY")
        print("2. Run: pip install supabase python-dotenv")

if __name__ == "__main__":
    main()

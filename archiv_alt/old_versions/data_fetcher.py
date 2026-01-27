#!/usr/bin/env python3
"""
PVGIS Data Fetcher - Downloads and caches solar radiation data locally
This script fetches data once and saves it to avoid repeated API calls and timeouts.
"""

import pandas as pd
import pickle
import os
from datetime import datetime
from pvlib.iotools import get_pvgis_hourly
import json

class PVGISDataManager:
    """Manages local storage and retrieval of PVGIS data."""
    
    def __init__(self, data_dir="pvgis_data"):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def _get_cache_filename(self, latitude, longitude, tilt, azimuth, year):
        """Generate a unique filename for the cache."""
        # Round coordinates to avoid tiny differences creating separate files
        lat_rounded = round(latitude, 2)
        lon_rounded = round(longitude, 2)
        return f"pvgis_{lat_rounded}_{lon_rounded}_{tilt}_{azimuth}_{year}.pkl"
    
    def _get_metadata_filename(self, latitude, longitude, tilt, azimuth, year):
        """Generate filename for metadata."""
        lat_rounded = round(latitude, 2)
        lon_rounded = round(longitude, 2)
        return f"pvgis_meta_{lat_rounded}_{lon_rounded}_{tilt}_{azimuth}_{year}.json"
    
    def has_cached_data(self, latitude, longitude, tilt, azimuth, year=2023):
        """Check if data is already cached locally."""
        cache_file = os.path.join(self.data_dir, self._get_cache_filename(latitude, longitude, tilt, azimuth, year))
        return os.path.exists(cache_file)
    
    def load_cached_data(self, latitude, longitude, tilt, azimuth, year=2023):
        """Load data from local cache."""
        cache_file = os.path.join(self.data_dir, self._get_cache_filename(latitude, longitude, tilt, azimuth, year))
        meta_file = os.path.join(self.data_dir, self._get_metadata_filename(latitude, longitude, tilt, azimuth, year))
        
        if not os.path.exists(cache_file):
            return None, None
        
        try:
            # Load data
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            # Load metadata
            meta = {}
            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
            
            print(f"✅ Loaded cached data: {len(data)} hourly points")
            print(f"   File: {os.path.basename(cache_file)}")
            return data, meta
            
        except Exception as e:
            print(f"Error loading cached data: {e}")
            return None, None
    
    def fetch_and_cache_data(self, latitude, longitude, tilt, azimuth, year=2023):
        """Fetch data from PVGIS and save it locally."""
        print(f"🌐 Fetching PVGIS data for: {latitude}°N, {longitude}°E")
        print(f"   Tilt: {tilt}°, Azimuth: {azimuth}°, Year: {year}")
        print("   This may take 30-60 seconds...")
        
        try:
            # Fetch data with longer timeout
            data, meta = get_pvgis_hourly(
                latitude=latitude,
                longitude=longitude,
                surface_tilt=tilt,
                surface_azimuth=azimuth,
                start=year,
                end=year,
                components=True,
                timeout=120  # 2 minutes timeout
            )
            
            # Save data to cache
            cache_file = os.path.join(self.data_dir, self._get_cache_filename(latitude, longitude, tilt, azimuth, year))
            meta_file = os.path.join(self.data_dir, self._get_metadata_filename(latitude, longitude, tilt, azimuth, year))
            
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Save metadata as JSON (convert non-serializable objects)
            meta_serializable = {}
            for key, value in meta.items():
                try:
                    json.dumps(value)  # Test if serializable
                    meta_serializable[key] = value
                except:
                    meta_serializable[key] = str(value)  # Convert to string if not
            
            with open(meta_file, 'w') as f:
                json.dump(meta_serializable, f, indent=2)
            
            print(f"✅ Successfully fetched and cached {len(data)} hourly data points")
            print(f"   Saved to: {os.path.basename(cache_file)}")
            return data, meta
            
        except Exception as e:
            print(f"❌ Error fetching PVGIS data: {e}")
            return None, None
    
    def get_data(self, latitude, longitude, tilt, azimuth, year=2023):
        """Get data - from cache if available, otherwise fetch and cache."""
        # Check if we have cached data
        if self.has_cached_data(latitude, longitude, tilt, azimuth, year):
            return self.load_cached_data(latitude, longitude, tilt, azimuth, year)
        else:
            return self.fetch_and_cache_data(latitude, longitude, tilt, azimuth, year)
    
    def list_cached_files(self):
        """List all cached data files."""
        files = [f for f in os.listdir(self.data_dir) if f.endswith('.pkl')]
        
        if not files:
            print("No cached data files found.")
            return
        
        print(f"📁 Cached data files in '{self.data_dir}':")
        for file in sorted(files):
            filepath = os.path.join(self.data_dir, file)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"   {file} ({size_mb:.1f} MB)")
    
    def clear_cache(self):
        """Clear all cached data."""
        files = os.listdir(self.data_dir)
        count = 0
        for file in files:
            filepath = os.path.join(self.data_dir, file)
            os.remove(filepath)
            count += 1
        print(f"🗑️  Cleared {count} cached files")

def main():
    """Test the data manager."""
    manager = PVGISDataManager()
    
    print("=== PVGIS Data Manager Test ===")
    
    # Test with Berlin coordinates
    lat, lon, tilt, azimuth = 52.5, 13.4, 30, 0
    
    print(f"\nTesting with Berlin: {lat}°N, {lon}°E, {tilt}° tilt, {azimuth}° azimuth")
    
    data, meta = manager.get_data(lat, lon, tilt, azimuth, 2023)
    
    if data is not None:
        print(f"\n📊 Data summary:")
        print(f"   Shape: {data.shape}")
        print(f"   Columns: {list(data.columns)}")
        print(f"   Date range: {data.index.min()} to {data.index.max()}")
        
        # Show sample radiation data
        total_radiation = data['poa_direct'] + data['poa_sky_diffuse'] + data['poa_ground_diffuse']
        print(f"   Radiation range: {total_radiation.min():.1f} - {total_radiation.max():.1f} W/m²")
        print(f"   Average radiation: {total_radiation.mean():.1f} W/m²")
    
    print(f"\n📂 Cache status:")
    manager.list_cached_files()

if __name__ == "__main__":
    main()

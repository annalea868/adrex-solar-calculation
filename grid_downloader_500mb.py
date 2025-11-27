#!/usr/bin/env python3
"""
Optimized Local Grid Downloader - 500MB Version
Downloads a lightweight grid optimized for TypeScript applications.
"""

import os
import time
import pickle
from datetime import datetime
from pvlib.iotools import get_pvgis_hourly
import json

class OptimizedGridDownloader:
    """Downloads optimized 500MB grid for TypeScript applications."""
    
    def __init__(self, data_dir="solar_grid_500mb"):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Optimized grid for Germany (500MB target)
        self.lat_range = (47.5, 55.0)  # South to North Germany
        self.lon_range = (6.0, 15.0)   # West to East Germany
        self.grid_resolution = 0.75    # 0.75° = ~85km spacing (was 0.5°)
        
        # Optimized configurations (4 key configs instead of 12)
        self.configurations = [
            (30, 0),    # 30° South (most common - 50% of installations)
            (30, 90),   # 30° West (morning sun)
            (30, 270),  # 30° East (evening sun)
            (45, 0),    # 45° South (steep roofs - alpine regions)
        ]
        
        print(f"🗺️  Optimized Grid Setup (500MB Version):")
        print(f"   Coverage: {self.lat_range[0]}°N to {self.lat_range[1]}°N")
        print(f"            {self.lon_range[0]}°E to {self.lon_range[1]}°E")
        print(f"   Resolution: {self.grid_resolution}° (~{self.grid_resolution*111:.0f}km)")
        print(f"   Configurations: {len(self.configurations)} (optimized for TypeScript)")
        
        # Calculate total downloads needed
        lat_points = int((self.lat_range[1] - self.lat_range[0]) / self.grid_resolution) + 1
        lon_points = int((self.lon_range[1] - self.lon_range[0]) / self.grid_resolution) + 1
        total_points = lat_points * lon_points
        total_downloads = total_points * len(self.configurations)
        
        print(f"   Grid points: {lat_points} × {lon_points} = {total_points}")
        print(f"   Total downloads: {total_downloads}")
        print(f"   Estimated time: {total_downloads * 45 / 3600:.1f} hours")
        print(f"   Storage needed: ~{total_downloads * 0.5 / 1024:.0f} MB")
        print(f"   TypeScript compatible: ✅")
    
    def get_filename(self, lat, lon, tilt, azimuth, year=2023):
        """Generate filename for grid data."""
        return f"grid_{lat:.1f}_{lon:.1f}_{tilt}_{azimuth}_{year}.pkl"
    
    def get_metadata_filename(self, lat, lon, tilt, azimuth, year=2023):
        """Generate filename for metadata."""
        return f"grid_meta_{lat:.1f}_{lon:.1f}_{tilt}_{azimuth}_{year}.json"
    
    def file_exists(self, lat, lon, tilt, azimuth, year=2023):
        """Check if file already exists."""
        filename = self.get_filename(lat, lon, tilt, azimuth, year)
        filepath = os.path.join(self.data_dir, filename)
        return os.path.exists(filepath)
    
    def download_location(self, lat, lon, tilt, azimuth, year=2023, retry_count=3):
        """Download data for one location/configuration."""
        if self.file_exists(lat, lon, tilt, azimuth, year):
            return True
        
        print(f"⬇️  {lat:.1f}°N, {lon:.1f}°E ({tilt}°/{azimuth}°)...", end=" ")
        
        for attempt in range(retry_count):
            try:
                # Add delay between requests to be nice to PVGIS
                time.sleep(3 + attempt)  # Slightly longer delay for stability
                
                # Download from PVGIS
                data, meta = get_pvgis_hourly(
                    latitude=lat,
                    longitude=lon,
                    surface_tilt=tilt,
                    surface_azimuth=azimuth,
                    start=year,
                    end=year,
                    components=True,
                    timeout=120  # 2 minute timeout
                )
                
                if data is not None and len(data) > 0:
                    # Save data file
                    data_filename = self.get_filename(lat, lon, tilt, azimuth, year)
                    data_filepath = os.path.join(self.data_dir, data_filename)
                    
                    with open(data_filepath, 'wb') as f:
                        pickle.dump(data, f)
                    
                    # Save metadata
                    meta_filename = self.get_metadata_filename(lat, lon, tilt, azimuth, year)
                    meta_filepath = os.path.join(self.data_dir, meta_filename)
                    
                    # Convert metadata to JSON-serializable format
                    meta_serializable = {}
                    if meta:
                        for key, value in meta.items():
                            try:
                                json.dumps(value)
                                meta_serializable[key] = value
                            except:
                                meta_serializable[key] = str(value)
                    
                    with open(meta_filepath, 'w') as f:
                        json.dump(meta_serializable, f, indent=2)
                    
                    print("✅")
                    return True
                else:
                    print(f"❌ No data (attempt {attempt + 1})")
                    
            except Exception as e:
                print(f"❌ Error (attempt {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    print(f"   🔄 Retrying in {5 + attempt * 2} seconds...")
                    time.sleep(5 + attempt * 2)
        
        print("❌ All attempts failed")
        return False
    
    def download_grid(self):
        """Download the optimized grid."""
        print("🚀 Starting optimized grid download (500MB version)...")
        print("=" * 60)
        
        start_time = datetime.now()
        total_downloads = 0
        successful_downloads = 0
        failed_downloads = 0
        
        # Generate all grid points
        lat = self.lat_range[0]
        while lat <= self.lat_range[1]:
            lon = self.lon_range[0]
            while lon <= self.lon_range[1]:
                
                print(f"\n📍 Location: {lat:.1f}°N, {lon:.1f}°E")
                
                for tilt, azimuth in self.configurations:
                    total_downloads += 1
                    
                    if self.download_location(lat, lon, tilt, azimuth):
                        successful_downloads += 1
                    else:
                        failed_downloads += 1
                    
                    # Progress update every 25 downloads (smaller batches)
                    if total_downloads % 25 == 0:
                        elapsed = datetime.now() - start_time
                        rate = total_downloads / elapsed.total_seconds() * 3600  # downloads per hour
                        remaining = (self.calculate_total_downloads() - total_downloads) / rate if rate > 0 else 0
                        
                        print(f"📊 Progress: {total_downloads}/{self.calculate_total_downloads()} downloads")
                        print(f"   Success rate: {successful_downloads/total_downloads*100:.1f}%")
                        print(f"   ETA: {remaining:.1f} hours remaining")
                
                lon += self.grid_resolution
            lat += self.grid_resolution
        
        # Final statistics
        elapsed = datetime.now() - start_time
        print("\n" + "=" * 60)
        print("🎉 Optimized grid download complete!")
        print(f"⏱️  Total time: {elapsed}")
        print(f"✅ Successful: {successful_downloads}")
        print(f"❌ Failed: {failed_downloads}")
        print(f"📊 Success rate: {successful_downloads/total_downloads*100:.1f}%")
        
        # Show file statistics
        self.show_grid_status()
    
    def calculate_total_downloads(self):
        """Calculate total number of downloads needed."""
        lat_points = int((self.lat_range[1] - self.lat_range[0]) / self.grid_resolution) + 1
        lon_points = int((self.lon_range[1] - self.lon_range[0]) / self.grid_resolution) + 1
        return lat_points * lon_points * len(self.configurations)
    
    def show_grid_status(self):
        """Show current grid download status."""
        if not os.path.exists(self.data_dir):
            print("❌ Grid directory not found")
            return
        
        files = [f for f in os.listdir(self.data_dir) if f.startswith('grid_') and f.endswith('.pkl')]
        total_size = 0
        
        for file in files:
            filepath = os.path.join(self.data_dir, file)
            total_size += os.path.getsize(filepath)
        
        print(f"\n📁 Optimized Grid Status:")
        print(f"   Files: {len(files)}")
        print(f"   Size: {total_size / (1024*1024):.0f} MB (Target: ~500 MB)")
        print(f"   Expected: {self.calculate_total_downloads()} files")
        print(f"   Coverage: {len(files)/self.calculate_total_downloads()*100:.1f}%")
        print(f"   TypeScript ready: {'✅' if total_size < 600*1024*1024 else '⚠️'}")
    
    def list_available_configurations(self):
        """List all available configurations in the grid."""
        if not os.path.exists(self.data_dir):
            return []
        
        configs = set()
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

def main():
    """Interactive optimized grid downloader."""
    downloader = OptimizedGridDownloader()
    
    print("🗺️  Optimized Solar Grid Downloader (500MB)")
    print("=" * 50)
    print("1. Download optimized grid (3-4 hours)")
    print("2. Show grid status")
    print("3. List available configurations")
    print("4. Test single location")
    
    choice = input("\nChoose option (1-4): ").strip()
    
    if choice == "1":
        print("\n⚠️  This will download the optimized solar grid for Germany.")
        print("   Estimated time: 3-4 hours")
        print("   Storage needed: ~500 MB")
        print("   Network traffic: ~250 MB download")
        print("   TypeScript compatible: ✅")
        
        confirm = input("\nContinue? (yes/no): ").strip().lower()
        if confirm in ['yes', 'y']:
            downloader.download_grid()
        else:
            print("Download cancelled.")
    
    elif choice == "2":
        downloader.show_grid_status()
    
    elif choice == "3":
        configs = downloader.list_available_configurations()
        print(f"\n📊 Available configurations: {len(configs)}")
        for tilt, azimuth in configs:
            azimuth_name = {0: "South", 90: "West", 270: "East"}
            print(f"   {tilt}° tilt, {azimuth}° azimuth ({azimuth_name.get(azimuth, 'Custom')})")
    
    elif choice == "4":
        # Test download
        lat = float(input("Latitude: "))
        lon = float(input("Longitude: "))
        tilt = int(input("Tilt: "))
        azimuth = int(input("Azimuth: "))
        
        success = downloader.download_location(lat, lon, tilt, azimuth)
        if success:
            print("✅ Test download successful!")
        else:
            print("❌ Test download failed!")
    
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()






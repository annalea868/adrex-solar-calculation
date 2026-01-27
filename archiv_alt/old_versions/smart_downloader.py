#!/usr/bin/env python3
"""
Smart PVGIS Downloader with Rate Limiting and Progress Saving
Downloads solar data safely with retries, delays, and progress tracking.
"""

import time
import json
import os
from datetime import datetime
import requests
from supabase_manager import SupabaseSolarManager
import pickle

class SmartPVGISDownloader:
    """Safe and resumable PVGIS data downloader."""
    
    def __init__(self, delay_between_requests=3, max_retries=3):
        self.delay = delay_between_requests
        self.max_retries = max_retries
        self.db_manager = SupabaseSolarManager()
        self.progress_file = "download_progress.json"
        self.failed_requests_file = "failed_requests.json"
        
        # Load existing progress
        self.progress = self.load_progress()
        self.failed_requests = self.load_failed_requests()
        
        print(f"🛡️  Smart downloader initialized")
        print(f"   Delay between requests: {delay_between_requests}s")
        print(f"   Max retries per request: {max_retries}")
    
    def load_progress(self):
        """Load download progress from file."""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            "completed_locations": [],
            "current_phase": "major_cities",
            "total_completed": 0,
            "start_time": None,
            "last_update": None
        }
    
    def save_progress(self):
        """Save current progress to file."""
        self.progress["last_update"] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def load_failed_requests(self):
        """Load list of failed requests."""
        if os.path.exists(self.failed_requests_file):
            with open(self.failed_requests_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_failed_request(self, location_config, error):
        """Save failed request for later retry."""
        failed_request = {
            "location": location_config,
            "error": str(error),
            "timestamp": datetime.now().isoformat()
        }
        self.failed_requests.append(failed_request)
        
        with open(self.failed_requests_file, 'w') as f:
            json.dump(self.failed_requests, f, indent=2)
    
    def download_with_retry(self, lat, lon, tilt, azimuth, year=2023):
        """Download data for one location with retry logic."""
        location_key = f"{lat}_{lon}_{tilt}_{azimuth}_{year}"
        
        # Check if already completed
        if location_key in self.progress["completed_locations"]:
            print(f"✅ Already downloaded: {lat}°N, {lon}°E ({tilt}°/{azimuth}°)")
            return True
        
        # Check if data already exists in database
        if self.db_manager.check_data_exists(lat, lon, tilt, azimuth, year):
            print(f"✅ Already in database: {lat}°N, {lon}°E ({tilt}°/{azimuth}°)")
            self.progress["completed_locations"].append(location_key)
            self.progress["total_completed"] += 1
            return True
        
        print(f"⬇️  Downloading: {lat}°N, {lon}°E ({tilt}°/{azimuth}°)...", end=" ")
        
        for attempt in range(self.max_retries):
            try:
                # Add small random delay to avoid overwhelming server
                actual_delay = self.delay + (attempt * 2)  # Increase delay on retries
                if attempt > 0:
                    print(f"🔄 Retry {attempt}/{self.max_retries}...", end=" ")
                
                time.sleep(actual_delay)
                
                # Use the existing upload method with timeout handling
                success = self.db_manager.upload_location_data(lat, lon, tilt, azimuth, year)
                
                if success:
                    print("✅")
                    self.progress["completed_locations"].append(location_key)
                    self.progress["total_completed"] += 1
                    self.save_progress()
                    return True
                else:
                    print(f"❌ Attempt {attempt + 1} failed")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                if attempt == self.max_retries - 1:
                    # Final attempt failed, save for later
                    self.save_failed_request({
                        "lat": lat, "lon": lon, "tilt": tilt, 
                        "azimuth": azimuth, "year": year
                    }, e)
        
        print("❌ All retries failed")
        return False
    
    def download_priority_locations(self):
        """Download data for high-priority locations first."""
        print("\n🎯 PHASE 1: Priority Locations (Major Cities)")
        print("=" * 60)
        
        if self.progress["start_time"] is None:
            self.progress["start_time"] = datetime.now().isoformat()
        
        # Major German cities - highest priority
        priority_cities = [
            ("Berlin", 52.5, 13.4),
            ("München", 48.1, 11.6),
            ("Hamburg", 53.6, 10.0),
            ("Köln", 50.9, 6.9),
            ("Frankfurt", 50.1, 8.7),
            ("Stuttgart", 48.8, 9.2),
            ("Düsseldorf", 51.2, 6.8),
            ("Dortmund", 51.5, 7.5),
            ("Dresden", 51.0, 13.7),
            ("Leipzig", 51.3, 12.4)
        ]
        
        # Most common solar configurations
        configurations = [
            (30, 0),    # 30° South (most common)
            (30, 90),   # 30° West
            (30, 270),  # 30° East
        ]
        
        total_priority = len(priority_cities) * len(configurations)
        completed_priority = 0
        
        for city_name, lat, lon in priority_cities:
            print(f"\n🏙️  {city_name} ({lat}°N, {lon}°E)")
            
            for tilt, azimuth in configurations:
                if self.download_with_retry(lat, lon, tilt, azimuth):
                    completed_priority += 1
                
                # Progress update
                progress_pct = (completed_priority / total_priority) * 100
                print(f"   📊 Priority progress: {completed_priority}/{total_priority} ({progress_pct:.1f}%)")
        
        print(f"\n✅ Priority phase complete: {completed_priority}/{total_priority} locations")
        self.progress["current_phase"] = "extended_cities"
        self.save_progress()
    
    def download_extended_coverage(self):
        """Download data for extended coverage around major cities."""
        print("\n🗺️  PHASE 2: Extended Coverage")
        print("=" * 60)
        
        # Extended coverage around major cities
        major_cities = [
            (52.5, 13.4),  # Berlin
            (48.1, 11.6),  # München
            (53.6, 10.0),  # Hamburg
            (50.9, 6.9),   # Köln
            (50.1, 8.7),   # Frankfurt
        ]
        
        configurations = [(30, 0), (30, 90), (30, 270)]
        
        total_extended = 0
        completed_extended = 0
        
        for base_lat, base_lon in major_cities:
            print(f"\n📍 Extending around {base_lat}°N, {base_lon}°E")
            
            # Create grid around each major city
            for lat_offset in [-0.3, -0.1, 0.1, 0.3]:
                for lon_offset in [-0.3, -0.1, 0.1, 0.3]:
                    lat = round(base_lat + lat_offset, 1)
                    lon = round(base_lon + lon_offset, 1)
                    
                    for tilt, azimuth in configurations:
                        total_extended += 1
                        if self.download_with_retry(lat, lon, tilt, azimuth):
                            completed_extended += 1
                        
                        # Progress update every 10 downloads
                        if total_extended % 10 == 0:
                            progress_pct = (completed_extended / total_extended) * 100
                            print(f"   📊 Extended progress: {completed_extended}/{total_extended} ({progress_pct:.1f}%)")
        
        print(f"\n✅ Extended phase complete: {completed_extended}/{total_extended} locations")
        self.progress["current_phase"] = "coarse_grid"
        self.save_progress()
    
    def download_coarse_grid(self):
        """Download coarse grid for rest of Germany."""
        print("\n🌍 PHASE 3: Coarse Grid (Rest of Germany)")
        print("=" * 60)
        print("⚠️  This phase will take the longest time!")
        
        # Germany boundaries
        lat_range = (47.5, 55.0)
        lon_range = (6.0, 15.0)
        resolution = 0.5
        
        configurations = [(30, 0)]  # Just south-facing for coarse grid
        
        total_coarse = 0
        completed_coarse = 0
        
        lat = lat_range[0]
        while lat <= lat_range[1]:
            lon = lon_range[0]
            while lon <= lon_range[1]:
                # Skip if too close to major cities (already covered)
                skip = False
                major_cities = [(52.5, 13.4), (48.1, 11.6), (53.6, 10.0), (50.9, 6.9), (50.1, 8.7)]
                
                for city_lat, city_lon in major_cities:
                    if abs(lat - city_lat) < 0.8 and abs(lon - city_lon) < 0.8:
                        skip = True
                        break
                
                if not skip:
                    for tilt, azimuth in configurations:
                        total_coarse += 1
                        if self.download_with_retry(lat, lon, tilt, azimuth):
                            completed_coarse += 1
                        
                        # Progress update every 20 downloads
                        if total_coarse % 20 == 0:
                            progress_pct = (completed_coarse / total_coarse) * 100
                            print(f"   📊 Coarse grid progress: {completed_coarse}/{total_coarse} ({progress_pct:.1f}%)")
                
                lon += resolution
            lat += resolution
        
        print(f"\n✅ Coarse grid complete: {completed_coarse}/{total_coarse} locations")
        self.progress["current_phase"] = "complete"
        self.save_progress()
    
    def resume_download(self):
        """Resume download from where it left off."""
        print(f"🔄 Resuming download from phase: {self.progress['current_phase']}")
        print(f"📊 Previously completed: {self.progress['total_completed']} locations")
        
        if self.progress["current_phase"] == "major_cities":
            self.download_priority_locations()
        
        if self.progress["current_phase"] == "extended_cities":
            self.download_extended_coverage()
        
        if self.progress["current_phase"] == "coarse_grid":
            self.download_coarse_grid()
        
        if self.progress["current_phase"] == "complete":
            print("✅ Download already complete!")
        
        # Show final statistics
        self.show_final_stats()
    
    def show_final_stats(self):
        """Show download completion statistics."""
        print("\n" + "=" * 60)
        print("📊 DOWNLOAD STATISTICS")
        print("=" * 60)
        
        if self.progress["start_time"]:
            start_time = datetime.fromisoformat(self.progress["start_time"])
            duration = datetime.now() - start_time
            print(f"⏱️  Total time: {duration}")
        
        print(f"✅ Successfully downloaded: {self.progress['total_completed']} locations")
        print(f"❌ Failed requests: {len(self.failed_requests)}")
        
        if self.failed_requests:
            print(f"\n🔄 To retry failed requests, run:")
            print(f"python3 smart_downloader.py --retry-failed")

def main():
    """Main function with command line options."""
    import sys
    
    if "--retry-failed" in sys.argv:
        print("🔄 Retrying failed requests...")
        downloader = SmartPVGISDownloader()
        # TODO: Implement retry logic for failed requests
        print("Feature not yet implemented")
        return
    
    if "--status" in sys.argv:
        downloader = SmartPVGISDownloader()
        downloader.show_final_stats()
        return
    
    print("🚀 Smart PVGIS Downloader Starting")
    print("=" * 60)
    print("This will safely download solar data for Germany in phases:")
    print("1. Major cities first (30 mins)")
    print("2. Extended coverage around cities (2-3 hours)")
    print("3. Coarse grid for rest of Germany (8-12 hours)")
    print()
    print("The download is resumable - you can stop and restart anytime!")
    print()
    
    response = input("Start download? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        downloader = SmartPVGISDownloader()
        downloader.resume_download()
    else:
        print("Download cancelled.")

if __name__ == "__main__":
    main()

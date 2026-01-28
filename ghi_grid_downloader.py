#!/usr/bin/env python3
"""
GHI Grid Downloader für Deutschland
Lädt GHI-Daten (horizontal) für ein optimiertes Grid über Deutschland.

Grid: 0.25° Nord-Süd, 0.5° Ost-West
Punkte: 589 Locations
Speicher: ~350 MB

Mit Safe-Download-Strategie:
- 3 Sekunden Pause zwischen Requests
- Retry bei Fehlern
- Progress wird gespeichert
- Kann jederzeit fortgesetzt werden
"""

import time
import pickle
import os
from datetime import datetime
from pvlib.iotools import get_pvgis_hourly
import json

class GHIGridDownloader:
    """Sicherer Download von GHI-Daten für Deutschland-Grid."""
    
    def __init__(self, cache_dir="ghi_grid"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Deutschland Grid-Parameter
        self.lat_range = (47.5, 55.0)  # Nord-Süd
        self.lon_range = (6.0, 15.0)   # Ost-West
        self.lat_resolution = 0.25     # Feiner (Nord-Süd wichtiger!)
        self.lon_resolution = 0.5      # Gröber
        
        # Download-Einstellungen
        self.delay_between_requests = 3  # Sekunden
        self.max_retries = 3
        self.year = 2023
        
        print("🗺️  GHI Grid Downloader für Deutschland")
        print(f"   Grid: {self.lat_resolution}° × {self.lon_resolution}°")
        print(f"   Cache: {cache_dir}")
        
        # Berechne Grid-Größe
        lat_steps = int((self.lat_range[1] - self.lat_range[0]) / self.lat_resolution) + 1
        lon_steps = int((self.lon_range[1] - self.lon_range[0]) / self.lon_resolution) + 1
        self.total_points = lat_steps * lon_steps
        
        print(f"   Punkte: {lat_steps} × {lon_steps} = {self.total_points}")
        print(f"   Geschätzte Zeit: 30-120 Minuten")
    
    def get_filename(self, lat, lon):
        """Dateiname für GHI-Cache."""
        return os.path.join(
            self.cache_dir,
            f"ghi_{lat:.2f}_{lon:.2f}_{self.year}.pkl"
        )
    
    def download_location(self, lat, lon):
        """Download GHI für eine Location mit Retry-Logik."""
        cache_file = self.get_filename(lat, lon)
        
        if os.path.exists(cache_file):
            return True  # Bereits vorhanden
        
        print(f"📡 {lat:.2f}°N, {lon:.2f}°E...", end=" ", flush=True)
        
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.delay_between_requests)
                
                # Horizontal surface = GHI
                data, meta = get_pvgis_hourly(
                    latitude=lat,
                    longitude=lon,
                    surface_tilt=0,  # Horizontal!
                    surface_azimuth=0,
                    start=self.year,
                    end=self.year,
                    components=True,
                    timeout=120
                )
                
                # Extract GHI
                data['ghi'] = data['poa_direct'] + data['poa_sky_diffuse'] + data['poa_ground_diffuse']
                
                # Save
                with open(cache_file, 'wb') as f:
                    pickle.dump({'data': data, 'meta': meta}, f)
                
                print("✅")
                return True
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️ Retry {attempt+1}...", end=" ", flush=True)
                    time.sleep(10 * (attempt + 1))
                else:
                    print(f"❌ Failed: {str(e)[:50]}")
                    return False
        
        return False
    
    def download_grid(self):
        """Download komplettes Grid mit Progress-Tracking."""
        start_time = datetime.now()
        
        print("\n" + "="*70)
        print("🚀 STARTE GHI-GRID DOWNLOAD")
        print("="*70)
        print(f"Start: {start_time.strftime('%H:%M:%S')}")
        print()
        
        downloaded = 0
        failed = 0
        skipped = 0
        
        lat = self.lat_range[0]
        point_num = 0
        
        while lat <= self.lat_range[1]:
            lon = self.lon_range[0]
            
            while lon <= self.lon_range[1]:
                point_num += 1
                
                # Check if exists
                if os.path.exists(self.get_filename(lat, lon)):
                    skipped += 1
                    print(f"⏭️  {lat:.2f}°N, {lon:.2f}°E (cached)")
                else:
                    if self.download_location(lat, lon):
                        downloaded += 1
                    else:
                        failed += 1
                
                # Progress alle 10 Punkte
                if point_num % 10 == 0:
                    elapsed = datetime.now() - start_time
                    rate = point_num / elapsed.total_seconds() * 3600
                    remaining = (self.total_points - point_num) / rate if rate > 0 else 0
                    
                    print(f"\n📊 Progress: {point_num}/{self.total_points} ({point_num/self.total_points*100:.1f}%)")
                    print(f"   Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}")
                    print(f"   Rate: {rate:.1f} Punkte/Stunde")
                    print(f"   ETA: {remaining:.1f} Stunden\n")
                
                lon += self.lon_resolution
            
            lat += self.lat_resolution
        
        # Final Statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "="*70)
        print("🎉 DOWNLOAD ABGESCHLOSSEN")
        print("="*70)
        print(f"Dauer: {duration}")
        print(f"Erfolgreich: {downloaded}")
        print(f"Bereits vorhanden: {skipped}")
        print(f"Fehlgeschlagen: {failed}")
        print(f"Gesamt: {point_num} Punkte")
        
        # Show cache size
        total_size = sum(
            os.path.getsize(os.path.join(self.cache_dir, f))
            for f in os.listdir(self.cache_dir)
            if f.endswith('.pkl')
        )
        print(f"Cache-Größe: {total_size / (1024*1024):.1f} MB")


if __name__ == "__main__":
    downloader = GHIGridDownloader()
    
    print("\n⚠️  WICHTIG: Dieser Download dauert 1-2 Stunden!")
    print("   589 Locations werden heruntergeladen")
    print("   Mit sicheren Pausen zwischen Requests")
    print()
    
    response = input("Download starten? (ja/nein): ").strip().lower()
    
    if response in ['ja', 'j', 'yes', 'y']:
        downloader.download_grid()
    else:
        print("Download abgebrochen.")

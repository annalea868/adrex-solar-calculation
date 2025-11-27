#!/usr/bin/env python3
"""
PVGIS Data Preloader for German Cities
Downloads and caches solar radiation data for common German locations and configurations.
"""

from data_fetcher import PVGISDataManager
import time

def preload_common_german_locations():
    """Preload data for common German cities and solar configurations."""
    
    manager = PVGISDataManager()
    
    # Common German cities with coordinates
    locations = [
        ("Berlin", 52.5, 13.4),
        ("München", 48.1, 11.6),
        ("Hamburg", 53.6, 10.0),
        ("Köln", 50.9, 6.9),
        ("Frankfurt", 50.1, 8.7),
        ("Stuttgart", 48.8, 9.2),
        ("Dresden", 51.0, 13.7),
        ("Hannover", 52.4, 9.7),
        ("Bremen", 53.1, 8.8),
        ("Leipzig", 51.3, 12.4)
    ]
    
    # Common solar panel configurations
    configurations = [
        (30, 0),    # 30° South (optimal)
        (45, 0),    # 45° South (steep roof)
        (25, 90),   # 25° West
        (25, 270),  # 25° East
        (30, 45),   # 30° Southwest
        (30, 315)   # 30° Southeast
    ]
    
    print("🌞 PVGIS Data Preloader for Germany")
    print(f"Will download data for {len(locations)} cities × {len(configurations)} configurations = {len(locations) * len(configurations)} datasets")
    print("This will take 20-30 minutes but makes the calculator super fast afterward!")
    print()
    
    total_downloads = 0
    total_cached = 0
    
    for city, lat, lon in locations:
        print(f"\n🏙️  {city} ({lat}°N, {lon}°E)")
        
        for tilt, azimuth in configurations:
            azimuth_name = {0: "Süd", 90: "West", 270: "Ost", 45: "SW", 315: "SO"}
            config_name = f"{tilt}° {azimuth_name.get(azimuth, f'{azimuth}°')}"
            
            print(f"   📊 {config_name}...", end=" ")
            
            if manager.has_cached_data(lat, lon, tilt, azimuth, 2023):
                print("✅ Bereits im Cache")
                total_cached += 1
            else:
                print("⬇️  Lade herunter...")
                data, meta = manager.fetch_and_cache_data(lat, lon, tilt, azimuth, 2023)
                if data is not None:
                    total_downloads += 1
                    print("      ✅ Erfolgreich")
                else:
                    print("      ❌ Fehler")
                
                # Small delay to be nice to the API
                time.sleep(2)
    
    print(f"\n🎉 Fertig!")
    print(f"   Neue Downloads: {total_downloads}")
    print(f"   Bereits im Cache: {total_cached}")
    print(f"   Gesamt: {total_downloads + total_cached}")
    
    # Show cache status
    print(f"\n📂 Cache-Übersicht:")
    manager.list_cached_files()

def preload_single_location():
    """Interactive preloader for a single location."""
    manager = PVGISDataManager()
    
    print("🌞 Einzelstandort-Datendownload")
    print()
    
    try:
        lat = float(input("Breitengrad: "))
        lon = float(input("Längengrad: "))
        tilt = float(input("Neigung (z.B. 30): "))
        azimuth = float(input("Ausrichtung (0=Süd, 90=West, 270=Ost): "))
        
        print()
        if manager.has_cached_data(lat, lon, tilt, azimuth, 2023):
            print("✅ Daten bereits im Cache vorhanden!")
        else:
            print("⬇️  Lade Daten herunter...")
            data, meta = manager.fetch_and_cache_data(lat, lon, tilt, azimuth, 2023)
            if data is not None:
                print("✅ Download erfolgreich!")
            else:
                print("❌ Download fehlgeschlagen")
    
    except Exception as e:
        print(f"Fehler: {e}")

def main():
    """Main menu for the preloader."""
    print("=== PVGIS Daten-Preloader ===")
    print()
    print("1. Alle deutschen Hauptstädte (empfohlen)")
    print("2. Einzelnen Standort")
    print("3. Cache-Status anzeigen")
    print("4. Cache löschen")
    print()
    
    choice = input("Wähle Option (1-4): ").strip()
    
    manager = PVGISDataManager()
    
    if choice == "1":
        preload_common_german_locations()
    elif choice == "2":
        preload_single_location()
    elif choice == "3":
        manager.list_cached_files()
    elif choice == "4":
        confirm = input("Cache wirklich löschen? (ja/nein): ").strip().lower()
        if confirm in ["ja", "j", "yes", "y"]:
            manager.clear_cache()
        else:
            print("Abgebrochen.")
    else:
        print("Ungültige Auswahl.")

if __name__ == "__main__":
    main()

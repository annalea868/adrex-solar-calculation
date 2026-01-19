#!/usr/bin/env python3
"""
Solar Irradiation Calculator - Local PVGIS Library
Calculates 15-minute solar irradiation intervals for any time period.
Uses PVGIS API once, then processes locally.

Input: PLZ or coordinates, tilt, azimuth, time period
Output: Table with 15-minute solar irradiation values
"""

import pandas as pd
from datetime import datetime, timedelta
from pvlib.iotools import get_pvgis_hourly
import pytz
import pickle
import os

class SolarIrradiationCalculator:
    """Calculate solar irradiation for custom time periods with 15-minute intervals."""
    
    def __init__(self, cache_dir="pvgis_cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # German postal code to coordinates mapping (sample)
        self.plz_to_coords = {
            '10115': (52.5200, 13.4050),  # Berlin
            '80331': (48.1351, 11.5820),  # München
            '20095': (53.5511, 9.9937),   # Hamburg
            '50667': (50.9375, 6.9603),   # Köln
            '60311': (50.1109, 8.6821),   # Frankfurt
            '70173': (48.7758, 9.1829),   # Stuttgart
            '01067': (51.0504, 13.7373),  # Dresden
            '30159': (52.3759, 9.7320),   # Hannover
            '28195': (53.0793, 8.8017),   # Bremen
            '04109': (51.3397, 12.3731),  # Leipzig
        }
        
        print("✅ Solar Irradiation Calculator initialisiert")
        print(f"   Cache-Verzeichnis: {cache_dir}")
    
    def plz_to_coordinates(self, plz):
        """Convert German postal code to coordinates."""
        if plz in self.plz_to_coords:
            return self.plz_to_coords[plz]
        else:
            print(f"⚠️  PLZ {plz} nicht in Datenbank")
            print("   Bitte Breiten- und Längengrad direkt eingeben")
            return None
    
    def get_cache_filename(self, lat, lon, tilt, azimuth, year):
        """Generate cache filename."""
        return os.path.join(
            self.cache_dir,
            f"pvgis_{lat:.2f}_{lon:.2f}_{tilt}_{azimuth}_{year}.pkl"
        )
    
    def load_or_fetch_pvgis_data(self, latitude, longitude, tilt, azimuth, year=2023):
        """
        Load PVGIS data from cache or fetch from API.
        Only makes API call if data not cached.
        """
        cache_file = self.get_cache_filename(latitude, longitude, tilt, azimuth, year)
        
        # Check cache first
        if os.path.exists(cache_file):
            print(f"✅ Lade Daten aus Cache...")
            with open(cache_file, 'rb') as f:
                cached = pickle.load(f)
            print(f"   {len(cached['data'])} Stunden-Datenpunkte geladen")
            return cached['data'], cached['meta']
        
        # Fetch from PVGIS API
        print(f"📡 Hole Daten von PVGIS API...")
        print(f"   Location: {latitude:.2f}°N, {longitude:.2f}°E")
        print(f"   Configuration: {tilt}° Neigung, {azimuth}° Azimut")
        print(f"   Jahr: {year}")
        print(f"   ⏳ Dies dauert 30-60 Sekunden...")
        
        try:
            # Convert user azimuth to PVGIS convention
            # User: 0°=North, 90°=East, 180°=South, 270°=West
            # PVGIS: 0°=South, 90°=West, 180°=North, 270°=East
            pvgis_azimuth = (azimuth + 180) % 360
            
            data, meta = get_pvgis_hourly(
                latitude=latitude,
                longitude=longitude,
                surface_tilt=tilt,
                surface_azimuth=pvgis_azimuth,
                start=year,
                end=year,
                components=True,
                timeout=120
            )
            
            # Save to cache
            with open(cache_file, 'wb') as f:
                pickle.dump({'data': data, 'meta': meta}, f)
            
            print(f"✅ Erfolgreich {len(data)} Stunden-Datenpunkte geholt")
            print(f"   Gespeichert in: {os.path.basename(cache_file)}")
            
            return data, meta
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen der PVGIS-Daten: {e}")
            return None, None
    
    def interpolate_to_15min(self, hourly_data):
        """
        Interpolate hourly data to 15-minute intervals.
        From 8,760 hours to 35,040 quarter-hours.
        """
        print(f"🔄 Interpoliere auf 15-Minuten-Intervalle...")
        print(f"   Eingabe: {len(hourly_data)} Stunden")
        
        # First, shift timestamps to round hours (PVGIS gives XX:11, we want XX:00)
        hourly_data_shifted = hourly_data.copy()
        hourly_data_shifted.index = hourly_data_shifted.index.floor('h')
        
        # Create complete hourly range
        start_hour = hourly_data_shifted.index.min()
        end_hour = hourly_data_shifted.index.max()
        full_hour_range = pd.date_range(start=start_hour, end=end_hour, freq='h')
        
        # Reindex to full hour range
        hourly_data_complete = hourly_data_shifted.reindex(full_hour_range)
        
        # Interpolate missing hours
        hourly_data_complete = hourly_data_complete.interpolate(method='linear')
        
        # Now resample to 15-minute intervals
        data_15min = hourly_data_complete.resample('15min').interpolate(method='linear')
        
        print(f"   Ausgabe: {len(data_15min)} Viertelstunden")
        
        return data_15min
    
    def calculate_irradiation_table(self, latitude, longitude, tilt, azimuth,
                                   start_date, start_time, end_date, end_time,
                                   plz=None, pv_system_kw=None, system_efficiency=0.8):
        """
        Calculate 15-minute solar irradiation table for custom time period.
        
        Parameters:
        - latitude, longitude: Location coordinates (or None if using PLZ)
        - tilt: Panel tilt angle (degrees, 0=horizontal, 90=vertical)
        - azimuth: Panel orientation (degrees, 0=North, 90=East, 180=South, 270=West)
        - start_date: Start date (DD/MM/YYYY string)
        - start_time: Start time (HH:MM string)
        - end_date: End date (DD/MM/YYYY string)
        - end_time: End time (HH:MM string)
        - plz: Optional German postal code
        
        Returns:
        - DataFrame with 15-minute irradiation values
        """
        
        print("\n" + "="*60)
        print("🔆 SOLAR IRRADIATION CALCULATION")
        print("="*60)
        
        # Handle PLZ if provided
        if plz:
            coords = self.plz_to_coordinates(plz)
            if coords:
                latitude, longitude = coords
                print(f"📍 PLZ {plz} → {latitude:.2f}°N, {longitude:.2f}°E")
            else:
                print("❌ PLZ nicht gefunden, verwende eingegebene Koordinaten")
        
        if latitude is None or longitude is None:
            print("❌ Keine gültigen Koordinaten")
            return None
        
        # Parse dates
        try:
            start_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
            end_dt = datetime.strptime(f"{end_date} {end_time}", "%d/%m/%Y %H:%M")
        except ValueError as e:
            print(f"❌ Datumsfehler: {e}")
            print("   Format: DD/MM/YYYY für Datum, HH:MM für Zeit")
            return None
        
        print(f"\n📅 Zeitraum:")
        print(f"   Start: {start_dt.strftime('%d.%m.%Y %H:%M')}")
        print(f"   Ende:  {end_dt.strftime('%d.%m.%Y %H:%M')}")
        
        duration = end_dt - start_dt
        print(f"   Dauer: {duration.days} Tage, {duration.seconds//3600} Stunden")
        
        # Calculate number of 15-minute intervals
        total_intervals = int(duration.total_seconds() / 900)  # 900 seconds = 15 minutes
        print(f"   Intervalle: {total_intervals} × 15 Minuten")
        
        # Get or fetch PVGIS data (uses 2023 as reference)
        reference_year = 2023
        print(f"\n📊 Lade Referenzdaten (Jahr {reference_year})...")
        
        hourly_data, meta = self.load_or_fetch_pvgis_data(
            latitude, longitude, tilt, azimuth, reference_year
        )
        
        if hourly_data is None:
            return None
        
        # Interpolate to 15-minute intervals
        data_15min = self.interpolate_to_15min(hourly_data)
        
        # Extract requested time period
        print(f"\n🔍 Extrahiere Zeitraum...")
        
        # Convert input dates to reference year for matching
        start_ref = start_dt.replace(year=reference_year)
        end_ref = end_dt.replace(year=reference_year)
        
        # Make timezone-aware
        if start_ref.tzinfo is None:
            start_ref = pytz.UTC.localize(start_ref)
        if end_ref.tzinfo is None:
            end_ref = pytz.UTC.localize(end_ref)
        
        # Filter data for requested period
        mask = (data_15min.index >= start_ref) & (data_15min.index <= end_ref)
        filtered_data = data_15min[mask]
        
        # Calculate total irradiation (create a copy to avoid warning)
        filtered_data = filtered_data.copy()
        
        # Calculate instantaneous irradiance (W/m²)
        filtered_data['total_irradiation_w_m2'] = (
            filtered_data['poa_direct'] + 
            filtered_data['poa_sky_diffuse'] + 
            filtered_data['poa_ground_diffuse']
        )
        
        # Calculate energy over 15-minute period (Wh/m²)
        # Energy = Power × Time
        # Wh/m² = W/m² × 0.25 hours (15 minutes = 0.25 hours)
        filtered_data['energie_15min_wh_m2'] = filtered_data['total_irradiation_w_m2'] * 0.25
        
        # Calculate PV energy production if system size provided
        # Using simplified formula: E = P_system × (Einstrahlung_Wh_m2 / 1000) × η_system
        # Time is already included in Einstrahlung_15min_Wh_m2!
        if pv_system_kw is not None:
            # E (kWh) = P_system (kW) × (Einstrahlung_15min (Wh/m²) / 1000) × η_system
            filtered_data['pv_energie_kwh'] = (
                pv_system_kw * 
                (filtered_data['energie_15min_wh_m2'] / 1000) * 
                system_efficiency
            )
        
        # Create result table
        result_dict = {
            'Datum': filtered_data.index.strftime('%d.%m.%Y'),
            'Uhrzeit': filtered_data.index.strftime('%H:%M'),
            'Strahlung_W_m2': filtered_data['total_irradiation_w_m2'].round(2).values,
            'Einstrahlung_15min_Wh_m2': filtered_data['energie_15min_wh_m2'].round(2).values,
        }
        
        # Add PV energy production if calculated
        if pv_system_kw is not None:
            result_dict['PV_Energie_kWh'] = filtered_data['pv_energie_kwh'].round(4).values
        
        # Add component details
        result_dict.update({
            'Direkte_Strahlung_W_m2': filtered_data['poa_direct'].round(2).values,
            'Diffuse_Strahlung_W_m2': filtered_data['poa_sky_diffuse'].round(2).values,
            'Reflexion_W_m2': filtered_data['poa_ground_diffuse'].round(2).values,
        })
        
        # Add optional columns if available
        if 'temp_air' in filtered_data.columns:
            result_dict['Temperatur_C'] = filtered_data['temp_air'].round(1).values
        if 'wind_speed' in filtered_data.columns:
            result_dict['Windgeschwindigkeit_m_s'] = filtered_data['wind_speed'].round(1).values
        
        result_table = pd.DataFrame(result_dict)
        
        print(f"✅ Tabelle erstellt: {len(result_table)} Intervalle (inkl. Nacht mit 0 W/m²)")
        
        # Count daylight hours for info
        daylight_count = len(result_table[result_table['Strahlung_W_m2'] > 0])
        
        print(f"\n📊 Statistik:")
        print(f"   Sonnenstunden-Intervalle: {daylight_count} ({daylight_count/len(result_table)*100:.1f}%)")
        print(f"   Nacht-Intervalle: {len(result_table) - daylight_count} ({(len(result_table)-daylight_count)/len(result_table)*100:.1f}%)")
        print(f"   Maximale Strahlung: {result_table['Strahlung_W_m2'].max():.1f} W/m²")
        print(f"   Gesamt-Einstrahlung: {result_table['Einstrahlung_15min_Wh_m2'].sum():.0f} Wh/m² ({result_table['Einstrahlung_15min_Wh_m2'].sum()/1000:.1f} kWh/m²)")
        
        # Show PV energy production if calculated
        if pv_system_kw is not None:
            total_pv_energy = result_table['PV_Energie_kWh'].sum()
            print(f"   PV-Energie produziert: {total_pv_energy:.2f} kWh (mit {pv_system_kw} kW System, {system_efficiency:.0%} Wirkungsgrad)")
        
        return result_table
    
    def save_table(self, table, filename):
        """Save result table to CSV."""
        table.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 Tabelle gespeichert: {filename}")
    
    def show_sample(self, table, n=10):
        """Show sample of the table."""
        print(f"\n📋 Beispiel (erste {n} Zeilen):")
        print(table.head(n).to_string(index=False))


def main():
    """Interactive solar irradiation calculator."""
    print("\n🔆" + "=" * 58 + "🔆")
    print()
    print("=== Solar Irradiation Calculator ===")
    print("Berechnet 15-Minuten-Intervalle für beliebige Zeiträume")
    print()
    
    calculator = SolarIrradiationCalculator()
    
    try:
        print("Bitte geben Sie die folgenden Parameter ein:")
        print()
        
        # Location input
        print("📍 STANDORT (PLZ oder Koordinaten):")
        location_input = input("PLZ oder Breitengrad eingeben (z.B. '10115' oder '52.5'): ").strip()
        
        plz = None
        latitude = None
        longitude = None
        
        # Check if input is PLZ (5 digits) or coordinate (contains decimal point)
        if location_input.isdigit() and len(location_input) == 5:
            # PLZ eingegeben
            plz = location_input
            coords = calculator.plz_to_coordinates(plz)
            if coords:
                latitude, longitude = coords
                print(f"   PLZ {plz} → {latitude:.2f}°N, {longitude:.2f}°E")
            else:
                print(f"   ❌ PLZ {plz} nicht gefunden")
                print("   Bitte Koordinaten eingeben:")
                latitude = float(input("   Breitengrad (z.B. 52.5): "))
                longitude = float(input("   Längengrad (z.B. 13.4): "))
        else:
            # Koordinaten eingegeben
            latitude = float(location_input)
            longitude = float(input("Längengrad (z.B. 13.4): "))
            print(f"   → Standort: {latitude:.2f}°N, {longitude:.2f}°E")
        
        # Panel configuration
        print("\n🏠 PANEL-KONFIGURATION:")
        tilt = int(input("Neigung in Grad (z.B. 30): "))
        azimuth = int(input("Ausrichtung in Grad (0°=Nord, 90°=Ost, 180°=Süd, 270°=West): "))
        
        # Time period
        print("\n📅 ZEITRAUM:")
        print("Start:")
        start_date = input("  Startdatum (DD/MM/YYYY, z.B. 01/06/2024): ")
        start_time = input("  Startzeit (HH:MM, z.B. 00:00): ")
        
        print("Ende:")
        end_date = input("  Enddatum (DD/MM/YYYY, z.B. 30/06/2024): ")
        end_time = input("  Endzeit (HH:MM, z.B. 23:45): ")
        
        # Optional: PV system size for energy calculation
        print("\n⚡ PV-SYSTEM (optional für Energie-Berechnung):")
        calc_energy = input("PV-Energie berechnen? (j/n): ").strip().lower()
        
        pv_system_kw = None
        system_efficiency = 0.8
        
        if calc_energy == 'j':
            pv_system_kw = float(input("  PV-Systemgröße in kW (z.B. 10): "))
            system_efficiency = float(input("  Systemwirkungsgrad (z.B. 0.8 für 80%): ") or "0.8")
        
        # Calculate irradiation table
        print("\n" + "="*60)
        print("🚀 Berechnung startet...")
        print("="*60)
        
        result_table = calculator.calculate_irradiation_table(
            latitude=latitude,
            longitude=longitude,
            tilt=tilt,
            azimuth=azimuth,
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
            plz=plz,
            pv_system_kw=pv_system_kw,
            system_efficiency=system_efficiency
        )
        
        if result_table is not None:
            # Show sample
            calculator.show_sample(result_table, n=10)
            
            # Ask to save
            print("\n")
            print("="*60)
            save = input("Tabelle als CSV speichern? (j/n): ").strip().lower()
            
            if save == 'j':
                # Generate default filename
                start_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
                end_dt = datetime.strptime(f"{end_date} {end_time}", "%d/%m/%Y %H:%M")
                default_name = f"solar_data_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.csv"
                
                print("\n💾 CSV-SPEICHERUNG:")
                print(f"   Standard-Dateiname: {default_name}")
                print(f"   Oder eigenen Namen eingeben")
                print("")  # Extra blank line
                filename = input("Dateiname eingeben (oder Enter für Standard): ").strip()
                print("")  # Extra blank line after input
                
                if not filename:
                    filename = default_name
                    print(f"→ Verwende Standard: {filename}")
                elif not filename.endswith('.csv'):
                    filename += '.csv'
                
                calculator.save_table(result_table, filename)
                print(f"✅ Erfolgreich gespeichert!")
                print(f"📁 Pfad: {os.path.abspath(filename)}")
            
            print("\n" + "="*60)
            print("🎉 FERTIG!")
            print("="*60)
            print(f"✅ {len(result_table)} Intervalle berechnet")
            
            if 'PV_Energie_kWh' in result_table.columns:
                total_pv = result_table['PV_Energie_kWh'].sum()
                print(f"⚡ PV-Energie produziert: {total_pv:.2f} kWh")
            else:
                print(f"📊 Gesamt-Einstrahlung: {result_table['Einstrahlung_15min_Wh_m2'].sum()/1000:.1f} kWh/m²")
            
        else:
            print("\n❌ Berechnung fehlgeschlagen")
            
    except KeyboardInterrupt:
        print("\n\nProgramm abgebrochen.")
    except ValueError as e:
        print(f"\n❌ Eingabefehler: {e}")
        print("💡 Bitte Format beachten:")
        print("   Datum: DD/MM/YYYY")
        print("   Zeit: HH:MM")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Energy System Simulator - Kombinierte PV-Speicher-Simulation
Simuliert komplettes Energiesystem mit Produktion, Verbrauch und Speicher.

Eingaben:
- Standort (PLZ oder Koordinaten)
- PV-Konfiguration (Tilt, Azimuth, Systemgröße)
- Zeitraum (Start/Ende)
- Batterie-Konfiguration
- Jahresverbrauch

Ausgabe:
- Detaillierte 15-Minuten-Tabelle
- Zusammenfassende Kennzahlen
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pvlib.iotools import get_pvgis_hourly
import pytz
import pickle
import os


class EnergySystemSimulator:
    """Kombinierter Simulator für PV-Produktion, Speicher und Verbrauch."""
    
    def __init__(self, cache_dir="pvgis_cache"):
        """
        Initialisiere Simulator.
        
        Parameters:
        - cache_dir: Verzeichnis für PVGIS-Daten-Cache
        """
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # File paths
        self.BATTERY_EXCEL_FILE = "2025-11_19_Nettokapazitäten Speicher.xlsx"
        self.HOUSEHOLD_PROFILE_FILE = "modeling/standardlastprofil-haushaltskunden-2026.xlsx"
        
        # German postal codes (sample)
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
        
        print("✅ Energy System Simulator initialisiert")
        print(f"   Cache: {cache_dir}")
    
    # ============================================================================
    # TEIL 1: PV-PRODUKTION (Solar Irradiation & Energy Calculation)
    # ============================================================================
    
    def plz_to_coordinates(self, plz):
        """Convert German postal code to coordinates."""
        if plz in self.plz_to_coords:
            return self.plz_to_coords[plz]
        return None
    
    def get_cache_filename(self, lat, lon, tilt, azimuth, year):
        """Generate cache filename for PVGIS data."""
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
            print(f"   ✅ Lade aus Cache...")
            with open(cache_file, 'rb') as f:
                cached = pickle.load(f)
            return cached['data'], cached['meta']
        
        # Fetch from PVGIS API
        print(f"   📡 Hole Daten von PVGIS API (kann 30-60s dauern)...")
        
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
            
            print(f"   ✅ Daten erfolgreich geholt und gecached")
            return data, meta
            
        except Exception as e:
            print(f"   ❌ Fehler beim Abrufen: {e}")
            return None, None
    
    def interpolate_to_15min(self, hourly_data):
        """Interpolate hourly PVGIS data to 15-minute intervals."""
        print(f"   🔄 Interpoliere auf 15-Min-Intervalle...")
        
        # Shift timestamps to round hours (PVGIS gives XX:11)
        hourly_data_shifted = hourly_data.copy()
        hourly_data_shifted.index = hourly_data_shifted.index.floor('h')
        
        # Create complete hourly range
        start_hour = hourly_data_shifted.index.min()
        end_hour = hourly_data_shifted.index.max()
        full_hour_range = pd.date_range(start=start_hour, end=end_hour, freq='h')
        
        # Reindex and interpolate
        hourly_data_complete = hourly_data_shifted.reindex(full_hour_range)
        hourly_data_complete = hourly_data_complete.interpolate(method='linear')
        
        # Resample to 15-minute intervals
        data_15min = hourly_data_complete.resample('15min').interpolate(method='linear')
        
        print(f"   ✅ {len(data_15min)} 15-Min-Intervalle erstellt")
        return data_15min
    
    def calculate_pv_production(self, latitude, longitude, tilt, azimuth,
                                start_date, start_time, end_date, end_time,
                                pv_system_kwp, system_efficiency=0.8):
        """
        Calculate PV energy production for time period.
        
        Returns:
        - DataFrame with datetime index and production values
        """
        print("\n" + "="*60)
        print("☀️  TEIL 1: PV-PRODUKTION BERECHNEN")
        print("="*60)
        print(f"   Standort: {latitude:.2f}°N, {longitude:.2f}°E")
        print(f"   Konfiguration: {tilt}° Neigung, {azimuth}° Azimut")
        print(f"   PV-System: {pv_system_kwp} kWp, {system_efficiency:.0%} Wirkungsgrad")
        
        # Parse dates
        start_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        end_dt = datetime.strptime(f"{end_date} {end_time}", "%d/%m/%Y %H:%M")
        
        print(f"   Zeitraum: {start_dt.strftime('%d.%m.%Y %H:%M')} bis {end_dt.strftime('%d.%m.%Y %H:%M')}")
        
        # Get PVGIS data (uses 2023 as reference)
        reference_year = 2023
        hourly_data, meta = self.load_or_fetch_pvgis_data(
            latitude, longitude, tilt, azimuth, reference_year
        )
        
        if hourly_data is None:
            return None
        
        # Interpolate to 15-minute intervals
        data_15min = self.interpolate_to_15min(hourly_data)
        
        # Extract requested time period
        print(f"   🔍 Extrahiere Zeitraum...")
        
        # Check if we have a year boundary crossing
        is_year_crossing = (end_dt.year > start_dt.year)
        
        if is_year_crossing:
            # Year crossing: e.g., 01/01/2022 to 01/01/2023 (full year)
            print(f"   ℹ️  Jahresübergang erkannt ({start_dt.year} → {end_dt.year})")
            
            # Calculate how many intervals we need
            duration = end_dt - start_dt
            num_intervals_needed = int(duration.total_seconds() / 900)  # 900s = 15min
            
            # Start from reference year
            start_ref = start_dt.replace(year=reference_year)
            if start_ref.tzinfo is None:
                start_ref = pytz.UTC.localize(start_ref)
            
            # Find start position in data
            start_idx = data_15min.index.get_indexer([start_ref], method='nearest')[0]
            
            # Take num_intervals_needed intervals, wrapping around if necessary
            total_intervals = len(data_15min)
            indices = [(start_idx + i) % total_intervals for i in range(num_intervals_needed)]
            
            filtered_data = data_15min.iloc[indices].copy()
            print(f"   ℹ️  {num_intervals_needed} Intervalle extrahiert (über Jahreswechsel)")
        else:
            # Normal case: same year
            start_ref = start_dt.replace(year=reference_year)
            end_ref = end_dt.replace(year=reference_year)
            
            if start_ref.tzinfo is None:
                start_ref = pytz.UTC.localize(start_ref)
            if end_ref.tzinfo is None:
                end_ref = pytz.UTC.localize(end_ref)
            
            mask = (data_15min.index >= start_ref) & (data_15min.index <= end_ref)
            filtered_data = data_15min[mask].copy()
        
        # Calculate irradiation
        filtered_data['Sonneneinstrahlung_W_m2'] = (
            filtered_data['poa_direct'] + 
            filtered_data['poa_sky_diffuse'] + 
            filtered_data['poa_ground_diffuse']
        )
        
        # Energy over 15-minute period (Wh/m²)
        filtered_data['Einstrahlung_15min_Wh_m2'] = filtered_data['Sonneneinstrahlung_W_m2'] * 0.25
        
        # PV energy production (kWh per 15 min)
        filtered_data['PV_Energie_kWh'] = (
            pv_system_kwp * 
            (filtered_data['Einstrahlung_15min_Wh_m2'] / 1000) * 
            system_efficiency
        )
        
        total_energy = filtered_data['PV_Energie_kWh'].sum()
        print(f"   ✅ PV-Produktion berechnet: {total_energy:.2f} kWh")
        
        return filtered_data
    
    # ============================================================================
    # TEIL 2: VERBRAUCH (Household Consumption)
    # ============================================================================
    
    def load_household_consumption(self, annual_consumption_kwh, target_datetimes):
        """
        Load and scale household standard load profile.
        
        Parameters:
        - annual_consumption_kwh: User's annual consumption
        - target_datetimes: DatetimeIndex with exact timestamps to extract
        
        Returns:
        - Array with consumption per 15-min interval (kWh)
        """
        print("\n" + "="*60)
        print("🏠 TEIL 2: VERBRAUCH BERECHNEN")
        print("="*60)
        print(f"   Datei: {self.HOUSEHOLD_PROFILE_FILE}")
        print(f"   Jahresverbrauch: {annual_consumption_kwh} kWh")
        
        try:
            df = pd.read_excel(self.HOUSEHOLD_PROFILE_FILE)
            df_clean = df.iloc[2:].copy()
            
            if 'SLP-HB [kWh]' not in df_clean.columns:
                raise ValueError("Spalte 'SLP-HB [kWh]' nicht gefunden")
            
            df_clean = df_clean.reset_index(drop=True)
            df_clean['IntervalStart'] = pd.to_datetime(df_clean['Datum'])
            
            # Validate
            first_date = df_clean['IntervalStart'].iloc[0]
            if first_date.month != 1 or first_date.day != 1:
                print(f"   ⚠️ WARNUNG: Profil startet am {first_date.strftime('%d.%m.%Y')} (erwartet: 01.01.)")
            
            # Scale profile
            profile_values = df_clean['SLP-HB [kWh]'].astype(float).values
            profile_sum = profile_values.sum()
            scale_factor = annual_consumption_kwh / profile_sum
            scaled_profile = profile_values * scale_factor
            
            # Create lookup dictionary
            profile_df = pd.DataFrame({
                'IntervalStart': df_clean['IntervalStart'],
                'Scaled_kWh': scaled_profile
            })
            profile_df['doy'] = profile_df['IntervalStart'].dt.dayofyear
            profile_df['minute_of_day'] = profile_df['IntervalStart'].dt.hour * 60 + profile_df['IntervalStart'].dt.minute
            
            print(f"   ✅ Profil geladen und skaliert (Faktor: {scale_factor:.6f})")
            
            # Extract for target datetimes
            lookup = profile_df.set_index(['doy', 'minute_of_day'])['Scaled_kWh'].to_dict()
            max_doy = int(profile_df['doy'].max())
            
            values = np.zeros(len(target_datetimes))
            
            for idx, ts in enumerate(target_datetimes):
                doy = ts.timetuple().tm_yday
                minute = ts.hour * 60 + ts.minute
                
                # Handle leap years
                if doy > max_doy:
                    doy = max_doy
                
                key = (doy, minute)
                values[idx] = lookup.get(key, 0.0)
            
            total_consumption = values.sum()
            print(f"   ✅ Verbrauch für Zeitraum: {total_consumption:.2f} kWh")
            
            return values
            
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
            return None
    
    # ============================================================================
    # TEIL 3: SPEICHER-SIMULATION (Battery Storage)
    # ============================================================================
    
    def simulate_storage(self, production_kwh, consumption_kwh, 
                        battery_capacity_kwh, battery_efficiency=0.95):
        """
        Simulate battery storage behavior.
        
        Parameters:
        - production_kwh: Array of PV production per 15-min
        - consumption_kwh: Array of consumption per 15-min
        - battery_capacity_kwh: Net battery capacity
        - battery_efficiency: Round-trip efficiency
        
        Returns:
        - Dict with arrays: battery_soc, grid_balance
        """
        print("\n" + "="*60)
        print("🔋 TEIL 3: SPEICHER-SIMULATION")
        print("="*60)
        print(f"   Batteriekapazität: {battery_capacity_kwh} kWh")
        print(f"   Wirkungsgrad: {battery_efficiency:.0%}")
        print(f"   Intervalle: {len(production_kwh)}")
        
        num_intervals = len(production_kwh)
        battery_soc = np.zeros(num_intervals)
        grid_balance = np.zeros(num_intervals)  # Positive=Einspeisung, Negative=Bezug
        
        current_soc = 0.0
        
        for i in range(num_intervals):
            prod = production_kwh[i]
            cons = consumption_kwh[i]
            
            battery_soc[i] = current_soc
            
            balance = prod - cons
            
            if balance > 0:
                # Excess production
                excess = balance
                
                # Try to charge battery
                if current_soc < battery_capacity_kwh:
                    charge_space = battery_capacity_kwh - current_soc
                    charge_amount = min(excess, charge_space)
                    actual_charge = charge_amount * battery_efficiency
                    current_soc += actual_charge
                    excess -= charge_amount
                
                # Remaining excess to grid (positive)
                grid_balance[i] = excess
            
            else:
                # Deficit (consumption > production)
                deficit = -balance
                
                # Try to use battery
                if current_soc > 0:
                    discharge_amount = min(deficit, current_soc)
                    actual_discharge = discharge_amount / battery_efficiency
                    current_soc -= discharge_amount
                    deficit -= discharge_amount
                
                # Remaining deficit from grid (negative)
                if deficit > 0:
                    grid_balance[i] = -deficit
        
        total_feed_in = grid_balance[grid_balance > 0].sum()
        total_draw = abs(grid_balance[grid_balance < 0].sum())
        
        print(f"   ✅ Simulation abgeschlossen")
        print(f"      Netzeinspeisung: {total_feed_in:.2f} kWh")
        print(f"      Netzbezug: {total_draw:.2f} kWh")
        
        return {
            'battery_soc': battery_soc,
            'grid_balance': grid_balance
        }
    
    # ============================================================================
    # HAUPTFUNKTION: Komplette Simulation
    # ============================================================================
    
    def run_complete_simulation(self, latitude, longitude, tilt, azimuth,
                                start_date, start_time, end_date, end_time,
                                pv_system_kwp, system_efficiency,
                                battery_capacity_kwh, battery_efficiency,
                                annual_consumption_kwh):
        """
        Run complete energy system simulation.
        
        Returns:
        - DataFrame with complete results
        - Dict with summary statistics
        """
        print("\n" + "="*70)
        print("🔆 ENERGIE-SYSTEM SIMULATION GESTARTET")
        print("="*70)
        
        # TEIL 1: PV-Produktion
        production_df = self.calculate_pv_production(
            latitude, longitude, tilt, azimuth,
            start_date, start_time, end_date, end_time,
            pv_system_kwp, system_efficiency
        )
        
        if production_df is None:
            print("\n❌ Produktion konnte nicht berechnet werden")
            return None, None
        
        # TEIL 2: Verbrauch
        consumption_array = self.load_household_consumption(
            annual_consumption_kwh,
            production_df.index
        )
        
        if consumption_array is None:
            print("\n❌ Verbrauch konnte nicht berechnet werden")
            return None, None
        
        # TEIL 3: Speicher-Simulation
        storage_results = self.simulate_storage(
            production_df['PV_Energie_kWh'].values,
            consumption_array,
            battery_capacity_kwh,
            battery_efficiency
        )
        
        # Erstelle Ergebnis-Tabelle
        print("\n" + "="*60)
        print("📊 ERGEBNISSE ZUSAMMENSTELLEN")
        print("="*60)
        
        result_table = pd.DataFrame({
            'Datum': production_df.index.strftime('%d.%m.%Y'),
            'Uhrzeit': production_df.index.strftime('%H:%M'),
            'Sonneneinstrahlung_W_m2': production_df['Sonneneinstrahlung_W_m2'].round(2),
            'Einstrahlung_15min_Wh_m2': production_df['Einstrahlung_15min_Wh_m2'].round(2),
            'PV_Energie_kWh': production_df['PV_Energie_kWh'].round(4),
            'Verbrauch_kWh': consumption_array.round(4),
            'Speicher_kWh': storage_results['battery_soc'].round(4),
            'Netz_kWh': storage_results['grid_balance'].round(4)
        })
        
        # Berechne Zusammenfassungswerte
        total_pv = result_table['PV_Energie_kWh'].sum()
        total_feed_in = result_table[result_table['Netz_kWh'] > 0]['Netz_kWh'].sum()
        total_draw = abs(result_table[result_table['Netz_kWh'] < 0]['Netz_kWh'].sum())
        total_consumption = result_table['Verbrauch_kWh'].sum()
        
        summary = {
            'total_pv_production': total_pv,
            'total_grid_feed_in': total_feed_in,
            'total_grid_draw': total_draw,
            'total_consumption': total_consumption,
            'num_intervals': len(result_table)
        }
        
        print(f"\n✅ Ergebnis-Tabelle erstellt: {len(result_table)} Intervalle")
        
        return result_table, summary


def main():
    """Interactive energy system simulator."""
    print("\n" + "="*70)
    print("🔆 ENERGIE-SYSTEM SIMULATOR")
    print("   PV-Produktion + Speicher + Verbrauch")
    print("="*70)
    
    simulator = EnergySystemSimulator()
    
    try:
        # EINGABEN
        print("\n📝 BITTE FOLGENDE PARAMETER EINGEBEN:\n")
        
        # 1. Standort
        print("📍 STANDORT:")
        location_input = input("   PLZ oder Breitengrad (z.B. '10115' oder '52.5'): ").strip()
        
        plz = None
        latitude = None
        longitude = None
        
        if location_input.isdigit() and len(location_input) == 5:
            plz = location_input
            coords = simulator.plz_to_coordinates(plz)
            if coords:
                latitude, longitude = coords
                print(f"   → {latitude:.2f}°N, {longitude:.2f}°E")
            else:
                print(f"   PLZ nicht gefunden")
                latitude = float(input("   Breitengrad: "))
                longitude = float(input("   Längengrad: "))
        else:
            latitude = float(location_input)
            longitude = float(input("   Längengrad: "))
        
        # 2. PV-Konfiguration
        print("\n☀️  PV-SYSTEM:")
        tilt = int(input("   Neigung in Grad (z.B. 30): "))
        azimuth = int(input("   Ausrichtung (0°=Nord, 90°=Ost, 180°=Süd, 270°=West): "))
        pv_system_kwp = float(input("   PV-Systemgröße in kWp (z.B. 10): "))
        system_efficiency = float(input("   Systemwirkungsgrad (z.B. 0.8 für 80%): ") or "0.8")
        
        # 3. Zeitraum
        print("\n📅 ZEITRAUM:")
        start_date = input("   Startdatum (DD/MM/YYYY, z.B. 01/06/2024): ")
        start_time = input("   Startzeit (HH:MM, z.B. 00:00): ")
        end_date = input("   Enddatum (DD/MM/YYYY, z.B. 30/06/2024): ")
        end_time = input("   Endzeit (HH:MM, z.B. 23:45): ")
        
        # 4. Batterie
        print("\n🔋 BATTERIE:")
        battery_capacity_kwh = float(input("   Speicherkapazität in kWh (z.B. 10): "))
        battery_efficiency = float(input("   Wirkungsgrad (z.B. 0.95 für 95%): ") or "0.95")
        
        # 5. Verbrauch
        print("\n🏠 VERBRAUCH:")
        annual_consumption_kwh = float(input("   Jahresverbrauch in kWh (z.B. 5000): "))
        
        # SIMULATION AUSFÜHREN
        print("\n" + "="*70)
        input("Drücke ENTER um Simulation zu starten...")
        
        result_table, summary = simulator.run_complete_simulation(
            latitude=latitude,
            longitude=longitude,
            tilt=tilt,
            azimuth=azimuth,
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
            pv_system_kwp=pv_system_kwp,
            system_efficiency=system_efficiency,
            battery_capacity_kwh=battery_capacity_kwh,
            battery_efficiency=battery_efficiency,
            annual_consumption_kwh=annual_consumption_kwh
        )
        
        if result_table is not None and summary is not None:
            # ERGEBNISSE ANZEIGEN
            print("\n" + "="*70)
            print("🎉 SIMULATION ABGESCHLOSSEN")
            print("="*70)
            
            print("\n📊 WICHTIGSTE KENNZAHLEN:")
            print(f"   1. Erzeugte Energie (PV):      {summary['total_pv_production']:>10.2f} kWh")
            print(f"   2. Netzeinspeisung:             {summary['total_grid_feed_in']:>10.2f} kWh")
            print(f"   3. Netzbezug:                   {summary['total_grid_draw']:>10.2f} kWh")
            print(f"   4. Gesamtverbrauch:             {summary['total_consumption']:>10.2f} kWh")
            
            # Validation check
            if '01/01/' in start_date and '31/12/' in end_date:
                diff = abs(summary['total_consumption'] - annual_consumption_kwh)
                print(f"\n   ✓ Kontrollwert (ganzes Jahr):")
                print(f"     Eingabe: {annual_consumption_kwh:.2f} kWh")
                print(f"     Berechnet: {summary['total_consumption']:.2f} kWh")
                print(f"     Differenz: {diff:.2f} kWh ({diff/annual_consumption_kwh*100:.2f}%)")
            
            # Sample anzeigen
            print(f"\n📋 TABELLEN-VORSCHAU (erste 10 Zeilen):")
            print(result_table.head(10).to_string(index=False))
            
            # CSV Export
            print("\n" + "="*70)
            save = input("\nErgebnisse als CSV speichern? (j/n): ").strip().lower()
            
            if save == 'j':
                default_name = f"simulation_{start_date.replace('/','')[:8]}_{end_date.replace('/','')[:8]}.csv"
                print(f"\n💾 CSV-EXPORT:")
                print(f"   Standard-Dateiname: {default_name}")
                filename = input("   Dateiname (oder Enter für Standard): ").strip()
                
                if not filename:
                    filename = default_name
                elif not filename.endswith('.csv'):
                    filename += '.csv'
                
                result_table.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"\n   ✅ Erfolgreich gespeichert!")
                print(f"   📁 Pfad: {os.path.abspath(filename)}")
            
            print("\n" + "="*70)
            print("✅ FERTIG!")
            print("="*70)
        
    except KeyboardInterrupt:
        print("\n\nProgramm abgebrochen.")
    except ValueError as e:
        print(f"\n❌ Eingabefehler: {e}")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


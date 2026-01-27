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
    
    # Available PV module types
    PV_MODULES = {
        'BAUER 445': {
            'name': 'BAUER Glas/Glas Black 445 Wp BS-445-108M10HBB-GG',
            'modul_flaeche_m2': 1.998108,  # Größe eines Moduls in m²
            'power_wp': 445  # Wp (Watt-Peak) pro Modul
        },
        'Winaico 450': {
            'name': 'Winaico WST-450 NFX54-B1 Full Black',
            'modul_flaeche_m2': 1.998108,  # Größe eines Moduls in m²
            'power_wp': 450  # Wp (Watt-Peak) pro Modul
        },
        'SOLYCO 445': {
            'name': 'SOLYCO R-TG 108n.4/445',
            'modul_flaeche_m2': 1.998108,  # Größe eines Moduls in m²
            'power_wp': 445  # Wp (Watt-Peak) pro Modul
        },
        'Winaico 480': {
            'name': 'Winaico WST-480 BDX54-BW ULTRA Black Glas/Glas',
            'modul_flaeche_m2': 2.04120,  # Größe eines Moduls in m²
            'power_wp': 480  # Wp (Watt-Peak) pro Modul
        }
    }
    
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
        self.BATTERY_EXCEL_FILE = "daten/2025-11_19_Nettokapazitäten Speicher (004).xlsx"
        self.HOUSEHOLD_PROFILE_FILE = "daten/standardlastprofil-haushaltskunden-2026.xlsx"
        
        # Load battery systems with efficiency data
        self.battery_systems = self.load_battery_systems()
        
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
        if self.battery_systems:
            print(f"   Speichersysteme: {len(self.battery_systems)} geladen")
    
    def load_battery_systems(self):
        """Load battery systems with capacity and efficiency from Excel."""
        try:
            df = pd.read_excel(self.BATTERY_EXCEL_FILE)
            
            battery_dict = {}
            
            for idx, row in df.iterrows():
                name = row.iloc[0].strip()  # Speicherhersteller / Typ
                capacity = float(row.iloc[1])  # Netto Kapazität
                efficiency_str = str(row.iloc[2])  # Effizienz (grob)
                storage_type = row.iloc[3]  # Speicher-Typ
                
                # Parse efficiency
                if '95' in efficiency_str or efficiency_str == '0.95':
                    efficiency = 0.95
                elif '75-80' in efficiency_str:
                    efficiency = 0.78  # Mittelwert von 75-80%
                else:
                    efficiency = 0.90  # Default fallback
                
                battery_dict[name] = {
                    'capacity_kwh': capacity,
                    'efficiency': efficiency,
                    'type': storage_type
                }
            
            return battery_dict
            
        except Exception as e:
            print(f"   ⚠️ Konnte Speichersysteme nicht laden: {e}")
            return {}
    
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
    
    def calculate_pv_production_single_roof(self, latitude, longitude, tilt, azimuth,
                                            start_date, start_time, end_date, end_time,
                                            pv_system_kwp, system_efficiency=0.8,
                                            roof_name="Dachfläche"):
        """
        Calculate PV energy production for a single roof surface.
        
        Returns:
        - DataFrame with datetime index and production values
        """
        print(f"\n   🏠 {roof_name}: {tilt}°/{azimuth}°, {pv_system_kwp} kWp")
        
        # Parse dates
        start_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        end_dt = datetime.strptime(f"{end_date} {end_time}", "%d/%m/%Y %H:%M")
        
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
        is_year_crossing = (end_dt.year > start_dt.year)
        
        if is_year_crossing:
            print(f"      Jahresübergang erkannt")
            num_intervals_needed = int((end_dt - start_dt).total_seconds() / 900)
            start_ref = start_dt.replace(year=reference_year)
            if start_ref.tzinfo is None:
                start_ref = pytz.UTC.localize(start_ref)
            
            start_idx = data_15min.index.get_indexer([start_ref], method='nearest')[0]
            total_intervals = len(data_15min)
            indices = [(start_idx + i) % total_intervals for i in range(num_intervals_needed)]
            filtered_data = data_15min.iloc[indices].copy()
        else:
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
        print(f"      ✅ {total_energy:.2f} kWh erzeugt")
        
        return filtered_data
    
    def calculate_pv_production(self, latitude, longitude, roof_surfaces,
                                start_date, start_time, end_date, end_time,
                                system_efficiency=0.8):
        """
        Calculate PV energy production for multiple roof surfaces.
        
        Parameters:
        - roof_surfaces: List of dicts with {tilt, azimuth, kwp, name}
        
        Returns:
        - DataFrame with combined production from all surfaces
        """
        print("\n" + "="*60)
        print("☀️  TEIL 1: PV-PRODUKTION BERECHNEN")
        print("="*60)
        print(f"   Standort: {latitude:.2f}°N, {longitude:.2f}°E")
        print(f"   Anzahl Dachflächen: {len(roof_surfaces)}")
        
        total_kwp = sum(roof['kwp'] for roof in roof_surfaces)
        print(f"   Gesamt-System: {total_kwp} kWp, {system_efficiency:.0%} Wirkungsgrad")
        
        # Parse dates once
        start_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        end_dt = datetime.strptime(f"{end_date} {end_time}", "%d/%m/%Y %H:%M")
        print(f"   Zeitraum: {start_dt.strftime('%d.%m.%Y %H:%M')} bis {end_dt.strftime('%d.%m.%Y %H:%M')}")
        
        # Calculate production for each roof surface
        all_roof_data = []
        combined_production = None
        
        for idx, roof in enumerate(roof_surfaces, 1):
            roof_data = self.calculate_pv_production_single_roof(
                latitude, longitude,
                roof['tilt'], roof['azimuth'],
                start_date, start_time, end_date, end_time,
                roof['kwp'], system_efficiency,
                roof_name=roof.get('name', f"Dachfläche {idx}")
            )
            
            if roof_data is None:
                print(f"      ❌ Fehler bei {roof.get('name', f'Dachfläche {idx}')}")
                return None
            
            all_roof_data.append(roof_data)
            
            # Combine production
            if combined_production is None:
                combined_production = roof_data['PV_Energie_kWh'].copy()
            else:
                combined_production += roof_data['PV_Energie_kWh']
        
        # Store individual roof data and combined totals
        result_data = all_roof_data[0].copy()
        
        # Add individual roof irradiation columns (per module on that roof)
        for i, (roof_data, roof_config) in enumerate(zip(all_roof_data, roof_surfaces), 1):
            # Einstrahlung auf diese Dachfläche (alle Module dieser Fläche)
            result_data[f'Strahlung_Dach{i}_W'] = (
                roof_data['Sonneneinstrahlung_W_m2'] * roof_config['modules']
            ).round(1)
            result_data[f'Einstrahlung_Dach{i}_Wh'] = (
                roof_data['Einstrahlung_15min_Wh_m2'] * roof_config['modules']
            ).round(1)
            result_data[f'PV_Dach{i}_kWh'] = roof_data['PV_Energie_kWh']
        
        # Calculate TOTAL irradiation on entire PV system (sum of all roofs!)
        total_strahlung_w = sum(
            all_roof_data[i]['Sonneneinstrahlung_W_m2'] * roof_surfaces[i]['modules']
            for i in range(len(roof_surfaces))
        )
        
        total_einstrahlung_wh = sum(
            all_roof_data[i]['Einstrahlung_15min_Wh_m2'] * roof_surfaces[i]['modules'] 
            for i in range(len(roof_surfaces))
        )
        
        result_data['Gesamt_Strahlung_W'] = pd.Series(total_strahlung_w, index=result_data.index)
        result_data['Gesamt_Einstrahlung_Wh'] = pd.Series(total_einstrahlung_wh, index=result_data.index)
        
        # Add combined total production column
        result_data['PV_Gesamt_kWh'] = combined_production
        
        total_energy = combined_production.sum()
        print(f"\n   ✅ GESAMT-PRODUKTION: {total_energy:.2f} kWh")
        print(f"      Einzelne Dachflächen:")
        for i, roof_config in enumerate(roof_surfaces, 1):
            roof_total = all_roof_data[i-1]['PV_Energie_kWh'].sum()
            percent = (roof_total / total_energy) * 100 if total_energy > 0 else 0
            print(f"      - Dachfläche {i}: {roof_total:.2f} kWh ({percent:.1f}%)")
        
        return result_data
    
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
    
    def run_complete_simulation(self, latitude, longitude, roof_surfaces,
                                start_date, start_time, end_date, end_time,
                                system_efficiency,
                                battery_capacity_kwh, battery_efficiency,
                                annual_consumption_kwh):
        """
        Run complete energy system simulation with multiple roof surfaces.
        
        Parameters:
        - roof_surfaces: List of dicts with {tilt, azimuth, kwp, name}
        
        Returns:
        - DataFrame with complete results
        - Dict with summary statistics
        """
        print("\n" + "="*70)
        print("🔆 ENERGIE-SYSTEM SIMULATION GESTARTET")
        print("="*70)
        
        # TEIL 1: PV-Produktion
        production_df = self.calculate_pv_production(
            latitude, longitude, roof_surfaces,
            start_date, start_time, end_date, end_time,
            system_efficiency
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
            production_df['PV_Gesamt_kWh'].values,  # ← Verwende Gesamt-Produktion
            consumption_array,
            battery_capacity_kwh,
            battery_efficiency
        )
        
        # Erstelle Ergebnis-Tabelle
        print("\n" + "="*60)
        print("📊 ERGEBNISSE ZUSAMMENSTELLEN")
        print("="*60)
        
        # Start with basic columns
        result_dict = {
            'Datum': production_df.index.strftime('%d.%m.%Y'),
            'Uhrzeit': production_df.index.strftime('%H:%M'),
        }
        
        # Add individual roof irradiation columns
        for col in production_df.columns:
            if col.startswith('Strahlung_Dach') and col.endswith('_W'):
                result_dict[col] = production_df[col].round(1)
            elif col.startswith('Einstrahlung_Dach') and col.endswith('_Wh'):
                result_dict[col] = production_df[col].round(1)
        
        # Add total irradiation columns
        result_dict['Gesamt_Strahlung_W'] = production_df['Gesamt_Strahlung_W'].round(1)
        result_dict['Gesamt_Einstrahlung_Wh'] = production_df['Gesamt_Einstrahlung_Wh'].round(1)
        
        # Add individual roof production columns
        for col in production_df.columns:
            if col.startswith('PV_Dach') and col.endswith('_kWh'):
                result_dict[col] = production_df[col].round(4)
        
        # Add total production and other columns
        result_dict.update({
            'PV_Gesamt_kWh': production_df['PV_Gesamt_kWh'].round(4),
            'Verbrauch_kWh': consumption_array.round(4),
            'Speicher_kWh': storage_results['battery_soc'].round(4),
            'Netz_kWh': storage_results['grid_balance'].round(4)
        })
        
        result_table = pd.DataFrame(result_dict)
        
        # Berechne Zusammenfassungswerte
        total_pv = result_table['PV_Gesamt_kWh'].sum()
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
        
        # 2. PV-Modultyp auswählen
        print("\n🔲 PV-MODULTYP:")
        print("   Verfügbare Module:")
        for i, (key, module) in enumerate(simulator.PV_MODULES.items(), 1):
            print(f"   {i}. {module['name']}")
            print(f"      → {module['modul_flaeche_m2']:.2f} m²/Modul, {module['power_wp']:.0f} Wp/Modul")
        
        print()
        module_choice = input("   Nummer des Modultyps (z.B. 2): ").strip()
        module_keys = list(simulator.PV_MODULES.keys())
        
        try:
            module_idx = int(module_choice) - 1
            selected_module_key = module_keys[module_idx]
            selected_module = simulator.PV_MODULES[selected_module_key]
            print(f"   ✅ Gewählt: {selected_module['name']}")
            print(f"      {selected_module['modul_flaeche_m2']:.2f} m²/Modul, {selected_module['power_wp']:.0f} Wp/Modul")
        except (ValueError, IndexError):
            print(f"   ❌ Ungültige Auswahl, verwende Standard (Winaico 450)")
            selected_module_key = 'Winaico 450'
            selected_module = simulator.PV_MODULES[selected_module_key]
        
        # 3. Systemwirkungsgrad
        print("\n⚙️  SYSTEMWIRKUNGSGRAD:")
        system_efficiency = float(input("   Wirkungsgrad (z.B. 0.8 für 80%): ") or "0.8")
        
        # 4. Dachflächen konfigurieren
        print("\n☀️  DACHFLÄCHEN:")
        
        roof_surfaces = []
        roof_number = 1
        total_modules = 0
        total_kwp = 0
        
        while True:
            print(f"\n   🏠 DACHFLÄCHE {roof_number}:")
            
            # Input für diese Dachfläche
            tilt = int(input(f"      Neigung in Grad (z.B. 30): "))
            azimuth = int(input(f"      Ausrichtung (0°=Nord, 90°=Ost, 180°=Süd, 270°=West): "))
            dach_flaeche_m2 = float(input(f"      Verfügbare Dachfläche in m² (z.B. 40): "))
            
            # Berechne Anzahl Module und kWp
            anzahl_module = int(dach_flaeche_m2 / selected_module['modul_flaeche_m2'])
            kwp_this_roof = (anzahl_module * selected_module['power_wp']) / 1000  # Wp → kWp
            nutzbare_flaeche = anzahl_module * selected_module['modul_flaeche_m2']
            
            print(f"      → {anzahl_module} Module passen auf {dach_flaeche_m2} m²")
            print(f"      → Nutzbare Fläche: {nutzbare_flaeche:.2f} m²")
            print(f"      → Leistung: {kwp_this_roof:.2f} kWp")
            
            if anzahl_module == 0:
                print(f"      ⚠️ Dachfläche zu klein für Module! Minimum: {selected_module['modul_flaeche_m2']:.2f} m²")
                continue
            
            # Add roof surface
            roof_surfaces.append({
                'tilt': tilt,
                'azimuth': azimuth,
                'kwp': kwp_this_roof,
                'modules': anzahl_module,
                'dach_flaeche_m2': dach_flaeche_m2,  # Größe der Dachfläche in m²
                'name': f"Dachfläche {roof_number}"
            })
            
            total_modules += anzahl_module
            total_kwp += kwp_this_roof
            
            # Ask if user wants to add another roof
            add_more = input(f"\n   Weitere Dachfläche hinzufügen? (j/n): ").strip().lower()
            if add_more != 'j':
                break
            
            roof_number += 1
        
        # Summary of roof configuration
        print(f"\n   📊 ZUSAMMENFASSUNG PV-SYSTEM:")
        print(f"      Modultyp: {selected_module['name']}")
        for i, roof in enumerate(roof_surfaces, 1):
            percent = (roof['kwp'] / total_kwp) * 100 if total_kwp > 0 else 0
            print(f"      Dachfläche {i}: {roof['tilt']}°/{roof['azimuth']}°, {roof['dach_flaeche_m2']} m², {roof['modules']} Module, {roof['kwp']:.2f} kWp ({percent:.1f}%)")
        print(f"      GESAMT: {total_modules} Module, {total_kwp:.2f} kWp")
        
        # 3. Zeitraum
        print("\n📅 ZEITRAUM:")
        start_date = input("   Startdatum (DD/MM/YYYY, z.B. 01/06/2024): ")
        start_time = input("   Startzeit (HH:MM, z.B. 00:00): ")
        end_date = input("   Enddatum (DD/MM/YYYY, z.B. 30/06/2024): ")
        end_time = input("   Endzeit (HH:MM, z.B. 23:45): ")
        
        # 4. Batterie-Auswahl
        print("\n🔋 BATTERIE-SYSTEM:")
        
        if simulator.battery_systems:
            # Show available battery systems grouped by type
            dc_systems = {k: v for k, v in simulator.battery_systems.items() if v['type'] == 'DC'}
            ac_systems = {k: v for k, v in simulator.battery_systems.items() if v['type'] == 'AC'}
            
            print("   Verfügbare Systeme:")
            print()
            
            all_systems = list(simulator.battery_systems.items())
            
            if dc_systems:
                print("   DC-Systeme (Effizienz 95%):")
                for i, (name, spec) in enumerate([item for item in all_systems if item[1]['type'] == 'DC'], 1):
                    print(f"   {i}. {name}: {spec['capacity_kwh']} kWh")
            
            dc_count = len(dc_systems)
            
            if ac_systems:
                print(f"\n   AC-Systeme (Effizienz ~78%):")
                for i, (name, spec) in enumerate([item for item in all_systems if item[1]['type'] == 'AC'], dc_count + 1):
                    print(f"   {i}. {name}: {spec['capacity_kwh']} kWh")
            
            print()
            battery_choice = input("   Nummer des Batterie-Systems: ").strip()
            
            try:
                battery_idx = int(battery_choice) - 1
                selected_battery_name = all_systems[battery_idx][0]
                selected_battery = all_systems[battery_idx][1]
                
                battery_capacity_kwh = selected_battery['capacity_kwh']
                battery_efficiency = selected_battery['efficiency']
                battery_type = selected_battery['type']
                
                print(f"\n   ✅ Gewählt: {selected_battery_name}")
                print(f"      Kapazität: {battery_capacity_kwh} kWh (netto)")
                print(f"      Effizienz: {battery_efficiency:.0%}")
                print(f"      Typ: {battery_type}-gekoppelt")
                
            except (ValueError, IndexError):
                print(f"   ⚠️ Ungültige Auswahl, verwende Standard (10 kWh, 95%)")
                battery_capacity_kwh = 10.0
                battery_efficiency = 0.95
        else:
            print("   ⚠️ Batteriesysteme konnten nicht geladen werden")
            print("   Manuelle Eingabe:")
            battery_capacity_kwh = float(input("   Speicherkapazität in kWh: "))
            battery_efficiency = float(input("   Wirkungsgrad (z.B. 0.95): ") or "0.95")
        
        # 5. Verbrauch
        print("\n🏠 VERBRAUCH:")
        annual_consumption_kwh = float(input("   Jahresverbrauch in kWh (z.B. 5000): "))
        
        # SIMULATION AUSFÜHREN
        print("\n" + "="*70)
        input("Drücke ENTER um Simulation zu starten...")
        
        result_table, summary = simulator.run_complete_simulation(
            latitude=latitude,
            longitude=longitude,
            roof_surfaces=roof_surfaces,
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
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


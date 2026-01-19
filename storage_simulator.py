#!/usr/bin/env python3
"""
Storage Simulator - Battery Energy Storage Simulation
Simulates battery charging/discharging with 15-minute intervals.

Tracks:
1. PV energy production (kWh per 15 min)
2. Household consumption (kWh per 15 min)
3. Battery state of charge (kWh)
4. Grid feed-in and consumption
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class StorageSimulator:
    """Simulate battery storage for PV system with 15-minute intervals."""
    
    # Battery systems loaded from Excel file
    BATTERY_SYSTEMS = None
    BATTERY_EXCEL_FILE = "2025-11_19_Nettokapazitäten Speicher.xlsx"
    HOUSEHOLD_PROFILE_FILE = "modeling/standardlastprofil-haushaltskunden-2026.xlsx"
    HOUSEHOLD_PROFILE_INTERVALS = 35040  # 365 Tage × 96 Intervalle
    
    @classmethod
    def load_battery_systems(cls):
        """Load battery systems from Excel file."""
        if cls.BATTERY_SYSTEMS is not None:
            return cls.BATTERY_SYSTEMS
        
        try:
            import pandas as pd
            df = pd.read_excel(cls.BATTERY_EXCEL_FILE)
            
            # Create dictionary from Excel data
            # Column 0: "Speicherhersteller / Typ"
            # Column 1: "Netto Kapazität" (in kWh)
            cls.BATTERY_SYSTEMS = {}
            
            for idx, row in df.iterrows():
                name = row.iloc[0]  # First column: system name
                capacity = row.iloc[1]  # Second column: "Netto Kapazität"
                
                # Clean up name for easier selection
                clean_name = name.strip()
                cls.BATTERY_SYSTEMS[clean_name] = float(capacity)
            
            return cls.BATTERY_SYSTEMS
            
        except Exception as e:
            print(f"⚠️  Konnte Excel-Datei nicht laden: {e}")
            print("   Verwende manuelle Eingabe")
            return {}
    
    def __init__(self, battery_capacity_kwh=None, battery_efficiency=0.95, battery_name=None):
        """
        Initialize storage simulator.
        
        Parameters:
        - battery_capacity_kwh: Net battery capacity (required if no battery_name)
        - battery_efficiency: Round-trip efficiency (default: 95%)
        - battery_name: Battery system name from Excel file
        
        Note: Either battery_name OR battery_capacity_kwh must be provided
        """
        # Load battery systems from Excel
        systems = self.load_battery_systems()
        
        if battery_name and battery_name in systems:
            # Use capacity from Excel "Netto Kapazität" column
            self.battery_capacity = systems[battery_name]
            self.battery_name = battery_name
            print(f"🔋 Storage Simulator initialisiert")
            print(f"   System: {battery_name}")
            print(f"   Speicherkapazität: {self.battery_capacity} kWh (netto aus Excel)")
        elif battery_capacity_kwh is not None:
            self.battery_capacity = battery_capacity_kwh
            self.battery_name = f"Custom {battery_capacity_kwh} kWh"
            print(f"🔋 Storage Simulator initialisiert")
            print(f"   Speicherkapazität: {battery_capacity_kwh} kWh (netto)")
        else:
            raise ValueError("Entweder battery_name oder battery_capacity_kwh muss angegeben werden!")
        
        self.battery_efficiency = battery_efficiency
        print(f"   Wirkungsgrad: {battery_efficiency:.0%}")
    
    @classmethod
    def list_available_systems(cls):
        """List all available battery systems from Excel."""
        systems = cls.load_battery_systems()
        
        if not systems:
            print("❌ Keine Speichersysteme verfügbar")
            return
        
        print("\n🔋 Verfügbare Speichersysteme (aus Excel):")
        print("="*60)
        
        # Group by manufacturer
        sungrow = {k: v for k, v in systems.items() if 'Sungrow' in k}
        sonnen = {k: v for k, v in systems.items() if 'sonnen' in k}
        solaredge = {k: v for k, v in systems.items() if 'SolarEdge' in k}
        
        if sungrow:
            print("\n📦 Sungrow SBR Serie:")
            for name, cap in sorted(sungrow.items(), key=lambda x: x[1]):
                print(f"   {name}: {cap} kWh (Netto)")
        
        if sonnen:
            print("\n📦 sonnenBatterie:")
            for name, cap in sorted(sonnen.items(), key=lambda x: x[1]):
                print(f"   {name}: {cap} kWh (Netto)")
        
        if solaredge:
            print("\n📦 SolarEdge:")
            for name, cap in sorted(solaredge.items(), key=lambda x: x[1]):
                print(f"   {name}: {cap} kWh (Netto)")
        
        print(f"\n✅ Gesamt: {len(systems)} Systeme aus 'Netto Kapazität' Spalte")
    
    def load_household_consumption(self, annual_consumption_kwh, target_intervals=None, target_datetimes=None):
        """
        Load the official household standard load profile (15-min intervals) and scale it.
        
        Parameters:
        - annual_consumption_kwh: User's annual consumption (kWh)
        - target_intervals: Optional number of intervals to match (fallback if datetimes missing)
        - target_datetimes: Optional pandas Series/list with exact timestamps to extract
        
        Returns:
        - Numpy array with consumption per interval (kWh)
        """
        print("\n📊 Lade Standardlastprofil Haushaltskunden...")
        print(f"   Datei: {self.HOUSEHOLD_PROFILE_FILE}")
        print(f"   Ziel-Jahresverbrauch: {annual_consumption_kwh} kWh")
        
        try:
            df = pd.read_excel(self.HOUSEHOLD_PROFILE_FILE)
            df_clean = df.iloc[2:].copy()  # Remove header/control rows
            
            if 'SLP-HB [kWh]' not in df_clean.columns:
                raise ValueError("Spalte 'SLP-HB [kWh]' nicht gefunden")
            
            df_clean = df_clean.reset_index(drop=True)
            df_clean['IntervalStart'] = pd.to_datetime(df_clean['Datum'])
            
            # Validate that profile starts on January 1st
            first_date = df_clean['IntervalStart'].iloc[0]
            if first_date.month != 1 or first_date.day != 1:
                print(f"   ⚠️ WARNUNG: Profil startet nicht am 1. Januar!")
                print(f"      Tatsächlicher Start: {first_date.strftime('%d.%m.%Y')}")
                print(f"      Dies kann zu falschen saisonalen Zuordnungen führen.")
            
            # Check profile covers full year (should be 35040 intervals = 365 days)
            expected_intervals = 365 * 96  # 96 intervals per day
            if len(df_clean) != expected_intervals:
                print(f"   ⚠️ WARNUNG: Profil hat {len(df_clean)} Intervalle (erwartet: {expected_intervals})")
                if len(df_clean) == 366 * 96:
                    print(f"      Profil enthält Schaltjahr (366 Tage)")
            
            profile_values = df_clean['SLP-HB [kWh]'].astype(float).values
            profile_sum = profile_values.sum()
            
            if profile_sum == 0:
                raise ValueError("Profil-Summe ist 0 kWh")
            
            scale_factor = annual_consumption_kwh / profile_sum
            scaled_profile = profile_values * scale_factor
            
            profile_df = pd.DataFrame({
                'IntervalStart': df_clean['IntervalStart'],
                'Scaled_kWh': scaled_profile
            })
            profile_df['doy'] = profile_df['IntervalStart'].dt.dayofyear
            profile_df['minute_of_day'] = profile_df['IntervalStart'].dt.hour * 60 + profile_df['IntervalStart'].dt.minute
            
            print(f"   ✅ {len(scaled_profile)} Intervalle geladen")
            print(f"   Profil-Summe nach Skalierung: {scaled_profile.sum():.2f} kWh")
            print(f"   Skalierungsfaktor: {scale_factor:.6f}")
            
            if target_datetimes is not None:
                return self._extract_profile_for_datetimes(profile_df, target_datetimes)
            
            if target_intervals and target_intervals != len(scaled_profile):
                return self._match_interval_length(
                    scaled_profile,
                    target_intervals,
                    annual_consumption_kwh
                )
            
            return scaled_profile
        
        except FileNotFoundError:
            print("   ❌ Standardlastprofil nicht gefunden.")
        except Exception as e:
            print(f"   ❌ Fehler beim Laden des Lastprofils: {e}")
        
        return None
    
    def _match_interval_length(self, consumption_array, target_intervals, annual_consumption_kwh):
        """
        Adjust consumption array to match the number of intervals of the production profile.
        Preserves the typical shape by repeating the pattern and rescales to expected total.
        """
        original_length = len(consumption_array)
        print(f"   ℹ️ Produktionsdaten haben {target_intervals} Intervalle (Profil: {original_length})")
        
        resized = np.resize(consumption_array, target_intervals)
        
        # Expected total consumption for the simulated time window
        fraction_of_year = target_intervals / original_length
        expected_total = annual_consumption_kwh * fraction_of_year
        current_total = resized.sum()
        
        if current_total > 0:
            resize_factor = expected_total / current_total
            resized *= resize_factor
            print(f"   Angepasste Summe für Zeitfenster: {resized.sum():.2f} kWh")
        else:
            print("   ⚠️ Angepasster Verbrauch ist 0 kWh, verwende Nullen.")
            resized = np.zeros(target_intervals)
        
        return resized
    
    def _extract_profile_for_datetimes(self, profile_df, target_datetimes):
        """
        Extract scaled consumption values that match the exact timestamps of the production data.
        """
        try:
            target_index = pd.to_datetime(target_datetimes)
        except Exception as e:
            print(f"   ❌ Konnte Ziel-Datumswerte nicht parsen: {e}")
            return None
        
        lookup = profile_df.set_index(['doy', 'minute_of_day'])['Scaled_kWh'].to_dict()
        max_doy = int(profile_df['doy'].max())
        
        values = np.zeros(len(target_index))
        missing = 0
        
        for idx, ts in enumerate(target_index):
            doy = ts.timetuple().tm_yday
            minute = ts.hour * 60 + ts.minute
            key = (doy, minute)
            
            if key not in lookup:
                # Handle leap day or calendar mismatches by wrapping into 365-day profile
                if doy > max_doy:
                    doy = max_doy
                else:
                    doy = ((doy - 1) % max_doy) + 1
                key = (doy, minute)
            
            value = lookup.get(key)
            if value is None:
                values[idx] = 0.0
                missing += 1
            else:
                values[idx] = value
        
        if missing:
            print(f"   ⚠️ {missing} Intervalle ohne SLP-Match → 0 kWh gesetzt")
        
        requested_total = values.sum()
        print(f"   ✅ {len(values)} Intervalle nach Kalender-Zuordnung, Summe: {requested_total:.2f} kWh")
        
        return values
    
    def create_dummy_consumption(self, num_intervals, annual_consumption_kwh):
        """
        ⚠️ DEPRECATED - FALLBACK ONLY ⚠️
        
        Create synthetic consumption profile using simple time-based averaging.
        This is ONLY used as emergency fallback if Standardlastprofil Excel cannot be loaded.
        
        WARNING: Does NOT use real seasonal patterns! 
        Uses generic day/night factors instead of actual consumption data.
        
        Parameters:
        - num_intervals: Number of 15-minute intervals
        - annual_consumption_kwh: Annual consumption
        
        Returns:
        - Array with consumption per 15-min interval (kWh)
        """
        print(f"\n⚠️  ACHTUNG: Verwende FALLBACK-Verbrauchsprofil!")
        print(f"   (Keine saisonalen Muster - nur generische Tag/Nacht-Verteilung)")
        print(f"   Jahresverbrauch: {annual_consumption_kwh} kWh")
        
        # Average consumption per interval
        avg_per_interval = annual_consumption_kwh / 35040  # 35040 intervals per year
        
        # Create time-based pattern (higher during day, lower at night)
        consumption = []
        
        for i in range(num_intervals):
            # Hour of day (0-23)
            hour = (i // 4) % 24
            
            # Consumption pattern (factor of average)
            if 6 <= hour < 9:  # Morning peak
                factor = 1.5
            elif 17 <= hour < 22:  # Evening peak
                factor = 1.8
            elif 0 <= hour < 6:  # Night
                factor = 0.5
            else:  # Day
                factor = 1.0
            
            consumption.append(avg_per_interval * factor)
        
        print(f"   ✅ {num_intervals} Intervalle erstellt")
        print(f"   Durchschnitt: {np.mean(consumption):.4f} kWh pro 15 Min")
        
        return np.array(consumption)
    
    def simulate(self, production_kwh, consumption_kwh, initial_soc_kwh=0):
        """
        Simulate battery storage for given production and consumption.
        
        Parameters:
        - production_kwh: Array of PV production per 15-min interval (kWh)
        - consumption_kwh: Array of consumption per 15-min interval (kWh)
        - initial_soc_kwh: Initial battery state of charge (default: 0)
        
        Returns:
        - DataFrame with detailed simulation results
        """
        print(f"\n🔄 Starte Simulation...")
        print(f"   Intervalle: {len(production_kwh)}")
        print(f"   Start-Ladezustand: {initial_soc_kwh:.2f} kWh")
        
        # Initialize tracking arrays
        num_intervals = len(production_kwh)
        battery_soc = np.zeros(num_intervals)  # State of charge
        grid_feed_in = np.zeros(num_intervals)  # Energy fed to grid
        grid_consumption = np.zeros(num_intervals)  # Energy from grid
        self_consumption = np.zeros(num_intervals)  # Direct self-consumption
        battery_charge = np.zeros(num_intervals)  # Energy charged to battery
        battery_discharge = np.zeros(num_intervals)  # Energy discharged from battery
        
        # Current battery state
        current_soc = initial_soc_kwh
        
        # Simulate each interval
        for i in range(num_intervals):
            prod = production_kwh[i]
            cons = consumption_kwh[i]
            
            # Store SOC at start of interval
            battery_soc[i] = current_soc
            
            # Calculate energy balance
            balance = prod - cons
            
            if balance > 0:
                # Excess production
                excess = balance
                
                # First: Direct self-consumption
                self_consumption[i] = cons
                
                # Second: Charge battery if space available
                if current_soc < self.battery_capacity:
                    # How much can we charge?
                    charge_space = self.battery_capacity - current_soc
                    charge_amount = min(excess, charge_space)
                    
                    # Apply charging efficiency
                    actual_charge = charge_amount * self.battery_efficiency
                    current_soc += actual_charge
                    battery_charge[i] = actual_charge
                    
                    excess -= charge_amount
                
                # Third: Remaining excess to grid
                if excess > 0:
                    grid_feed_in[i] = excess
            
            else:
                # Deficit (consumption > production)
                deficit = -balance
                
                # First: Use all production
                self_consumption[i] = prod
                
                # Second: Use battery if available
                if current_soc > 0:
                    discharge_amount = min(deficit, current_soc)
                    
                    # Apply discharging efficiency
                    actual_discharge = discharge_amount / self.battery_efficiency
                    current_soc -= discharge_amount
                    battery_discharge[i] = discharge_amount
                    
                    deficit -= discharge_amount
                
                # Third: Remaining deficit from grid
                if deficit > 0:
                    grid_consumption[i] = deficit
        
        # Create results DataFrame
        results = pd.DataFrame({
            'Produktion_kWh': production_kwh,
            'Verbrauch_kWh': consumption_kwh,
            'Speicher_Ladezustand_kWh': battery_soc,
            'Eigenverbrauch_kWh': self_consumption,
            'Speicher_Ladung_kWh': battery_charge,
            'Speicher_Entladung_kWh': battery_discharge,
            'Netzeinspeisung_kWh': grid_feed_in,
            'Netzbezug_kWh': grid_consumption
        })
        
        # Calculate summary statistics
        print(f"\n✅ Simulation abgeschlossen!")
        print(f"\n📊 Zusammenfassung:")
        print(f"   Gesamt-Produktion: {results['Produktion_kWh'].sum():.2f} kWh")
        print(f"   Gesamt-Verbrauch: {results['Verbrauch_kWh'].sum():.2f} kWh")
        print(f"   Eigenverbrauch: {results['Eigenverbrauch_kWh'].sum():.2f} kWh")
        print(f"   Netzeinspeisung: {results['Netzeinspeisung_kWh'].sum():.2f} kWh")
        print(f"   Netzbezug: {results['Netzbezug_kWh'].sum():.2f} kWh")
        
        # Calculate key metrics
        total_production = results['Produktion_kWh'].sum()
        total_consumption = results['Verbrauch_kWh'].sum()
        total_self_consumption = results['Eigenverbrauch_kWh'].sum()
        
        if total_production > 0:
            self_consumption_rate = (total_self_consumption / total_production) * 100
            print(f"\n🎯 Eigenverbrauchsquote: {self_consumption_rate:.1f}%")
        
        if total_consumption > 0:
            autarky_rate = ((total_consumption - results['Netzbezug_kWh'].sum()) / total_consumption) * 100
            print(f"🎯 Autarkiegrad: {autarky_rate:.1f}%")
        
        # Battery usage
        total_charged = results['Speicher_Ladung_kWh'].sum()
        total_discharged = results['Speicher_Entladung_kWh'].sum()
        print(f"\n🔋 Speicher-Nutzung:")
        print(f"   Geladen: {total_charged:.2f} kWh")
        print(f"   Entladen: {total_discharged:.2f} kWh")
        print(f"   Zyklen: {total_charged / self.battery_capacity:.1f}")
        
        return results
    
    def simulate_from_csv(self, production_csv, consumption_csv_or_annual_kwh):
        """
        Run simulation from CSV files.
        
        Parameters:
        - production_csv: CSV file from solar_irradiation_calculator
        - consumption_csv_or_annual_kwh: Either CSV file or annual consumption (kWh)
        """
        print(f"\n🔆 STORAGE SIMULATION")
        print("="*60)
        
        # Load production data
        print(f"📊 Lade Produktionsdaten...")
        prod_df = pd.read_csv(production_csv)
        
        if 'PV_Energie_kWh' not in prod_df.columns:
            print("❌ CSV muss 'PV_Energie_kWh' Spalte enthalten")
            return None
        
        production = prod_df['PV_Energie_kWh'].values
        print(f"   ✅ {len(production)} Intervalle geladen")
        
        # Load or create consumption data
        prod_datetimes = None
        if {'Datum', 'Uhrzeit'}.issubset(prod_df.columns):
            try:
                prod_datetimes = pd.to_datetime(
                    prod_df['Datum'].astype(str) + " " + prod_df['Uhrzeit'].astype(str)
                )
            except Exception as e:
                print(f"   ⚠️ Konnte Produktions-Zeitstempel nicht parsen: {e}")
                prod_datetimes = None
        
        if isinstance(consumption_csv_or_annual_kwh, str):
            # Load from CSV
            print(f"📊 Lade Verbrauchsdaten...")
            cons_df = pd.read_csv(consumption_csv_or_annual_kwh)
            consumption = cons_df['Verbrauch_kWh'].values
        else:
            # Scale household standard load profile to requested annual consumption
            annual_kwh = float(consumption_csv_or_annual_kwh)
            consumption = self.load_household_consumption(
                annual_kwh,
                target_intervals=len(production),
                target_datetimes=prod_datetimes
            )
            
            if consumption is None:
                print("\n" + "="*60)
                print("⚠️  WARNUNG: Standardlastprofil konnte nicht geladen werden!")
                print("   Verwende FALLBACK mit synthetischem Profil")
                print("   → Keine korrekten saisonalen Verbrauchsmuster!")
                print("="*60)
                consumption = self.create_dummy_consumption(len(production), annual_kwh)
        
        print(f"   ✅ {len(consumption)} Intervalle")
        
        # Run simulation
        results = self.simulate(production, consumption)
        
        # Add datetime info from production CSV
        if 'Datum' in prod_df.columns and 'Uhrzeit' in prod_df.columns:
            results.insert(0, 'Datum', prod_df['Datum'].values)
            results.insert(1, 'Uhrzeit', prod_df['Uhrzeit'].values)
        
        return results
    
    def save_results(self, results, filename):
        """Save simulation results to CSV."""
        results.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 Ergebnisse gespeichert: {filename}")
        print(f"📁 Pfad: {os.path.abspath(filename)}")


def main():
    """Interactive storage simulator."""
    print("\n🔋" + "=" * 58 + "🔋")
    print()
    print("=== Battery Storage Simulator ===")
    print("Simuliert Speicher-Lade/Entlade-Zyklen")
    print()
    
    try:
        # Battery configuration
        print("🔋 SPEICHER-KONFIGURATION:")
        print()
        
        # Show available systems
        show_systems = input("Verfügbare Speichersysteme anzeigen? (j/n): ").strip().lower()
        if show_systems == 'j':
            StorageSimulator.list_available_systems()
            print()
        
        # Ask for system selection
        use_predefined = input("Vordefiniertes System aus Excel verwenden? (j/n): ").strip().lower()
        
        if use_predefined == 'j':
            print("\nBitte genauen Systemnamen aus der Liste eingeben")
            print("(z.B. 'Sungrow SBR096 / 9,6 kWh')")
            system_name = input("\nSystemname: ").strip()
            efficiency = float(input("Wirkungsgrad (z.B. 0.95 für 95%): ") or "0.95")
            
            simulator = StorageSimulator(
                battery_name=system_name,
                battery_efficiency=efficiency
            )
        else:
            print("\nBitte Speicherkapazität manuell eingeben:")
            capacity = float(input("Speicherkapazität in kWh: "))
            efficiency = float(input("Wirkungsgrad (z.B. 0.95 für 95%): ") or "0.95")
            
            simulator = StorageSimulator(
                battery_capacity_kwh=capacity,
                battery_efficiency=efficiency
            )
        
        # Production data
        print("\n☀️ PRODUKTIONSDATEN:")
        prod_csv = input("CSV-Datei mit PV-Produktion: ").strip()
        
        if not os.path.exists(prod_csv):
            print(f"❌ Datei nicht gefunden: {prod_csv}")
            return
        
        # Consumption data
        print("\n🏠 VERBRAUCHSDATEN:")
        use_csv = input("Verbrauchs-CSV vorhanden? (j/n): ").strip().lower()
        
        if use_csv == 'j':
            cons_csv = input("CSV-Datei mit Verbrauch: ").strip()
            consumption_input = cons_csv
        else:
            annual_kwh = float(input("Jahresverbrauch in kWh (z.B. 5000): "))
            consumption_input = annual_kwh
            print("   → Skaliere Standardlastprofil auf Nutzer-Verbrauch")
        
        # Run simulation
        print("\n" + "="*60)
        print("🚀 Simulation startet...")
        print("="*60)
        
        results = simulator.simulate_from_csv(prod_csv, consumption_input)
        
        if results is not None:
            # Show sample
            print(f"\n📋 Beispiel (erste 10 Zeilen):")
            print(results.head(10).to_string(index=False))
            
            # Save results
            print()
            save = input("\nErgebnisse speichern? (j/n): ").strip().lower()
            if save == 'j':
                default_name = "storage_simulation_results.csv"
                print(f"Standard-Dateiname: {default_name}")
                filename = input("Dateiname (Enter für Standard): ").strip()
                
                if not filename:
                    filename = default_name
                elif not filename.endswith('.csv'):
                    filename += '.csv'
                
                simulator.save_results(results, filename)
            
            print("\n" + "="*60)
            print("🎉 SIMULATION ABGESCHLOSSEN!")
            print("="*60)
        
    except KeyboardInterrupt:
        print("\n\nProgramm abgebrochen.")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")


def quick_demo():
    """Quick demo with synthetic data."""
    print("\n🚀 Quick Demo - Storage Simulation")
    print("="*50)
    
    # Create simulator
    simulator = StorageSimulator(battery_capacity_kwh=10.0, battery_efficiency=0.95)
    
    # Create synthetic data for one week
    num_intervals = 672  # 7 days × 96 intervals
    
    # Synthetic production (sunny day pattern)
    production = []
    for i in range(num_intervals):
        hour = (i // 4) % 24
        # Solar production peaks at noon
        if 6 <= hour < 20:
            # Sine curve for solar production
            hour_in_day = hour - 6
            production_factor = np.sin(np.pi * hour_in_day / 14)
            production.append(max(0, production_factor * 2.0))  # Max 2 kWh per 15 min
        else:
            production.append(0)
    
    production = np.array(production)
    
    # Synthetic consumption (5000 kWh/year = ~0.143 kWh per 15 min avg)
    consumption = simulator.create_dummy_consumption(num_intervals, 5000)
    
    # Run simulation
    results = simulator.simulate(production, consumption)
    
    # Add datetime for clarity
    start_date = datetime(2024, 6, 1)
    dates = pd.date_range(start=start_date, periods=num_intervals, freq='15min')
    results.insert(0, 'Datum', dates.strftime('%d.%m.%Y'))
    results.insert(1, 'Uhrzeit', dates.strftime('%H:%M'))
    
    # Show sample
    print(f"\n📋 Beispiel-Ergebnisse (Mittag-Stunden):")
    # Show midday hours where interesting things happen
    midday_sample = results.iloc[48:60]  # Around noon
    print(midday_sample.to_string(index=False))
    
    print(f"\n✅ Demo erfolgreich!")


if __name__ == "__main__":
    import sys
    
    if "--demo" in sys.argv:
        quick_demo()
    else:
        main()


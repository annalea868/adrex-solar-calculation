#!/usr/bin/env python3
"""
Simple Storage Simulator - Step 1
Only tracks PV production and battery charging (no consumption yet).

Tracks:
1. PV energy production (kWh per 15 min)
2. Battery state of charge (kWh)
"""

import pandas as pd
import numpy as np
import os

class SimpleStorageSimulator:
    """Simple battery storage simulator - only production and charging."""
    
    # Battery systems loaded from Excel file
    BATTERY_SYSTEMS = None
    BATTERY_EXCEL_FILE = "2025-11_19_Nettokapazitäten Speicher.xlsx"
    
    @classmethod
    def load_battery_systems(cls):
        """Load battery systems from Excel file."""
        if cls.BATTERY_SYSTEMS is not None:
            return cls.BATTERY_SYSTEMS
        
        try:
            df = pd.read_excel(cls.BATTERY_EXCEL_FILE)
            
            # Create dictionary from Excel data
            # Column 0: "Speicherhersteller / Typ"
            # Column 1: "Netto Kapazität" (in kWh)
            cls.BATTERY_SYSTEMS = {}
            
            for idx, row in df.iterrows():
                name = row.iloc[0]  # First column: system name
                capacity = row.iloc[1]  # Second column: "Netto Kapazität"
                
                clean_name = name.strip()
                cls.BATTERY_SYSTEMS[clean_name] = float(capacity)
            
            return cls.BATTERY_SYSTEMS
            
        except Exception as e:
            print(f"⚠️  Konnte Excel-Datei nicht laden: {e}")
            return {}
    
    @classmethod
    def list_available_systems(cls):
        """List all available battery systems from Excel."""
        systems = cls.load_battery_systems()
        
        if not systems:
            print("❌ Keine Speichersysteme verfügbar")
            return
        
        print("\n🔋 Verfügbare Speichersysteme (aus Excel 'Netto Kapazität'):")
        print("="*70)
        
        # Group by manufacturer
        sungrow = {k: v for k, v in systems.items() if 'Sungrow' in k}
        sonnen = {k: v for k, v in systems.items() if 'sonnen' in k}
        solaredge = {k: v for k, v in systems.items() if 'SolarEdge' in k}
        
        if sungrow:
            print("\n📦 Sungrow SBR Serie:")
            for name, cap in sorted(sungrow.items(), key=lambda x: x[1]):
                print(f"   {name}: {cap} kWh")
        
        if sonnen:
            print("\n📦 sonnenBatterie:")
            for name, cap in sorted(sonnen.items(), key=lambda x: x[1]):
                print(f"   {name}: {cap} kWh")
        
        if solaredge:
            print("\n📦 SolarEdge:")
            for name, cap in sorted(solaredge.items(), key=lambda x: x[1]):
                print(f"   {name}: {cap} kWh")
        
        print(f"\n✅ Gesamt: {len(systems)} Systeme verfügbar")
    
    def __init__(self, battery_capacity_kwh=None, battery_efficiency=0.95, battery_name=None):
        """
        Initialize simple storage simulator.
        
        Parameters:
        - battery_capacity_kwh: Net battery capacity (required if no battery_name)
        - battery_efficiency: Round-trip efficiency (default: 95%)
        - battery_name: Battery system name from Excel file
        """
        # Load battery systems from Excel
        systems = self.load_battery_systems()
        
        if battery_name and battery_name in systems:
            # Use capacity from Excel "Netto Kapazität" column
            self.battery_capacity = systems[battery_name]
            self.battery_name = battery_name
            print(f"🔋 Simple Storage Simulator initialisiert")
            print(f"   System: {battery_name}")
            print(f"   Speicherkapazität: {self.battery_capacity} kWh (Netto aus Excel)")
        elif battery_capacity_kwh is not None:
            self.battery_capacity = battery_capacity_kwh
            self.battery_name = f"Custom {battery_capacity_kwh} kWh"
            print(f"🔋 Simple Storage Simulator initialisiert")
            print(f"   Speicherkapazität: {battery_capacity_kwh} kWh (Netto)")
        else:
            raise ValueError("Entweder battery_name oder battery_capacity_kwh muss angegeben werden!")
        
        self.battery_efficiency = battery_efficiency
        print(f"   Lade-Wirkungsgrad: {battery_efficiency:.0%}")
    
    def simulate_charging_only(self, production_kwh, initial_soc_kwh=0):
        """
        Simulate battery charging from PV production only.
        No consumption considered yet - just tracks how battery fills up.
        
        Parameters:
        - production_kwh: Array of PV production per 15-min interval (kWh)
        - initial_soc_kwh: Initial battery state of charge (default: 0)
        
        Returns:
        - DataFrame with production and battery state
        """
        print(f"\n🔄 Starte Lade-Simulation (nur Produktion)...")
        print(f"   Intervalle: {len(production_kwh)}")
        print(f"   Start-Ladezustand: {initial_soc_kwh:.2f} kWh")
        
        # Initialize tracking arrays
        num_intervals = len(production_kwh)
        battery_soc = np.zeros(num_intervals)  # State of charge
        battery_charge = np.zeros(num_intervals)  # Energy charged to battery
        excess_energy = np.zeros(num_intervals)  # Energy that couldn't be stored
        
        # Current battery state
        current_soc = initial_soc_kwh
        
        # Simulate each interval
        for i in range(num_intervals):
            prod = production_kwh[i]
            
            # Store SOC at start of interval
            battery_soc[i] = current_soc
            
            # Try to charge battery with all production
            if current_soc < self.battery_capacity:
                # How much space is available?
                charge_space = self.battery_capacity - current_soc
                charge_amount = min(prod, charge_space)
                
                # Apply charging efficiency
                actual_charge = charge_amount * self.battery_efficiency
                current_soc += actual_charge
                battery_charge[i] = actual_charge
                
                # Track excess that couldn't be stored
                excess_energy[i] = prod - charge_amount
            else:
                # Battery is full, all production is excess
                excess_energy[i] = prod
        
        # Create results DataFrame
        results = pd.DataFrame({
            'Produktion_kWh': production_kwh,
            'Speicher_Ladezustand_kWh': battery_soc,
            'Speicher_Ladung_kWh': battery_charge,
            'Ueberschuss_kWh': excess_energy
        })
        
        # Calculate summary statistics
        print(f"\n✅ Simulation abgeschlossen!")
        print(f"\n📊 Zusammenfassung:")
        print(f"   Gesamt-Produktion: {results['Produktion_kWh'].sum():.2f} kWh")
        print(f"   In Speicher geladen: {results['Speicher_Ladung_kWh'].sum():.2f} kWh")
        print(f"   Überschuss (nicht speicherbar): {results['Ueberschuss_kWh'].sum():.2f} kWh")
        print(f"   Speicher-Auslastung: {(results['Speicher_Ladung_kWh'].sum() / results['Produktion_kWh'].sum() * 100):.1f}%")
        
        # Battery usage
        total_charged = results['Speicher_Ladung_kWh'].sum()
        print(f"\n🔋 Speicher-Nutzung:")
        print(f"   Geladen: {total_charged:.2f} kWh")
        print(f"   Zyklen: {total_charged / self.battery_capacity:.1f}")
        print(f"   Max Ladezustand: {results['Speicher_Ladezustand_kWh'].max():.2f} kWh")
        print(f"   Speicher wurde voll: {'Ja' if results['Speicher_Ladezustand_kWh'].max() >= self.battery_capacity * 0.99 else 'Nein'}")
        
        return results
    
    def simulate_from_csv(self, production_csv):
        """
        Run charging simulation from CSV file.
        
        Parameters:
        - production_csv: CSV file from solar_irradiation_calculator
        """
        print(f"\n🔆 STORAGE CHARGING SIMULATION (Step 1)")
        print("="*60)
        
        # Load production data
        print(f"📊 Lade Produktionsdaten...")
        prod_df = pd.read_csv(production_csv)
        
        if 'PV_Energie_kWh' not in prod_df.columns:
            print("❌ CSV muss 'PV_Energie_kWh' Spalte enthalten")
            return None
        
        production = prod_df['PV_Energie_kWh'].values
        print(f"   ✅ {len(production)} Intervalle geladen")
        print(f"   Gesamt-Produktion: {production.sum():.2f} kWh")
        
        # Run simulation
        results = self.simulate_charging_only(production)
        
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
    """Interactive simple storage simulator."""
    print("\n🔋" + "=" * 58 + "🔋")
    print()
    print("=== Simple Storage Simulator (Step 1) ===")
    print("Simuliert nur Speicher-Ladung durch PV-Produktion")
    print("(Verbrauch kommt in Step 2)")
    print()
    
    try:
        # Battery configuration
        print("🔋 SPEICHER-KONFIGURATION:")
        print()
        
        # Show available systems
        show_systems = input("Verfügbare Speichersysteme anzeigen? (j/n): ").strip().lower()
        if show_systems == 'j':
            SimpleStorageSimulator.list_available_systems()
            print()
        
        # Ask for system selection
        use_predefined = input("Vordefiniertes System aus Excel verwenden? (j/n): ").strip().lower()
        
        if use_predefined == 'j':
            print("\nBitte genauen Systemnamen aus der Liste eingeben")
            print("(z.B. 'Sungrow SBR096 / 9,6 kWh')")
            system_name = input("\nSystemname: ").strip()
            efficiency = float(input("Lade-Wirkungsgrad (z.B. 0.95 für 95%): ") or "0.95")
            
            simulator = SimpleStorageSimulator(
                battery_name=system_name,
                battery_efficiency=efficiency
            )
        else:
            print("\nBitte Speicherkapazität manuell eingeben:")
            capacity = float(input("Speicherkapazität in kWh: "))
            efficiency = float(input("Lade-Wirkungsgrad (z.B. 0.95 für 95%): ") or "0.95")
            
            simulator = SimpleStorageSimulator(
                battery_capacity_kwh=capacity,
                battery_efficiency=efficiency
            )
        
        # Production data
        print("\n☀️ PRODUKTIONSDATEN:")
        prod_csv = input("CSV-Datei mit PV-Produktion: ").strip()
        
        if not os.path.exists(prod_csv):
            print(f"❌ Datei nicht gefunden: {prod_csv}")
            return
        
        # Run simulation
        print("\n" + "="*60)
        print("🚀 Simulation startet...")
        print("="*60)
        
        results = simulator.simulate_from_csv(prod_csv)
        
        if results is not None:
            # Show sample
            print(f"\n📋 Beispiel (erste 20 Zeilen):")
            print(results.head(20).to_string(index=False))
            
            # Save results
            print()
            save = input("\nErgebnisse speichern? (j/n): ").strip().lower()
            if save == 'j':
                default_name = "storage_charging_results.csv"
                print(f"\nStandard-Dateiname: {default_name}")
                filename = input("Dateiname (Enter für Standard): ").strip()
                
                if not filename:
                    filename = default_name
                elif not filename.endswith('.csv'):
                    filename += '.csv'
                
                simulator.save_results(results, filename)
            
            print("\n" + "="*60)
            print("🎉 STEP 1 ABGESCHLOSSEN!")
            print("="*60)
            print("✅ Produktion und Speicher-Ladung simuliert")
            print("➡️  Nächster Step: Verbrauch hinzufügen")
        
    except KeyboardInterrupt:
        print("\n\nProgramm abgebrochen.")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")


def quick_demo():
    """Quick demo with synthetic data."""
    print("\n🚀 Quick Demo - Simple Storage (nur Ladung)")
    print("="*50)
    
    # Create simulator with 10 kWh battery
    simulator = SimpleStorageSimulator(battery_capacity_kwh=10.0, battery_efficiency=0.95)
    
    # Create synthetic production for one day
    num_intervals = 96  # 1 day × 96 intervals
    
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
    
    # Run simulation
    results = simulator.simulate_charging_only(production)
    
    # Add datetime for clarity
    from datetime import datetime
    start_date = datetime(2024, 6, 15)
    dates = pd.date_range(start=start_date, periods=num_intervals, freq='15min')
    results.insert(0, 'Datum', dates.strftime('%d.%m.%Y'))
    results.insert(1, 'Uhrzeit', dates.strftime('%H:%M'))
    
    # Show interesting hours (morning to afternoon)
    print(f"\n📋 Beispiel (06:00 - 14:00):")
    morning_sample = results.iloc[24:56]  # 6am to 2pm
    print(morning_sample.to_string(index=False))
    
    print(f"\n✅ Demo erfolgreich!")
    print(f"   Speicher erreichte: {results['Speicher_Ladezustand_kWh'].max():.2f} kWh")


if __name__ == "__main__":
    import sys
    
    if "--demo" in sys.argv:
        quick_demo()
    else:
        main()



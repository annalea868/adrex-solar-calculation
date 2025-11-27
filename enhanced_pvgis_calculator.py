#!/usr/bin/env python3
"""
Enhanced PVGIS Solar Calculator
Like main.py but with all frontend parameters included.
Uses PVGIS API for any location worldwide - no grid data limitations.

Enhanced Formula: E = (N_eff * P_mod * (G / 1000) * eta_sys * T_effect) * (dt / 3600)
"""

import pandas as pd
from datetime import datetime, timedelta
from pvlib.iotools import get_pvgis_hourly
import numpy as np

class EnhancedPVGISCalculator:
    """Enhanced solar calculator using PVGIS API with all frontend parameters."""
    
    def __init__(self):
        self.data = None
        self.meta = None
        
        # Initialize databases with frontend parameters
        self.pv_modules = self.get_pv_modules_database()
        self.inverters = self.get_inverters_database()
        
        print(f"✅ Enhanced PVGIS Calculator ready")
        print(f"   Available PV module types: {len(self.pv_modules)}")
        print(f"   Works for ANY location worldwide!")
    
    def get_pv_modules_database(self):
        """Database of PV modules from frontend."""
        return {
            "winaico_gg_black_450": {
                "name": "Winaico GG Black 450 Wp",  # From frontend screenshots
                "power_wp": 450,
                "efficiency": 0.205,
                "temp_coefficient": -0.0038
            },
            "winaico_gg_black_400": {
                "name": "Winaico GG Black 400 Wp",
                "power_wp": 400,
                "efficiency": 0.195,
                "temp_coefficient": -0.0038
            },
            "generic_400": {
                "name": "Generic 400 Wp Module",
                "power_wp": 400,
                "efficiency": 0.20,
                "temp_coefficient": -0.004
            }
        }
    
    def get_inverters_database(self):
        """Database of inverters from frontend."""
        return {
            "quality_inverter": {
                "name": "Qualitäts-Wechselrichter",  # From frontend screenshots
                "efficiency": 0.96
            },
            "standard_inverter": {
                "name": "Standard-Wechselrichter",
                "efficiency": 0.94
            },
            "premium_inverter": {
                "name": "Premium-Wechselrichter",
                "efficiency": 0.98
            }
        }
    
    def get_radiation_data(self, latitude, longitude, tilt, azimuth, year=2023):
        """
        Fetch radiation data from PVGIS API - works for any location.
        Same as main.py but enhanced for frontend parameters.
        """
        try:
            print(f"🌐 Fetching PVGIS data for coordinates: {latitude}°N, {longitude}°E")
            print(f"   Tilt: {tilt}°, Azimuth: {azimuth}°, Year: {year}")
            
            # Get hourly data from PVGIS (same as main.py)
            data, meta = get_pvgis_hourly(
                latitude=latitude,
                longitude=longitude,
                surface_tilt=tilt,
                surface_azimuth=azimuth,
                start=year,
                end=year,
                components=True
            )
            
            self.data = data
            self.meta = meta
            
            print(f"✅ Successfully fetched {len(data)} hourly data points")
            print(f"   Data source: {meta.get('inputs', {}).get('radiation_database', 'PVGIS-SARAH')}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error fetching PVGIS data: {e}")
            return None
    
    def get_radiation_at_time(self, target_datetime):
        """
        Get radiation value for a specific date and time.
        Same logic as main.py but enhanced error handling.
        """
        if self.data is None:
            print("❌ No radiation data available. Please fetch data first.")
            return None
        
        try:
            # Make target_datetime timezone-aware if needed (same as main.py)
            if target_datetime.tzinfo is None:
                import pytz
                target_datetime = pytz.UTC.localize(target_datetime)
            
            # Find the closest time match
            closest_time = None
            min_diff = float('inf')
            
            for idx in self.data.index:
                if idx.tzinfo is None:
                    import pytz
                    idx_aware = pytz.UTC.localize(idx)
                else:
                    idx_aware = idx
                
                time_diff = abs((target_datetime - idx_aware).total_seconds())
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest_time = idx
            
            if closest_time is not None:
                # Calculate total irradiance from POA components (same as main.py)
                direct = self.data.loc[closest_time, 'poa_direct']
                sky_diffuse = self.data.loc[closest_time, 'poa_sky_diffuse'] 
                ground_diffuse = self.data.loc[closest_time, 'poa_ground_diffuse']
                
                # Total global irradiance on the tilted surface
                radiation = direct + sky_diffuse + ground_diffuse
                
                print(f"☀️  Radiation at {target_datetime}: {radiation:.1f} W/m²")
                print(f"   Direct: {direct:.1f}, Sky diffuse: {sky_diffuse:.1f}, Ground diffuse: {ground_diffuse:.1f}")
                print(f"   Closest data point: {closest_time}")
                return radiation
            else:
                print(f"❌ No data found for time {target_datetime}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting radiation: {e}")
            return None
    
    def calculate_enhanced_energy(self, N, P_mod, G, eta_sys, dt, 
                                 # Enhanced parameters from frontend
                                 pv_module_type="generic_400",
                                 dimensionsfaktor_pv=2.0,
                                 inverter_type="standard_inverter", 
                                 shading_losses=0.0,
                                 system_age_years=0,
                                 ambient_temp_c=25.0):
        """
        Enhanced energy calculation with all frontend parameters.
        
        🔆 ENHANCED FORMULA:
        E = (N_eff * P_mod * (G / 1000) * eta_sys * T_effect) * (dt / 3600)
        
        Where:
        - N_eff = N * (dimensionsfaktor_pv / 2.0)  [from frontend]
        - eta_sys = η_inverter * (1-L_shading) * (1-L_age) * (1-L_other)
        - T_effect = 1 + γ * (T_cell - 25°C)
        """
        
        if G is None or G < 0:
            return 0
        
        print(f"\n🔆 ENHANCED ENERGY CALCULATION")
        print(f"=" * 50)
        
        # Get module specifications
        if pv_module_type in self.pv_modules:
            module_spec = self.pv_modules[pv_module_type]
            print(f"📱 Module: {module_spec['name']}")
        else:
            module_spec = {"temp_coefficient": -0.004, "name": "Unknown"}
            print(f"📱 Module: Unknown (using defaults)")
        
        # Calculate effective module count with dimensionsfaktor
        N_effective = int(N * dimensionsfaktor_pv / 2.0)
        print(f"🏠 Modules: {N} → {N_effective} (Dimensionsfaktor: {dimensionsfaktor_pv})")
        
        # Get inverter efficiency
        if inverter_type in self.inverters:
            inverter_spec = self.inverters[inverter_type]
            inverter_efficiency = inverter_spec['efficiency']
            print(f"⚡ Inverter: {inverter_spec['name']} ({inverter_efficiency*100:.0f}%)")
        else:
            inverter_efficiency = 0.94
            print(f"⚡ Inverter: Unknown (using 94% default)")
        
        # Calculate enhanced system efficiency
        base_losses = 0.05  # 5% other losses (wiring, soiling, mismatch)
        age_losses = system_age_years * 0.005  # 0.5% per year degradation
        
        enhanced_efficiency = (
            inverter_efficiency *      # Inverter efficiency
            (1 - shading_losses) *     # Shading losses
            (1 - base_losses) *        # Other system losses  
            (1 - age_losses)           # Age degradation
        )
        
        print(f"📊 System Efficiency Calculation:")
        print(f"   Inverter: {inverter_efficiency*100:.1f}%")
        print(f"   Shading losses: -{shading_losses*100:.1f}%")
        print(f"   Other losses: -{base_losses*100:.1f}%")
        print(f"   Age losses: -{age_losses*100:.1f}% ({system_age_years} years)")
        print(f"   → Total efficiency: {enhanced_efficiency*100:.1f}%")
        
        # Calculate temperature effect
        cell_temp = ambient_temp_c + (G / 1000) * 25  # Simplified NOCT model
        temp_effect = 1 + module_spec['temp_coefficient'] * (cell_temp - 25)
        
        print(f"🌡️  Temperature Effect:")
        print(f"   Ambient: {ambient_temp_c:.1f}°C")
        print(f"   Cell temp: {cell_temp:.1f}°C")
        print(f"   Temp coefficient: {module_spec['temp_coefficient']*100:.2f}%/°C")
        print(f"   → Temperature effect: {temp_effect*100:.1f}%")
        
        # Enhanced energy calculation
        print(f"\n💡 ENHANCED ENERGY FORMULA:")
        print(f"   E = N_eff × P_mod × (G/1000) × η_sys × T_effect × (dt/3600)")
        print(f"   E = {N_effective} × {P_mod:.2f} × ({G:.0f}/1000) × {enhanced_efficiency:.3f} × {temp_effect:.3f} × ({dt}/3600)")
        
        E = (N_effective * P_mod * (G / 1000) * enhanced_efficiency * temp_effect) * (dt / 3600)
        
        print(f"   E = {E:.4f} kWh")
        
        return E
    
    def calculate_energy_for_datetime(self, latitude, longitude, tilt, azimuth, 
                                    target_datetime, N, P_mod, dt,
                                    # Enhanced frontend parameters
                                    pv_module_type="generic_400",
                                    dimensionsfaktor_pv=2.0,
                                    inverter_type="standard_inverter",
                                    shading_losses=0.0,
                                    system_age_years=0,
                                    year=None):
        """
        Complete enhanced calculation with all frontend parameters.
        Like main.py but with frontend enhancements.
        """
        if year is None:
            year = target_datetime.year
        
        # Fetch radiation data (same as main.py)
        if (self.data is None or 
            self.meta is None or 
            self.meta.get('inputs', {}).get('lat') != latitude or
            self.meta.get('inputs', {}).get('lon') != longitude):
            
            data = self.get_radiation_data(latitude, longitude, tilt, azimuth, year)
            if data is None:
                return None
        
        # Get radiation for specific time (same as main.py)
        G = self.get_radiation_at_time(target_datetime)
        if G is None:
            return None
        
        # Enhanced energy calculation with frontend parameters
        E = self.calculate_enhanced_energy(
            N, P_mod, G, 0.8, dt,  # eta_sys will be recalculated inside
            pv_module_type=pv_module_type,
            dimensionsfaktor_pv=dimensionsfaktor_pv,
            inverter_type=inverter_type,
            shading_losses=shading_losses,
            system_age_years=system_age_years,
            ambient_temp_c=25.0  # Summer estimate
        )
        
        results = {
            'datetime': target_datetime,
            'latitude': latitude,
            'longitude': longitude,
            'tilt': tilt,
            'azimuth': azimuth,
            'radiation_W_per_m2': G,
            'num_modules': N,
            'power_per_module_kWp': P_mod,
            'energy_kWh': E,
            'energy_Wh': E * 1000,
            'data_source': 'Enhanced PVGIS API (Any Location)'
        }
        
        return results

def main():
    """Enhanced interactive calculator like main.py with frontend parameters."""
    
    print("🔆" + "=" * 58 + "🔆")
    print("    ENHANCED SOLAR ENERGY CALCULATOR")
    print("    PVGIS API + All Frontend Parameters")
    print("    Works for ANY location worldwide!")
    print("🔆" + "=" * 58 + "🔆")
    
    try:
        calculator = EnhancedPVGISCalculator()
        
        # Show available options
        print(f"\n🔧 VERFÜGBARE PV-MODULE:")
        for key, module in calculator.pv_modules.items():
            print(f"   {key}: {module['name']} ({module['power_wp']} Wp)")
        
        print(f"\n⚡ VERFÜGBARE WECHSELRICHTER:")
        for key, inverter in calculator.inverters.items():
            print(f"   {key}: {inverter['name']} ({inverter['efficiency']*100:.0f}%)")
        
        print(f"\n" + "=" * 60)
        print("📝 PARAMETER EINGABE:")
        print("=" * 60)
        
        # Location input (works for any location!)
        print(f"\n🌍 STANDORT (beliebiger Ort weltweit):")
        print(f"   Beispiele: Berlin (52.5, 13.4), München (48.1, 11.6), Hamburg (53.6, 10.0)")
        latitude = float(input("Breitengrad (z.B. 52.5 für Berlin): "))
        longitude = float(input("Längengrad (z.B. 13.4 für Berlin): "))
        
        # System configuration
        print(f"\n📐 ANLAGEN-KONFIGURATION:")
        print(f"   Neigung: 30° optimal, 35° Steildach, 15° Flachdach")
        print(f"   Azimuth: 0° Süd, 90° West, 270° Ost, 180° Nord")
        tilt = float(input("Neigung in Grad (z.B. 30 für optimal): "))
        azimuth = float(input("Ausrichtung in Grad (z.B. 0 für Süd): "))
        
        # Date/Time input
        print(f"\n📅 DATUM UND UHRZEIT:")
        print(f"   Beispiele: Sommer=2023-06-15, Winter=2023-12-15, Frühling=2023-03-21")
        date_str = input("Datum (YYYY-MM-DD, z.B. 2023-06-15): ")
        time_str = input("Uhrzeit (HH:MM, z.B. 12:00): ")
        target_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        # Basic system parameters
        print(f"\n🏠 SYSTEM-PARAMETER:")
        print(f"   Beispiele: 20 Module = ~8kWp, 30 Module = ~12kWp, 40 Module = ~16kWp")
        N = int(input("Anzahl der Module (z.B. 30): "))
        print(f"   Beispiele: 0.4 für 400Wp, 0.45 für 450Wp, 0.5 für 500Wp")
        P_mod = float(input("Nennleistung pro Modul in kWp (z.B. 0.45): "))
        print(f"   Beispiele: 900=15Min, 3600=1Std, 86400=1Tag")
        dt = int(input("Zeitraum in Sekunden (z.B. 3600 für 1 Stunde): "))
        
        # Enhanced frontend parameters
        print(f"\n⚙️  ERWEITERTE PARAMETER (vom Frontend):")
        print(f"   Module Typen: winaico_gg_black_450, winaico_gg_black_400, generic_400")
        pv_module_type = input("PV Modul Typ (z.B. winaico_gg_black_450): ") or "generic_400"
        
        print(f"   Dimensionsfaktor: 1.5=klein, 2.0=standard, 2.5=groß")
        dimensionsfaktor_input = input("Dimensionsfaktor PV (z.B. 2.0): ") or "2.0"
        dimensionsfaktor_pv = float(dimensionsfaktor_input)
        
        print(f"   Wechselrichter: quality_inverter, standard_inverter, premium_inverter")
        inverter_type = input("Wechselrichter Typ (z.B. quality_inverter): ") or "standard_inverter"
        
        print(f"   Verschattung: 0=keine, 5=5%, 10=10%, 20=starke Verschattung")
        shading_input = input("Verschattung in % (z.B. 0): ") or "0"
        shading_losses = float(shading_input) / 100.0
        
        print(f"   Anlagenalter: 0=neu, 5=5Jahre, 10=10Jahre")
        age_input = input("Anlagenalter in Jahren (z.B. 0): ") or "0"
        system_age_years = int(age_input)
        
        # Calculation
        print(f"\n" + "=" * 60)
        print("⚡ ENHANCED CALCULATION STARTING...")
        print("=" * 60)
        
        results = calculator.calculate_energy_for_datetime(
            latitude=latitude,
            longitude=longitude,
            tilt=tilt,
            azimuth=azimuth,
            target_datetime=target_datetime,
            N=N,
            P_mod=P_mod,
            dt=dt,
            # Enhanced parameters
            pv_module_type=pv_module_type,
            dimensionsfaktor_pv=dimensionsfaktor_pv,
            inverter_type=inverter_type,
            shading_losses=shading_losses,
            system_age_years=system_age_years
        )
        
        if results:
            print(f"\n🎉 ERGEBNISSE")
            print("=" * 60)
            print(f"📍 Standort: {results['latitude']:.2f}°N, {results['longitude']:.2f}°E")
            print(f"📐 Ausrichtung: {results['azimuth']:.1f}° (0°=Süd), Neigung: {results['tilt']:.1f}°")
            print(f"📅 Datum/Zeit: {results['datetime']}")
            print(f"☀️  Sonneneinstrahlung G: {results['radiation_W_per_m2']:.1f} W/m²")
            print(f"🏠 Module: {results['num_modules']} Stück")
            print(f"⚡ Leistung pro Modul: {results['power_per_module_kWp']:.2f} kWp")
            print(f"🗄️  Datenquelle: {results['data_source']}")
            print()
            print(f">>> ERZEUGTE ENERGIE: {results['energy_kWh']:.4f} kWh <<<")
            print(f">>> ERZEUGTE ENERGIE: {results['energy_Wh']:.1f} Wh <<<")
            print("=" * 60)
            
        else:
            print("\n❌ Berechnung fehlgeschlagen!")
            print("💡 Mögliche Ursachen:")
            print("   - PVGIS API nicht erreichbar")
            print("   - Ungültige Koordinaten")
            print("   - Ungültiges Datum/Zeit")
            
    except KeyboardInterrupt:
        print("\n\nProgramm beendet.")
    except ValueError as e:
        print(f"\n❌ Eingabefehler: {e}")
        print("💡 Bitte überprüfen Sie das Eingabeformat.")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Enhanced Interactive Solar Calculator
Simple calculator like main.py but with all frontend parameters included.
User inputs parameters → Gets solar irradiation and energy production E.
"""

import os
import pickle
import math
from datetime import datetime
import pandas as pd

class EnhancedInteractiveSolarCalculator:
    """Interactive solar calculator with all frontend parameters."""
    
    def __init__(self, data_dir="solar_grid_500mb"):
        self.data_dir = data_dir
        self.grid_resolution = 0.75
        
        # Check if grid data exists
        if not os.path.exists(data_dir):
            print(f"❌ Grid directory '{data_dir}' not found!")
            print("   Run 'python3 grid_downloader_500mb.py' first.")
            raise FileNotFoundError(f"Grid directory {data_dir} not found")
        
        # Load available configurations
        self.available_configs = self.load_available_configurations()
        
        # Initialize databases with frontend parameters
        self.pv_modules = self.get_pv_modules_database()
        self.inverters = self.get_inverters_database()
        
        print(f"✅ Enhanced Interactive Solar Calculator ready")
        print(f"   Available PV module types: {len(self.pv_modules)}")
        print(f"   Available configurations: {len(self.available_configs)}")
    
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
    
    def load_available_configurations(self):
        """Load available tilt/azimuth configurations."""
        configs = set()
        try:
            files = [f for f in os.listdir(self.data_dir) if f.startswith('grid_') and f.endswith('.pkl')]
            for file in files:
                parts = file.replace('grid_', '').replace('.pkl', '').split('_')
                if len(parts) >= 4:
                    try:
                        tilt = int(parts[2])
                        azimuth = int(parts[3])
                        configs.add((tilt, azimuth))
                    except:
                        pass
            return sorted(list(configs))
        except Exception as e:
            print(f"Error loading configurations: {e}")
            return []
    
    def find_nearest_configuration(self, target_tilt, target_azimuth):
        """Find nearest available configuration."""
        if not self.available_configs:
            return None
        
        # Check for exact match
        if (target_tilt, target_azimuth) in self.available_configs:
            return (target_tilt, target_azimuth)
        
        # Find nearest by distance
        min_distance = float('inf')
        nearest_config = None
        
        for tilt, azimuth in self.available_configs:
            azimuth_diff = min(
                abs(target_azimuth - azimuth),
                abs(target_azimuth - azimuth + 360),
                abs(target_azimuth - azimuth - 360)
            )
            distance = math.sqrt((target_tilt - tilt)**2 + azimuth_diff**2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_config = (tilt, azimuth)
        
        return nearest_config
    
    def load_grid_data(self, lat, lon, tilt, azimuth):
        """Load radiation data from grid file."""
        filename = f"grid_{lat}_{lon}_{tilt}_{azimuth}_2023.pkl"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            return data
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None
    
    def get_radiation_for_datetime(self, latitude, longitude, tilt, azimuth, target_datetime):
        """Get solar radiation for specific location and time."""
        
        # Find nearest configuration
        config = self.find_nearest_configuration(tilt, azimuth)
        if not config:
            print("❌ No suitable configuration found")
            return None
        
        actual_tilt, actual_azimuth = config
        print(f"🎯 Using configuration: {actual_tilt}°/{actual_azimuth}°")
        
        # Find grid points for interpolation
        lat_grid = round(latitude / self.grid_resolution) * self.grid_resolution
        lon_grid = round(longitude / self.grid_resolution) * self.grid_resolution
        
        # Load grid data
        data = self.load_grid_data(lat_grid, lon_grid, actual_tilt, actual_azimuth)
        if data is None:
            print(f"❌ No grid data for {lat_grid}, {lon_grid}")
            return None
        
        try:
            # Find closest time match
            target_ts = pd.Timestamp(target_datetime)
            if hasattr(data, 'index'):
                time_diff = abs(data.index - target_ts)
                closest_idx = time_diff.idxmin()
                
                # Calculate total radiation
                direct = data.loc[closest_idx, 'poa_direct']
                sky_diffuse = data.loc[closest_idx, 'poa_sky_diffuse']
                ground_diffuse = data.loc[closest_idx, 'poa_ground_diffuse']
                
                total_radiation = direct + sky_diffuse + ground_diffuse
                
                print(f"☀️  Solar radiation found: {total_radiation:.1f} W/m²")
                print(f"   Direct: {direct:.1f} W/m²")
                print(f"   Sky diffuse: {sky_diffuse:.1f} W/m²")
                print(f"   Ground diffuse: {ground_diffuse:.1f} W/m²")
                
                return total_radiation
            
        except Exception as e:
            print(f"Error extracting radiation: {e}")
            return None
        
        return None
    
    def calculate_enhanced_energy_production(self, 
                                           latitude, longitude, tilt, azimuth, target_datetime,
                                           pv_module_type, module_count, dimensionsfaktor_pv,
                                           inverter_type, shading_losses, system_age_years,
                                           time_period_hours):
        """
        Calculate energy production with all frontend parameters.
        
        🔆 ENHANCED ENERGY PRODUCTION FORMULA:
        E = P_system × (G/1000) × η_system × T_effect × t
        
        Where:
        - P_system = (N_effective × P_module) / 1000  [kW]
        - N_effective = module_count × (dimensionsfaktor_pv / 2.0)
        - G = Solar irradiance [W/m²]
        - η_system = η_inverter × (1-L_shading) × (1-L_age) × (1-L_other)
        - T_effect = 1 + γ × (T_cell - 25°C)
        - t = time_period_hours
        """
        
        print(f"\n🔆 ENERGY PRODUCTION CALCULATION")
        print(f"=" * 50)
        
        # Get module specifications
        if pv_module_type not in self.pv_modules:
            print(f"❌ Unknown module type: {pv_module_type}")
            return None
        
        module_spec = self.pv_modules[pv_module_type]
        
        # Get inverter specifications
        if inverter_type not in self.inverters:
            print(f"❌ Unknown inverter type: {inverter_type}")
            return None
        
        inverter_spec = self.inverters[inverter_type]
        
        # Calculate effective module count with dimensionsfaktor
        effective_module_count = int(module_count * dimensionsfaktor_pv / 2.0)
        
        # Calculate system power
        total_power_kw = (effective_module_count * module_spec['power_wp']) / 1000
        
        print(f"📊 SYSTEM CONFIGURATION:")
        print(f"   Module type: {module_spec['name']}")
        print(f"   Module count: {module_count} → {effective_module_count} (with factor {dimensionsfaktor_pv})")
        print(f"   Module power: {module_spec['power_wp']} Wp")
        print(f"   Total system power: {total_power_kw:.1f} kWp")
        print(f"   Inverter: {inverter_spec['name']} ({inverter_spec['efficiency']*100:.0f}%)")
        
        # Get solar irradiance
        print(f"\n☀️  SOLAR IRRADIANCE LOOKUP:")
        G = self.get_radiation_for_datetime(latitude, longitude, tilt, azimuth, target_datetime)
        
        if G is None:
            print("❌ Could not determine solar irradiance")
            return None
        
        # Calculate system efficiency
        print(f"\n⚙️  SYSTEM EFFICIENCY CALCULATION:")
        base_losses = 0.05  # 5% other losses (wiring, soiling, mismatch)
        age_losses = system_age_years * 0.005  # 0.5% per year degradation
        
        system_efficiency = (
            inverter_spec['efficiency'] *     # Inverter efficiency
            (1 - shading_losses) *            # Shading losses
            (1 - base_losses) *               # Other system losses
            (1 - age_losses)                  # Age degradation
        )
        
        print(f"   Inverter efficiency: {inverter_spec['efficiency']*100:.1f}%")
        print(f"   Shading losses: {shading_losses*100:.1f}%")
        print(f"   Other losses: {base_losses*100:.1f}%")
        print(f"   Age degradation: {age_losses*100:.1f}% ({system_age_years} years)")
        print(f"   → Total system efficiency: {system_efficiency*100:.1f}%")
        
        # Calculate temperature effect
        print(f"\n🌡️  TEMPERATURE EFFECT CALCULATION:")
        ambient_temp = 25.0  # Estimate for summer
        cell_temp = ambient_temp + (G / 1000) * 25  # Simplified NOCT model
        temp_effect = 1 + module_spec['temp_coefficient'] * (cell_temp - 25)
        
        print(f"   Ambient temperature: {ambient_temp:.1f}°C (estimated)")
        print(f"   Cell temperature: {cell_temp:.1f}°C")
        print(f"   Temperature coefficient: {module_spec['temp_coefficient']*100:.2f}%/°C")
        print(f"   → Temperature effect: {temp_effect*100:.1f}%")
        
        # Calculate energy production
        print(f"\n💡 ENERGY PRODUCTION FORMULA:")
        print(f"   E = P_system × (G/1000) × η_system × T_effect × t")
        print(f"   E = {total_power_kw:.1f} × ({G:.0f}/1000) × {system_efficiency:.3f} × {temp_effect:.3f} × {time_period_hours}")
        
        energy_kwh = (
            total_power_kw *           # System power [kW]
            (G / 1000) *              # Irradiance factor
            system_efficiency *       # System efficiency
            temp_effect *             # Temperature effect
            time_period_hours         # Time period [h]
        )
        
        print(f"   E = {energy_kwh:.3f} kWh")
        
        # Results
        results = {
            'datetime': target_datetime,
            'latitude': latitude,
            'longitude': longitude,
            'tilt': tilt,
            'azimuth': azimuth,
            'solar_irradiance_w_m2': G,
            'pv_module_type': pv_module_type,
            'module_count': module_count,
            'effective_module_count': effective_module_count,
            'dimensionsfaktor_pv': dimensionsfaktor_pv,
            'total_power_kw': total_power_kw,
            'inverter_type': inverter_type,
            'system_efficiency': system_efficiency,
            'temperature_effect': temp_effect,
            'shading_losses': shading_losses,
            'system_age_years': system_age_years,
            'time_period_hours': time_period_hours,
            'energy_kwh': energy_kwh,
            'energy_wh': energy_kwh * 1000
        }
        
        return results

def main():
    """Interactive calculator with frontend parameters."""
    
    print("🔆" + "=" * 58 + "🔆")
    print("    ENHANCED SOLAR ENERGY CALCULATOR")
    print("    With All Frontend Parameters")
    print("🔆" + "=" * 58 + "🔆")
    
    try:
        calculator = EnhancedInteractiveSolarCalculator()
        
        # Show available data
        print(f"\n📍 VERFÜGBARE GRID-DATEN:")
        for tilt, azimuth in calculator.available_configs:
            direction = "Süd" if azimuth == 0 else "Ost" if azimuth == 270 else "West" if azimuth == 90 else f"{azimuth}°"
            print(f"   {tilt}° Neigung, {azimuth}° Azimuth ({direction})")
        
        print(f"\n🔧 VERFÜGBARE PV-MODULE:")
        for key, module in calculator.pv_modules.items():
            print(f"   {key}: {module['name']} ({module['power_wp']} Wp)")
        
        print(f"\n⚡ VERFÜGBARE WECHSELRICHTER:")
        for key, inverter in calculator.inverters.items():
            print(f"   {key}: {inverter['name']} ({inverter['efficiency']*100:.0f}%)")
        
        print(f"\n" + "=" * 60)
        print("📝 PARAMETER EINGABE - Bitte alle Werte eingeben:")
        print("=" * 60)
        
        # Location input with examples
        print(f"\n🌍 STANDORT:")
        print(f"   Verfügbare Beispiele: München (48.1, 11.6)")
        latitude = float(input("Breitengrad (z.B. 48.1 für München): "))
        longitude = float(input("Längengrad (z.B. 11.6 für München): "))
        
        # Date/Time input
        print(f"\n📅 DATUM UND UHRZEIT:")
        print(f"   Beispiele: Sommer=2023-06-15, Winter=2023-12-15")
        date_str = input("Datum (YYYY-MM-DD, z.B. 2023-06-15): ")
        time_str = input("Uhrzeit (HH:MM, z.B. 12:00): ")
        target_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        # System configuration
        print(f"\n🏠 PV-ANLAGE KONFIGURATION:")
        print(f"   Verfügbare Konfigurationen: 25°/270° (Ost)")
        tilt = int(input("Neigung in Grad (z.B. 25 für verfügbare Daten): "))
        azimuth = int(input("Ausrichtung in Grad (z.B. 270 für Ost): "))
        
        # PV Module selection
        print(f"\n🔧 PV-MODULE:")
        print(f"   Optionen: winaico_gg_black_450, winaico_gg_black_400, generic_400")
        pv_module_type = input("PV Modul Typ (z.B. winaico_gg_black_450): ")
        module_count = int(input("Anzahl Module (z.B. 40 für 18kWp System): "))
        
        # Frontend parameters
        print(f"\n⚙️  ERWEITERTE PARAMETER (vom Frontend):")
        dimensionsfaktor_pv = float(input("Dimensionsfaktor PV (z.B. 2.0 Standard): "))
        
        print(f"   Wechselrichter Optionen: quality_inverter, standard_inverter, premium_inverter")
        inverter_type = input("Wechselrichter Typ (z.B. quality_inverter): ")
        
        shading_input = input("Verschattung in % (z.B. 0 für keine, 5 für 5%): ")
        shading_losses = float(shading_input) / 100.0  # Convert to decimal
        
        system_age_years = int(input("Anlagenalter in Jahren (z.B. 0 für neu, 5 für 5 Jahre): "))
        
        # Time period
        print(f"\n⏱️  ZEITRAUM:")
        print(f"   Beispiele: 1 Stunde, 0.25 für 15 Minuten, 24 für 1 Tag")
        time_period_hours = float(input("Zeitraum in Stunden (z.B. 1.0 für 1 Stunde): "))
        
        # Calculation
        print(f"\n" + "=" * 60)
        print("⚡ BERECHNUNG LÄUFT...")
        print("=" * 60)
        
        results = calculator.calculate_enhanced_energy_production(
            latitude=latitude,
            longitude=longitude,
            tilt=tilt,
            azimuth=azimuth,
            target_datetime=target_datetime,
            pv_module_type=pv_module_type,
            module_count=module_count,
            dimensionsfaktor_pv=dimensionsfaktor_pv,
            inverter_type=inverter_type,
            shading_losses=shading_losses,
            system_age_years=system_age_years,
            time_period_hours=time_period_hours
        )
        
        if results:
            print(f"\n🎉 ERGEBNISSE")
            print("=" * 60)
            print(f"📍 Standort: {results['latitude']:.2f}°N, {results['longitude']:.2f}°E")
            print(f"📐 Konfiguration: {results['tilt']}° Neigung, {results['azimuth']}° Azimuth")
            print(f"📅 Datum/Zeit: {results['datetime']}")
            print(f"☀️  Sonneneinstrahlung: {results['solar_irradiance_w_m2']:.1f} W/m²")
            print(f"🏠 PV-System: {results['module_count']} Module → {results['effective_module_count']} effektiv")
            print(f"⚡ Systemleistung: {results['total_power_kw']:.1f} kWp")
            print(f"📊 Systemwirkungsgrad: {results['system_efficiency']*100:.1f}%")
            print(f"🌡️  Temperatureffekt: {results['temperature_effect']*100:.1f}%")
            print(f"⏱️  Zeitraum: {results['time_period_hours']} Stunden")
            print()
            print(f">>> ERZEUGTE ENERGIE: {results['energy_kwh']:.4f} kWh <<<")
            print(f">>> ERZEUGTE ENERGIE: {results['energy_wh']:.1f} Wh <<<")
            print("=" * 60)
            
        else:
            print("\n❌ Berechnung fehlgeschlagen!")
            print("💡 Mögliche Ursachen:")
            print("   - Standort außerhalb verfügbarer Grid-Daten")
            print("   - Ungültige Konfiguration")
            print("   - Ungültiges Datum/Zeit")
            
    except KeyboardInterrupt:
        print("\n\nProgramm beendet.")
    except ValueError as e:
        print(f"\n❌ Eingabefehler: {e}")
        print("💡 Bitte überprüfen Sie das Eingabeformat.")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    main()

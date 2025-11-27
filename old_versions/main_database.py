#!/usr/bin/env python3
"""
Solar Energy Calculator using Supabase Database
Fast and reliable solar energy calculations for any location in Germany.
"""

from datetime import datetime
from supabase_manager import SupabaseSolarManager

class DatabaseSolarCalculator:
    """Solar energy calculator using Supabase database."""
    
    # System efficiency constant
    SYSTEM_EFFICIENCY = 0.8  # 80%
    
    def __init__(self):
        try:
            self.db_manager = SupabaseSolarManager()
            print("✅ Connected to solar radiation database")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("💡 Make sure you have set up your .env file with Supabase credentials")
            raise
    
    def calculate_energy_for_datetime(self, latitude, longitude, tilt, azimuth, 
                                    target_datetime, N, P_mod, dt):
        """
        Calculate energy generation using database radiation data.
        
        Parameters:
        - latitude: Breitengrad
        - longitude: Längengrad  
        - tilt: Neigung (degrees)
        - azimuth: Ausrichtung (degrees, 0=South, 90=West, 270=East)
        - target_datetime: datetime object
        - N: Anzahl der Module
        - P_mod: Nennleistung pro Modul in kWp
        - dt: Zeitraum in Sekunden
        
        Returns:
        - dict with results or None if no data found
        """
        try:
            print(f"🔍 Looking up radiation data...")
            print(f"   Location: {latitude}°N, {longitude}°E")
            print(f"   Configuration: {tilt}° tilt, {azimuth}° azimuth")
            print(f"   DateTime: {target_datetime}")
            
            # Get radiation data from database
            radiation_data = self.db_manager.get_radiation_for_datetime(
                latitude, longitude, tilt, azimuth, target_datetime
            )
            
            if not radiation_data:
                print(f"❌ No radiation data found for this location/time")
                print(f"💡 Try a major German city or run database population first")
                return None
            
            G = radiation_data['total_radiation']
            print(f"☀️  Found radiation: {G:.1f} W/m²")
            print(f"   Direct: {radiation_data['poa_direct']:.1f} W/m²")
            print(f"   Sky diffuse: {radiation_data['poa_sky_diffuse']:.1f} W/m²") 
            print(f"   Ground diffuse: {radiation_data['poa_ground_diffuse']:.1f} W/m²")
            
            # Calculate energy using the formula
            E = self.calculate_energy(N, P_mod, G, dt)
            
            results = {
                'datetime': target_datetime,
                'latitude': latitude,
                'longitude': longitude,
                'tilt': tilt,
                'azimuth': azimuth,
                'radiation_W_per_m2': G,
                'radiation_components': {
                    'direct': radiation_data['poa_direct'],
                    'sky_diffuse': radiation_data['poa_sky_diffuse'],
                    'ground_diffuse': radiation_data['poa_ground_diffuse']
                },
                'num_modules': N,
                'power_per_module_kWp': P_mod,
                'system_efficiency': self.SYSTEM_EFFICIENCY,
                'time_period_seconds': dt,
                'energy_kWh': E,
                'energy_Wh': E * 1000,
                'data_source': 'Supabase Database (PVGIS)',
                'temperature': radiation_data.get('temperature')
            }
            
            return results
            
        except Exception as e:
            print(f"❌ Error calculating energy: {e}")
            return None
    
    def calculate_energy(self, N, P_mod, G, dt):
        """
        Calculate energy using the standard formula.
        E = (N * P_mod * (G / 1000) * eta_sys) * (dt / 3600)
        """
        if G is None or G < 0:
            return 0
        
        E = (N * P_mod * (G / 1000) * self.SYSTEM_EFFICIENCY) * (dt / 3600)
        return E
    
    def find_nearest_location(self, latitude, longitude):
        """Find the nearest location with data in the database."""
        # This would implement spatial queries to find nearest data points
        # For now, we round to nearest 0.1 degree
        return round(latitude, 1), round(longitude, 1)


def main():
    """Interactive solar calculator using database."""
    print("\n")
    print("🔆" + "=" * 46 + "🔆")
    print()
    print("=== Solar Energy Calculator (Database) ===")
    print("Using Supabase database for instant calculations")
    print()
    
    try:
        calculator = DatabaseSolarCalculator()
        
        # Get user input
        print("Please enter the following parameters:")
        
        latitude = float(input("Breitengrad (z.B. 52.5): "))
        longitude = float(input("Längengrad (z.B. 13.4): "))
        tilt = int(input("Neigung in Grad (z.B. 30): "))
        azimuth = int(input("Ausrichtung in Grad (0°=Süd, 90°=West, 270°=Ost): "))
        
        # Date and time input
        date_str = input("Datum (YYYY-MM-DD, z.B. 2023-06-15): ")
        time_str = input("Uhrzeit (HH:MM, z.B. 12:00): ")
        
        # Parse datetime
        datetime_str = f"{date_str} {time_str}"
        target_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        
        # System parameters
        N = int(input("Anzahl der Module (z.B. 30): "))
        P_mod = float(input("Nennleistung pro Modul in kWp (z.B. 0.41 für 410Wp): "))
        dt = int(input("Zeitraum in Sekunden (z.B. 900 für 15 Min): "))
        
        print("\n" + "="*50)
        print("⚡ Berechnung läuft...")
        
        # Calculate energy
        results = calculator.calculate_energy_for_datetime(
            latitude, longitude, tilt, azimuth, target_datetime,
            N, P_mod, dt
        )
        
        if results:
            print("\n" + "="*50)
            print("🎉 ERGEBNISSE")
            print("="*50)
            print(f"📍 Standort: {results['latitude']:.2f}°N, {results['longitude']:.2f}°E")
            print(f"🧭 Ausrichtung: {results['azimuth']}° (0°=Süd)")
            print(f"📐 Neigung: {results['tilt']}°")
            print(f"📅 Datum/Zeit: {results['datetime']}")
            print(f"☀️  Globalstrahlung: {results['radiation_W_per_m2']:.1f} W/m²")
            print(f"🏠 Anzahl Module: {results['num_modules']}")
            print(f"⚡ Leistung pro Modul: {results['power_per_module_kWp']:.2f} kWp")
            print(f"📊 Systemwirkungsgrad: {results['system_efficiency']:.1%} (fest)")
            print(f"⏱️  Zeitraum: {results['time_period_seconds']} Sekunden")
            print(f"🗄️  Datenquelle: {results['data_source']}")
            
            if results.get('temperature'):
                print(f"🌡️  Temperatur: {results['temperature']:.1f}°C")
            
            print("\n" + "🎯 ENERGIEERZEUGUNG:")
            print(f">>> {results['energy_kWh']:.4f} kWh <<<")
            print(f">>> {results['energy_Wh']:.1f} Wh <<<")
            
            # Show radiation breakdown
            components = results['radiation_components']
            print(f"\n📊 Strahlungskomponenten:")
            print(f"   Direkte Strahlung: {components['direct']:.1f} W/m²")
            print(f"   Himmelsdiffuse: {components['sky_diffuse']:.1f} W/m²")
            print(f"   Bodenreflexion: {components['ground_diffuse']:.1f} W/m²")
            
        else:
            print("\n❌ Fehler bei der Berechnung!")
            print("💡 Mögliche Ursachen:")
            print("   - Keine Daten für diesen Standort in der Datenbank")
            print("   - Verbindungsproblem zur Datenbank")
            print("   - Ungültige Koordinaten")
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except ValueError as e:
        print(f"\n❌ Eingabefehler: {e}")
        print("💡 Bitte überprüfen Sie Ihre Eingaben")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        print("💡 Stellen Sie sicher, dass:")
        print("   - .env Datei existiert mit SUPABASE_URL und SUPABASE_KEY")
        print("   - Internetverbindung besteht")
        print("   - Datenbank wurde initialisiert")


if __name__ == "__main__":
    main()

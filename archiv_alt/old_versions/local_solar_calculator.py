#!/usr/bin/env python3
"""
Local Solar Calculator - Grid-based with Interpolation
Uses pre-downloaded local grid files for instant solar calculations.
Includes intelligent nearest-configuration matching.
"""

import os
import pickle
import math
from datetime import datetime
import pandas as pd

class LocalSolarCalculator:
    """Solar calculator using local grid files with interpolation and nearest-config matching."""
    
    SYSTEM_EFFICIENCY = 0.8  # 80% system efficiency (fixed)
    
    def __init__(self, data_dir="solar_grid"):
        self.data_dir = data_dir
        self.grid_resolution = 0.5  # 0.5° grid spacing
        
        if not os.path.exists(data_dir):
            print(f"❌ Grid directory '{data_dir}' not found!")
            print("   Run 'python3 grid_downloader.py' first to download the grid.")
            raise FileNotFoundError(f"Grid directory {data_dir} not found")
        
        # Load available configurations
        self.available_configs = self.load_available_configurations()
        
        print(f"✅ Local solar calculator ready")
        print(f"   Grid directory: {data_dir}")
        print(f"   Available configurations: {len(self.available_configs)}")
        print(f"   Grid resolution: {self.grid_resolution}° (~{self.grid_resolution*111:.0f}km)")
    
    def load_available_configurations(self):
        """Load all available tilt/azimuth configurations from grid files."""
        configs = set()
        
        try:
            files = [f for f in os.listdir(self.data_dir) if f.startswith('grid_') and f.endswith('.pkl')]
            
            for file in files:
                # Parse filename: grid_lat_lon_tilt_azimuth_year.pkl
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
        """
        Find the nearest available configuration for given tilt/azimuth.
        Uses Euclidean distance in configuration space.
        """
        if not self.available_configs:
            print("❌ No configurations available in grid")
            return None
        
        # Check for exact match first
        if (target_tilt, target_azimuth) in self.available_configs:
            print(f"✅ Exact configuration match: {target_tilt}°/{target_azimuth}°")
            return (target_tilt, target_azimuth)
        
        # Find nearest configuration
        min_distance = float('inf')
        nearest_config = None
        
        for tilt, azimuth in self.available_configs:
            # Calculate distance in configuration space
            # Weight azimuth differences less since solar impact is smaller
            tilt_diff = abs(target_tilt - tilt)
            
            # Handle azimuth wraparound (0° and 360° are the same)
            azimuth_diff = min(
                abs(target_azimuth - azimuth),
                abs(target_azimuth - azimuth + 360),
                abs(target_azimuth - azimuth - 360)
            )
            
            # Weight tilt more heavily as it has bigger impact on solar generation
            distance = math.sqrt((tilt_diff * 2)**2 + azimuth_diff**2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_config = (tilt, azimuth)
        
        if nearest_config:
            tilt_diff = abs(target_tilt - nearest_config[0])
            azimuth_diff = min(
                abs(target_azimuth - nearest_config[1]),
                abs(target_azimuth - nearest_config[1] + 360),
                abs(target_azimuth - nearest_config[1] - 360)
            )
            
            print(f"📍 Nearest configuration: {nearest_config[0]}°/{nearest_config[1]}°")
            print(f"   Difference: {tilt_diff}° tilt, {azimuth_diff}° azimuth")
            
            if tilt_diff > 10 or azimuth_diff > 45:
                print(f"⚠️  Large configuration difference - results may be less accurate")
        
        return nearest_config
    
    def get_grid_filename(self, lat, lon, tilt, azimuth, year=2023):
        """Generate filename for grid data."""
        return f"grid_{lat:.1f}_{lon:.1f}_{tilt}_{azimuth}_{year}.pkl"
    
    def load_grid_data(self, lat, lon, tilt, azimuth, year=2023):
        """Load data from grid file."""
        filename = self.get_grid_filename(lat, lon, tilt, azimuth, year)
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            return data
        except Exception as e:
            print(f"Error loading grid file {filename}: {e}")
            return None
    
    def find_grid_points(self, latitude, longitude):
        """Find the 4 surrounding grid points for interpolation."""
        # Round to grid boundaries
        lat_lower = math.floor(latitude / self.grid_resolution) * self.grid_resolution
        lat_upper = lat_lower + self.grid_resolution
        lon_lower = math.floor(longitude / self.grid_resolution) * self.grid_resolution
        lon_upper = lon_lower + self.grid_resolution
        
        # Ensure we're within Germany bounds
        lat_lower = max(47.5, lat_lower)
        lat_upper = min(55.0, lat_upper)
        lon_lower = max(6.0, lon_lower)
        lon_upper = min(15.0, lon_upper)
        
        grid_points = [
            (lat_lower, lon_lower),
            (lat_lower, lon_upper),
            (lat_upper, lon_lower),
            (lat_upper, lon_upper)
        ]
        
        return grid_points
    
    def interpolate_radiation(self, latitude, longitude, tilt, azimuth, target_datetime):
        """
        Get radiation value using bilinear interpolation from 4 nearest grid points.
        """
        # Find nearest available configuration
        config = self.find_nearest_configuration(tilt, azimuth)
        if not config:
            return None
        
        actual_tilt, actual_azimuth = config
        
        # Get surrounding grid points
        grid_points = self.find_grid_points(latitude, longitude)
        
        # Load data from grid points
        grid_data = []
        for grid_lat, grid_lon in grid_points:
            data = self.load_grid_data(grid_lat, grid_lon, actual_tilt, actual_azimuth)
            if data is not None:
                radiation = self.extract_radiation_from_data(data, target_datetime)
                grid_data.append({
                    'lat': grid_lat,
                    'lon': grid_lon,
                    'radiation': radiation
                })
        
        if len(grid_data) == 0:
            print("❌ No grid data available for this location")
            return None
        
        # If we have less than 4 points, use nearest neighbor
        if len(grid_data) < 4:
            print(f"⚠️  Using nearest neighbor (only {len(grid_data)} grid points available)")
            # Find closest point
            min_distance = float('inf')
            closest_radiation = None
            
            for point in grid_data:
                distance = math.sqrt((latitude - point['lat'])**2 + (longitude - point['lon'])**2)
                if distance < min_distance and point['radiation'] is not None:
                    min_distance = distance
                    closest_radiation = point['radiation']
            
            return closest_radiation
        
        # Bilinear interpolation
        try:
            # Sort points for interpolation
            # We need: bottom-left, bottom-right, top-left, top-right
            grid_data.sort(key=lambda p: (p['lat'], p['lon']))
            
            if len(grid_data) == 4:
                # Full bilinear interpolation
                x1, y1 = grid_data[0]['lon'], grid_data[0]['lat']  # bottom-left
                x2, y2 = grid_data[3]['lon'], grid_data[3]['lat']  # top-right
                
                # Get radiation values
                r11 = grid_data[0]['radiation']  # bottom-left
                r12 = grid_data[2]['radiation']  # top-left
                r21 = grid_data[1]['radiation']  # bottom-right
                r22 = grid_data[3]['radiation']  # top-right
                
                # Check for None values
                if any(r is None for r in [r11, r12, r21, r22]):
                    # Fall back to average of available values
                    valid_values = [r for r in [r11, r12, r21, r22] if r is not None]
                    if valid_values:
                        return sum(valid_values) / len(valid_values)
                    return None
                
                # Bilinear interpolation formula
                x, y = longitude, latitude
                
                radiation = (
                    r11 * (x2 - x) * (y2 - y) +
                    r21 * (x - x1) * (y2 - y) +
                    r12 * (x2 - x) * (y - y1) +
                    r22 * (x - x1) * (y - y1)
                ) / ((x2 - x1) * (y2 - y1))
                
                print(f"🔍 Interpolated radiation: {radiation:.1f} W/m²")
                return radiation
            
        except Exception as e:
            print(f"Error in interpolation: {e}")
        
        # Fall back to simple average
        valid_radiations = [p['radiation'] for p in grid_data if p['radiation'] is not None]
        if valid_radiations:
            avg_radiation = sum(valid_radiations) / len(valid_radiations)
            print(f"🔍 Average radiation: {avg_radiation:.1f} W/m²")
            return avg_radiation
        
        return None
    
    def extract_radiation_from_data(self, data, target_datetime):
        """Extract radiation value for specific datetime from PVGIS data."""
        try:
            # Make target_datetime timezone-aware if needed
            if target_datetime.tzinfo is None:
                import pytz
                target_datetime = pytz.UTC.localize(target_datetime)
            
            # Find closest time match
            closest_time = None
            min_diff = float('inf')
            
            for idx in data.index:
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
                # Calculate total radiation from components
                direct = data.loc[closest_time, 'poa_direct']
                sky_diffuse = data.loc[closest_time, 'poa_sky_diffuse']
                ground_diffuse = data.loc[closest_time, 'poa_ground_diffuse']
                
                total_radiation = direct + sky_diffuse + ground_diffuse
                return total_radiation
            
            return None
            
        except Exception as e:
            print(f"Error extracting radiation: {e}")
            return None
    
    def calculate_energy_for_datetime(self, latitude, longitude, tilt, azimuth, 
                                    target_datetime, N, P_mod, dt):
        """
        Calculate energy generation for specific location and time.
        """
        print(f"🔋 Calculating energy for {latitude:.3f}°N, {longitude:.3f}°E")
        print(f"   Configuration: {tilt}° tilt, {azimuth}° azimuth")
        print(f"   Date/Time: {target_datetime}")
        
        # Get radiation using interpolation and nearest config matching
        G = self.interpolate_radiation(latitude, longitude, tilt, azimuth, target_datetime)
        
        if G is None:
            print("❌ Could not determine radiation for this location/configuration")
            return None
        
        # Calculate energy using the standard formula
        E = (N * P_mod * (G / 1000) * self.SYSTEM_EFFICIENCY) * (dt / 3600)
        
        results = {
            'datetime': target_datetime,
            'latitude': latitude,
            'longitude': longitude,
            'tilt': tilt,
            'azimuth': azimuth,
            'radiation_W_per_m2': G,
            'num_modules': N,
            'power_per_module_kWp': P_mod,
            'system_efficiency': self.SYSTEM_EFFICIENCY,
            'time_period_seconds': dt,
            'energy_kWh': E,
            'energy_Wh': E * 1000,
            'data_source': 'Local Grid (Interpolated)'
        }
        
        return results

def main():
    """Interactive solar calculator using local grid."""
    print("\n🔆" + "=" * 46 + "🔆")
    print()
    print("=== Local Solar Calculator ===")
    print("Instant calculations using pre-downloaded grid")
    print()
    
    try:
        calculator = LocalSolarCalculator()
        
        # Show available configurations
        print(f"\n📊 Available configurations in grid:")
        for i, (tilt, azimuth) in enumerate(calculator.available_configs):
            if i < 10:  # Show first 10
                print(f"   {tilt}° tilt, {azimuth}° azimuth")
            elif i == 10:
                print(f"   ... and {len(calculator.available_configs) - 10} more")
                break
        
        print("\nPlease enter the following parameters:")
        
        # Get user input
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
        print("⚡ Calculating from local grid...")
        
        # Calculate energy
        results = calculator.calculate_energy_for_datetime(
            latitude, longitude, tilt, azimuth, target_datetime,
            N, P_mod, dt
        )
        
        if results:
            print("\n" + "="*50)
            print("🎉 RESULTS")
            print("="*50)
            print(f"📍 Location: {results['latitude']:.3f}°N, {results['longitude']:.3f}°E")
            print(f"🧭 Orientation: {results['azimuth']}° (0°=South)")
            print(f"📐 Tilt: {results['tilt']}°")
            print(f"📅 Date/Time: {results['datetime']}")
            print(f"☀️  Global radiation: {results['radiation_W_per_m2']:.1f} W/m²")
            print(f"🏠 Modules: {results['num_modules']}")
            print(f"⚡ Power per module: {results['power_per_module_kWp']:.2f} kWp")
            print(f"📊 System efficiency: {results['system_efficiency']:.1%} (fixed)")
            print(f"⏱️  Time period: {results['time_period_seconds']} seconds")
            print(f"🗄️  Data source: {results['data_source']}")
            
            print(f"\n🎯 ENERGY GENERATION:")
            print(f">>> {results['energy_kWh']:.4f} kWh <<<")
            print(f">>> {results['energy_Wh']:.1f} Wh <<<")
            
        else:
            print("\n❌ Calculation failed!")
            print("💡 Possible causes:")
            print("   - Location outside Germany")
            print("   - Grid data not downloaded for this area")
            print("   - Invalid date/time")
            
    except FileNotFoundError:
        print("❌ Grid data not found!")
        print("💡 Please run 'python3 grid_downloader.py' first to download the solar grid.")
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except ValueError as e:
        print(f"\n❌ Input error: {e}")
        print("💡 Please check your input values")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

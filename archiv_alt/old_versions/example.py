#!/usr/bin/env python3
"""
Example usage of the Solar Energy Calculator
This file demonstrates how to use the calculator programmatically
"""

from main import SolarEnergyCalculator
from datetime import datetime

def example_usage():
    """Demonstrate various usage scenarios."""
    
    print("=== Solar Energy Calculator Examples ===\n")
    
    # Create calculator instance
    calc = SolarEnergyCalculator()
    
    # Example 1: Typical house installation in Berlin
    print("🏠 Example 1: House installation in Berlin")
    print("- Location: Berlin (52.5°N, 13.4°E)")
    print("- 25 modules x 400 Wp each = 10 kWp total")
    print("- 30° tilt, South-facing (0°)")
    print("- 80% system efficiency (fixed)")
    print("- Energy calculation for 1 hour on June 15, 2023 at noon")
    
    result1 = calc.calculate_energy_for_datetime(
        latitude=52.5,
        longitude=13.4,
        tilt=30,
        azimuth=0,  # South
        target_datetime=datetime(2023, 6, 15, 12, 0),
        N=25,
        P_mod=0.4,  # 400 Wp = 0.4 kWp
        dt=3600  # 1 hour
    )
    
    if result1:
        print(f"✅ Energy generated: {result1['energy_kWh']:.3f} kWh")
        print(f"   Solar radiation: {result1['radiation_W_per_m2']:.1f} W/m²")
        print(f"   Expected daily energy (summer): ~{result1['energy_kWh'] * 10:.1f} kWh")
    print()
    
    # Example 2: East-West installation
    print("🌅 Example 2: East-West installation in Munich")
    print("- Location: Munich (48.1°N, 11.6°E)")
    print("- Split installation: 15 modules East + 15 modules West")
    print("- 25° tilt")
    print("- 80% system efficiency")
    print("- Comparing morning (8 AM) vs evening (6 PM)")
    
    # East-facing modules at 8 AM
    result2_east = calc.calculate_energy_for_datetime(
        latitude=48.1,
        longitude=11.6,
        tilt=25,
        azimuth=270,  # East
        target_datetime=datetime(2023, 7, 1, 8, 0),
        N=15,
        P_mod=0.35,  # 350 Wp modules
        dt=900  # 15 minutes
    )
    
    # West-facing modules at 6 PM
    result2_west = calc.calculate_energy_for_datetime(
        latitude=48.1,
        longitude=11.6,
        tilt=25,
        azimuth=90,  # West
        target_datetime=datetime(2023, 7, 1, 18, 0),
        N=15,
        P_mod=0.35,
        dt=900  # 15 minutes
    )
    
    if result2_east and result2_west:
        print(f"✅ East modules (8 AM): {result2_east['energy_Wh']:.0f} Wh in 15 min")
        print(f"   Radiation: {result2_east['radiation_W_per_m2']:.1f} W/m²")
        print(f"✅ West modules (6 PM): {result2_west['energy_Wh']:.0f} Wh in 15 min")
        print(f"   Radiation: {result2_west['radiation_W_per_m2']:.1f} W/m²")
        print(f"   Total: {result2_east['energy_Wh'] + result2_west['energy_Wh']:.0f} Wh")
    print()
    
    # Example 3: Winter vs Summer comparison
    print("❄️☀️ Example 3: Seasonal comparison in Hamburg")
    print("- Location: Hamburg (53.6°N, 10.0°E)")
    print("- 20 modules x 450 Wp")
    print("- 35° tilt, South-facing")
    print("- 80% system efficiency (fixed)")
    print("- Comparing winter (Dec 21) vs summer (Jun 21) at noon")
    
    # Winter solstice
    result3_winter = calc.calculate_energy_for_datetime(
        latitude=53.6,
        longitude=10.0,
        tilt=35,
        azimuth=0,
        target_datetime=datetime(2023, 12, 21, 12, 0),
        N=20,
        P_mod=0.45,
        dt=3600  # 1 hour
    )
    
    # Summer solstice
    result3_summer = calc.calculate_energy_for_datetime(
        latitude=53.6,
        longitude=10.0,
        tilt=35,
        azimuth=0,
        target_datetime=datetime(2023, 6, 21, 12, 0),
        N=20,
        P_mod=0.45,
        dt=3600  # 1 hour
    )
    
    if result3_winter and result3_summer:
        print(f"❄️ Winter (Dec 21): {result3_winter['energy_kWh']:.3f} kWh/h")
        print(f"   Radiation: {result3_winter['radiation_W_per_m2']:.1f} W/m²")
        print(f"☀️ Summer (Jun 21): {result3_summer['energy_kWh']:.3f} kWh/h")
        print(f"   Radiation: {result3_summer['radiation_W_per_m2']:.1f} W/m²")
        ratio = result3_summer['energy_kWh'] / result3_winter['energy_kWh'] if result3_winter['energy_kWh'] > 0 else float('inf')
        print(f"   Summer/Winter ratio: {ratio:.1f}x")
    print()
    
    print("=== Formula Used ===")
    print("E = (N * P_mod * (G / 1000) * eta_sys) * (dt / 3600)")
    print("Where:")
    print("- E: Energy in kWh")
    print("- N: Number of modules")
    print("- P_mod: Power per module in kWp")
    print("- G: Global radiation in W/m² (from PVGIS)")
    print("- eta_sys: System efficiency (fixed at 0.8 = 80%)")
    print("- dt: Time period in seconds")
    print()
    print("Data source: PVGIS (EU Photovoltaic Geographical Information System)")
    print("Radiation components: Direct + Sky Diffuse + Ground Diffuse")

def quick_calculation():
    """Quick calculation for user input.""" 
    print("\n=== Quick Calculation ===")
    print("Enter your system parameters:")
    
    try:
        lat = float(input("Latitude (Breitengrad): "))
        lon = float(input("Longitude (Längengrad): "))
        tilt = float(input("Tilt (Neigung) in degrees: "))
        azimuth = float(input("Azimuth (0°=South, 90°=West, 270°=East): "))
        n_modules = int(input("Number of modules: "))
        p_mod = float(input("Power per module (kWp): "))
        # System efficiency is now fixed at 80%
        
        # Use current summer noon as default
        target_time = datetime(2023, 6, 15, 12, 0)
        print(f"Calculating for {target_time} (summer noon)...")
        
        calc = SolarEnergyCalculator()
        result = calc.calculate_energy_for_datetime(
            lat, lon, tilt, azimuth, target_time,
            n_modules, p_mod, 3600
        )
        
        if result:
            print(f"\n🔆 Results:")
            print(f"Energy per hour: {result['energy_kWh']:.3f} kWh")
            print(f"Solar radiation: {result['radiation_W_per_m2']:.1f} W/m²")
            print(f"System size: {n_modules * p_mod:.1f} kWp")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    example_usage()
    
    # Uncomment the line below for quick interactive calculation
    # quick_calculation()

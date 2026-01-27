#!/usr/bin/env python3
"""
Demo: Enhanced Energy Production Calculators
Shows both 500MB Grid and Direct API calculators with all frontend parameters.
"""

import sys
import os
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from solar_calculator_500mb import OptimizedSolarCalculator
from solar_calculator_pvgis_direct import PVGISDirectSolarCalculator

def demo_enhanced_calculators():
    """Demo both enhanced energy production calculators."""
    
    print("🔆" + "="*80 + "🔆")
    print("    ENHANCED ENERGY PRODUCTION CALCULATORS DEMO")
    print("    All Frontend Parameters Included")
    print("🔆" + "="*80 + "🔆")
    
    # Common parameters (from frontend screenshots)
    location = {
        'latitude': 52.5,
        'longitude': 13.4,
        'name': 'Berlin'
    }
    
    datetime_target = datetime(2023, 6, 15, 12, 0)  # Summer noon
    
    # PV System Configuration (from frontend)
    pv_system = {
        'pv_module_type': 'winaico_gg_black_450',
        'module_count': 40,
        'tilt': 30.0,
        'azimuth': 0.0,  # South-facing
        'dimensionsfaktor_pv': 2.0
    }
    
    # System Parameters (from frontend)
    system_params = {
        'inverter_type': 'quality_inverter',
        'installation_type': 'standard',
        'shading_losses': 0.05,  # 5% shading
        'system_age_years': 2,
        'ambient_temp_c': 25.0,
        'time_period_hours': 1.0
    }
    
    print(f"\n📍 Test Location: {location['name']} ({location['latitude']:.1f}°N, {location['longitude']:.1f}°E)")
    print(f"📅 Date/Time: {datetime_target}")
    print(f"🏠 PV System: {pv_system['module_count']}x {pv_system['pv_module_type']}")
    print(f"📐 Configuration: {pv_system['tilt']}°/{pv_system['azimuth']}° (South)")
    print(f"⚙️  Advanced: {system_params['inverter_type']}, {system_params['shading_losses']*100:.0f}% shading, {system_params['system_age_years']} years old")
    
    # Test 1: 500MB Grid Calculator
    print("\n" + "="*80)
    print("🗄️  TEST 1: 500MB GRID CALCULATOR (Enhanced)")
    print("="*80)
    
    try:
        grid_calculator = OptimizedSolarCalculator()
        
        grid_result = grid_calculator.calculate_enhanced_energy_production(
            latitude=location['latitude'],
            longitude=location['longitude'],
            target_datetime=datetime_target,
            **pv_system,
            **system_params
        )
        
        if grid_result:
            print(f"\n✅ 500MB Grid Results:")
            print(f"   📊 Energy Production: {grid_result['energy_kwh']:.3f} kWh")
            print(f"   ☀️  Solar Irradiance: {grid_result['irradiance_w_m2']:.0f} W/m²")
            print(f"   🌡️  Temperature Effect: {grid_result['temperature_effect']*100:.1f}%")
            print(f"   ⚙️  System Efficiency: {grid_result['system_efficiency']*100:.1f}%")
            print(f"   🎯 Specific Yield: {grid_result['specific_yield_kwh_kwp']:.3f} kWh/kWp")
            print(f"   📈 Improvement over simple: {grid_result['improvement_percent']:+.1f}%")
            print(f"   🔧 Data Source: {grid_result['data_source']}")
        else:
            print("❌ 500MB Grid calculation failed")
            
    except Exception as e:
        print(f"❌ 500MB Grid calculator error: {e}")
    
    # Test 2: PVGIS Direct Calculator
    print("\n" + "="*80)
    print("🌐 TEST 2: PVGIS DIRECT CALCULATOR (Real-time)")
    print("="*80)
    
    try:
        pvgis_calculator = PVGISDirectSolarCalculator()
        
        print("⏳ Fetching real-time PVGIS data via pvlib... (may take 30-60 seconds)")
        
        api_result = pvgis_calculator.calculate_enhanced_energy_production(
            latitude=location['latitude'],
            longitude=location['longitude'],
            target_datetime=datetime_target,
            **pv_system,
            **system_params,
            use_pvgis_calculation=True  # Use PVGIS internal calculation
        )
        
        if api_result:
            print(f"\n✅ Direct API Results (Real-time):")
            print(f"   📊 Energy Production: {api_result['energy_kwh']:.3f} kWh")
            print(f"   ☀️  Solar Irradiance: {api_result['irradiance_w_m2']:.0f} W/m²")
            print(f"   🌡️  Real Temperature: {api_result['ambient_temp_c']:.1f}°C")
            print(f"   🌡️  Temperature Effect: {api_result['temperature_effect']*100:.1f}%")
            print(f"   ⚙️  System Efficiency: {api_result['system_efficiency']*100:.1f}%")
            print(f"   🎯 Specific Yield: {api_result['specific_yield_kwh_kwp']:.3f} kWh/kWp")
            print(f"   📈 Improvement over simple: {api_result['improvement_percent']:+.1f}%")
            print(f"   🌐 PVGIS Database: {api_result['pvgis_database']}")
            print(f"   ⏰ Data Timestamp: {api_result['pvgis_record_time']}")
            print(f"   🔧 PVGIS Power Output: {api_result['pvgis_power_w']:.0f} W")
            print(f"   🎯 PVGIS System Losses: {api_result['pvgis_system_losses_pct']:.1f}%")
        else:
            print("❌ Direct API calculation failed")
            
    except Exception as e:
        print(f"❌ Direct API calculator error: {e}")
    
    # Comparison
    print("\n" + "="*80)
    print("🔄 COMPARISON & ANALYSIS")
    print("="*80)
    
    if 'grid_result' in locals() and 'api_result' in locals() and grid_result and api_result:
        print(f"\n📊 Energy Production Comparison:")
        print(f"   500MB Grid:  {grid_result['energy_kwh']:.3f} kWh")
        print(f"   Direct API:  {api_result['energy_kwh']:.3f} kWh")
        
        difference = api_result['energy_kwh'] - grid_result['energy_kwh']
        difference_pct = (difference / grid_result['energy_kwh'] * 100) if grid_result['energy_kwh'] > 0 else 0
        
        print(f"   Difference:  {difference:+.3f} kWh ({difference_pct:+.1f}%)")
        
        print(f"\n🌡️ Environmental Data Comparison:")
        print(f"   Grid Temperature:     {grid_result.get('ambient_temp_c', 'N/A')}°C (estimated)")
        print(f"   API Temperature:      {api_result['ambient_temp_c']:.1f}°C (real-time)")
        
        print(f"   Grid Irradiance:      {grid_result['irradiance_w_m2']:.0f} W/m² (interpolated)")
        print(f"   PVGIS Irradiance:     {api_result['irradiance_w_m2']:.0f} W/m² (real-time)")
        
        print(f"\n⚙️ System Performance Comparison:")
        print(f"   Grid Efficiency:      {grid_result['system_efficiency']*100:.1f}%")
        print(f"   API Efficiency:       {api_result['system_efficiency']*100:.1f}%")
        
        print(f"\n🎯 Accuracy Analysis:")
        if abs(difference_pct) < 5:
            print(f"   ✅ Results very similar ({abs(difference_pct):.1f}% difference)")
            print(f"   💡 500MB grid provides excellent approximation with instant results")
        elif abs(difference_pct) < 15:
            print(f"   ⚠️  Moderate difference ({abs(difference_pct):.1f}%)")
            print(f"   💡 Consider using API for critical calculations")
        else:
            print(f"   ❌ Significant difference ({abs(difference_pct):.1f}%)")
            print(f"   💡 Weather conditions may be unusual - API recommended")
            
    else:
        print("❌ Could not compare results - one or both calculations failed")
    
    # Frontend Parameter Benefits
    print(f"\n💡 Enhanced Formula Benefits (vs Simple 0.8 Efficiency):")
    print(f"   ✅ Dynamic system efficiency based on components")
    print(f"   ✅ Real temperature effects on module performance") 
    print(f"   ✅ Module-specific characteristics (efficiency, temp coefficient)")
    print(f"   ✅ Installation type losses (DC/AC wiring)")
    print(f"   ✅ Shading losses from user input")
    print(f"   ✅ System aging/degradation effects")
    print(f"   ✅ Inverter type efficiency")
    print(f"   ✅ Dimensionsfaktor PV (sizing factor)")
    
    print(f"\n🎯 Use Case Recommendations:")
    print(f"   🗄️  500MB Grid: Fast batch calculations, offline apps, TypeScript integration")
    print(f"   🌐 PVGIS Direct: Real-time accuracy, critical calculations, official PVGIS data")
    
    print(f"\n🔆 Both calculators now include ALL frontend parameters! 🔆")

def main():
    """Run the enhanced calculators demo."""
    try:
        demo_enhanced_calculators()
        
        print(f"\n" + "="*80)
        print(f"✅ Demo completed successfully!")
        print(f"💡 Use these enhanced calculators for your simulation project.")
        print(f"="*80)
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Demo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

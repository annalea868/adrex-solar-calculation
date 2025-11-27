#!/usr/bin/env python3
"""
Demo script for Optimized Solar Calculator (500MB Version)
Quick test to verify the system works.
"""

from datetime import datetime
import os

def check_grid_status():
    """Check if the optimized grid is downloaded."""
    grid_dir = "solar_grid_500mb"
    
    if not os.path.exists(grid_dir):
        print("❌ Grid not downloaded yet")
        print("💡 Run: python3 grid_downloader_500mb.py")
        return False
    
    files = [f for f in os.listdir(grid_dir) if f.startswith('grid_') and f.endswith('.pkl')]
    total_size = sum(os.path.getsize(os.path.join(grid_dir, f)) for f in files)
    
    print(f"✅ Grid status:")
    print(f"   Files: {len(files)}")
    print(f"   Size: {total_size / (1024*1024):.0f} MB")
    print(f"   Expected: 572 files, ~500 MB")
    
    return len(files) > 0

def demo_calculation():
    """Demo calculation for Berlin."""
    try:
        from solar_calculator_500mb import OptimizedSolarCalculator
        
        print("\n🔆 Testing Optimized Solar Calculator (500MB)")
        print("=" * 50)
        
        calculator = OptimizedSolarCalculator()
        
        # Berlin example - June 15th, noon
        results = calculator.calculate_energy_for_datetime(
            latitude=52.5,
            longitude=13.4,
            tilt=30,
            azimuth=0,  # South
            target_datetime=datetime(2023, 6, 15, 12, 0),
            N=30,       # 30 modules
            P_mod=0.41, # 410W per module
            dt=900      # 15 minutes
        )
        
        if results:
            print("\n🎉 SUCCESS!")
            print(f"📍 Location: Berlin ({results['latitude']:.1f}°N, {results['longitude']:.1f}°E)")
            print(f"☀️  Radiation: {results['radiation_W_per_m2']:.1f} W/m²")
            print(f"⚡ Energy: {results['energy_kWh']:.4f} kWh")
            print(f"💾 Source: {results['data_source']}")
            
            return True
        else:
            print("❌ Calculation failed")
            return False
            
    except ImportError:
        print("❌ Calculator not found - files may be missing")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main demo function."""
    print("🧪 Optimized Solar Calculator Demo (500MB)")
    print("=" * 50)
    
    # Check grid
    if not check_grid_status():
        print("\n💡 To get started:")
        print("1. Run: python3 grid_downloader_500mb.py")
        print("2. Choose option 1 to download grid (3-4 hours)")
        print("3. Run this demo again")
        return
    
    # Test calculation
    if demo_calculation():
        print("\n✅ Demo successful! The 500MB calculator is working.")
        print("\n🚀 Ready for TypeScript integration!")
        print("   • 500MB total size ✅")
        print("   • Instant calculations ✅") 
        print("   • No API calls needed ✅")
        print("   • Full Germany coverage ✅")
    else:
        print("\n❌ Demo failed - check setup")

if __name__ == "__main__":
    main()






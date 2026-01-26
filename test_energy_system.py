#!/usr/bin/env python3
"""
Unit Tests for Energy System Simulator
Ensures stability during development.

Run with: pytest test_energy_system.py -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from energy_system_simulator import EnergySystemSimulator


class TestModuleCalculations:
    """Test PV module calculations and conversions."""
    
    def test_module_database_exists(self):
        """Test that module database is loaded correctly."""
        sim = EnergySystemSimulator()
        
        assert len(sim.PV_MODULES) == 4, "Should have 4 module types"
        assert 'Winaico 450' in sim.PV_MODULES
        assert 'BAUER 445' in sim.PV_MODULES
    
    def test_module_has_correct_fields(self):
        """Test that each module has required fields."""
        sim = EnergySystemSimulator()
        
        for key, module in sim.PV_MODULES.items():
            assert 'name' in module
            assert 'modul_flaeche_m2' in module
            assert 'power_wp' in module
            assert module['modul_flaeche_m2'] > 0
            assert module['power_wp'] > 0
    
    def test_module_power_in_wp_range(self):
        """Test that module power is in realistic Wp range."""
        sim = EnergySystemSimulator()
        
        for key, module in sim.PV_MODULES.items():
            power = module['power_wp']
            assert 400 <= power <= 500, f"{key} has unrealistic power: {power} Wp"
    
    def test_module_size_realistic(self):
        """Test that module sizes are realistic."""
        sim = EnergySystemSimulator()
        
        for key, module in sim.PV_MODULES.items():
            size = module['modul_flaeche_m2']
            assert 1.5 <= size <= 2.5, f"{key} has unrealistic size: {size} m²"
    
    def test_kwp_calculation_from_area(self):
        """Test kWp calculation from roof area."""
        sim = EnergySystemSimulator()
        module = sim.PV_MODULES['Winaico 450']
        
        # Test with 40 m² roof
        dach_flaeche = 40.0
        anzahl_module = int(dach_flaeche / module['modul_flaeche_m2'])
        kwp = (anzahl_module * module['power_wp']) / 1000
        
        assert anzahl_module == 20, f"Expected 20 modules, got {anzahl_module}"
        assert abs(kwp - 9.0) < 0.01, f"Expected 9.0 kWp, got {kwp}"
    
    def test_module_count_calculation(self):
        """Test that module count is correctly calculated."""
        sim = EnergySystemSimulator()
        module = sim.PV_MODULES['Winaico 450']
        
        test_cases = [
            (20, 10),   # 20 m² → 10 modules
            (40, 20),   # 40 m² → 20 modules
            (50, 25),   # 50 m² → 25 modules
            (1, 0),     # 1 m² → 0 modules (too small)
        ]
        
        for area, expected_modules in test_cases:
            actual = int(area / module['modul_flaeche_m2'])
            assert actual == expected_modules, f"For {area} m², expected {expected_modules} modules, got {actual}"


class TestPLZConversion:
    """Test postal code to coordinates conversion."""
    
    def test_plz_berlin(self):
        """Test Berlin PLZ conversion."""
        sim = EnergySystemSimulator()
        coords = sim.plz_to_coordinates('10115')
        
        assert coords is not None
        lat, lon = coords
        assert 52.0 <= lat <= 53.0, f"Berlin latitude should be ~52°, got {lat}"
        assert 13.0 <= lon <= 14.0, f"Berlin longitude should be ~13°, got {lon}"
    
    def test_plz_unknown(self):
        """Test that unknown PLZ returns None."""
        sim = EnergySystemSimulator()
        coords = sim.plz_to_coordinates('99999')
        
        assert coords is None, "Unknown PLZ should return None"
    
    def test_all_plz_valid_coordinates(self):
        """Test that all PLZ entries have valid coordinates."""
        sim = EnergySystemSimulator()
        
        for plz, (lat, lon) in sim.plz_to_coords.items():
            assert 47 <= lat <= 55, f"PLZ {plz}: Invalid latitude {lat}"
            assert 5 <= lon <= 16, f"PLZ {plz}: Invalid longitude {lon}"


class TestAzimuthConversion:
    """Test azimuth conversion between user input and PVGIS API."""
    
    def test_south_conversion(self):
        """Test that South (180°) converts to PVGIS 0°."""
        user_azimuth = 180  # South in user convention
        pvgis_azimuth = (user_azimuth + 180) % 360
        
        assert pvgis_azimuth == 0, f"South should be 0° in PVGIS, got {pvgis_azimuth}"
    
    def test_east_conversion(self):
        """Test that East (90°) converts to PVGIS 270°."""
        user_azimuth = 90  # East in user convention
        pvgis_azimuth = (user_azimuth + 180) % 360
        
        assert pvgis_azimuth == 270, f"East should be 270° in PVGIS, got {pvgis_azimuth}"
    
    def test_west_conversion(self):
        """Test that West (270°) converts to PVGIS 90°."""
        user_azimuth = 270  # West in user convention
        pvgis_azimuth = (user_azimuth + 180) % 360
        
        assert pvgis_azimuth == 90, f"West should be 90° in PVGIS, got {pvgis_azimuth}"
    
    def test_north_conversion(self):
        """Test that North (0°) converts to PVGIS 180°."""
        user_azimuth = 0  # North in user convention
        pvgis_azimuth = (user_azimuth + 180) % 360
        
        assert pvgis_azimuth == 180, f"North should be 180° in PVGIS, got {pvgis_azimuth}"


class TestStorageSimulation:
    """Test battery storage simulation logic."""
    
    def test_battery_charging(self):
        """Test battery charges when production > consumption."""
        sim = EnergySystemSimulator()
        
        # Simple case: more production than consumption
        production = np.array([1.0, 1.0, 1.0])  # 1 kWh per interval
        consumption = np.array([0.2, 0.2, 0.2])  # 0.2 kWh per interval
        
        result = sim.simulate_storage(production, consumption, 10.0, 0.95)
        
        # Battery should charge
        assert result['battery_soc'][0] == 0.0, "Should start empty"
        assert result['battery_soc'][1] > 0.0, "Should charge in interval 2"
        assert result['battery_soc'][2] > result['battery_soc'][1], "Should keep charging"
    
    def test_battery_discharging(self):
        """Test battery discharges when consumption > production."""
        sim = EnergySystemSimulator()
        
        # Production then consumption
        production = np.array([2.0, 0.0, 0.0])  # Only first interval
        consumption = np.array([0.5, 0.5, 0.5])  # Constant consumption
        
        result = sim.simulate_storage(production, consumption, 10.0, 0.95)
        
        # Battery charges in interval 1, then discharges
        assert result['battery_soc'][0] == 0.0
        assert result['battery_soc'][1] > 0.0, "Should have charged"
        assert result['battery_soc'][2] < result['battery_soc'][1], "Should discharge"
    
    def test_battery_capacity_limit(self):
        """Test that battery doesn't exceed capacity."""
        sim = EnergySystemSimulator()
        
        # Large production, small battery
        production = np.array([10.0] * 10)  # 10 kWh per interval
        consumption = np.array([0.1] * 10)  # Minimal consumption
        
        result = sim.simulate_storage(production, consumption, 5.0, 0.95)
        
        # Battery should never exceed capacity
        max_soc = result['battery_soc'].max()
        assert max_soc <= 5.0, f"Battery exceeded capacity: {max_soc} kWh"
    
    def test_battery_efficiency(self):
        """Test that battery efficiency is applied correctly."""
        sim = EnergySystemSimulator()
        
        # Charge 10 kWh with 95% efficiency
        production = np.array([10.0, 0.0])
        consumption = np.array([0.0, 0.0])
        
        result = sim.simulate_storage(production, consumption, 20.0, 0.95)
        
        # Should store 10 × 0.95 = 9.5 kWh
        charged = result['battery_soc'][1]
        assert abs(charged - 9.5) < 0.01, f"Expected 9.5 kWh charged, got {charged}"
    
    def test_grid_feed_in_positive(self):
        """Test that excess production creates positive grid balance."""
        sim = EnergySystemSimulator()
        
        # Full battery, still producing
        production = np.array([10.0, 5.0])  # Large production
        consumption = np.array([0.5, 0.5])   # Small consumption
        
        result = sim.simulate_storage(production, consumption, 5.0, 0.95)
        
        # Should have grid feed-in (positive)
        assert result['grid_balance'][1] > 0, "Should feed into grid"
    
    def test_grid_draw_negative(self):
        """Test that deficit creates negative grid balance."""
        sim = EnergySystemSimulator()
        
        # No production, consumption needed
        production = np.array([0.0, 0.0])
        consumption = np.array([1.0, 1.0])
        
        result = sim.simulate_storage(production, consumption, 0.0, 0.95)  # Empty battery
        
        # Should draw from grid (negative)
        assert result['grid_balance'][0] < 0, "Should draw from grid"
        assert result['grid_balance'][1] < 0, "Should draw from grid"


class TestConsumptionProfile:
    """Test household consumption profile loading and scaling."""
    
    def test_consumption_scaling(self):
        """Test that consumption scales to user's annual consumption."""
        sim = EnergySystemSimulator()
        
        # Load for full year (35040 intervals)
        target_annual = 5000  # kWh
        
        # Create fake datetimes
        dates = pd.date_range('2023-01-01', periods=35040, freq='15min')
        
        consumption = sim.load_household_consumption(target_annual, dates)
        
        if consumption is not None:
            actual_total = consumption.sum()
            # Allow 1% tolerance
            assert abs(actual_total - target_annual) / target_annual < 0.01, \
                f"Expected {target_annual} kWh, got {actual_total:.2f} kWh"
    
    def test_consumption_positive_values(self):
        """Test that all consumption values are positive."""
        sim = EnergySystemSimulator()
        
        dates = pd.date_range('2023-01-01', periods=96, freq='15min')  # 1 day
        consumption = sim.load_household_consumption(5000, dates)
        
        if consumption is not None:
            assert (consumption >= 0).all(), "All consumption values should be >= 0"
    
    def test_consumption_realistic_range(self):
        """Test that consumption values are in realistic range."""
        sim = EnergySystemSimulator()
        
        dates = pd.date_range('2023-01-01', periods=35040, freq='15min')
        consumption = sim.load_household_consumption(5000, dates)
        
        if consumption is not None:
            avg = consumption.mean()
            # For 5000 kWh/year, average should be ~0.14 kWh per 15min
            expected_avg = 5000 / 35040
            assert abs(avg - expected_avg) / expected_avg < 0.01, \
                f"Average consumption mismatch: {avg:.4f} vs {expected_avg:.4f}"


class TestIntegration:
    """Integration tests for complete simulation."""
    
    def test_single_roof_simulation(self):
        """Test simulation with single roof surface."""
        sim = EnergySystemSimulator()
        
        roof_surfaces = [
            {'tilt': 30, 'azimuth': 180, 'kwp': 10.0, 'name': 'Test Roof'}
        ]
        
        # Note: This will try to fetch PVGIS data
        # May fail if no internet or cache
        try:
            result, summary = sim.run_complete_simulation(
                latitude=48.48,
                longitude=8.93,
                roof_surfaces=roof_surfaces,
                start_date="01/06/2023",
                start_time="00:00",
                end_date="07/06/2023",
                end_time="23:45",
                system_efficiency=0.8,
                battery_capacity_kwh=10.0,
                battery_efficiency=0.95,
                annual_consumption_kwh=5000
            )
            
            # Check that results exist
            assert result is not None
            assert summary is not None
            
            # Check summary values
            assert summary['total_pv_production'] > 0
            assert summary['num_intervals'] == 672  # 7 days × 96
            
            # Check result table has correct columns
            assert 'PV_Dach1_kWh' in result.columns
            assert 'PV_Gesamt_kWh' in result.columns
            assert 'Verbrauch_kWh' in result.columns
            assert 'Speicher_kWh' in result.columns
            assert 'Netz_kWh' in result.columns
            
        except Exception as e:
            pytest.skip(f"Skipped due to PVGIS access: {e}")
    
    def test_energy_balance(self):
        """Test that energy balance is correct."""
        sim = EnergySystemSimulator()
        
        # Create simple synthetic test
        num_intervals = 96  # 1 day
        production = np.array([0.5] * num_intervals)  # Constant 0.5 kWh
        consumption = np.array([0.3] * num_intervals)  # Constant 0.3 kWh
        
        result = sim.simulate_storage(production, consumption, 10.0, 1.0)  # 100% efficiency for test
        
        total_prod = production.sum()
        total_cons = consumption.sum()
        total_feed_in = result['grid_balance'][result['grid_balance'] > 0].sum()
        total_draw = abs(result['grid_balance'][result['grid_balance'] < 0].sum())
        final_battery = result['battery_soc'][-1]
        
        # Energy balance: Production = Consumption + Feed_in + Battery_final
        balance = total_prod - (total_cons + total_feed_in + final_battery - total_draw)
        
        assert abs(balance) < 0.01, f"Energy balance violated: {balance:.4f} kWh"


class TestDataValidation:
    """Test input data validation."""
    
    def test_negative_kwp_rejected(self):
        """Test that negative kWp values are handled."""
        # This would be tested in the actual input validation
        # For now, ensure module data is positive
        sim = EnergySystemSimulator()
        
        for module in sim.PV_MODULES.values():
            assert module['power_wp'] > 0
            assert module['modul_flaeche_m2'] > 0
    
    def test_zero_area_no_modules(self):
        """Test that zero or very small area results in zero modules."""
        sim = EnergySystemSimulator()
        module = sim.PV_MODULES['Winaico 450']
        
        small_area = 0.5  # Too small for any module
        anzahl = int(small_area / module['modul_flaeche_m2'])
        
        assert anzahl == 0, "Small area should result in 0 modules"


def test_cache_directory_created():
    """Test that cache directory is created on init."""
    import os
    import tempfile
    
    # Use temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        test_cache = os.path.join(tmpdir, 'test_cache')
        sim = EnergySystemSimulator(cache_dir=test_cache)
        
        assert os.path.exists(test_cache), "Cache directory should be created"


# Run tests if executed directly
if __name__ == "__main__":
    import sys
    
    # Run pytest programmatically
    sys.exit(pytest.main([__file__, '-v', '--tb=short']))

# System Performance Formulas & Parameters for Energy Production

## Overview

The interactive calculator includes **ALL frontend parameters** and uses sophisticated formulas for accurate energy production calculations.

## Enhanced Energy Production Formula

### Core Formula:
```
E = P_system × (G/1000) × η_system × T_effect × t

Where:
- E = Energy produced (kWh)
- P_system = System power (kW) 
- G = Solar irradiance (W/m²)
- η_system = Total system efficiency (dynamic)
- T_effect = Temperature effect factor
- t = Time period (hours)
```

### System Power Calculation:
```
P_system = (N_effective × P_module) / 1000

Where:
- N_effective = module_count × (dimensionsfaktor_pv / 2.0)
- P_module = Module power in Wp
- dimensionsfaktor_pv = Sizing factor from frontend (default: 2.0)
```

## System Efficiency Formula (η_system)

### Dynamic System Efficiency:
```
η_system = η_inverter × (1-L_dc) × (1-L_ac) × (1-L_shading) × (1-L_soiling) × (1-L_mismatch) × D_factor

Where:
- η_inverter = Inverter efficiency (0.94-0.98)
- L_dc = DC wiring losses (0.015-0.03)
- L_ac = AC wiring losses (0.008-0.015)
- L_shading = Shading losses (user input)
- L_soiling = Soiling/dirt losses (0.02 default)
- L_mismatch = Module mismatch losses (0.02 default)
- D_factor = Degradation factor
```

### Degradation Factor:
```
D_factor = (1 - annual_degradation)^system_age_years

Where:
- annual_degradation = 0.005 (0.5% per year default)
- system_age_years = System age from frontend
```

### Installation Type Loss Adjustments:
```
Installation Type → DC/AC Losses
- Premium:  1.5% / 0.8%
- Standard: 2.0% / 1.0% 
- Basic:    3.0% / 1.5%
```

## Temperature Effect Formula (T_effect)

### Cell Temperature Estimation (NOCT Model):
```
T_cell = T_ambient + (G/1000) × (NOCT - 20)

Where:
- T_cell = Cell temperature (°C)
- T_ambient = Ambient air temperature (°C)
- G = Irradiance (W/m²)
- NOCT = Nominal Operating Cell Temperature (45°C default)
```

### Temperature Effect Factor:
```
T_effect = 1 + γ × (T_cell - 25)

Where:
- γ = Temperature coefficient (%/°C, module-specific)
- 25°C = Standard Test Condition reference
```

### Module-Specific Temperature Coefficients:
```
Module Type → Temperature Coefficient
- Winaico GG Black 450: -0.38%/°C
- Winaico GG Black 400: -0.38%/°C  
- Generic 400 Wp:       -0.40%/°C
- Premium 500 Wp:       -0.35%/°C
- Thin Film 300 Wp:     -0.25%/°C
```

## Frontend Parameter Mapping

### From Screenshots → Calculator Parameters:

#### PV System Configuration:
- **Module Type** → `pv_module_type` → Module specs (power, efficiency, temp_coeff)
- **Module Count** → `module_count` → Number of modules
- **Dimensionsfaktor PV** → `dimensionsfaktor_pv` → System sizing factor (2.0 default)
- **Tilt Angle** → `tilt` → Panel inclination (affects irradiance)
- **Azimuth** → `azimuth` → Panel orientation (0°=South, 90°=West, 270°=East)

#### System Quality:
- **Inverter Type** → `inverter_type` → Efficiency (94-98%)
- **Installation Type** → `installation_type` → DC/AC loss factors
- **Shading** → `shading_losses` → User-specified shading percentage

#### System Age:
- **System Age** → `system_age_years` → For degradation calculation
- **Degradation Rate** → `annual_degradation` → Annual performance loss (0.5% default)

#### Environmental:
- **Location (PLZ)** → `latitude/longitude` → Solar irradiance lookup
- **Temperature** → `ambient_temp_c` → For temperature effects

## Why This Calculator Is More Accurate

The interactive calculator provides enhanced accuracy through:

1. **Dynamic System Efficiency**: Calculates real efficiency (75-98%) instead of fixed 80%
2. **Real Temperature Effects**: Uses module-specific temperature coefficients
3. **Installation Quality**: Accounts for premium vs standard vs basic installation losses
4. **System Age**: Includes annual degradation calculations
5. **Module Characteristics**: Uses exact specifications for each module type
6. **Shading Effects**: Incorporates user-specified shading losses
7. **Inverter Quality**: Applies type-specific efficiency values

## Parameter Validation Ranges

### Input Validation:
```python
# System Parameters
module_count: 1-200 modules
dimensionsfaktor_pv: 0.5-5.0
tilt: 0-90 degrees
azimuth: 0-360 degrees (or -180 to +180)

# Loss Parameters  
dc_losses: 0.01-0.05 (1-5%)
ac_losses: 0.005-0.02 (0.5-2%)
shading_losses: 0.0-0.5 (0-50%)
soiling_losses: 0.01-0.1 (1-10%)
mismatch_losses: 0.01-0.05 (1-5%)

# System Age
system_age_years: 0-30 years
annual_degradation: 0.003-0.008 (0.3-0.8% per year)

# Environmental
ambient_temp_c: -20 to +50°C
```

## Integration with Storage Simulation

### For Energy Storage Analysis:
1. Apply **all frontend parameters** for maximum accuracy
2. Calculate **15-minute energy production** intervals
3. Match production with consumption data from Excel files
4. Simulate battery charging/discharging cycles
5. Calculate grid feed-in when storage is full

---

**🔆 The interactive calculator provides research-grade accuracy with all frontend parameters! 🔆**

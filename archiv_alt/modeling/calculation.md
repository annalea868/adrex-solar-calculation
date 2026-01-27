I'll scan the codebase to find where `matrix_ev_quote` is referenced and how it's consumed, then read the relevant code to infer the meaning of the table.
Search files...

I’m going to locate how `consumptionCharacteristics` and the `householdValue` factor are defined to clarify how `matrix_ev_quote` values are adjusted, and also check how `storageSize`, `pvSize`, and `totalConsumption` units are handled so I can explain the axes of the table precisely.
Search files...

Ran tool
Read file: /home/deepmetis/Documents/DeepMetis/Adrex/spc-platform/src/lib/utils/summary.calculate.helper.ts
Read file: /home/deepmetis/Documents/DeepMetis/Adrex/spc-platform/src/lib/utils/summary.calculate.helper.ts

I looked up where `matrix_ev_quote` is used in the calculations and traced how the indices are built and the value is interpreted.

### What the table is
- **Purpose**: A 2D lookup table that gives a base self-consumption share (EV = Eigenverbrauchsquote) in percent for a PV system, depending on battery sizing and PV sizing relative to annual load.
- **Cell value meaning**: The number in each cell is the baseline percentage of PV yield that is self-consumed before adjusting for the user’s consumption pattern.

### Axes (how it’s indexed)
- **Columns (x-axis)**: `ratioPvConsumption` = PV size or PV yield relative to annual consumption, discretized in steps of 0.1 and scaled by 10.
  - Household/Total: `pvSize / (consumption_kWh_per_year * 0.001)` → essentially kWp per MWh/y
  - Heat pump: `pvYield / (heatPumpConsumption * 0.001)` → kWh/y per MWh/y
  - E-car: `pvSize / (eCarConsumption * 0.001)` → kWp per MWh/y
- **Rows (y-axis)**: `ratioBatConsumption` = Storage capacity relative to annual consumption, discretized similarly, but the index is inverted as `165 - ratioBatConsumption`. So the top row corresponds to larger battery-to-load ratios.
  - `storageSize_kWh / (consumption_kWh_per_year * 0.001)` → kWh per MWh/y

### How it’s used (core formulas)
- Household EV quote:
```162:171:src/lib/utils/summary.calculate.helper.ts
const evFaktor = this.configuratorStore.characteristicsConsumption.characteristicsConsumption ? consumptionCharacteristics.find(
    (c) => c.id === this.configuratorStore.characteristicsConsumption.characteristicsConsumption
)!.householdValue : 0;

this.evQuoteHouse = Math.trunc(
    matrix_ev_quote[165 - this.ratioBatConsumption][this.ratioPvConsumption] * evFaktor
);
```
- Heat pump EV quote:
```239:246:src/lib/utils/summary.calculate.helper.ts
const evFaktorHeatPump = consumptionCharacteristics.find(
    (c) => c.id === this.configuratorStore.characteristicsConsumption.characteristicsConsumption
)!.heatPumpValue;

this.evQuoteHeatPump = Math.trunc(
    matrix_ev_quote[165 - ratioBatConsumptionHeatPump][ratioPvConsumptionHeatPump] * evFaktorHeatPump
);
```
- E-car EV quote:
```277:285:src/lib/utils/summary.calculate.helper.ts
const evFaktorECar = consumptionCharacteristics.find(
    (c) => c.id === this.configuratorStore.characteristicsConsumption.characteristicsConsumption
)!.electricCarValue;

this.evQuoteECar = Math.trunc(
    matrix_ev_quote[165 - ratioBatConsumptionECar][ratioPvConsumptionECar] * evFaktorECar
);
```
- Total EV quote:
```311:319:src/lib/utils/summary.calculate.helper.ts
const evFaktor = consumptionCharacteristics.find(
    (c) => c.id === this.configuratorStore.characteristicsConsumption.characteristicsConsumption
)!.householdValue;

this.evQuoteTotal = Math.trunc(
    matrix_ev_quote[165 - ratioBatConsumptionTotal][ratioPvConsumptionTotal] * evFaktor
);
```

### Consumption profile adjustment
- The table’s base percentage is multiplied by a factor from `consumptionCharacteristics` to reflect user behavior:
  - `householdValue`, `heatPumpValue`, `electricCarValue` (e.g., Day vs Night vs Optimized profiles).

### Example (how to read a cell)
- Annual household consumption: 5,000 kWh/y → 5 MWh/y
- Battery: 10 kWh → `ratioBatConsumption = round(10 / 5, 1) * 10 = 20`
- PV size: 8 kWp → `ratioPvConsumption = round(8 / 5, 1) * 10 = 16`
- Table lookup: `matrix_ev_quote[165 - 20][16]`
- Multiply by the profile factor (e.g., `householdValue = 1.1` for “day”) to get the final EV quote in percent.

Status update:
- Located all usages of `matrix_ev_quote`. Confirmed axes, units, inversion, discretization, and the adjustment by consumption profile factors. Verified how it feeds EV quote, EV energy, and self-sufficiency.

- The table gives the baseline self-consumption percentage as a function of storage-to-load and PV-to-load ratios.
- Columns = PV size/yield to annual consumption; rows = battery capacity to annual consumption (inverted index).
- Values are scaled by `consumptionCharacteristics` factors to reflect day/night/optimized usage.
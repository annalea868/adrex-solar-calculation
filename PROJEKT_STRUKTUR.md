# Projekt-Struktur - Energy System Simulator

## 📁 Haupt-Dateien (RELEVANT)

### Simulator:
```
energy_system_simulator.py          ← HAUPTPROGRAMM für Simulation
test_energy_system.py               ← Unit Tests (27 Tests)
```

### Dokumentation:
```
README.md                           ← Projekt-Übersicht
SIMULATION_PLAN.md                  ← Erklärt Lookup-Tables und Ziel
TESTSZENARIEN.md                    ← 7 Test-Szenarien (0-6) für Validierung
TABELLENSTRUKTUR.md                 ← Erklärung der CSV-Ausgabe
TESTING_DOCUMENTATION.md            ← Test-Dokumentation
```

### Ordner:
```
📁 daten/                           ← ALLE DATEN
   ├── 2025-11_19_Nettokapazitäten Speicher (004).xlsx  ← Batterien
   ├── 2025-11_19_Nettokapazitäten Speicher.xlsx        ← Batterien (alt)
   ├── SPEICHER_SYSTEME_NEU.md                          ← Batterie-Doku
   └── HAUSHALT_LASTPROFIL_INFO.md                      ← Verbrauchs-Doku

📁 modeling/                        ← Lastgangdaten (Kunde)
   ├── standardlastprofil-haushaltskunden-2026.xlsx
   ├── 2025-05-27_Wärmepumpe_Lastgänge.xlsx
   ├── Standardlastprofile_Elektrofahrzeuge_Anhang_E.xlsx
   ├── misc.ts (Lookup-Tables)
   └── calculation.md (Erklärt Lookup-Tables)

📁 test_results/                    ← Lokale Test-Simulationen (ignored)
   └── *.csv (Simulationsergebnisse)

📁 pvgis_cache/                     ← PVGIS-Daten-Cache (ignored)

📁 archiv_alt/                      ← Alte/nicht mehr benötigte Dateien

📁 old_versions/                    ← Sehr alte Versionen

📁 Demo Adrex Calculation 9.9.25/   ← Demo-Calculator (separate)
```

---

## 🗑️ Archivierte Dateien (NICHT MEHR RELEVANT)

### In `archiv_alt/`:

**Alte Calculator (ersetzt durch energy_system_simulator.py):**
- solar_irradiation_calculator.py
- storage_simulator.py
- solar_calculator_500mb.py
- grid_downloader_500mb.py
- enhanced_solar_calculator.py
- solar_calculator_pvgis_direct.py
- demo_*.py
- direct_api_energy_calculator.py
- enhanced_pvgis_calculator.py

**Veraltete Dokumentation:**
- PARAMETER_ERKLAERUNG.md (alte Parameter)
- MULTI_ROOF_ANLEITUNG.md (veraltet)
- MODULTYP_FEATURE.md (veraltet)
- SYSTEM_PERFORMANCE_FORMULAS.md (erweiterte Parameter nicht verwendet)
- ENERGY_SIMULATOR_ANLEITUNG.md (veraltet)
- README_500MB.md (500MB Grid nicht mehr verwendet)
- OPTIMIZATION_SUMMARY.md (alt)
- SETUP_500MB.md (alt)
- SPEICHER_SYSTEME.md (alte Version ohne Effizienz)

---

## ✅ Was du BRAUCHST:

### Für Simulation:
1. **energy_system_simulator.py** starten
2. **TESTSZENARIEN.md** für Input-Werte
3. Excel-Dateien müssen vorhanden sein

### Für Verständnis:
1. **SIMULATION_PLAN.md** - Erklärt das Ziel
2. **TABELLENSTRUKTUR.md** - Erklärt die Ausgabe
3. **HAUSHALT_LASTPROFIL_INFO.md** - Erklärt Verbrauchsdaten

### Für Entwicklung:
1. **test_energy_system.py** - Tests ausführen
2. **TESTING_DOCUMENTATION.md** - Test-Anleitung

---

## 🎯 Empfehlung:

**Behalte im Root-Verzeichnis:**
- ✅ energy_system_simulator.py
- ✅ test_energy_system.py
- ✅ Aktuelle Dokumentation (TESTSZENARIEN.md, etc.)
- ✅ Excel-Dateien
- ✅ modeling/ Ordner

**Alles andere ist im Archiv** und kann ignoriert werden!

---

## 🚀 Workflow:

1. **Simulation starten:**
   ```bash
   python3 energy_system_simulator.py
   ```

2. **Tests ausführen:**
   ```bash
   python3 -m pytest test_energy_system.py -v
   ```

3. **Dokumentation lesen:**
   - TESTSZENARIEN.md für Test-Inputs
   - TABELLENSTRUKTUR.md für Ausgabe-Format

**Das wars! Alles andere ist Archiv.** 📦

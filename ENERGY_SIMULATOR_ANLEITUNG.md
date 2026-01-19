# Energy System Simulator - Anleitung

## 🎯 Was macht dieses Tool?

Der **Energy System Simulator** ist ein **kombiniertes Tool**, das alle drei Komponenten in **EINEM** Durchlauf simuliert:

1. ☀️  **PV-Produktion** (Sonneneinstrahlung → Energie)
2. 🏠 **Verbrauch** (Standardlastprofil skaliert)
3. 🔋 **Speicher** (Batterie-Simulation mit Netzinteraktion)

## 🚀 Verwendung

### Start

```bash
python3 energy_system_simulator.py
```

### Eingaben (interaktiv)

Das Tool fragt dich nach folgenden Parametern:

#### 1. Standort
- **PLZ** (z.B. `10115` für Berlin) ODER
- **Koordinaten** (Breitengrad + Längengrad)

#### 2. PV-System
- **Neigung** (Grad, z.B. `30`)
- **Ausrichtung** (0°=Nord, 90°=Ost, 180°=Süd, 270°=West)
- **Systemgröße** (kW, z.B. `10`)
- **Wirkungsgrad** (z.B. `0.8` für 80%)

#### 3. Zeitraum
- **Startdatum** (DD/MM/YYYY)
- **Startzeit** (HH:MM)
- **Enddatum** (DD/MM/YYYY)
- **Endzeit** (HH:MM)

#### 4. Batterie
- **Kapazität** (kWh, z.B. `10`)
- **Wirkungsgrad** (z.B. `0.95` für 95%)

#### 5. Verbrauch
- **Jahresverbrauch** (kWh, z.B. `5000`)

## 📊 Ausgabe

### 1. Tabelle (CSV-Export möglich)

Für **jedes 15-Minuten-Intervall** im gewählten Zeitraum:

| Spalte | Beschreibung | Einheit |
|--------|--------------|---------|
| `Datum` | Datum | DD.MM.YYYY |
| `Uhrzeit` | Uhrzeit | HH:MM |
| `Sonneneinstrahlung_W_m2` | Momentane Strahlung | W/m² |
| `Einstrahlung_15min_Wh_m2` | Energie über 15 Min | Wh/m² |
| `PV_Energie_kWh` | Erzeugte PV-Energie | kWh |
| `Verbrauch_kWh` | Haushaltsverbrauch | kWh |
| `Speicher_kWh` | Speicher-Füllstand | kWh |
| `Netz_kWh` | Netzinteraktion | kWh |

**Netz_kWh Bedeutung:**
- **Positiv**: Einspeisung ins Netz
- **Negativ**: Bezug aus dem Netz

### 2. Zusammenfassung (4 Kennzahlen)

```
📊 WICHTIGSTE KENNZAHLEN:
   1. Erzeugte Energie (PV):      xxx.xx kWh
   2. Netzeinspeisung:             xxx.xx kWh
   3. Netzbezug:                   xxx.xx kWh
   4. Gesamtverbrauch:             xxx.xx kWh
```

### 3. Kontrollwert (bei Jahres-Simulation)

Wenn der Zeitraum **genau 1 Jahr** ist (01.01 bis 31.12):
- Vergleicht **eingegebenen Jahresverbrauch** mit **berechnetem Gesamtverbrauch**
- Sollte **identisch** sein → Validierung der Skalierung

## 🔄 Ablauf

```
┌─────────────────────────────────────┐
│  1. Eingaben erfassen               │
│     (Standort, PV, Zeitraum, etc.)  │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  2. PV-Produktion berechnen         │
│     - PVGIS API (gecached)          │
│     - Interpolation 1h → 15min      │
│     - Zeitraum extrahieren          │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  3. Verbrauch berechnen             │
│     - Standardlastprofil laden      │
│     - Auf Jahresverbrauch skalieren │
│     - Kalender-basiert zuordnen     │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  4. Speicher simulieren             │
│     - Produktion vs. Verbrauch      │
│     - Batterie laden/entladen       │
│     - Netz-Interaktion berechnen    │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  5. Ergebnisse anzeigen & speichern │
│     - 4 Kennzahlen                  │
│     - Tabellen-Vorschau             │
│     - CSV-Export                    │
└─────────────────────────────────────┘
```

## 📁 Benötigte Dateien

Das Tool benötigt:

1. **`modeling/standardlastprofil-haushaltskunden-2026.xlsx`**
   - Standardlastprofil für Haushaltskunden
   - 35.040 Intervalle (365 Tage × 96 pro Tag)

2. **`2025-11_19_Nettokapazitäten Speicher.xlsx`** (optional)
   - Wird aktuell nicht verwendet, aber vorhanden für spätere Erweiterung

3. **PVGIS API Zugang**
   - Erste Abfrage: 30-60 Sekunden
   - Danach: gecacht in `pvgis_cache/` Ordner

## 💡 Beispiel-Eingaben

### Szenario: 1-Wochen-Test (Berlin, Juni)

```
Standort:        10115
Neigung:         30
Ausrichtung:     0
Systemgröße:     10 kW
Wirkungsgrad:    0.8
Startdatum:      01/06/2024
Startzeit:       00:00
Enddatum:        07/06/2024
Endzeit:         23:45
Batterie:        10 kWh
Effizienz:       0.95
Jahresverbrauch: 5000 kWh
```

**Ergebnis:**
- 672 Intervalle (7 Tage × 96)
- Detaillierte Tabelle für jede Viertelstunde
- 4 Zusammenfassungswerte

## ⚠️ Wichtige Hinweise

### Zeitraum-Logik
- Das Tool verwendet **2023 als Referenzjahr** für Wetterdaten
- Dein eingegebenes Jahr wird auf 2023 **gemappt** (gleiche Tage/Monate)
- Für echte 2024/2025 Daten müsste man Live-Wetter-APIs nutzen

### Verbrauchsprofil
- Basiert auf **deutschem Standardlastprofil** (VDN/BDEW)
- Berücksichtigt **saisonale Schwankungen** (Winter vs. Sommer)
- **Kalender-genau**: Nutzt echte Tages- und Uhrzeitmuster

### Cache
- PVGIS-Daten werden **lokal gespeichert** (`pvgis_cache/`)
- Zweite Simulation mit **gleicher Konfiguration** ist sofort
- Cache-Datei-Format: `pvgis_LAT_LON_TILT_AZIMUTH_YEAR.pkl`

## 🔧 Technische Details

### Struktur des Codes

Das Skript ist klar in **3 Teile** gegliedert:

```python
# TEIL 1: PV-PRODUKTION
def calculate_pv_production(...)
    # PVGIS API → Stunden-Daten → 15-Min-Interpolation

# TEIL 2: VERBRAUCH
def load_household_consumption(...)
    # Excel → Skalierung → Kalender-Zuordnung

# TEIL 3: SPEICHER-SIMULATION
def simulate_storage(...)
    # Produktion vs. Verbrauch → Batterie → Netz
```

### Batterie-Logik

Für **jedes 15-Minuten-Intervall**:

1. **Produktion > Verbrauch** (Überschuss):
   ```
   Überschuss → Batterie laden (bis voll)
   Rest → Netzeinspeisung (positiv)
   ```

2. **Verbrauch > Produktion** (Defizit):
   ```
   Defizit → Batterie entladen (bis leer)
   Rest → Netzbezug (negativ)
   ```

### Wirkungsgrad

- **Laden**: `Speicher += Energie × efficiency`
- **Entladen**: `Energie = Speicher / efficiency`



## 🔜 Nächste Schritte

Mögliche Erweiterungen:
- Dimensionsfaktoren PV/Speicher hinzufügen
- Heat Pump Verbrauch integrieren
- E-Car Verbrauch integrieren
- Wirtschaftlichkeitsrechnung (Kosten, Ersparnisse)
- Vergleich mit Lookup-Tabellen aus `misc.ts`


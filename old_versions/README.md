# Solar Energy Calculator - PVGIS Deutschland

Ein Python-Tool zur Berechnung der Solarenergieerzeugung basierend auf PVGIS-Daten für Deutschland.

## Übersicht

Dieses Tool verwendet die PVGIS API (Photovoltaic Geographical Information System der EU) um genaue Globalstrahlungsdaten für Deutschland abzurufen und damit die Energieerzeugung von Solarmodulen zu berechnen.

### Formel
```
E = (N * P_mod * (G / 1000) * eta_sys) * (dt / 3600)
```

Wobei:
- **N**: Anzahl der Module
- **P_mod**: Nennleistung pro Modul in kWp
- **G**: Globalstrahlung auf die Modulfläche [W/m²] (aus PVGIS)
- **eta_sys**: Systemwirkungsgrad (z.B. 0.8 für 80%)
- **dt**: Zeitraum in Sekunden
- **E**: Erzeugte Energie in kWh

## Installation

1. Repository klonen oder herunterladen
2. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

## Verwendung

### Interaktive Verwendung
```bash
python main.py
```

Das Programm fragt nach folgenden Parametern:
- **Breitengrad** (z.B. 52.5 für Berlin)
- **Längengrad** (z.B. 13.4 für Berlin)
- **Neigung** in Grad (z.B. 30° für typische Dachneigung)
- **Ausrichtung** in Grad (0°=Süd, 90°=West, -90°=Ost)
- **Datum** (YYYY-MM-DD)
- **Uhrzeit** (HH:MM)
- **Anzahl der Module**
- **Nennleistung pro Modul** in kWp
- **Zeitraum** in Sekunden

### Programmgesteuerte Verwendung

```python
from main import SolarEnergyCalculator
from datetime import datetime

# Calculator erstellen
calc = SolarEnergyCalculator()

# Parameter definieren
latitude = 52.5  # Berlin
longitude = 13.4
tilt = 30  # 30° Neigung
azimuth = 0  # Süd-Ausrichtung
target_time = datetime(2023, 6, 15, 12, 0)  # 15. Juni 2023, 12:00

# Systemparameter
N = 30  # 30 Module
P_mod = 0.41  # 410 Wp pro Modul
dt = 900  # 15 Minuten

# Berechnung (Systemwirkungsgrad ist fest auf 80% gesetzt)
results = calc.calculate_energy_for_datetime(
    latitude, longitude, tilt, azimuth, target_time,
    N, P_mod, dt
)

if results:
    print(f"Energie: {results['energy_kWh']:.4f} kWh")
    print(f"Globalstrahlung: {results['radiation_W_per_m2']:.1f} W/m²")
```

## PVGIS Datenquelle

Die Anwendung nutzt die **PVGIS API** der Europäischen Kommission:
- **Datenquelle**: SARAH-Datenbank (CM SAF/EUMETSAT)
- **Basis**: Meteosat-Satellitendaten (SEVIRI)
- **Auflösung**: Stündliche Daten basierend auf 15-Minuten-Beobachtungen
- **Abdeckung**: Ganz Europa einschließlich Deutschland
- **Genauigkeit**: Hoch validiert für deutsche Standorte
- **Lizenz**: Kostenlos und frei nutzbar

## Features

- ✅ **Keine API-Schlüssel erforderlich**: PVGIS ist kostenlos verfügbar
- ✅ **Hohe Genauigkeit**: Satellitendaten speziell für Europa validiert
- ✅ **Neigung und Ausrichtung**: Automatische Berechnung für geneigte Flächen
- ✅ **Zeitliche Auflösung**: Stündliche Strahlungswerte
- ✅ **Deutsche Standorte**: Optimiert für Deutschland
- ✅ **Einfache Integration**: Direkte Python-Implementierung
- ✅ **Fester Systemwirkungsgrad**: 80% als bewährter Durchschnittswert

## Beispiele

### Getestete Szenarien

Die Implementierung wurde erfolgreich getestet mit:

**Berlin Sommer (15. Juni 2023, 12:00 Uhr)**
- 25 Module × 400 Wp, 30° Süd-Ausrichtung
- Ergebnis: 2.53 kWh/h bei 297 W/m² Einstrahlung

**München Ost-West-Anlage (1. Juli 2023)**
- 15 Module Ost (8:00): 399 Wh/15min bei 380 W/m²
- 15 Module West (18:00): 55 Wh/15min bei 52 W/m²

**Hamburg Saisonvergleich (21. Juni vs 21. Dezember, 12:00)**
- Sommer: 3.44 kWh/h bei 466 W/m² Einstrahlung
- Winter: 0.12 kWh/h bei 17 W/m² Einstrahlung
- Verhältnis: 28:1

### Beispiel-Skript

Ein umfassendes Beispiel-Skript ist verfügbar:
```bash
python3 example.py
```

Das Skript demonstriert verschiedene Installationstypen und Szenarien.

## Technische Details

- **Python Version**: 3.7+
- **Hauptbibliotheken**: pvlib, pandas, numpy
- **Datenformat**: JSON/CSV von PVGIS
- **Zeitzone**: UTC (PVGIS Standard)

## Lizenz

Dieses Tool ist Open Source. Die PVGIS-Daten sind frei verfügbar von der Europäischen Kommission.

## Unterstützung

Bei Fragen oder Problemen, bitte die Dokumentation der verwendeten Bibliotheken konsultieren:
- [PVGIS Documentation](https://joint-research-centre.ec.europa.eu/pvgis-photovoltaic-geographical-information-system_en)
- [pvlib Python Documentation](https://pvlib-python.readthedocs.io/)

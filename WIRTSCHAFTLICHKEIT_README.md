# Wirtschaftlichkeitsberechnung

## 📋 Übersicht

Die `wirtschaftlichkeit.py` berechnet alle finanziellen Kennzahlen aus den Simulationsergebnissen.

## 🔗 Workflow

```
1. energy_system_simulator_local_poa.py ausführen
   ↓ (erzeugt CSV mit 15-Minuten-Daten)
   
2. wirtschaftlichkeit.py ausführen
   ↓ (liest CSV + User-Inputs für Preise)
   
3. Übersichtsblatt mit allen Kennzahlen
```

## 📊 Was wird berechnet?

### ✅ Aus Simulator (Summary):
- Jahresertrag (kWh)
- PV-Größe (kWp) 
- Netzeinspeisung (kWh)
- Netzbezug (kWh)
- Verbrauch pro Typ (Haushalt, E-Auto, WP)

### 🔍 Aus CSV (nachberechnet):
- **Eigenstrom** für jeden Verbraucher (kWh/a)
  - Logik: Verbrauch - anteiliger Netzbezug

### 💰 Wirtschaftlichkeits-Kennzahlen:
1. Spezifischer Ertrag (kWh/kWp/a)
2. Eigenverbrauchsquoten (%)
3. Autarkiegrade (%) - mit Limits!
4. Durchschnittlicher Strompreis (€/kWh)
5. Jährliche Ersparnis (€/a)
6. Jährliche Vergütung (€/a)
7. Gesamtvorteil (€)
8. Rendite (%/a)
9. Stromentstehungskosten (€/kWh)
10. Amortisationszeit (Jahre)

## 🎯 Verwendung

```bash
# 1. Simulation ausführen
python3 energy_system_simulator_local_poa.py
# → Erzeugt: test_results/simulation_01012023_31122023.csv

# 2. Wirtschaftlichkeit berechnen
python3 wirtschaftlichkeit.py
# → Gibt Pfad zur CSV an
# → Gibt Preise/Parameter ein
# → Erhält Übersichtsblatt
```

## 📝 Benötigte Inputs

### Von der Simulation (automatisch):
- CSV-Datei mit 15-Minuten-Werten

### Vom User:
1. **PV-System:**
   - PV-Größe [kWp]
   - Modultyp
   
2. **Speicher:**
   - Speicherkapazität [kWh]
   - Speichertyp

3. **Wirtschaftlichkeit:**
   - Investition netto [€]
   - Aktueller Strompreis [€/kWh]
   - Preissteigerungsrate [%/a]
   - Inflation [%/a]
   - Laufzeit [Jahre]
   - Einspeisevergütung [€/kWh] (optional, default 0.08)

## ⚠️ Wichtige Limits

Aus CALCULATION.pdf:

- **Spezifischer Ertrag:** Max. 940 kWh/kWp/a
- **Autarkie Haushalt:** Max. 80%
- **Autarkie Wärmepumpe:** Max. 55%
- **Gesamtautarkie:** Max. 80%

Diese Limits werden automatisch angewendet.

## 🔧 Technische Details

### Eigenstrom-Berechnung:

Für jedes 15-Minuten-Intervall:

```python
if Netz_kWh < 0:
    # Netzbezug vorhanden
    netzbezug = abs(Netz_kWh)
    anteil_haushalt = Haushalt_Verbrauch_kWh / Gesamt_Verbrauch_kWh
    netzbezug_haushalt = netzbezug × anteil_haushalt
    eigenstrom_haushalt = Haushalt_Verbrauch_kWh - netzbezug_haushalt
else:
    # Kein Netzbezug → gesamter Verbrauch ist Eigenstrom
    eigenstrom_haushalt = Haushalt_Verbrauch_kWh
```

Dann: `Jahres_Eigenstrom = Summe aller Intervalle`

### Durchschnittlicher Strompreis:

```python
ø_Strompreis = aktueller_Preis × ((1 + rate)^Laufzeit - 1) / (rate × Laufzeit)
```

Berücksichtigt die Preissteigerung über die Jahre.

## 📄 Output-Beispiel

```
📋 ÜBERSICHTSBLATT - DEINE SOLARSTROMANLAGE
======================================================================

🔲 SYSTEM-KONFIGURATION:
   PV-Größe:          22.50 kWp
   Modultyp:          Winaico 450
   Speicherkapazität: 11.00 kWh
   Speichertyp:       sonnenBatterie 10 P+ / 11,0

📊 ERTRÄGE UND PREISE:
   Spezifischer Ertrag:   940.00 kWh/kWp/a
   Jahresertrag:          21,150.00 kWh/a
   Aktueller Strompreis:  0.35 €/kWh
   Preissteigerungsrate:  4.00 %/a
   Inflation:             3.00 %/a
   Laufzeit:              20 Jahre

🏠 VERBRAUCH UND QUOTEN:
   Verbrauch Hausstrom:          3,000.00 kWh/a
   Eigenverbrauch Hausstrom:     11.35 %
   Eigenstrom Hausstrom:         2,400.00 kWh/a
   Autarkie Hausstrom:           80.00 %

💶 WIRTSCHAFTLICHKEIT:
   Invest netto:                 37,700.00 €
   Jährl. Ersparnis:             1,721.81 €/a
   Jährl. Vergütung:             1,379.19 €/a
   Gesamtvorteil (20 Jahre):    62,020.09 €
   Rendite:                      7.23 %/a
   Stromentstehungskosten:       0.0890 €/kWh
   Amortisationszeit:            12.16 Jahre
```

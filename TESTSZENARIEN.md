# Testszenarien für Energy System Simulator

## 📍 Gemeinsame Parameter (alle Szenarien)

**Standort: Rottenburg am Neckar**
```
Breitengrad:  48.48
Längengrad:   8.93
```

**Zeitraum:**
```
Startdatum:   01/01/2023
Startzeit:    00:00
Enddatum:     31/12/2023
Endzeit:      23:45
```

**Wirkungsgrade (konstant für alle Tests):**
```
Systemwirkungsgrad (PV):    0.80 (80%)
Batterie-Wirkungsgrad:      0.95 (95%)
```


**Batterien:**
- Alle Kapazitäten entsprechen realen Systemen aus verfügbaren Produkten
- Siehe SPEICHER_SYSTEME.md für Details

---

## 🔬 SZENARIO 0: "Basis-Szenario" (simulationtest3)
**Dateiname:** `simulationtest3.csv` / `szenario0_basis.csv`  
**Phänomen:** Ausgewogenes Standard-System

```
Neigung:                    32°
Ausrichtung:                180° (Süd)
PV-Systemgröße:             8 kWp
Batteriekapazität:          10 kWh (sonnenBatterie 10)
Jahresverbrauch:            3000 kWh
```

**Erwartetes Ergebnis:**
- PV/Verbrauch-Ratio: 2.67
- Gut ausbalanciertes System
- Moderater Überschuss im Sommer
- Referenz existiert für Vergleiche    

---

## 🔬 SZENARIO 1: "Kleine Anlage, Kleiner Speicher"
**Dateiname:** `szenario1_klein_klein.csv`  
**Phänomen:** Hoher Netzbezug, wenig Autarkie

```
Neigung:                    30°
Ausrichtung:                180° (Süd)
PV-Systemgröße:             7 kWp
Batteriekapazität:          5 kWh (sonnenBatterie 10 hybrid)
Jahresverbrauch:            4500 kWh
```

**Erwartetes Ergebnis:**
- PV/Verbrauch-Ratio: 1.56
- System zu klein für Verbrauch
- Speicher oft leer
- Hoher Netzbezug im Winter

---

## ⚡ SZENARIO 2: "Mittlere Anlage, Sehr Kleiner Speicher, Ost-Dach"
**Dateiname:** `szenario2_mittel_mini_speicher.csv`  
**Phänomen:** Ost-Ausrichtung mit kleinem Speicher, Morgen-Überschuss

```
Neigung:                    30°
Ausrichtung:                90° (Ost)
PV-Systemgröße:             10 kWp
Batteriekapazität:          4.85 kWh (SolarEdge Home Batterie)
Jahresverbrauch:            3500 kWh
```

**Erwartetes Ergebnis:**
- PV/Verbrauch-Ratio: 2.86
- Ost-Dach: Produktion vormittags, weniger Gesamtertrag als Süd
- Speicher zu klein für morgendlichen Überschuss
- Gute Eigenverbrauchsquote am Vormittag

---

## 🌞 SZENARIO 3: "Große Anlage, Mittlerer Speicher"
**Dateiname:** `szenario3_gross_mittel.csv`  
**Phänomen:** Überschusseinspeisung besonders im Sommer

```
Neigung:                    35°
Ausrichtung:                180° (Süd)
PV-Systemgröße:             12 kWp
Batteriekapazität:          9.7 kWh (SolarEdge Home Batterie)
Jahresverbrauch:            4000 kWh
```

**Erwartetes Ergebnis:**
- PV/Verbrauch-Ratio: 3.00
- Große Überschüsse im Sommer
- Gute Winterversorgung
- Hohe Netzeinspeisung

---

## ⚖️ SZENARIO 4: "Mittlere Anlage, Großer Speicher, Süd-West"
**Dateiname:** `szenario4_optimal.csv`  
**Phänomen:** Süd-West-Dach mit großem Speicher, Nachmittagsproduktion

```
Neigung:                    30°
Ausrichtung:                225° (Süd-West)
PV-Systemgröße:             9 kWp
Batteriekapazität:          12.8 kWh (Sungrow SBR128)
Jahresverbrauch:            4000 kWh
```

**Erwartetes Ergebnis:**
- PV/Verbrauch-Ratio: 2.25
- Süd-West: Produktion bis in den frühen Nachmittag (etwas verzögert im Vergl. zu reinem Süd-Dach)
- Großer Speicher kann Abendverbrauch abdecken (nicht im Winter)
- Gute Eigenverbrauchsquote trotz Abweichung von Süd

---

## 🏠 SZENARIO 5: "Große Anlage, Großer Speicher - Maximale Autarkie"
**Dateiname:** `szenario5_maxautarkie.csv`  
**Phänomen:** Sehr hohe Eigenverbrauchsquote und Autarkiegrad

```
Neigung:                    30°
Ausrichtung:                180° (Süd)
PV-Systemgröße:             11 kWp
Batteriekapazität:          16 kWh (Sungrow SBR160)
Jahresverbrauch:            3800 kWh
```

**Erwartetes Ergebnis:**
- PV/Verbrauch-Ratio: 2.89
- Fast vollständige Autarkie im Sommer
- Sehr wenig Netzbezug
- Maximale Eigennutzung

---

## 📈 SZENARIO 6: "Mittlere Anlage, Hoher Verbrauch - Unterdeckung"
**Dateiname:** `szenario6_unterdeckung.csv`  
**Phänomen:** System reicht nicht aus, trotz Speicher hoher Netzbezug

```
Neigung:                    30°
Ausrichtung:                165° (Süd-Süd-Ost, leichte Abweichung)
PV-Systemgröße:             8 kWp
Batteriekapazität:          9.6 kWh (Sungrow SBR096)
Jahresverbrauch:            9000 kWh
```

**Erwartetes Ergebnis:**
- PV/Verbrauch-Ratio: 0.89
- System deutlich zu klein für sehr hohen Verbrauch
- Trotz PV und Speicher sehr viel Netzbezug nötig (PV Energie reicht nur im Hoch-Sommer)
- Autarkie nur ~30-35%

---

## 📊 Erwartete Kennzahlen (Jahreswerte)

| Szenario | PV-Produktion | Netzeinspeisung | Netzbezug | Autarkiegrad |
|----------|---------------|-----------------|-----------|--------------|
| 0 Basis (Süd) | ~8.000 kWh | ~4.000 kWh | ~500 kWh | ~85% |
| 1 Klein-Klein (Süd) | ~7.000 kWh | ~500 kWh | ~3.000 kWh | ~60% |
| 2 Mittel-Mini (Ost) | ~8.500 kWh | ~4.500 kWh | ~900 kWh | ~74% |
| 3 Groß-Mittel (Süd) | ~12.000 kWh | ~7.000 kWh | ~600 kWh | ~85% |
| 4 Optimal (Süd-West) | ~8.500 kWh | ~2.800 kWh | ~1.000 kWh | ~75% |
| 5 Max-Autarkie (Süd) | ~11.000 kWh | ~5.000 kWh | ~500 kWh | ~88% |
| 6 Unterdeckung (Süd-Süd-Ost) | ~7.800 kWh | ~200 kWh | ~6.800 kWh | ~33% |

---

## 🎯 Phänomene die gezeigt werden sollen

### 1. Dachausrichtungen (Szenario 0, 2, 4, 6)
- **Süd (0, 1, 3, 5):** Optimaler Ertrag, gleichmäßige Tagesverteilung
- **Ost (2):** Morgen-Produktion, geringerer Gesamtertrag (-15%)
- **Süd-West (4):** Nachmittags-Produktion, guter Gesamtertrag (-5%)
- **Süd-Süd-Ost (6):** Leichte Abweichung, minimaler Ertragsverlust (-3%)

### 2. Speicher zu klein (Szenario 2)
- Speicher wird schnell voll (besonders vormittags bei Ost)
- Viel Überschuss-Einspeisung trotz Speicher
- Zeigt: Speicher sollte zur PV-Größe passen

### 3. Speicher optimal (Szenario 4)
- Gute Balance zwischen PV, Speicher und Verbrauch
- Süd-West-Ausrichtung kompensiert durch großen Speicher
- Zeigt: Richtige Dimensionierung wichtiger als perfekte Ausrichtung

### 4. System zu klein (Szenario 1 & 6)
- Hoher Netzbezug
- Niedrige Autarkie
- Zeigt: PV-Größe muss zum Verbrauch passen

### 5. Überdimensioniert (Szenario 3 & 5)
- Viel Netzeinspeisung
- Wirtschaftlich zu prüfen
- Zeigt: Mehr PV ≠ automatisch besser

---

## 🔋 Verwendete Batteriesysteme

| Szenario | Kapazität | Modell |
|----------|-----------|--------|
| 0 Basis | 10.0 kWh | sonnenBatterie 10 |
| 1 Klein-Klein | 5.0 kWh | sonnenBatterie 10 hybrid |
| 2 Mittel-Mini | 4.85 kWh | SolarEdge Home Batterie |
| 3 Groß-Mittel | 9.7 kWh | SolarEdge Home Batterie |
| 4 Optimal | 12.8 kWh | Sungrow SBR128 |
| 5 Max-Autarkie | 16.0 kWh | Sungrow SBR160 |
| 6 Unterdeckung | 9.6 kWh | Sungrow SBR096 |

**Alle Kapazitäten sind NETTO-Werte** (nutzbare Speicherkapazität)

## 💡 Hinweise für Tests

1. **Cache:** Erste Ausführung dauert ~60 Sekunden (PVGIS API)
2. **Speicherort:** Alle Szenarien nutzen gleichen Standort → Cache wird wiederverwendet
3. **Dateiformat:** CSV mit 35.040 Zeilen (ein ganzes Jahr, 15-Min-Intervalle)
4. **Vergleich:** Nutze Excel/LibreOffice um Szenarien zu vergleichen
5. **Batterien:** Alle Kapazitäten entsprechen realen Produkten aus SPEICHER_SYSTEME.md

## 🔄 Änderung zur alten Konvention

**ALT:**
- Süd = 0°
- West = 90°
- Ost = 270°

**NEU (Standard-Kompass):**
- Nord = 0°
- Ost = 90°
- **Süd = 180°** ← Für alle Szenarien
- West = 270°


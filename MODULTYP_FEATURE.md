# Modultyp-Feature - Berechnung basierend auf Dachfläche

## 🎯 Neue Funktionalität

Statt **kWp direkt einzugeben**, berechnet das System jetzt automatisch:

**Input:**
- Modultyp (aus Liste wählen)
- Dachfläche in m²

**Berechnung:**
- Anzahl Module = Dachfläche ÷ Modulfläche
- Gesamt-kWp = Anzahl Module × Leistung pro Modul

## 🔲 Verfügbare Modultypen

| Nr | Name | Fläche/Modul | Leistung/Modul | kWp/m² |
|----|------|--------------|----------------|--------|
| 1 | BAUER Glas/Glas Black 445 Wp | 1.998 m² | 445 Wp | 0.223 |
| 2 | Winaico WST-450 NFX54-B1 | 1.998 m² | 450 Wp | 0.225 |
| 3 | SOLYCO R-TG 108n.4/445 | 1.998 m² | 445 Wp | 0.223 |
| 4 | Winaico WST-480 BDX54-BW | 2.041 m² | 480 Wp | 0.235 |

## 🔄 Neue Input-Reihenfolge

```
1. 📍 STANDORT
   → PLZ oder Koordinaten

2. 🔲 PV-MODULTYP
   → Wähle aus 4 verfügbaren Modulen
   
3. ⚙️  SYSTEMWIRKUNGSGRAD
   → z.B. 0.8 für 80%

4. ☀️  DACHFLÄCHEN
   
   🏠 DACHFLÄCHE 1:
      → Neigung (Grad)
      → Ausrichtung (0-360°)
      → Dachfläche (m²)
      → System berechnet: X Module, Y kWp
   
   → Weitere Dachfläche? (j/n)
   
   🏠 DACHFLÄCHE 2: (falls j)
      → Neigung
      → Ausrichtung
      → Dachfläche (m²)
      → System berechnet: X Module, Y kWp
   
   ... (beliebig oft wiederholbar)
   
   📊 ZUSAMMENFASSUNG:
      → Gesamt-Module
      → Gesamt-kWp

5. 📅 ZEITRAUM
   → Start/Ende

6. 🔋 BATTERIE
   → Kapazität

7. 🏠 VERBRAUCH
   → Jahresverbrauch
```

## 💡 Beispiel-Session

### Eingaben:
```
Standort:        48.48 / 8.93 (Rottenburg)
Modultyp:        2 (Winaico 450)
Wirkungsgrad:    0.8

DACHFLÄCHE 1:
  Neigung:       30°
  Ausrichtung:   180° (Süd)
  Fläche:        40 m²
  → 20 Module, 9.00 kWp

Weitere Dachfläche? j

DACHFLÄCHE 2:
  Neigung:       30°
  Ausrichtung:   90° (Ost)
  Fläche:        20 m²
  → 10 Module, 4.50 kWp

Weitere Dachfläche? n

GESAMT: 30 Module, 13.50 kWp
```

## 📊 Berechnungsformel

### Für jede Dachfläche:

```
Anzahl_Module = floor(Dachfläche_m² / Modul_m²)

Beispiel:
  40 m² / 1.998 m² = 20.02 → 20 Module (abgerundet)

kWp_Dachfläche = Anzahl_Module × Leistung_pro_Modul

Beispiel:
  20 Module × 0.450 kWp = 9.00 kWp
```

### Nutzbare Fläche:

```
Nutzbare_Fläche = Anzahl_Module × Modul_m²

Beispiel:
  20 Module × 1.998 m² = 39.96 m²
  
Ungenutzt: 40.00 - 39.96 = 0.04 m² (zu klein für weiteres Modul)
```

## 🎯 Vorteile

1. ✅ **Realistischer:** Nutzer kennen ihre Dachfläche in m²
2. ✅ **Automatisch:** System berechnet optimale Modulanzahl
3. ✅ **Modul-spezifisch:** Unterschiedliche Modulgrößen berücksichtigt
4. ✅ **Transparent:** Zeigt Anzahl Module und nutzbare Fläche
5. ✅ **Fehler-sicher:** Warnt wenn Dachfläche zu klein

## 📋 Ausgabe-Tabelle (erweitert)

### Spalten bei 2 Dachflächen:

```csv
Datum,Uhrzeit,
Sonneneinstrahlung_W_m2,Einstrahlung_15min_Wh_m2,
PV_Dach1_kWh,PV_Dach2_kWh,PV_Gesamt_kWh,
Verbrauch_kWh,Speicher_kWh,Netz_kWh
```

**Jede Dachfläche** hat ihre eigene Produktions-Spalte!
**PV_Gesamt_kWh** ist die Summe und wird für Speicher-Simulation verwendet.

## 🔬 Für Testszenarien

Die Szenarien müssen jetzt angepasst werden mit:
- Modultyp-Auswahl
- Dachflächen in m² statt kWp

### Beispiel Szenario 0:
```
Alt: 8 kWp direkt
Neu: Winaico 450 + 35.5 m² → 17 Module → 7.65 kWp
     (oder 40 m² → 20 Module → 9.00 kWp)
```

## ⚡ Wichtig für deine Tests

Du musst jetzt entscheiden:
- **Welchen Modultyp** für alle Szenarien? (z.B. immer Winaico 450)
- **Wie groß** sind die Dachflächen in m²?

Für **8 kWp mit Winaico 450** brauchst du etwa **35-36 m² Dachfläche**.

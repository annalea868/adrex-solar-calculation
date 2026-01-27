# Multi-Roof Feature - Mehrere Dachflächen

## 🎯 Neue Funktion

Der **Energy System Simulator** unterstützt jetzt **mehrere Dachflächen** mit unterschiedlichen:
- Neigungen
- Ausrichtungen  
- kWp-Verteilungen

## 🏠 Typische Anwendungsfälle

### Beispiel 1: Ost-West-Dach
```
Gesamt-System: 10 kWp

Dachfläche 1: Ost-Seite
  - Neigung: 30°
  - Ausrichtung: 90° (Ost)
  - Anteil: 5 kWp (50%)

Dachfläche 2: West-Seite
  - Neigung: 30°
  - Ausrichtung: 270° (West)
  - Anteil: 5 kWp (50%)
```

### Beispiel 2: Hauptdach Süd + Garage West
```
Gesamt-System: 12 kWp

Dachfläche 1: Hauptdach Süd
  - Neigung: 35°
  - Ausrichtung: 180° (Süd)
  - Anteil: 8 kWp (67%)

Dachfläche 2: Garagendach West
  - Neigung: 15°
  - Ausrichtung: 270° (West)
  - Anteil: 4 kWp (33%)
```

### Beispiel 3: Pultdach mit Süd-Ost + Süd-West
```
Gesamt-System: 9 kWp

Dachfläche 1: Süd-Ost
  - Neigung: 30°
  - Ausrichtung: 135° (Süd-Ost)
  - Anteil: 4.5 kWp (50%)

Dachfläche 2: Süd-West
  - Neigung: 30°
  - Ausrichtung: 225° (Süd-West)
  - Anteil: 4.5 kWp (50%)
```

## 🔄 Ablauf im Simulator

### Schritt 1: Gesamt-kWp eingeben
```
☀️  PV-SYSTEM:
   Gesamt PV-Systemgröße in kWp (z.B. 10): 10
   Systemwirkungsgrad (z.B. 0.8 für 80%): 0.8
```

### Schritt 2: Erste Dachfläche (Pflicht)
```
   🏠 DACHFLÄCHE 1:
      Neigung in Grad (z.B. 30): 30
      Ausrichtung (0°=Nord, 90°=Ost, 180°=Süd, 270°=West): 180
      Anteil in kWp (Enter für alle 10 kWp): 6
```

### Schritt 3: Weitere Dachfläche? (Optional)
```
   Weitere Dachfläche hinzufügen? (j/n): j
   
   🏠 DACHFLÄCHE 2:
      Neigung in Grad: 30
      Ausrichtung (0°=Nord, 90°=Ost, 180°=Süd, 270°=West): 90
      Verbleibend: 4.00 kWp
      Anteil in kWp (Enter für alle 4.00 kWp): [Enter]
```

### Schritt 4: Zusammenfassung
```
   📊 ZUSAMMENFASSUNG:
      Dachfläche 1: 30°/180°, 6.0 kWp (60.0%)
      Dachfläche 2: 30°/90°, 4.0 kWp (40.0%)
      Gesamt: 10.0 kWp
```

## ⚡ Wie werden die Produktionen kombiniert?

### Für jede Dachfläche separat:
1. PVGIS-Daten holen (für spezifische Tilt/Azimuth)
2. 15-Minuten-Intervalle berechnen
3. PV-Energie = kWp × Einstrahlung × Effizienz

### Dann kombiniert:
```
Gesamt-Produktion pro 15-Min = 
    Dachfläche 1 Produktion +
    Dachfläche 2 Produktion +
    ...
```

## 📊 Beispiel-Rechnung (12:00 Mittag)

**Ost-West-Dach (10 kWp gesamt):**

| Zeit | Ost (5 kWp) | West (5 kWp) | Gesamt |
|------|-------------|--------------|--------|
| 08:00 | 1.2 kWh | 0.3 kWh | 1.5 kWh |
| 12:00 | 0.8 kWh | 0.8 kWh | 1.6 kWh |
| 16:00 | 0.3 kWh | 1.2 kWh | 1.5 kWh |

**Vorteil:** Gleichmäßigere Produktion über den Tag!

## 🆚 Einzeldach vs. Multi-Dach

### Reines Süd-Dach (10 kWp):
```
Mittags-Spitze: 3.0 kWh pro 15 Min
Morgens/Abends: 0.5 kWh pro 15 Min
→ Hohe Spitzen, Speicher wird schnell voll
```

### Ost-West-Dach (2×5 kWp):
```
Mittags-Plateau: 1.8 kWh pro 15 Min
Morgens/Abends: 1.2 kWh pro 15 Min
→ Flachere Kurve, bessere Eigenverbrauchsquote!
```

## ⚙️ Technische Details

### Cache-Verwaltung
Jede Dachflächen-Konfiguration wird separat gecached:
```
pvgis_48.48_8.93_30_180_2023.pkl  ← Süd-Dach
pvgis_48.48_8.93_30_90_2023.pkl   ← Ost-Dach
pvgis_48.48_8.93_25_270_2023.pkl  ← West-Dach (andere Neigung!)
```

Beim zweiten Durchlauf: Alle Daten aus Cache → schnell!

### Strahlungswerte in der Ausgabe
```
Sonneneinstrahlung_W_m2 = Gewichteter Durchschnitt aller Dachflächen
Einstrahlung_15min_Wh_m2 = Gewichteter Durchschnitt aller Dachflächen
PV_Energie_kWh = Summe aller Dachflächen ✅
```

## ✅ Vorteile

1. **Realistischer:** Meiste Häuser haben mehrere Dachseiten
2. **Genauer:** Berücksichtigt tatsächliche Dachgeometrie
3. **Flexibel:** Beliebig viele Dachflächen möglich
4. **Optimiert:** Zeigt Vorteil von Ost-West vs. nur Süd

## 💡 Tipps

### Verteilung festlegen
- **Gleichmäßig:** Ost-West je 50%
- **Süd-dominant:** 70% Süd, 30% Ost/West
- **Nach Dachgröße:** Größeres Dach = mehr kWp

### Wann mehrere Dachflächen sinnvoll?
✅ Ost-West-Dächer (Satteldach)
✅ Hauptdach + Garage/Anbau
✅ Pultdach mit zwei Richtungen
✅ L-förmiges Gebäude

### Wann eine Dachfläche ausreicht?
- Reines Süd-Dach
- Flachdach (alle Module gleich ausgerichtet)
- Sehr kleine Anlagen

## 🔜 Verwendung für Testszenarien

Du kannst jetzt realistische Multi-Dach-Szenarien erstellen:

**Szenario 7 (Beispiel):** Ost-West Satteldach
```
Gesamt: 10 kWp
Dachfläche 1: 30°/90° (Ost), 5 kWp
Dachfläche 2: 30°/270° (West), 5 kWp
→ Zeigt: Bessere Eigenverbrauchsquote trotz geringerem Gesamtertrag
```



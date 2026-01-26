# Tabellenstruktur - Energy System Simulator

## 📊 Neue Spalten-Struktur

Die CSV-Tabelle enthält jetzt **detaillierte Einstrahlungs- und Produktionsdaten** für jede Dachfläche.

### Bei 2 Dachflächen (Ost-West-Dach):

```csv
Datum,Uhrzeit,
Strahlung_Dach1_W,Einstrahlung_Dach1_Wh,PV_Dach1_kWh,
Strahlung_Dach2_W,Einstrahlung_Dach2_Wh,PV_Dach2_kWh,
Gesamt_Strahlung_W,Gesamt_Einstrahlung_Wh,PV_Gesamt_kWh,
Verbrauch_kWh,Speicher_kWh,Netz_kWh
```

### Spalten-Erklärung:

#### Für jede Dachfläche (wiederholt sich):
1. **Strahlung_DachX_W** - Strahlungsleistung die auf alle Module dieser Dachfläche trifft (W)
2. **Einstrahlung_DachX_Wh** - Energie über 15 Min auf alle Module dieser Dachfläche (Wh)
3. **PV_DachX_kWh** - Produzierte Energie dieser Dachfläche (kWh)

#### Gesamt (Summe aller Dachflächen):
4. **Gesamt_Strahlung_W** - Summe Strahlungsleistung auf ALLE Module (W)
5. **Gesamt_Einstrahlung_Wh** - Summe Energie über 15 Min auf ALLE Module (Wh)
6. **PV_Gesamt_kWh** - Summe produzierte Energie ALLER Dachflächen (kWh)

#### System:
7. **Verbrauch_kWh** - Haushaltsverbrauch in 15 Min (kWh)
8. **Speicher_kWh** - Batterie-Füllstand (kWh)
9. **Netz_kWh** - Netzinteraktion (positiv=Einspeisung, negativ=Bezug)

## 💡 Beispiel-Zeile (12:00 Mittag, Ost-West-Dach)

### Konfiguration:
- **Dachfläche 1 (Süd):** 30°/180°, 20 Module à 450 Wp, 40 m²
- **Dachfläche 2 (Ost):** 30°/90°, 10 Module à 450 Wp, 20 m²
- **Gesamt:** 30 Module, 13.5 kWp

### Beispiel-Werte um 12:00:

```csv
01.06.2023,12:00,
16000,4000,3.2,    ← Dach 1 (Süd): 16kW Strahlung → 4kWh Einstrahlung → 3.2 kWh produziert
8000,2000,1.6,     ← Dach 2 (Ost): 8kW Strahlung → 2kWh Einstrahlung → 1.6 kWh produziert  
24000,6000,4.8,    ← Gesamt: 24kW → 6kWh → 4.8 kWh
0.3,8.5,+4.2       ← Verbrauch 0.3, Speicher 8.5 kWh, Netz +4.2 kWh Einspeisung
```

## 🔍 Analyse-Möglichkeiten

### 1. Vergleich Dachflächen
```
Mittags (12:00): Süd produziert 3.2 kWh, Ost nur 1.6 kWh
Morgens (08:00): Ost produziert 2.0 kWh, Süd nur 1.5 kWh
→ Zeigt Vorteil von Ost-West-Verteilung!
```

### 2. Einstrahlung vs. Produktion
```
Gesamt_Einstrahlung_Wh: 6000 Wh
PV_Gesamt_kWh: 4.8 kWh = 4800 Wh
Wirkungsgrad: 4800 / 6000 = 80% ✓
```

### 3. Wann ist welches Dach produktiv?
```
Morgens: Ost-Dach >> Süd-Dach
Mittags: Süd-Dach ≈ Ost-Dach  
Abends: West-Dach >> Süd-Dach (falls vorhanden)
```

## 📈 Spalten-Anzahl bei verschiedenen Konfigurationen

| Dachflächen | Spalten Einstrahlung | Spalten PV | Gesamt-Spalten |
|-------------|---------------------|------------|----------------|
| 1 | 2 + 2 = 4 | 1 + 1 = 2 | 11 |
| 2 | 4 + 2 = 6 | 2 + 1 = 3 | 14 |
| 3 | 6 + 2 = 8 | 3 + 1 = 4 | 17 |

**Legende:**
- Einzel-Dach-Spalten: Strahlung_W + Einstrahlung_Wh pro Dach
- Gesamt-Spalten: Gesamt_Strahlung_W + Gesamt_Einstrahlung_Wh
- PV-Spalten: PV_DachX_kWh pro Dach + PV_Gesamt_kWh
- Basis: Datum, Uhrzeit, Verbrauch, Speicher, Netz (5 Spalten)

## 🎯 Vorteile der neuen Struktur

1. ✅ **Vollständige Transparenz** - Jede Dachfläche einzeln sichtbar
2. ✅ **Vergleichbarkeit** - Direkt Ost vs. West vs. Süd vergleichen
3. ✅ **Validierung** - Gesamt = Summe aller Einzelwerte
4. ✅ **Analyse** - Optimale Dach-Verteilung erkennbar
5. ✅ **Korrekt** - Gesamt-Werte für Speicher-Simulation

## 💾 CSV-Beispiel (Kopfzeile bei Ost-West-Dach)

```
Datum,Uhrzeit,
Strahlung_Dach1_W,Einstrahlung_Dach1_Wh,PV_Dach1_kWh,
Strahlung_Dach2_W,Einstrahlung_Dach2_Wh,PV_Dach2_kWh,
Gesamt_Strahlung_W,Gesamt_Einstrahlung_Wh,PV_Gesamt_kWh,
Verbrauch_kWh,Speicher_kWh,Netz_kWh
```

**Perfekt für detaillierte Analyse und Optimierung!** 📊

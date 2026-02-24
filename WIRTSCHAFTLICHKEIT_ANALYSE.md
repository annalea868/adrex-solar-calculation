# Wirtschaftlichkeitsberechnung - Analyse & Planung

## 📊 Ziel: Alle Werte aus dem Übersichtsblatt berechnen

---

## ✅ Was der Simulator BEREITS liefert (NICHT neu berechnen!)

### Aus energy_system_simulator_local_poa.py:

**System-Konfiguration:**
- ✅ PV Größe (kWp) - aus Modul-Berechnung
- ✅ Modultyp - User-Input
- ✅ Anzahl Module - berechnet aus Dachfläche
- ✅ Kapazität (kWh) - aus Batterie-Auswahl
- ✅ Speichertyp - User-Input
- ✅ Anzahl Batteriemodule - berechnet

**Energie-Daten (aus Simulation):**
- ✅ **Jahresertrag [kWh/a]** - `total_pv_production` aus Summary
- ✅ **Verbrauch Hausstrom [kWh/a]** - aus Haushaltsprofil (skaliert)
- ✅ **Verbrauch Wärmepumpe [kWh/a]** - User-Input (skaliert)
- ✅ **Verbrauch E-Auto [kWh/a]** - berechnet aus km/Jahr
- ✅ **Gesamtverbrauch [kWh/a]** - Summe aller Verbraucher
- ✅ **Eigenstrom Hausstrom [kWh/a]** - aus Simulation (Haushalt-Array)
- ✅ **Eigenstrom Wärmepumpe [kWh/a]** - aus Simulation (WP-Array)
- ✅ **Eigenstrom E-Auto [kWh/a]** - aus Simulation (E-Auto-Array)
- ✅ **Netzeinspeisung [kWh/a]** - `total_grid_feed_in` aus Summary
- ✅ **Netzbezug [kWh/a]** - `total_grid_draw` aus Summary

---

## ❌ Was NOCH FEHLT (muss berechnet werden!)

### A) Ertrags- und Leistungskennzahlen:

1. **Spezifischer Ertrag [kWh/kWp/a]**
   - Formel: `Jahresertrag / PV-Größe`
   - Beispiel: 21.150 / 22,5 = 940 kWh/kWp/a

### B) User-Inputs (Preise & Laufzeit):

2. **Aktueller Strompreis [€/kWh]** - User-Input
3. **Preissteigerungsrate [%/a]** - User-Input (z.B. 4%)
4. **Inflation [%/a]** - User-Input (z.B. 3%)
5. **Aktueller Kraftstoffpreis [€/L]** - User-Input (für E-Auto)
6. **Laufzeit [Jahre]** - User-Input (z.B. 20)

### C) Eigenverbrauchs- und Autarkie-Quoten:

7. **Eigenverbrauch Hausstrom [%]**
   - Formel: `(Eigenstrom_Haus / Jahresertrag) × 100`
   - Beispiel: (2.400 / 21.150) × 100 = 11,35%

8. **Eigenverbrauch Wärmepumpe [%]**
   - Formel: `(Eigenstrom_WP / Jahresertrag) × 100`

9. **Eigenverbrauch E-Auto [%]**
   - Formel: `(Eigenstrom_ECar / Jahresertrag) × 100`

10. **Gesamteigenverbrauch [%]**
    - Formel: `((Eigenstrom_Haus + Eigenstrom_WP + Eigenstrom_ECar) / Jahresertrag) × 100`

11. **Autarkie Hausstrom [%]** (max 80%)
    - Formel: `(Eigenstrom_Haus / Verbrauch_Haus) × 100`
    - Beispiel: (2.400 / 3.000) × 100 = 80,0%
    - WICHTIG: Auf 80% begrenzt!

12. **Autarkie Wärmepumpe [%]** (max 55%)
    - Formel: `(Eigenstrom_WP / Verbrauch_WP) × 100`
    - WICHTIG: Auf 55% begrenzt!

13. **Autarkie E-Auto [%]**
    - Formel: `(Eigenstrom_ECar / Verbrauch_ECar) × 100`

14. **Gesamtautarkie [%]** (max 80%)
    - Formel: `((Eigenstrom_Gesamt) / Verbrauch_Gesamt) × 100`
    - WICHTIG: Auf 80% begrenzt!

### D) Wirtschaftlichkeits-Kennzahlen:

15. **Invest netto [€]**
    - Aus Preiskalkulation (PV-System + Speicher + Installation)
    - ODER: User-Input

16. **Jährliche Ersparnis [€/a]**
    - Formel: `Eigenstrom_Gesamt × aktueller_Strompreis`
    - ABER: Berücksichtigt Preissteigerung über Laufzeit!
    - → Durchschnittlicher Strompreis über Laufzeit nötig

17. **Durchschnittlicher Strompreis über Laufzeit [€/kWh]**
    - Formel aus CALCULATION.pdf:
    ```
    ø_Strompreis = aktueller_Preis × ((1 + Preissteigerung)^Laufzeit - 1) / (Preissteigerung × Laufzeit)
    ```

18. **Jährliche Vergütung [€/a]**
    - Formel: `Netzeinspeisung × Einspeisevergütung`
    - Einspeisevergütung: aktuell ca. 0,08 €/kWh (User-Input oder Konstante)
    - ABER: Berücksichtigt Änderungen über Laufzeit!

19. **Gesamtvorteil [€]** (über Laufzeit)
    - Formel: `(Jährl. Ersparnis + Jährl. Vergütung) × Laufzeit - Invest_netto`
    - ODER genauer: NPV-Berechnung mit Inflation

20. **Rendite [%/a]**
    - Eigenkapitalrendite
    - Formel aus CALCULATION.pdf (interner Zinsfuß)

21. **Stromentstehungskosten [€/kWh]**
    - Formel: `Invest_netto / (Jahresertrag × Laufzeit)`
    - Beispiel: 37.700 / (21.150 × 20) = 0,089 €/kWh
    - BESSER: Berücksichtigt Wartung, Degradation

22. **Amortisationszeit [Jahre]**
    - Formel: `Invest_netto / (Jährl. Ersparnis + Jährl. Vergütung)`
    - ABER: Dynamisch mit Preissteigerung!

### E) Finanzierungs-Tabelle (Optional):

23. **Laufzeit-Tabelle** (5, 10, 15, 20 Jahre)
    - Eff. Jahreszinssatz [%]
    - Mtl. Zahlung inkl. Gebühren [€]
    - → Benötigt Finanzierungsparameter (Zinssatz, Gebühren)

---

## 🔧 Formeln aus CALCULATION.pdf (die wir brauchen)

### 1. Spezifischer Ertrag (Seite 1)
```
Spezifischer_Ertrag = Jahresertrag / PV_Leistung
```
**Hinweis:** Max. 940 kWh/kWp begrenzt

### 2. Eigenverbrauchsquote (Seite 3)
```
EV_Quote = (Eigenstrom / PV_Ertrag) × 100
```

### 3. Autarkiegrad (Seite 3)
```
Autarkie = (Eigenstrom / Verbrauch) × 100
```
**Limits:**
- Haushalt: max. 80%
- Wärmepumpe: max. 55%
- Gesamt: max. 80%

### 4. Durchschnittlicher Strompreis (aus CALCULATION.pdf Seite 6)
```
ORIGINAL-FORMEL:
Preis_1 = aktueller Strompreis
Preis_i+1 = Preis_i × (1 + (Preissteigerung + Inflation)/100)
Summe_Kosten = Σ(Verbrauch_Jahr × Preis_i) für i=1..Laufzeit
durchschn. Strompreis = Summe_Kosten / (Verbrauch_Jahr × Laufzeit)

IMPLEMENTIERT (genau):
Jahr für Jahr berechnen mit Preissteigerung + Inflation
```

### 5. Einspeisevergütung (aus CALCULATION.pdf Seite 5)
```
ORIGINAL-FORMEL (stufenweise):
- Bis 10 kWp: 0,0803 €/kWh
- 10-40 kWp: 0,0695 €/kWh  
- 40-100 kWp: 0,0568 €/kWh

Gewichtete Berechnung:
Vergütungssatz = (P/10 × 0,0803) + ((P-10)/P × 0,0695)  [für P < 40 kWp]

IMPLEMENTIERT:
Stufenweise Berechnung je nach PV-Größe
```

### 6. Jährliche Ersparnis (aus CALCULATION.pdf Seite 6)
```
ORIGINAL-FORMEL:
Ersparnis/Jahr = Eigenverbrauch_gesamt × durchschnittlicher Strompreis

IMPLEMENTIERT (genau wie Original):
Mit dynamischem Durchschnittspreis über Laufzeit
```

### 7. Jährliche Vergütung (aus CALCULATION.pdf Seite 5)
```
ORIGINAL-FORMEL:
Vergütung/Jahr = (PV-Ertrag - Eigenverbrauch_gesamt) × Vergütungssatz
               = Netzeinspeisung × Vergütungssatz

IMPLEMENTIERT (genau wie Original):
Mit gestuftem Vergütungssatz
```

### 8. Gesamtvorteil (aus CALCULATION.pdf Seite 6)
```
ORIGINAL-FORMEL:
Gesamtvorteil = (Ersparnis/Jahr + Vergütung/Jahr) × Laufzeit

IMPLEMENTIERT (genau wie Original):
Einfache Summe ohne Barwertberechnung
```

### 9. Rendite (aus CALCULATION.pdf Seite 6)
```
ORIGINAL-FORMEL:
ROI = ((Gesamtvorteil - Investition × (1 - Restwertfaktor)) / Investition) / Laufzeit × 100
Restwertfaktor = 0,8 (20% Restwert nach Laufzeit)

IMPLEMENTIERT (genau wie Original):
Mit Restwertfaktor 0,8
```

### 10. Stromentstehungskosten (aus CALCULATION.pdf Seite 6)
```
ORIGINAL-FORMEL:
LCOE = Investition / (Jahresertrag × Laufzeit)

IMPLEMENTIERT (genau wie Original):
Ohne Degradation (wie im PDF)
```

### 11. Amortisationszeit (aus CALCULATION.pdf Seite 6)
```
ORIGINAL-FORMEL:
Amortisation = Investition / (Ersparnis/Jahr + Vergütung/Jahr)

IMPLEMENTIERT (genau wie Original):
Einfache statische Berechnung
```

---

## 📋 Zusammenfassung

### ✅ Vom Simulator (nicht neu berechnen):
- Jahresertrag (kWh)
- Alle Verbrauchswerte (kWh)
- Eigenstrom für jeden Verbraucher (kWh)
- Netzeinspeisung (kWh)
- Netzbezug (kWh)

### ❌ Neu zu berechnen:
1. **Einfache Berechnungen:**
   - Spezifischer Ertrag (Division)
   - Eigenverbrauchsquoten (%) - aus Simulationsdaten
   - Autarkiegrade (%) - aus Simulationsdaten

2. **User-Inputs:**
   - Strompreis, Preissteigerung, Inflation, Laufzeit
   - Einspeisevergütung
   - Investitionskosten

3. **Wirtschaftlichkeit:**
   - Durchschnittlicher Strompreis über Laufzeit
   - Jährliche Ersparnis (dynamisch)
   - Jährliche Vergütung (dynamisch)
   - Gesamtvorteil (NPV)
   - Rendite (IRR oder vereinfacht)
   - Stromentstehungskosten (LCOE)
   - Amortisationszeit (dynamisch)

4. **Optional:**
   - Finanzierungsrechnung (Raten, Zinsen)

---

## 🎯 Nächste Schritte

1. ✅ Diese Analyse prüfen
2. 🔄 Neue Datei erstellen: `wirtschaftlichkeit.py`
3. 🔄 Input-Parameter definieren
4. 🔄 Berechnungsfunktionen implementieren
5. 🔄 Integration mit Simulator-Ergebnissen
6. 🔄 Output-Format festlegen

# Parameter-Erklärung für Solar Irradiation Calculator

## 📊 Ausgabe-Parameter der CSV-Tabelle

### **1. Strahlung_W_m2** ⭐ HAUPTWERT
**Was ist das?**
- Momentane Strahlungsleistung zum Zeitpunkt
- Die Leistung die auf 1 Quadratmeter Panel fällt

**Einheit:** W/m² (Watt pro Quadratmeter)

**Beispiel:** 400 W/m² bedeutet 400 Watt Leistung pro m²

**Für PV-Formel:** ✅ **JA - Das ist das G in der Formel!**
```
E = P_system × (G/1000) × η_system × t
              ↑
         Strahlung_W_m2
```

---

### **2. Einstrahlung_15min_Wh_m2**
**Was ist das?**
- Gesamte Energie die in 15 Minuten ankommt
- Strahlung_W_m2 × 0.25 Stunden

**Einheit:** Wh/m² (Wattstunden pro Quadratmeter)

**Beispiel:** 400 W/m² × 0.25h = 100 Wh/m²

**Für PV-Formel:** ℹ️ Hilfswert für Verständnis, nicht direkt verwendet

---

### **3. PV_Energie_kWh** ⭐ ERGEBNIS
**Was ist das?**
- Die tatsächlich produzierte Energie deiner PV-Anlage
- Berechnet mit der Core Formula

**Einheit:** kWh (Kilowattstunden)

**Berechnung:**
```
PV_Energie_kWh = P_system × (Strahlung_W_m2/1000) × η_system × 0.25
```

**Beispiel:** 10 kW × (400/1000) × 0.8 × 0.25 = 0.8 kWh

**Für Simulation:** ✅ **DAS brauchst du für Storage-Simulation!**

---

### **4. Direkte_Strahlung_W_m2** (Detail)
**Was ist das?**
- Nur die direkten Sonnenstrahlen
- Ohne Wolken-Streuung

**Einheit:** W/m²

**Info:** Teil von Strahlung_W_m2
```
Strahlung_W_m2 = Direkte + Diffuse + Reflexion
```

**Für PV-Formel:** ℹ️ Bereits in Strahlung_W_m2 enthalten

---

### **5. Diffuse_Strahlung_W_m2** (Detail)
**Was ist das?**
- Gestreutes Licht vom Himmel
- Durch Wolken und Atmosphäre gestreut

**Einheit:** W/m²

**Wichtig:** An bewölkten Tagen ist fast alles diffus!

**Für PV-Formel:** ℹ️ Bereits in Strahlung_W_m2 enthalten

---

### **6. Reflexion_W_m2** (Detail)
**Was ist das?**
- Vom Boden reflektiertes Licht
- Besonders wichtig bei Schnee oder hellen Flächen

**Einheit:** W/m²

**Typisch:** 2-5% der Gesamt-Strahlung (bei Schnee bis 20%)

**Für PV-Formel:** ℹ️ Bereits in Strahlung_W_m2 enthalten

---

### **7. Temperatur_C** (Zusatzinfo)
**Was ist das?**
- Lufttemperatur zum Zeitpunkt

**Einheit:** °C (Grad Celsius)

**Wichtig:** Höhere Temperatur = geringere PV-Effizienz!

**Für PV-Formel:** ℹ️ Optional für erweiterte Berechnung (T_effect)

---

### **8. Windgeschwindigkeit_m_s** (Zusatzinfo)
**Was ist das?**
- Windgeschwindigkeit

**Einheit:** m/s (Meter pro Sekunde)

**Wichtig:** Wind kühlt Panels = bessere Effizienz

**Für PV-Formel:** ℹ️ Optional für Kühlungseffekt

---

## 🎯 Zusammenfassung für deine Simulation

### **Für einfache Energie-Berechnung brauchst du:**
1. **Strahlung_W_m2** → Das G in der Formel
2. **PV_Energie_kWh** → Direkt verwendbar!

### **Die anderen Werte sind:**
- **Komponenten** (Direkt, Diffuse, Reflexion): Zur Info wie sich Strahlung zusammensetzt
- **Zusatzinfo** (Temperatur, Wind): Für erweiterte Modelle

### **Beispiel-Zeile erklärt:**
```
04:00  |  104.64 W/m²  |  26.16 Wh/m²  |  0.2093 kWh
       ↓                ↓                ↓
   Momentan-         Energie in      PV produziert
   Leistung         15 Minuten       in 15 Min
```

**Für Storage-Simulation nutze:** `PV_Energie_kWh` Spalte!

Diese Werte kannst du direkt mit deinen Verbrauchsdaten (auch 15-Minuten-Intervalle) matchen.



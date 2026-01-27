# Lokale POA-Berechnung - Unterschiede

## 📊 Zwei Versionen des Simulators:

### **Version 1:** `energy_system_simulator.py` (Original)
**Methode:** POA direkt von PVGIS holen

**Ablauf:**
```
Für jede Dachfläche:
  → PVGIS API-Call (Tilt + Azimuth spezifisch)
  → Bekommt fertige POA-Daten
  → Keine lokale Berechnung nötig
```

**Vorteile:**
- ✅ Sehr genau (PVGIS berücksichtigt Horizont, Atmosphäre)
- ✅ Einfacher Code
- ✅ Bewährte Methode

**Nachteile:**
- ❌ 1 API-Call pro Dachflächen-Konfiguration
- ❌ Timeouts möglich bei vielen Konfigurationen
- ❌ Braucht Internet

---

### **Version 2:** `energy_system_simulator_local_poa.py` (Neu)
**Methode:** GHI holen, dann lokal POA berechnen

**Ablauf:**
```
Einmal pro Location:
  → PVGIS API-Call (nur horizontal/GHI)
  → Cache lokal

Für jede Dachfläche:
  → Berechne Sonnenposition (lokal, pvlib)
  → GHI → DNI/DHI zerlegen (lokal, Erbs-Modell)
  → POA berechnen (lokal, pvlib.irradiance)
```

**Vorteile:**
- ✅ Nur 1 API-Call pro Location (nicht pro Dachfläche!)
- ✅ Beliebig viele Dachflächen ohne neue API-Calls
- ✅ Schneller für Multi-Roof Szenarien
- ✅ Funktioniert offline nach erstem Download

**Nachteile:**
- ⚠️ Etwas weniger genau (kein Horizont, vereinfachtes Modell)
- ⚠️ Komplexerer Code

---

## 🔄 Beispiel-Vergleich:

### **Szenario:** Ost-West-Dach (2 Flächen)

**Original-Version:**
```
API-Call 1: POA für 30°/90° (Ost)   → 30-60s
API-Call 2: POA für 30°/270° (West) → 30-60s
────────────────────────────────────────────
Gesamt: 2 API-Calls, 60-120s
```

**Local-POA-Version:**
```
API-Call 1: GHI (horizontal)         → 30-60s
Lokal: POA für 30°/90° berechnen     → <1s
Lokal: POA für 30°/270° berechnen    → <1s
────────────────────────────────────────────
Gesamt: 1 API-Call, ~30-60s
```

**Bei 3 Dachflächen:**
- Original: 3 API-Calls, 90-180s
- Local: 1 API-Call, ~30-60s

**Bei 5 Dachflächen:**
- Original: 5 API-Calls, 150-300s (Timeout-Risiko!)
- Local: 1 API-Call, ~30-60s

---

## 📈 Genauigkeits-Vergleich:

| Aspekt | Original (PVGIS direkt) | Local (GHI → POA) |
|--------|------------------------|-------------------|
| Sonnenposition | PVGIS intern | pvlib (gleich gut) |
| Horizont-Verschattung | ✅ Berücksichtigt | ❌ Nicht berücksichtigt |
| Atmosphäre | ✅ PVGIS-Modell | ⚠️ Erbs-Modell (einfacher) |
| Boden-Reflexion | ✅ Automatisch | ⚠️ Fix 20% (albedo=0.2) |
| DNI/DHI Zerlegung | ✅ PVGIS-Daten | ⚠️ Erbs-Schätzung |

**Genauigkeits-Unterschied:** ~2-5% (Local meist etwas niedriger)

---

## 🎯 Wann welche Version?

### **Verwende Original** (`energy_system_simulator.py`):
- ✅ Maximale Genauigkeit wichtig
- ✅ Wenige Dachflächen (1-2)
- ✅ Stabile Internetverbindung
- ✅ Produktions-Umgebung

### **Verwende Local-POA** (`energy_system_simulator_local_poa.py`):
- ✅ Viele verschiedene Dachkonfigurationen testen
- ✅ Multi-Roof Szenarien (3+ Flächen)
- ✅ Offline-Entwicklung gewünscht
- ✅ API-Timeouts vermeiden

---

## 💡 Empfehlung für deine Validierung:

**Nutze die Original-Version:**
- Deine 7 Testszenarien haben 1-2 Dachflächen
- Genauigkeit ist wichtig für Validierung
- Cache macht es nach dem ersten Mal schnell

**Nutze Local-POA für:**
- Experimentieren mit vielen Konfigurationen
- Ost-West-Süd 3-Flächen-Tests
- Entwicklung ohne Internet

Beide Versionen sind jetzt verfügbar! 🚀

# PLZ-Geocoding - Lokale Datenbank

## ✅ Unterstützte Eingabe-Formate

Die beiden Simulatoren akzeptieren:
1. **Vollständige Adressen** (HubSpot-Format): `"Dudenstraße 80, 10965 Berlin, Deutschland"`
2. **Nur PLZ**: `"10965"`
3. **Koordinaten** (wie vorher): `"52.5"` + Längengrad-Eingabe

## 📦 PLZ-Datenbank

Die deutsche PLZ-Datenbank ist **im Repository enthalten** (`plz_data/`):
```
plz_data/
├── DE.txt         (2.3 MB) - Alle deutschen PLZ mit Koordinaten
├── DE-index.txt   (1.3 MB) - Index für schnellen Zugriff
└── README.md      - Dokumentation
```

**Größe:** 3.6 MB gesamt  
**Quelle:** Erstellt mit [pgeocode](https://github.com/symerio/pgeocode) (Daten von GeoNames)  
**Abdeckung:** ~8000 deutsche Postleitzahlen

### Automatische Verwendung

Die Simulatoren kopieren diese Dateien automatisch beim ersten Start 
in den pgeocode Cache (`~/.cache/pgeocode/`). 

**Kein Setup erforderlich** - funktioniert sofort nach `git clone`!

## 🎯 Verwendung im Simulator

### Input-Beispiele beim Start:

**1. HubSpot-Adresse** (aus Deal):
```
📍 STANDORT:
   Eingabe: Dudenstraße 80, 10965 Berlin, Deutschland
   ✅ PLZ 10965 gefunden: 52.4855°N, 13.3946°E
```

**2. Nur PLZ**:
```
📍 STANDORT:
   Eingabe: 72108
   ✅ PLZ 72108 gefunden: 48.4796°N, 8.9500°E
```

**3. Koordinaten** (direkte Eingabe):
```
📍 STANDORT:
   Eingabe: 52.5
   Längengrad: 13.4
   ✅ Koordinaten: 52.5000°N, 13.4000°E
```

## 🔧 Technische Implementierung

### Funktionen in beiden Simulatoren:

**`extract_plz_from_address(address_string)`**  
Extrahiert deutsche PLZ (5 Ziffern) aus beliebigem Text mit Regex-Pattern `\b(\d{5})\b`.

**`plz_to_coordinates(plz_or_address)`**  
Konvertiert PLZ oder Adresse zu Koordinaten. Verwendet die lokale pgeocode-Datenbank.

**`_setup_pgeocode()`**  
Kopiert automatisch die PLZ-Dateien aus `plz_data/` in den pgeocode Cache.

## 📊 Vorteile

**Gegenüber alter Lösung (hardcodiertes Dictionary):**
- ✅ **8000+ PLZ** statt nur 10 Städte
- ✅ **Adress-Extraktion** (HubSpot-Integration)
- ✅ **Vollständig offline** - keine API-Calls
- ✅ **Keine Wartung** nötig
- ✅ **< 0.1 Sekunden** pro Lookup

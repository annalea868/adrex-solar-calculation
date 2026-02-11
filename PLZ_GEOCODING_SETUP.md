# PLZ-Geocoding mit pgeocode - Setup & Verwendung

## ✅ Was wurde implementiert?

Die beiden Simulatoren unterstützen jetzt:
1. **Vollständige Adressen** (HubSpot-Format): `"Dudenstraße 80, 10965 Berlin, Deutschland"`
2. **Nur PLZ**: `"10965"`
3. **Koordinaten** (wie vorher): `"52.5"` + Längengrad-Eingabe

## 🔧 Technische Details

### Neue Funktionen in beiden Simulatoren:

#### 1. `extract_plz_from_address(address_string)`
Extrahiert deutsche PLZ (5 Ziffern) aus beliebigem Text.

**Beispiele:**
- `"Dudenstraße 80, 10965 Berlin, Deutschland"` → `"10965"`
- `"72108"` → `"72108"`
- `"München 80331, Germany"` → `"80331"`

#### 2. `plz_to_coordinates(plz_or_address)`
Konvertiert PLZ oder Adresse zu Koordinaten mit **pgeocode**.

**Vorteile:**
- ✅ Offline (nach erstem Download)
- ✅ Alle deutschen PLZ (~8000+)
- ✅ Keine API-Keys nötig
- ✅ Keine Rate-Limits
- ✅ Sehr schnell

## 📦 Installation

```bash
pip3 install -r requirements.txt
```

Das ist alles! Die PLZ-Datenbank ist bereits im Repository enthalten.

## ✅ Lokale PLZ-Datenbank (NEU!)

Die deutsche PLZ-Datenbank (~3.6 MB) ist jetzt **im Repository enthalten**:
```
plz_data/
├── DE.txt         (2.3 MB)
└── DE-index.txt   (1.3 MB)
```

**Vorteile:**
- ✅ **Kein Internet-Download** beim Setup
- ✅ **Kein SSL-Problem** (keine Zertifikate nötig)
- ✅ **Sofort einsatzbereit** nach Git Clone
- ✅ **Funktioniert offline** von Anfang an

Die Simulatoren kopieren diese Dateien automatisch beim ersten Start 
in den pgeocode Cache (`~/.cache/pgeocode/`).

## 🧪 Test

Nach der Installation kannst du die Funktion testen:

```python
import pgeocode

nomi = pgeocode.Nominatim('de')
result = nomi.query_postal_code("10965")

print(f"Breitengrad: {result.latitude}")   # 52.5003
print(f"Längengrad: {result.longitude}")   # 13.3889
print(f"Stadt: {result.place_name}")       # Berlin
```

## 📋 Verwendung im Simulator

### Input-Beispiele:

1. **HubSpot-Adresse** (aus Deal):
   ```
   Eingabe: Dudenstraße 80, 10965 Berlin, Deutschland
   → PLZ 10965 gefunden: 52.5003°N, 13.3889°E
   ```

2. **Nur PLZ**:
   ```
   Eingabe: 72108
   → PLZ 72108 gefunden: 48.4800°N, 8.9300°E
   ```

3. **Koordinaten** (wie vorher):
   ```
   Eingabe: 52.5
   Längengrad: 13.4
   → Koordinaten: 52.5000°N, 13.4000°E
   ```

## 🗂️ Geänderte Dateien

1. **requirements.txt** - `pgeocode>=0.4.0` hinzugefügt
2. **energy_system_simulator.py** - PLZ-Extraktion implementiert
3. **energy_system_simulator_local_poa.py** - PLZ-Extraktion implementiert

## 🎯 Workflow für Adrex-Mitarbeiter

1. HubSpot Deal auswählen
2. Adresse wird automatisch eingefügt (z.B. "Dudenstraße 80, 10965 Berlin, Deutschland")
3. Python-Script extrahiert PLZ automatisch ("10965")
4. pgeocode liefert Koordinaten (52.5003°N, 13.3889°E)
5. GHI-Daten aus lokalem Grid werden verwendet
6. Simulation läuft!

## 📊 Performance

- **Erste Verwendung:** ~2-5 Sekunden (Download der Datenbank)
- **Danach:** < 0.1 Sekunden pro PLZ-Lookup (offline!)
- **Datenbank-Größe:** ~2 MB (wird in `~/.cache/pgeocode/` gespeichert)

## ✅ Vorteile gegenüber der alten Lösung

**Alt (hardcodiertes Dictionary):**
- ❌ Nur 10 Städte
- ❌ Manuell gepflegt
- ❌ Keine Adress-Unterstützung

**Neu (pgeocode):**
- ✅ 8000+ deutsche PLZ
- ✅ Automatisch aktuell
- ✅ Adress-Extraktion
- ✅ Offline & schnell
- ✅ Keine Wartung nötig

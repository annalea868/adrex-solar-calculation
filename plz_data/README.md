# PLZ-Datenbank (Deutsche Postleitzahlen)

Dieser Ordner enthält die lokale PLZ-Datenbank für Deutschland.

## 📁 Dateien

- **DE.txt** (2.3 MB) - Hauptdatenbank mit ~8000 deutschen Postleitzahlen
- **DE-index.txt** (1.3 MB) - Index für schnellen Zugriff

## 🎯 Verwendung

Die Simulatoren (`energy_system_simulator.py` und `energy_system_simulator_local_poa.py`) 
laden diese Dateien automatisch beim Start.

**Kein manuelles Setup erforderlich!**

Beim ersten Start werden die Dateien in den pgeocode Cache kopiert:
```
~/.cache/pgeocode/
```

## 📊 Daten-Quelle

Die Datenbank stammt von GeoNames (https://www.geonames.org/)
und wird von pgeocode verwendet.

## ✅ Vorteile

- ✅ **Offline-Betrieb** - Kein Internet-Download beim Setup
- ✅ **Schnell** - Sofort verfügbar
- ✅ **Zuverlässig** - Keine API-Abhängigkeit
- ✅ **Vollständig** - ~8000 deutsche PLZ

## 🔄 Update

Diese Dateien müssen normalerweise nicht aktualisiert werden.
PLZ ändern sich selten.

Falls Update nötig:
```bash
# Cache löschen
rm -rf ~/.cache/pgeocode/

# pgeocode lädt neue Version
python3 -c "import pgeocode; pgeocode.Nominatim('de')"

# Neue Dateien ins Repository kopieren
cp ~/.cache/pgeocode/DE*.txt plz_data/
```

## 📏 Größe

Gesamt: ~3.6 MB (beides zusammen)

Diese Größe ist akzeptabel für Git-Repositories und ermöglicht
vollständige Offline-Funktionalität.

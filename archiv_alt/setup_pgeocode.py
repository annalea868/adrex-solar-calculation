#!/usr/bin/env python3
"""
Einmaliges Setup-Script für pgeocode PLZ-Datenbank
Lädt die deutsche PLZ-Datenbank mit SSL-Workaround
"""

import ssl
import sys

print("🔧 pgeocode Setup-Script")
print("=" * 60)
print("Dieses Script lädt einmalig die deutsche PLZ-Datenbank.")
print("Danach funktioniert alles offline!\n")

# Temporär SSL-Verifikation deaktivieren (nur für diesen Download)
print("⚠️  Deaktiviere SSL-Verifikation für einmaligen Download...")
ssl._create_default_https_context = ssl._create_unverified_context

try:
    print("📥 Lade pgeocode-Datenbank...")
    import pgeocode
    
    print("   Initialisiere deutsche PLZ-Datenbank...")
    nomi = pgeocode.Nominatim('de')
    
    print("   Teste Datenbank...")
    # Test mit bekannten PLZ
    test_plz = ['10965', '80331', '72108']
    for plz in test_plz:
        result = nomi.query_postal_code(plz)
        print(f"   ✅ PLZ {plz}: {result.place_name} ({result.latitude:.4f}°N, {result.longitude:.4f}°E)")
    
    print("\n" + "=" * 60)
    print("✅ Setup erfolgreich abgeschlossen!")
    print("Die PLZ-Datenbank ist jetzt lokal gespeichert.")
    print("Ab jetzt funktioniert pgeocode offline ohne SSL-Problem.")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Fehler beim Setup: {e}")
    print("\nAlternative Lösung:")
    print("1. Öffne Terminal")
    print("2. Führe aus: /Applications/Python\\ 3.10/Install\\ Certificates.command")
    print("3. Starte dieses Script erneut")
    sys.exit(1)

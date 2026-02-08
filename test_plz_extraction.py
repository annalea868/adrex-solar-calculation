#!/usr/bin/env python3
"""
Quick test for PLZ extraction and pgeocode functionality
"""

import pgeocode
import re

def extract_plz_from_address(address_string):
    """Extract German postal code (PLZ) from a full address string."""
    plz_pattern = r'\b(\d{5})\b'
    match = re.search(plz_pattern, address_string)
    if match:
        return match.group(1)
    return None

def plz_to_coordinates(plz_or_address, nomi):
    """Convert German postal code or full address to coordinates."""
    plz = extract_plz_from_address(plz_or_address)
    
    if not plz:
        return None
    
    result = nomi.query_postal_code(plz)
    
    if nomi.query_postal_code.__module__.startswith('pandas'):
        import pandas as pd
        if pd.isna(result.latitude) or pd.isna(result.longitude):
            return None
    
    return (result.latitude, result.longitude)

# Initialize pgeocode
print("🧪 Testing pgeocode PLZ extraction...\n")
nomi = pgeocode.Nominatim('de')

# Test cases
test_cases = [
    "Dudenstraße 80, 10965 Berlin, Deutschland",  # HubSpot-style full address
    "10965",  # Just PLZ
    "72108 Rottenburg",  # PLZ + city
    "80331 München, Deutschland",  # PLZ + city + country
    "Invalid input",  # Should fail gracefully
]

for test in test_cases:
    plz = extract_plz_from_address(test)
    coords = plz_to_coordinates(test, nomi)
    
    print(f"Input: '{test}'")
    print(f"   → PLZ: {plz}")
    if coords:
        print(f"   → Koordinaten: {coords[0]:.4f}°N, {coords[1]:.4f}°E")
    else:
        print(f"   → ❌ Keine Koordinaten gefunden")
    print()

print("✅ Test abgeschlossen!")

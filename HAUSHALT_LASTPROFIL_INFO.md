# Standardlastprofil Haushaltskunden - Analyse

## 📊 Datei-Struktur

**Datei:** `standardlastprofil-haushaltskunden-2026.xlsx`

### Inhalt:
- **35,040 Intervalle** (365 Tage × 96 Intervalle pro Tag)
- **15-Minuten-Takt** für ganzes Jahr 2026
- **Spalte:** `SLP-HB [kWh]` = Standardlastprofil Haushaltskunden

## 📈 Wichtige Erkenntnis:

### **Referenz-Jahresverbrauch im Profil:**
```
Summe aller Werte = 1,000,000 kWh
```

**Das bedeutet:** Die Werte sind **normalisiert auf 1 Million kWh**!

## 🔄 Skalierung auf Benutzer-Verbrauch

### **Die Lösung ist einfach:**

```python
# Benutzer gibt ein: 7,000 kWh Jahresverbrauch
user_annual_consumption = 7000  # kWh

# Profil-Summe
profile_sum = 1000000  # kWh

# Skalierungsfaktor
scale_factor = user_annual_consumption / profile_sum
# = 7000 / 1000000 = 0.007

# Für jedes Intervall:
user_consumption_15min = profile_value × scale_factor
```

### **Beispiel-Rechnung:**

**Profil-Wert um 12:15:** 48.04 kWh

**Für 7,000 kWh/Jahr Haushalt:**
```
48.04 × 0.007 = 0.336 kWh pro 15 Minuten
```

**Für 5,000 kWh/Jahr Haushalt:**
```
48.04 × 0.005 = 0.240 kWh pro 15 Minuten
```

**Für 10,000 kWh/Jahr Haushalt:**
```
48.04 × 0.010 = 0.480 kWh pro 15 Minuten
```

## 📊 Profil-Statistik

### Werte im Original-Profil:
- **Minimum:** 10.69 kWh (Nacht)
- **Maximum:** 60.29 kWh (Abend-Spitze)
- **Durchschnitt:** 28.54 kWh pro 15 Min

### Typischer Tagesverlauf (normalisiert):
```
Zeit    Verbrauch   Beschreibung
────────────────────────────────
00:00   29.80 kWh   Nacht (niedrig)
06:00   17.77 kWh   Früh-Morgen (sehr niedrig)
09:00   34.51 kWh   Vormittag (steigend)
12:00   48.04 kWh   Mittag (hoch)
18:00   56.72 kWh   Abend-Spitze (höchster Verbrauch!)
22:00   40.37 kWh   Spät-Abend (fallend)
```

## 💡 Implementierung

### **Python-Code zum Skalieren:**

```python
import pandas as pd

def load_and_scale_household_profile(annual_consumption_kwh):
    """
    Lädt Standardlastprofil und skaliert auf Benutzer-Verbrauch.
    
    Parameters:
    - annual_consumption_kwh: Jahresverbrauch des Benutzers (z.B. 7000)
    
    Returns:
    - DataFrame mit skalierten 15-Minuten-Werten
    """
    # Lade Excel
    df = pd.read_excel('modeling/standardlastprofil-haushaltskunden-2026.xlsx')
    
    # Entferne Header-Zeilen (erste 2 Zeilen)
    df_clean = df.iloc[2:].copy()
    
    # Original-Summe
    profile_sum = df_clean['SLP-HB [kWh]'].sum()  # 1,000,000 kWh
    
    # Skalierungsfaktor
    scale_factor = annual_consumption_kwh / profile_sum
    
    # Skaliere alle Werte
    df_clean['Verbrauch_kWh'] = df_clean['SLP-HB [kWh]'] * scale_factor
    
    # Validierung
    actual_sum = df_clean['Verbrauch_kWh'].sum()
    print(f'✅ Skaliert auf {actual_sum:.2f} kWh (Ziel: {annual_consumption_kwh})')
    
    return df_clean[['Datum', 'Uhrzeit', 'Verbrauch_kWh']]

# Beispiel:
profile_7000 = load_and_scale_household_profile(7000)
# Summe = exakt 7000 kWh ✅
```

## 🎯 Für deine Simulation

### **Vorteile dieser Methode:**

1. ✅ **Exakte Summe:** Garantiert dass Summe = Benutzer-Eingabe
2. ✅ **Realistische Verteilung:** Behält typisches Verbrauchsmuster
3. ✅ **Einfach:** Nur eine Multiplikation
4. ✅ **Flexibel:** Funktioniert für jeden Jahresverbrauch

### **Verwendung:**

```python
# Benutzer sagt: "Ich verbrauche 7000 kWh/Jahr"
user_annual = 7000

# Lade und skaliere Profil
consumption_profile = load_and_scale_household_profile(user_annual)

# Jetzt hast du 35,040 Intervalle die zusammen genau 7000 kWh ergeben!
```

## ✅ Zusammenfassung

**Original-Profil:** 1,000,000 kWh Jahresverbrauch (normalisiert)

**Skalierung:** Einfach multiplizieren mit `(Benutzer-Verbrauch / 1,000,000)`

**Ergebnis:** Realistische 15-Minuten-Werte die exakt auf Benutzer-Verbrauch summieren!


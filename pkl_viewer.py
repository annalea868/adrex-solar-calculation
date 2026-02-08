#!/usr/bin/env python3
"""
PKL Viewer - Konvertiert .pkl Dateien in lesbare Formate
Speziell für GHI-Grid Dateien.

Verwendung:
  python3 pkl_viewer.py ghi_grid/ghi_47.50_7.00_2023.pkl

Optionen:
  --csv     Speichert als CSV
  --json    Speichert als JSON
  --preview Zeigt nur Vorschau (Standard)
"""

import pickle
import pandas as pd
import sys
import os

def view_pkl_file(pkl_file, output_format='preview'):
    """Load and display/convert pickle file."""
    
    if not os.path.exists(pkl_file):
        print(f"❌ Datei nicht gefunden: {pkl_file}")
        return
    
    # Load pickle
    with open(pkl_file, 'rb') as f:
        data_dict = pickle.load(f)
    
    data = data_dict['data']
    meta = data_dict.get('meta', {})
    
    print(f"\n📊 DATEI: {os.path.basename(pkl_file)}")
    print("="*70)
    print(f"Zeilen: {len(data)}")
    print(f"Spalten: {list(data.columns)}")
    print(f"Zeitraum: {data.index.min()} bis {data.index.max()}")
    print()
    
    if output_format == 'preview':
        # Zeige Vorschau
        print("Erste 20 Zeilen:")
        print(data.head(20))
        print()
        print("Statistik:")
        print(data.describe())
        
    elif output_format == 'csv':
        # Speichere als CSV
        csv_file = pkl_file.replace('.pkl', '.csv')
        data.to_csv(csv_file)
        print(f"✅ Gespeichert als: {csv_file}")
        print(f"   Öffne mit Excel/LibreOffice")
        
    elif output_format == 'json':
        # Speichere als JSON
        json_file = pkl_file.replace('.pkl', '.json')
        data.to_json(json_file, orient='records', date_format='iso')
        print(f"✅ Gespeichert als: {json_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python3 pkl_viewer.py <pkl-datei> [--csv|--json|--preview]")
        print()
        print("Beispiel:")
        print("  python3 pkl_viewer.py ghi_grid/ghi_47.50_7.00_2023.pkl")
        print("  python3 pkl_viewer.py ghi_grid/ghi_47.50_7.00_2023.pkl --csv")
        sys.exit(1)
    
    pkl_file = sys.argv[1]
    output_format = 'preview'
    
    if '--csv' in sys.argv:
        output_format = 'csv'
    elif '--json' in sys.argv:
        output_format = 'json'
    
    view_pkl_file(pkl_file, output_format)

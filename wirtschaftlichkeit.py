#!/usr/bin/env python3
"""
Wirtschaftlichkeitsberechnung für Energy System Simulator
Berechnet finanzielle Kennzahlen aus Simulationsergebnissen.

Input:
- CSV-Datei vom energy_system_simulator_local_poa.py
- Zusätzliche User-Inputs (Strompreis, Laufzeit, etc.)

Output:
- Alle Werte aus dem Übersichtsblatt
- Eigenverbrauch, Autarkie, Rendite, Amortisation, etc.
"""

import pandas as pd
import numpy as np
from pathlib import Path


class WirtschaftlichkeitsRechner:
    """Berechnet Wirtschaftlichkeits-Kennzahlen aus Simulationsdaten."""
    
    def __init__(self):
        """Initialisiere Rechner."""
        # Konstanten
        self.EINSPEISEVERGUETUNG = 0.08  # €/kWh (Standard 2023)
        self.MAX_AUTARKIE_HAUSHALT = 80.0  # %
        self.MAX_AUTARKIE_WAERMEPUMPE = 55.0  # %
        self.MAX_AUTARKIE_GESAMT = 80.0  # %
        self.MAX_SPEZ_ERTRAG = 940.0  # kWh/kWp/a
        
    # ============================================================================
    # TEIL 1: EIGENSTROM-BERECHNUNG aus CSV
    # ============================================================================
    
    def calculate_eigenstrom_from_csv(self, df):
        """
        Berechne Eigenstrom für jeden Verbraucher aus der Simulations-CSV.
        
        Logik:
        - Wenn Netz_kWh < 0: Netzbezug → Verbrauch wird teilweise aus Netz gedeckt
        - Wenn Netz_kWh >= 0: Kein Netzbezug → Gesamter Verbrauch ist Eigenstrom
        
        Parameters:
        - df: DataFrame mit Spalten Haushalt_Verbrauch_kWh, ECar_Verbrauch_kWh, 
              Waermepumpe_Verbrauch_kWh, Gesamt_Verbrauch_kWh, Netz_kWh
        
        Returns:
        - Dict mit Jahressummen für jeden Verbraucher
        """
        print("\n" + "="*70)
        print("🔍 EIGENSTROM-ANALYSE")
        print("="*70)
        
        num_intervals = len(df)
        
        eigenstrom_haushalt = np.zeros(num_intervals)
        eigenstrom_ecar = np.zeros(num_intervals)
        eigenstrom_waermepumpe = np.zeros(num_intervals)
        
        # Use iloc for positional indexing (works with any index type)
        for i in range(num_intervals):
            haushalt = df.iloc[i]['Haushalt_Verbrauch_kWh']
            ecar = df.iloc[i]['ECar_Verbrauch_kWh']
            waermepumpe = df.iloc[i]['Waermepumpe_Verbrauch_kWh']
            gesamt = df.iloc[i]['Gesamt_Verbrauch_kWh']
            netz = df.iloc[i]['Netz_kWh']
            
            if netz < 0:
                # Netzbezug vorhanden → Verbrauch wird teilweise aus Netz gedeckt
                netzbezug = abs(netz)
                
                if gesamt > 0:
                    # Anteiliger Netzbezug für jeden Verbraucher
                    anteil_haushalt = haushalt / gesamt
                    anteil_ecar = ecar / gesamt
                    anteil_waermepumpe = waermepumpe / gesamt
                    
                    netzbezug_haushalt = netzbezug * anteil_haushalt
                    netzbezug_ecar = netzbezug * anteil_ecar
                    netzbezug_waermepumpe = netzbezug * anteil_waermepumpe
                    
                    eigenstrom_haushalt[i] = max(0, haushalt - netzbezug_haushalt)
                    eigenstrom_ecar[i] = max(0, ecar - netzbezug_ecar)
                    eigenstrom_waermepumpe[i] = max(0, waermepumpe - netzbezug_waermepumpe)
                else:
                    eigenstrom_haushalt[i] = 0
                    eigenstrom_ecar[i] = 0
                    eigenstrom_waermepumpe[i] = 0
            else:
                # Kein Netzbezug → gesamter Verbrauch ist Eigenstrom
                eigenstrom_haushalt[i] = haushalt
                eigenstrom_ecar[i] = ecar
                eigenstrom_waermepumpe[i] = waermepumpe
        
        # Jahressummen
        jahres_eigenstrom = {
            'eigenstrom_haushalt': eigenstrom_haushalt.sum(),
            'eigenstrom_ecar': eigenstrom_ecar.sum(),
            'eigenstrom_waermepumpe': eigenstrom_waermepumpe.sum(),
            'eigenstrom_gesamt': eigenstrom_haushalt.sum() + eigenstrom_ecar.sum() + eigenstrom_waermepumpe.sum()
        }
        
        print(f"\n📊 EIGENSTROM (Jahressummen):")
        print(f"   Haushalt:      {jahres_eigenstrom['eigenstrom_haushalt']:>10.2f} kWh")
        print(f"   E-Auto:        {jahres_eigenstrom['eigenstrom_ecar']:>10.2f} kWh")
        print(f"   Wärmepumpe:    {jahres_eigenstrom['eigenstrom_waermepumpe']:>10.2f} kWh")
        print(f"   GESAMT:        {jahres_eigenstrom['eigenstrom_gesamt']:>10.2f} kWh")
        
        return jahres_eigenstrom
    
    # ============================================================================
    # TEIL 2: KENNZAHLEN-BERECHNUNG
    # ============================================================================
    
    def calculate_spezifischer_ertrag(self, jahresertrag, pv_groesse_kwp):
        """
        Spezifischer Ertrag [kWh/kWp/a]
        Begrenzt auf max. 940 kWh/kWp/a
        """
        if pv_groesse_kwp is None or pv_groesse_kwp == 0:
            return 0
        
        spez_ertrag = jahresertrag / pv_groesse_kwp
        spez_ertrag = min(spez_ertrag, self.MAX_SPEZ_ERTRAG)
        return spez_ertrag
    
    def calculate_eigenverbrauchsquoten(self, eigenstrom_dict, jahresertrag):
        """
        Eigenverbrauchsquoten [%]
        = (Eigenstrom / PV-Ertrag) × 100
        """
        if jahresertrag == 0:
            return {
                'ev_quote_haushalt': 0,
                'ev_quote_ecar': 0,
                'ev_quote_waermepumpe': 0,
                'ev_quote_gesamt': 0
            }
        
        return {
            'ev_quote_haushalt': (eigenstrom_dict['eigenstrom_haushalt'] / jahresertrag) * 100,
            'ev_quote_ecar': (eigenstrom_dict['eigenstrom_ecar'] / jahresertrag) * 100,
            'ev_quote_waermepumpe': (eigenstrom_dict['eigenstrom_waermepumpe'] / jahresertrag) * 100,
            'ev_quote_gesamt': (eigenstrom_dict['eigenstrom_gesamt'] / jahresertrag) * 100
        }
    
    def calculate_autarkiegrade(self, eigenstrom_dict, verbrauch_dict):
        """
        Autarkiegrade [%] mit Limits
        = (Eigenstrom / Verbrauch) × 100
        
        Limits:
        - Haushalt: max. 80%
        - Wärmepumpe: max. 55%
        - Gesamt: max. 80%
        """
        autarkie_haushalt = 0
        if verbrauch_dict['verbrauch_haushalt'] > 0:
            autarkie_haushalt = (eigenstrom_dict['eigenstrom_haushalt'] / verbrauch_dict['verbrauch_haushalt']) * 100
            autarkie_haushalt = min(autarkie_haushalt, self.MAX_AUTARKIE_HAUSHALT)
        
        autarkie_ecar = 0
        if verbrauch_dict['verbrauch_ecar'] > 0:
            autarkie_ecar = (eigenstrom_dict['eigenstrom_ecar'] / verbrauch_dict['verbrauch_ecar']) * 100
            # Kein Limit für E-Auto laut CALCULATION.pdf
        
        autarkie_waermepumpe = 0
        if verbrauch_dict['verbrauch_waermepumpe'] > 0:
            autarkie_waermepumpe = (eigenstrom_dict['eigenstrom_waermepumpe'] / verbrauch_dict['verbrauch_waermepumpe']) * 100
            autarkie_waermepumpe = min(autarkie_waermepumpe, self.MAX_AUTARKIE_WAERMEPUMPE)
        
        autarkie_gesamt = 0
        if verbrauch_dict['verbrauch_gesamt'] > 0:
            autarkie_gesamt = (eigenstrom_dict['eigenstrom_gesamt'] / verbrauch_dict['verbrauch_gesamt']) * 100
            autarkie_gesamt = min(autarkie_gesamt, self.MAX_AUTARKIE_GESAMT)
        
        return {
            'autarkie_haushalt': autarkie_haushalt,
            'autarkie_ecar': autarkie_ecar,
            'autarkie_waermepumpe': autarkie_waermepumpe,
            'autarkie_gesamt': autarkie_gesamt
        }
    
    # ============================================================================
    # TEIL 3: WIRTSCHAFTLICHKEITS-BERECHNUNGEN
    # ============================================================================
    
    def calculate_durchschnittlicher_strompreis(self, aktueller_preis, preissteigerung, laufzeit):
        """
        Durchschnittlicher Strompreis über Laufzeit [€/kWh]
        Berücksichtigt Preissteigerung über die Jahre.
        
        Formel aus CALCULATION.pdf:
        ø_Strompreis = aktueller_Preis × ((1 + Preissteigerung)^Laufzeit - 1) / (Preissteigerung × Laufzeit)
        """
        if preissteigerung == 0:
            return aktueller_preis
        
        preis_rate = preissteigerung / 100  # % zu Dezimal
        
        avg_preis = aktueller_preis * (
            ((1 + preis_rate) ** laufzeit - 1) / (preis_rate * laufzeit)
        )
        
        return avg_preis
    
    def calculate_jaehrliche_ersparnis(self, eigenstrom_gesamt, durchschnittlicher_strompreis):
        """
        Jährliche Ersparnis [€/a]
        = Eigenstrom × durchschnittlicher Strompreis
        """
        return eigenstrom_gesamt * durchschnittlicher_strompreis
    
    def calculate_jaehrliche_verguetung(self, netzeinspeisung, einspeiseverguetung):
        """
        Jährliche Vergütung [€/a]
        = Netzeinspeisung × Einspeisevergütung
        """
        return netzeinspeisung * einspeiseverguetung
    
    def calculate_gesamtvorteil(self, jaehrliche_ersparnis, jaehrliche_verguetung, 
                                invest_netto, laufzeit):
        """
        Gesamtvorteil [€] über Laufzeit
        = (Ersparnis + Vergütung) × Laufzeit - Investition
        """
        return (jaehrliche_ersparnis + jaehrliche_verguetung) * laufzeit - invest_netto
    
    def calculate_stromentstehungskosten(self, invest_netto, jahresertrag, laufzeit):
        """
        Stromentstehungskosten (LCOE) [€/kWh]
        = Investition / (Jahresertrag × Laufzeit)
        
        Vereinfachte Formel ohne Degradation und Wartungskosten.
        """
        if jahresertrag == 0 or laufzeit == 0:
            return 0
        
        return invest_netto / (jahresertrag * laufzeit)
    
    def calculate_amortisationszeit(self, invest_netto, jaehrliche_ersparnis, 
                                   jaehrliche_verguetung):
        """
        Amortisationszeit [Jahre]
        = Investition / (Jährliche Ersparnis + Jährliche Vergütung)
        
        Vereinfachte Formel (statisch).
        """
        jahresvorteil = jaehrliche_ersparnis + jaehrliche_verguetung
        
        if jahresvorteil == 0:
            return float('inf')
        
        return invest_netto / jahresvorteil
    
    def calculate_rendite(self, gesamtvorteil, invest_netto, laufzeit):
        """
        Eigenkapitalrendite [%/a]
        = ((Gesamtvorteil / Investition) / Laufzeit) × 100
        
        Vereinfachte Formel.
        """
        if invest_netto == 0 or laufzeit == 0:
            return 0
        
        return ((gesamtvorteil / invest_netto) / laufzeit) * 100
    
    # ============================================================================
    # HAUPTFUNKTION: Vollständige Wirtschaftlichkeitsberechnung
    # ============================================================================
    
    def berechne_wirtschaftlichkeit(self, 
                                   csv_filepath=None,
                                   dataframe=None,
                                   pv_groesse_kwp=None,
                                   invest_netto=None,
                                   aktueller_strompreis=None,
                                   preissteigerung=None,
                                   inflation=None,
                                   laufzeit=None,
                                   einspeiseverguetung=None):
        """
        Berechne alle Wirtschaftlichkeits-Kennzahlen.
        
        Parameters:
        - csv_filepath: Pfad zur CSV vom Simulator (ODER dataframe)
        - dataframe: DataFrame direkt vom Simulator (alternativ zu csv_filepath)
        - pv_groesse_kwp: PV-Größe [kWp] (optional, wenn im Summary)
        - invest_netto: Investitionskosten [€]
        - aktueller_strompreis: Aktueller Strompreis [€/kWh]
        - preissteigerung: Preissteigerungsrate [%/a]
        - inflation: Inflationsrate [%/a]
        - laufzeit: Betrachtungszeitraum [Jahre]
        - einspeiseverguetung: Einspeisevergütung [€/kWh] (optional, default 0.08)
        
        Returns:
        - Dict mit allen Kennzahlen
        """
        if einspeiseverguetung is None:
            einspeiseverguetung = self.EINSPEISEVERGUETUNG
        
        print("\n" + "="*70)
        print("💰 WIRTSCHAFTLICHKEITS-BERECHNUNG")
        print("="*70)
        
        # 1. Daten laden (CSV oder DataFrame)
        if dataframe is not None:
            df = dataframe
            print(f"\n📊 Verwende Simulationsdaten aus DataFrame")
            print(f"   ✅ {len(df)} Intervalle")
        elif csv_filepath:
            print(f"\n📂 Lade Simulationsdaten: {csv_filepath}")
            df = pd.read_csv(csv_filepath)
            print(f"   ✅ {len(df)} Intervalle geladen")
        else:
            raise ValueError("Entweder csv_filepath oder dataframe muss angegeben werden")
        
        # 2. Jahressummen aus CSV
        jahresertrag = df['PV_Gesamt_kWh'].sum()
        netzeinspeisung = df[df['Netz_kWh'] > 0]['Netz_kWh'].sum()
        netzbezug = abs(df[df['Netz_kWh'] < 0]['Netz_kWh'].sum())
        
        verbrauch_haushalt = df['Haushalt_Verbrauch_kWh'].sum()
        verbrauch_ecar = df['ECar_Verbrauch_kWh'].sum()
        verbrauch_waermepumpe = df['Waermepumpe_Verbrauch_kWh'].sum()
        verbrauch_gesamt = df['Gesamt_Verbrauch_kWh'].sum()
        
        print(f"\n📊 JAHRESSUMMEN aus Simulation:")
        print(f"   PV-Ertrag:        {jahresertrag:>10.2f} kWh")
        print(f"   Netzeinspeisung:  {netzeinspeisung:>10.2f} kWh")
        print(f"   Netzbezug:        {netzbezug:>10.2f} kWh")
        print(f"   Verbrauch Gesamt: {verbrauch_gesamt:>10.2f} kWh")
        print(f"      Haushalt:      {verbrauch_haushalt:>10.2f} kWh")
        print(f"      E-Auto:        {verbrauch_ecar:>10.2f} kWh")
        print(f"      Wärmepumpe:    {verbrauch_waermepumpe:>10.2f} kWh")
        
        # 3. Eigenstrom berechnen
        eigenstrom_dict = self.calculate_eigenstrom_from_csv(df)
        
        verbrauch_dict = {
            'verbrauch_haushalt': verbrauch_haushalt,
            'verbrauch_ecar': verbrauch_ecar,
            'verbrauch_waermepumpe': verbrauch_waermepumpe,
            'verbrauch_gesamt': verbrauch_gesamt
        }
        
        # 4. Eigenverbrauchsquoten
        ev_quoten = self.calculate_eigenverbrauchsquoten(eigenstrom_dict, jahresertrag)
        
        print(f"\n📈 EIGENVERBRAUCHSQUOTEN:")
        print(f"   Haushalt:      {ev_quoten['ev_quote_haushalt']:>6.2f} %")
        print(f"   E-Auto:        {ev_quoten['ev_quote_ecar']:>6.2f} %")
        print(f"   Wärmepumpe:    {ev_quoten['ev_quote_waermepumpe']:>6.2f} %")
        print(f"   GESAMT:        {ev_quoten['ev_quote_gesamt']:>6.2f} %")
        
        # 5. Autarkiegrade (mit Limits!)
        autarkiegrade = self.calculate_autarkiegrade(eigenstrom_dict, verbrauch_dict)
        
        print(f"\n🏠 AUTARKIEGRADE (mit Limits):")
        print(f"   Haushalt:      {autarkiegrade['autarkie_haushalt']:>6.2f} % (max. {self.MAX_AUTARKIE_HAUSHALT}%)")
        print(f"   E-Auto:        {autarkiegrade['autarkie_ecar']:>6.2f} %")
        print(f"   Wärmepumpe:    {autarkiegrade['autarkie_waermepumpe']:>6.2f} % (max. {self.MAX_AUTARKIE_WAERMEPUMPE}%)")
        print(f"   GESAMT:        {autarkiegrade['autarkie_gesamt']:>6.2f} % (max. {self.MAX_AUTARKIE_GESAMT}%)")
        
        # 6. Wirtschaftlichkeits-Kennzahlen
        print(f"\n" + "="*70)
        print("💶 WIRTSCHAFTLICHKEIT")
        print("="*70)
        
        # Durchschnittlicher Strompreis
        avg_strompreis = self.calculate_durchschnittlicher_strompreis(
            aktueller_strompreis, preissteigerung, laufzeit
        )
        print(f"\n   Aktueller Strompreis:         {aktueller_strompreis:.4f} €/kWh")
        print(f"   ø Strompreis ({laufzeit} Jahre): {avg_strompreis:.4f} €/kWh")
        
        # Jährliche Ersparnis
        jaehrl_ersparnis = self.calculate_jaehrliche_ersparnis(
            eigenstrom_dict['eigenstrom_gesamt'], avg_strompreis
        )
        print(f"   Jährliche Ersparnis:          {jaehrl_ersparnis:>10.2f} €/a")
        
        # Jährliche Vergütung
        jaehrl_verguetung = self.calculate_jaehrliche_verguetung(
            netzeinspeisung, einspeiseverguetung
        )
        print(f"   Jährliche Vergütung:          {jaehrl_verguetung:>10.2f} €/a")
        print(f"   (Einspeisung {netzeinspeisung:.0f} kWh × {einspeiseverguetung:.4f} €/kWh)")
        
        # Gesamtvorteil
        gesamtvorteil = self.calculate_gesamtvorteil(
            jaehrl_ersparnis, jaehrl_verguetung, invest_netto, laufzeit
        )
        print(f"\n   Gesamtvorteil ({laufzeit} Jahre): {gesamtvorteil:>10.2f} €")
        
        # Stromentstehungskosten
        lcoe = self.calculate_stromentstehungskosten(invest_netto, jahresertrag, laufzeit)
        print(f"   Stromentstehungskosten:       {lcoe:.4f} €/kWh")
        
        # Amortisationszeit
        amortisation = self.calculate_amortisationszeit(
            invest_netto, jaehrl_ersparnis, jaehrl_verguetung
        )
        print(f"   Amortisationszeit:            {amortisation:.2f} Jahre")
        
        # Rendite
        rendite = self.calculate_rendite(gesamtvorteil, invest_netto, laufzeit)
        print(f"   Eigenkapitalrendite:          {rendite:.2f} %/a")
        
        # Zusammenfassendes Dict
        ergebnis = {
            # Energie-Daten
            'jahresertrag': jahresertrag,
            'netzeinspeisung': netzeinspeisung,
            'netzbezug': netzbezug,
            'verbrauch_gesamt': verbrauch_gesamt,
            'verbrauch_haushalt': verbrauch_haushalt,
            'verbrauch_ecar': verbrauch_ecar,
            'verbrauch_waermepumpe': verbrauch_waermepumpe,
            
            # Eigenstrom
            **eigenstrom_dict,
            
            # Eigenverbrauchsquoten
            **ev_quoten,
            
            # Autarkiegrade
            **autarkiegrade,
            
            # Wirtschaftlichkeit
            'invest_netto': invest_netto,
            'aktueller_strompreis': aktueller_strompreis,
            'avg_strompreis': avg_strompreis,
            'preissteigerung': preissteigerung,
            'inflation': inflation,
            'laufzeit': laufzeit,
            'einspeiseverguetung': einspeiseverguetung,
            'jaehrl_ersparnis': jaehrl_ersparnis,
            'jaehrl_verguetung': jaehrl_verguetung,
            'gesamtvorteil': gesamtvorteil,
            'lcoe': lcoe,
            'amortisationszeit': amortisation,
            'rendite': rendite
        }
        
        return ergebnis
    
    # ============================================================================
    # OUTPUT: Übersichtsblatt
    # ============================================================================
    
    def print_uebersichtsblatt(self, ergebnis, pv_groesse_kwp, speicher_kwh, 
                              modultyp, speichertyp):
        """
        Druckt alle Werte im Format des Übersichtsblatts.
        """
        print("\n\n" + "="*70)
        print("📋 ÜBERSICHTSBLATT - DEINE SOLARSTROMANLAGE")
        print("="*70)
        
        # System-Konfiguration
        print(f"\n🔲 SYSTEM-KONFIGURATION:")
        print(f"   PV-Größe:          {pv_groesse_kwp:.2f} kWp")
        print(f"   Modultyp:          {modultyp}")
        print(f"   Speicherkapazität: {speicher_kwh:.2f} kWh")
        print(f"   Speichertyp:       {speichertyp}")
        
        # Spezifischer Ertrag
        spez_ertrag = self.calculate_spezifischer_ertrag(ergebnis['jahresertrag'], pv_groesse_kwp)
        
        print(f"\n📊 ERTRÄGE UND PREISE:")
        print(f"   Spezifischer Ertrag:   {spez_ertrag:.2f} kWh/kWp/a")
        print(f"   Jahresertrag:          {ergebnis['jahresertrag']:,.2f} kWh/a")
        print(f"   Aktueller Strompreis:  {ergebnis['aktueller_strompreis']:.2f} €/kWh")
        print(f"   Preissteigerungsrate:  {ergebnis['preissteigerung']:.2f} %/a")
        print(f"   Inflation:             {ergebnis['inflation']:.2f} %/a")
        print(f"   Laufzeit:              {ergebnis['laufzeit']:.0f} Jahre")
        
        print(f"\n🏠 VERBRAUCH UND QUOTEN:")
        print(f"   Verbrauch Hausstrom:          {ergebnis['verbrauch_haushalt']:>10,.2f} kWh/a")
        print(f"   Verbrauch Wärmepumpe:         {ergebnis['verbrauch_waermepumpe']:>10,.2f} kWh/a")
        print(f"   Verbrauch E-Auto:             {ergebnis['verbrauch_ecar']:>10,.2f} kWh/a")
        print(f"   Gesamtverbrauch:              {ergebnis['verbrauch_gesamt']:>10,.2f} kWh/a")
        print(f"\n   Eigenverbrauch Hausstrom:     {ergebnis['ev_quote_haushalt']:>6.2f} %")
        print(f"   Eigenverbrauch Wärmepumpe:    {ergebnis['ev_quote_waermepumpe']:>6.2f} %")
        print(f"   Eigenverbrauch E-Auto:        {ergebnis['ev_quote_ecar']:>6.2f} %")
        print(f"   Gesamteigenverbrauch:         {ergebnis['ev_quote_gesamt']:>6.2f} %")
        print(f"\n   Eigenstrom Hausstrom:         {ergebnis['eigenstrom_haushalt']:>10,.2f} kWh/a")
        print(f"   Eigenstrom Wärmepumpe:        {ergebnis['eigenstrom_waermepumpe']:>10,.2f} kWh/a")
        print(f"   Eigenstrom E-Auto:            {ergebnis['eigenstrom_ecar']:>10,.2f} kWh/a")
        print(f"\n   Autarkie Hausstrom:           {ergebnis['autarkie_haushalt']:>6.2f} %")
        print(f"   Autarkie Wärmepumpe:          {ergebnis['autarkie_waermepumpe']:>6.2f} %")
        print(f"   Autarkie E-Auto:              {ergebnis['autarkie_ecar']:>6.2f} %")
        print(f"   Gesamtautarkie:               {ergebnis['autarkie_gesamt']:>6.2f} %")
        
        print(f"\n💶 WIRTSCHAFTLICHKEIT:")
        print(f"   Invest netto:                 {ergebnis['invest_netto']:>10,.2f} €")
        print(f"   Jährl. Ersparnis:             {ergebnis['jaehrl_ersparnis']:>10,.2f} €/a")
        print(f"   Jährl. Vergütung:             {ergebnis['jaehrl_verguetung']:>10,.2f} €/a")
        print(f"   Gesamtvorteil ({ergebnis['laufzeit']:.0f} Jahre): {ergebnis['gesamtvorteil']:>10,.2f} €")
        print(f"   Rendite:                      {ergebnis['rendite']:>6.2f} %/a")
        print(f"   Stromentstehungskosten:       {ergebnis['lcoe']:.4f} €/kWh")
        print(f"   Amortisationszeit:            {ergebnis['amortisationszeit']:.2f} Jahre")
        
        print("\n" + "="*70)
        
        return ergebnis


def main():
    """Interactive Wirtschaftlichkeitsberechnung."""
    print("\n" + "="*70)
    print("💰 WIRTSCHAFTLICHKEITS-RECHNER")
    print("   Für Energy System Simulator")
    print("="*70)
    
    rechner = WirtschaftlichkeitsRechner()
    
    try:
        # 1. CSV-Datei auswählen
        print("\n📂 CSV-DATEI:")
        csv_file = input("   Pfad zur Simulations-CSV (z.B. 'test_results/simulation.csv'): ").strip()
        
        if not Path(csv_file).exists():
            print(f"   ❌ Datei nicht gefunden: {csv_file}")
            return
        
        # 2. PV-System-Daten
        print("\n🔲 PV-SYSTEM:")
        pv_groesse_kwp = float(input("   PV-Größe [kWp] (z.B. 22.5): "))
        modultyp = input("   Modultyp (z.B. 'Winaico 450'): ").strip()
        
        # 3. Speicher-Daten
        print("\n🔋 SPEICHER:")
        speicher_kwh = float(input("   Speicherkapazität [kWh] (z.B. 11.0): "))
        speichertyp = input("   Speichertyp (z.B. 'sonnenBatterie 10 P+ / 11,0'): ").strip()
        
        # 4. Wirtschaftlichkeits-Parameter
        print("\n💰 WIRTSCHAFTLICHKEITS-PARAMETER:")
        invest_netto = float(input("   Investition netto [€] (z.B. 37700): "))
        aktueller_strompreis = float(input("   Aktueller Strompreis [€/kWh] (z.B. 0.35): "))
        preissteigerung = float(input("   Preissteigerungsrate [%/a] (z.B. 4.0): "))
        inflation = float(input("   Inflation [%/a] (z.B. 3.0): "))
        laufzeit = int(input("   Laufzeit [Jahre] (z.B. 20): "))
        
        print("\n🔌 EINSPEISUNG:")
        einspeiseverguetung_input = input(f"   Einspeisevergütung [€/kWh] (Enter für {rechner.EINSPEISEVERGUETUNG}): ").strip()
        einspeiseverguetung = float(einspeiseverguetung_input) if einspeiseverguetung_input else rechner.EINSPEISEVERGUETUNG
        
        # 5. Berechnung durchführen
        print("\n" + "="*70)
        input("Drücke ENTER um Berechnung zu starten...")
        
        ergebnis = rechner.berechne_wirtschaftlichkeit(
            csv_filepath=csv_file,
            invest_netto=invest_netto,
            aktueller_strompreis=aktueller_strompreis,
            preissteigerung=preissteigerung,
            inflation=inflation,
            laufzeit=laufzeit,
            einspeiseverguetung=einspeiseverguetung
        )
        
        # 6. Übersichtsblatt ausgeben
        rechner.print_uebersichtsblatt(
            ergebnis, pv_groesse_kwp, speicher_kwh, modultyp, speichertyp
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Abbruch durch Benutzer")
    except Exception as e:
        print(f"\n\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test script för decision_vault operations"""

import sys
from datetime import date, timedelta
from decision_vault_operations import (
    lagra_beslut, 
    hämta_beslut, 
    uppdatera_beslut_status,
    få_beslut_statistik
)

def test_lagra_beslut():
    """Test 1: Lagra beslut"""
    print("Test 1: Lagrar testbeslut...")
    try:
        result = lagra_beslut(
            beslut="Vi använder Python som huvudspråk för backend",
            typ="teknik",
            datum=date.today(),
            kommentar="Beslut efter teamdiskussion"
        )
        
        if result["success"]:
            print("✅ Beslut lagrat framgångsrikt")
            print(f"   ID: {result['data'].get('id')}")
            print(f"   Beslut: {result['data'].get('beslut')}")
            return result["data"]
        else:
            print(f"❌ Misslyckades lagra beslut: {result.get('error', 'Okänt fel')}")
            return None
            
    except Exception as e:
        print(f"❌ Fel vid lagring: {e}")
        return None

def test_hämta_beslut():
    """Test 2: Hämta beslut"""
    print("\nTest 2: Hämtar beslut...")
    try:
        result = hämta_beslut(limit=10)
        
        if result["success"]:
            count = result.get('count', 0)
            print(f"✅ Hämtade {count} beslut")
            
            if count > 0:
                print("   Senaste beslut:")
                for i, beslut in enumerate(result["data"][:3], 1):
                    beslut_text = beslut.get("beslut", "")[:50]
                    typ = beslut.get("typ", "")
                    datum = beslut.get("datum", "")
                    print(f"   {i}. {beslut_text}... ({typ}, {datum})")
            
            return True
        else:
            print(f"❌ Misslyckades hämta beslut: {result.get('error', 'Okänt fel')}")
            return False
            
    except Exception as e:
        print(f"❌ Fel vid hämtning: {e}")
        return False

def test_filtrera_beslut():
    """Test 3: Filtrera beslut per typ"""
    print("\nTest 3: Filtrerar beslut per typ...")
    try:
        result = hämta_beslut(limit=5, typ="teknik")
        
        if result["success"]:
            count = result.get('count', 0)
            print(f"✅ Hämtade {count} teknikbeslut")
            return True
        else:
            print(f"❌ Misslyckades filtrera: {result.get('error', 'Okänt fel')}")
            return False
            
    except Exception as e:
        print(f"❌ Fel vid filtrering: {e}")
        return False

def test_statistik():
    """Test 4: Få statistik"""
    print("\nTest 4: Hämtar statistik...")
    try:
        result = få_beslut_statistik()
        
        if result["success"]:
            print("✅ Statistik hämtad")
            print(f"   Totalt: {result.get('totalt', 0)} beslut")
            print(f"   Aktiva: {result.get('aktiva', 0)}")
            print(f"   Inaktiva: {result.get('inaktiva', 0)}")
            
            per_typ = result.get('per_typ', {})
            if per_typ:
                print("   Per typ:")
                for typ, stats in per_typ.items():
                    print(f"     {typ}: {stats['aktiva']}/{stats['totalt']}")
            
            return True
        else:
            print(f"❌ Misslyckades hämta statistik: {result.get('error', 'Okänt fel')}")
            return False
            
    except Exception as e:
        print(f"❌ Fel vid statistik: {e}")
        return False

def main():
    """Kör alla decision_vault tester"""
    print("Decision Vault System Tests")
    print("=" * 40)
    
    tests_passed = 0
    
    if test_lagra_beslut():
        tests_passed += 1
    
    if test_hämta_beslut():
        tests_passed += 1
    
    if test_filtrera_beslut():
        tests_passed += 1
    
    if test_statistik():
        tests_passed += 1
    
    # Sammanfattning
    print("\n" + "=" * 40)
    print(f"Tester godkända: {tests_passed}/4")
    
    if tests_passed >= 3:
        print("✅ Decision Vault systemet fungerar!")
        print("\n💡 Användning:")
        print("   from decision_vault_operations import lagra_beslut")
        print('   lagra_beslut("Ditt beslut", "teknik")')
        return True
    else:
        print("❌ Några tester misslyckades.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
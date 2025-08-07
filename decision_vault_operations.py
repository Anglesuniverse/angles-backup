"""
Operations för decision_vault tabellen
Hanterar svenska beslutsdokumentation i Supabase
"""

import os
from datetime import date, datetime
from config import supabase
from typing import Optional, List, Dict, Any

def lagra_beslut(beslut: str, typ: str, datum: Optional[date] = None, 
                aktivt: bool = True, kommentar: Optional[str] = None) -> Dict[str, Any]:
    """
    Lagra ett beslut i decision_vault tabellen
    
    Args:
        beslut: Beslutets innehåll
        typ: Typ av beslut (strategi, teknik, etik, etc.)
        datum: Datum för beslutet (default: idag)
        aktivt: Om beslutet är aktivt (default: True)
        kommentar: Valfri kommentar
    
    Returns:
        dict: Resultat med success/error information
    """
    
    if not beslut or not beslut.strip():
        raise ValueError("Beslut kan inte vara tomt")
    
    if not typ or not typ.strip():
        raise ValueError("Typ kan inte vara tom")
    
    # Validera typ
    giltiga_typer = ['strategi', 'teknik', 'etik', 'arkitektur', 'process', 'säkerhet', 'annat']
    if typ.lower() not in giltiga_typer:
        raise ValueError(f"Typ måste vara en av: {', '.join(giltiga_typer)}")
    
    try:
        # Förbered data
        beslut_data = {
            "beslut": beslut.strip(),
            "typ": typ.lower(),
            "datum": (datum or date.today()).isoformat(),
            "aktivt": aktivt
        }
        
        if kommentar:
            beslut_data["kommentar"] = kommentar.strip()
        
        # Lagra i Supabase
        result = supabase.table("decision_vault").insert(beslut_data).execute()
        
        if result.data:
            return {
                "success": True,
                "data": result.data[0],
                "message": "Beslut lagrat framgångsrikt"
            }
        else:
            return {
                "success": False,
                "error": "Ingen data returnerades från insert-operation",
                "message": "Misslyckades att lagra beslut"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Databasoperation misslyckades: {str(e)}"
        }

def hämta_beslut(limit: int = 20, typ: Optional[str] = None, 
                endast_aktiva: bool = True) -> Dict[str, Any]:
    """
    Hämta beslut från decision_vault tabellen
    
    Args:
        limit: Max antal beslut att hämta
        typ: Filtrera på typ (valfritt)
        endast_aktiva: Visa endast aktiva beslut
    
    Returns:
        dict: Lista med beslut eller error information
    """
    
    try:
        query = supabase.table("decision_vault").select("*")
        
        # Filtrera på aktiva beslut
        if endast_aktiva:
            query = query.eq("aktivt", True)
        
        # Filtrera på typ
        if typ:
            query = query.eq("typ", typ.lower())
        
        # Sortera och begränsa
        result = query.order("datum", desc=True).limit(limit).execute()
        
        return {
            "success": True,
            "data": result.data,
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Misslyckades att hämta beslut: {str(e)}"
        }

def uppdatera_beslut_status(beslut_id: str, aktivt: bool) -> Dict[str, Any]:
    """
    Uppdatera status för ett beslut (aktivt/inaktivt)
    
    Args:
        beslut_id: UUID för beslutet
        aktivt: Ny status
    
    Returns:
        dict: Resultat av uppdateringen
    """
    
    try:
        result = supabase.table("decision_vault").update(
            {"aktivt": aktivt}
        ).eq("id", beslut_id).execute()
        
        if result.data:
            return {
                "success": True,
                "data": result.data[0],
                "message": f"Beslut status uppdaterad till {'aktiv' if aktivt else 'inaktiv'}"
            }
        else:
            return {
                "success": False,
                "message": "Inget beslut hittades med det ID:t"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Misslyckades att uppdatera status: {str(e)}"
        }

def få_beslut_statistik() -> Dict[str, Any]:
    """
    Få statistik över beslut i databasen
    
    Returns:
        dict: Statistik över beslut per typ och status
    """
    
    try:
        # Hämta alla beslut för statistik
        result = supabase.table("decision_vault").select("typ, aktivt").execute()
        
        if not result.data:
            return {
                "success": True,
                "totalt": 0,
                "aktiva": 0,
                "inaktiva": 0,
                "per_typ": {}
            }
        
        beslut = result.data
        totalt = len(beslut)
        aktiva = len([b for b in beslut if b["aktivt"]])
        inaktiva = totalt - aktiva
        
        # Statistik per typ
        per_typ = {}
        for beslut_item in beslut:
            typ = beslut_item["typ"]
            if typ not in per_typ:
                per_typ[typ] = {"totalt": 0, "aktiva": 0}
            per_typ[typ]["totalt"] += 1
            if beslut_item["aktivt"]:
                per_typ[typ]["aktiva"] += 1
        
        return {
            "success": True,
            "totalt": totalt,
            "aktiva": aktiva,
            "inaktiva": inaktiva,
            "per_typ": per_typ
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Misslyckades att hämta statistik: {str(e)}"
        }
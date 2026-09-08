"""
Geocodifica i nodi timeout usando il nome del nodo.
Estrae la località dal nome e cerca le coordinate su Nominatim.
Aggiorna node_positions.json con le nuove posizioni.
"""
import json
import time
import re
import requests
import os

NODE_POSITIONS = r"C:\Users\camil\gizero-dashboard\backend\data\node_positions.json"
NODI_NOMI     = r"C:\Users\camil\gizero-dashboard\backend\data\nodi_nomi.json"

# Carica posizioni esistenti
with open(NODE_POSITIONS, "r") as f:
    positions = json.load(f)

# Carica nomi nodi
with open(NODI_NOMI, "r", encoding="utf-8") as f:
    nomi = json.load(f)

def estrai_localita(nome):
    """
    Estrae la località dal nome del nodo.
    Es: 'EDUGREEN - Pindemonte VR - hchosensor005' → 'Pindemonte VR'
        'LA MOTTA - TH Stalla' → 'LA MOTTA'
        'AGSM 004 Watteco - Palestra Bentegodi' → 'Verona'
    """
    # Pattern: parola(e) seguite da sigla provincia (2 lettere maiuscole)
    match = re.search(r'[-–]\s*([^-–]+?)\s+([A-Z]{2})\s*[-–]', nome)
    if match:
        citta = match.group(1).strip()
        provincia = match.group(2).strip()
        return f"{citta} {provincia} Italy"
    
    # Pattern: solo città senza provincia
    match = re.search(r'[-–]\s*([A-Za-z\s]+?)\s*[-–]', nome)
    if match:
        citta = match.group(1).strip()
        if len(citta) > 3 and not any(c.isdigit() for c in citta):
            return f"{citta} Italy"
    
    return None

def geocodifica(query):
    """Cerca coordinate su Nominatim."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": "GizeroDashboard/1.0"},
            timeout=10
        )
        results = r.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        print(f"  Errore geocodifica '{query}': {e}")
    return None, None

# Processa nodi senza posizione
aggiunti = 0
non_trovati = 0

for deveui, info in nomi.items():
    if deveui in positions:
        continue  # già ha posizione, salta
    
    nome = info.get("nome", "")
    if not nome:
        continue
    
    localita = estrai_localita(nome)
    if not localita:
        print(f"  Nessuna località estratta da: {nome}")
        non_trovati += 1
        continue
    
    lat, lon = geocodifica(localita)
    if lat and lon:
        positions[deveui] = {
            "lat": lat,
            "lon": lon,
            "quality": "bassa",
            "n_gw": 0,
            "metodo": "geocodifica_nome"
        }
        aggiunti += 1
        print(f"✓ {nome[:50]:<50} → {localita} → {lat:.4f}, {lon:.4f}")
    else:
        print(f"✗ Non trovato: {localita} (da: {nome[:40]})")
        non_trovati += 1
    
    time.sleep(1.1)  # Nominatim richiede max 1 req/sec

# Salva
with open(NODE_POSITIONS, "w") as f:
    json.dump(positions, f, indent=2)

print(f"\nDone — aggiunti: {aggiunti}, non trovati: {non_trovati}")
print(f"Totale posizioni: {len(positions)}")
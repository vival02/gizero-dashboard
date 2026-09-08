import json
import requests

NODE_POSITIONS = r"C:\Users\camil\gizero-dashboard\backend\data\node_positions.json"
NODI_NOMI     = r"C:\Users\camil\gizero-dashboard\backend\data\nodi_nomi.json"

with open(NODE_POSITIONS, "r") as f:
    positions = json.load(f)

with open(NODI_NOMI, "r", encoding="utf-8") as f:
    nomi = json.load(f)

# Nodi senza posizione
senza = [(dev, info.get("nome", ""))
         for dev, info in nomi.items()
         if dev not in positions]
senza.sort(key=lambda x: x[1])

print(f"Nodi senza posizione: {len(senza)}")
print("Comandi: [s] = conosco l'indirizzo | [n] = salta | [q] = salva ed esci\n")

aggiunti = 0

def geocodifica_indirizzo(indirizzo):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": indirizzo, "format": "json", "limit": 1},
            headers={"User-Agent": "GizeroDashboard/1.0"},
            timeout=10
        )
        results = r.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        print(f"  Errore: {e}")
    return None, None

for i, (deveui, nome) in enumerate(senza):
    print(f"[{i+1}/{len(senza)}] {nome}")
    print(f"        {deveui}")

    risposta = input("Conosci l'indirizzo? [s/n/q]: ").strip().lower()

    if risposta == 'q':
        print("Uscita...")
        break

    if risposta != 's':
        print()
        continue

    while True:
        indirizzo = input("  Indirizzo (es. Via Roma 1, Verona): ").strip()
        lat, lon = geocodifica_indirizzo(indirizzo)

        if lat and lon:
            print(f"  Trovato: {lat:.5f}, {lon:.5f}")
            conf = input("  Corretto? [invio=sì / n=riprova / s=salta]: ").strip().lower()
            if conf == 's':
                print()
                break
            elif conf == 'n':
                continue
            else:
                positions[deveui] = {
                    "lat": lat,
                    "lon": lon,
                    "quality": "alta",
                    "n_gw": 0,
                    "metodo": "manuale"
                }
                aggiunti += 1
                print(f"  ✓ Aggiunto\n")
                # Salva subito
                with open(NODE_POSITIONS, "w") as f:
                    json.dump(positions, f, indent=2)
                break
        else:
            print("  Non trovato su Nominatim.")
            riprova = input("  Vuoi riprovare con un indirizzo diverso? [s/n]: ").strip().lower()
            if riprova != 's':
                print()
                break

print(f"\nDone — aggiunti {aggiunti} nodi.")
print(f"Totale posizioni: {len(positions)}")
from fastapi import APIRouter
import json
import os

router = APIRouter()

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

@router.get("/")
def get_gateway():
    with open(os.path.join(DATA, "gateway_positions.json"), "r", encoding="utf-8", errors="ignore") as f:
        gw_pos = json.load(f)

    gateway_list = []
    for gweui, info in gw_pos.items():
        lat = info.get("lat")
        lon = info.get("lon")
        if not lat or not lon:
            continue
        gateway_list.append({
            "gweui":           gweui,
            "nome":            info.get("name", gweui[-8:]),
            "lat":             lat,
            "lon":             lon,
            "rssi_medio":      -90.0,
            "sf_medio":        8.0,
            "n_nodi":          0,
            "n_pacchetti":     0,
            "ultimo_contatto": "N/D",
            "attivo":          True,
        })

    return {"gateway": gateway_list}
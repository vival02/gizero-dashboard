from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import nodi, gateway, batteria, stats

app = FastAPI(title="Gizero Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nodi.router,     prefix="/api/nodi",     tags=["nodi"])
app.include_router(gateway.router,  prefix="/api/gateway",  tags=["gateway"])
app.include_router(batteria.router, prefix="/api/batteria", tags=["batteria"])
app.include_router(stats.router,    prefix="/api/stats",    tags=["stats"])

@app.get("/health")
def health():
    return {"status": "ok"}
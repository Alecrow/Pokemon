from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_all_pokemon, get_all_zones
from graph import PokemonGraph
from optimizer import EVOptimizer
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Grafo y Optimizador
# Intentar localizar adjacency.json
ADJ_PATH = "adjacency.json"
if not os.path.exists(ADJ_PATH):
    # Fallback para desarrollo local si backend se ejecuta desde su carpeta
    potential_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "map", "adjacency.json")
    if os.path.exists(potential_path):
        ADJ_PATH = potential_path
    else:
        logger.warning("adjacency.json no encontrado. La optimización no funcionará correctamente hasta que se copie el archivo.")

graph = PokemonGraph(ADJ_PATH)
optimizer = EVOptimizer(graph)

app = FastAPI(
    title="Pokemon EV Training API",
    description="API para optimizar el entrenamiento de EVs en Pokemon Fire Red",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Endpoint de bienvenida"""
    return {
        "message": "Pokemon EV Training API",
        "version": "1.0.0",
        "endpoints": {
            "pokemon": "/api/pokemon",
            "zones": "/api/zones",
            "docs": "/docs"
        }
    }

@app.get("/api/pokemon")
def get_pokemon():
    """
    Obtiene la lista de todos los Pokémon disponibles en la base de datos.
    Retorna nombre, tipos y EVs que otorgan.
    """
    try:
        logger.info("Consultando lista de Pokémon...")
        pokemon_list = get_all_pokemon()
        
        # Formatear respuesta
        formatted_pokemon = [
            {
                "id": p["id"],
                "pokedex_number": p["pokedex_number"],
                "name": p["name"],
                "type1": p["type1"],
                "type2": p["type2"],
                "evs": {
                    "hp": p["ev_hp"],
                    "attack": p["ev_attack"],
                    "defense": p["ev_defense"],
                    "sp_attack": p["ev_sp_attack"],
                    "sp_defense": p["ev_sp_defense"],
                    "speed": p["ev_speed"]
                }
            }
            for p in pokemon_list
        ]
        
        logger.info(f"Se encontraron {len(formatted_pokemon)} Pokémon")
        return {
            "count": len(formatted_pokemon),
            "pokemon": formatted_pokemon
        }
    except Exception as e:
        logger.error(f"Error obteniendo Pokémon: {e}")
        raise HTTPException(status_code=500, detail=f"Error al consultar Pokémon: {str(e)}")

@app.get("/api/zones")
def get_zones():
    """
    Obtiene la lista de todas las zonas disponibles en el mapa de Kanto.
    """
    try:
        logger.info("Consultando lista de zonas...")
        zones_list = get_all_zones()
        
        # Formatear respuesta
        formatted_zones = [
            {
                "id": z["id"],
                "code": z["code"],
                "name": z["name"],
                "region": z["region"],
                "zone_type": z["zone_type"]
            }
            for z in zones_list
        ]
        
        logger.info(f"Se encontraron {len(formatted_zones)} zonas")
        return {
            "count": len(formatted_zones),
            "zones": formatted_zones
        }
    except Exception as e:
        logger.error(f"Error obteniendo zonas: {e}")
        raise HTTPException(status_code=500, detail=f"Error al consultar zonas: {str(e)}")

@app.get("/health")
def health_check():
    """Endpoint para verificar que el servicio está activo"""
    return {"status": "healthy"}

from typing import Dict, Optional

class OptimizationRequest(BaseModel):
    start_zone: str
    # Deprecated single target fields
    target_stat: Optional[str] = None
    target_evs: Optional[int] = None
    # New multi-target field
    targets: Optional[Dict[str, int]] = None
    
    pokemon_level: int = 50
    lambda_val: float = 0.1

@app.post("/api/optimize")
def optimize_ev_training(request: OptimizationRequest):
    """
    Calcula la ruta óptima para entrenar EVs.
    Soporta un solo objetivo (target_stat) o múltiples (targets).
    """
    try:
        # Normalizar entrada
        targets = request.targets
        if not targets:
            if request.target_stat and request.target_evs:
                targets = {request.target_stat: request.target_evs}
            else:
                raise HTTPException(status_code=400, detail="Debes especificar 'targets' o 'target_stat'/'target_evs'")

        logger.info(f"Optimizando para {targets} desde {request.start_zone}")
        
        result = optimizer.find_optimal_multistat_route(
            request.start_zone,
            targets,
            request.lambda_val,
            request.pokemon_level
        )
        
        if not result:
            return {"message": "No se encontró una ruta adecuada."}
            
        return {
            "optimal_route": result["route"],
            "total_cost": result["total_cost"],
            "message": f"Ruta optimizada encontrada con costo total {result['total_cost']:.2f}"
        }
    except Exception as e:
        logger.error(f"Error en optimización: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculando optimización: {str(e)}")

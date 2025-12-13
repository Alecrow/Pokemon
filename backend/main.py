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

from typing import Dict, Optional, List

class OptimizationRequest(BaseModel):
    pokemon_name: str
    pokemon_level: int = 50
    start_zone: str
    accessible_zones: List[str] = []
    target_stat: str
    target_evs: int
    has_macho_brace: bool = False
    has_pokerus: bool = False
    lambda_penalty: float = 0.1

@app.post("/api/optimize")
async def optimize_ev_training(request: OptimizationRequest):
    """
    Calcula la ruta óptima para entrenar EVs.
    """
    try:
        logger.info(f"Optimizando desde {request.start_zone} para {request.target_stat}")
        
        # Construct target_evs dict
        target_evs_dict = {request.target_stat: request.target_evs}
        
        # Construct current_evs dict (assume 0 for now as frontend doesn't send it)
        current_evs_dict = {
            "HP": 0, "Attack": 0, "Defense": 0, 
            "Special Attack": 0, "Special Defense": 0, "Speed": 0
        }
        
        result = await optimizer.find_optimal_path(
            start_zone=request.start_zone,
            current_evs=current_evs_dict,
            target_evs=target_evs_dict,
            accessible_zones=request.accessible_zones,
            has_macho_brace=request.has_macho_brace,
            has_pokerus=request.has_pokerus,
            lambda_penalty=request.lambda_penalty,
            pokemon_level=request.pokemon_level
        )
        
        # Add metadata to result for frontend display
        if result:
            result['pokemon_name'] = request.pokemon_name
            result['target_stat'] = request.target_stat
            result['total_battles'] = result['total_encounters']
            # Generate a description
            result['optimal_route_description'] = f"Start at {request.start_zone}. Travel {result['total_distance']} tiles. Defeat {result['total_encounters']} Pokemon."
            
            # Transform path for frontend if needed
            # Frontend expects: ev_path: [{pokemon, ev_yield, count}]
            # Backend returns: path: [{type, zone, target_pokemon, count, ...}]
            
            frontend_path = []
            for step in result['path']:
                if step['type'] == 'farm':
                    frontend_path.append({
                        "pokemon": step['target_pokemon'],
                        "ev_yield": f"{step['stat_focus']} (Yield TBD)", # Simplify
                        "count": step['count']
                    })
            result['ev_path'] = frontend_path

        return result
    except Exception as e:
        logger.error(f"Error en optimización: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculando optimización: {str(e)}")

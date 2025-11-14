from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import get_all_pokemon, get_all_zones
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

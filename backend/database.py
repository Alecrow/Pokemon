import psycopg2
from psycopg2.extras import RealDictCursor
import os

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'pokemon_ev'),
    'user': os.getenv('POSTGRES_USER', 'trainer'),
    'password': os.getenv('POSTGRES_PASSWORD', 'pikachu123'),
    'port': int(os.getenv('POSTGRES_PORT', 5432))
}

def get_db_connection():
    """Crea y retorna una conexión a la base de datos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        raise

def get_all_pokemon():
    """Obtiene todos los Pokémon ordenados por nombre"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, pokedex_number, name, type1, type2,
                   ev_hp, ev_attack, ev_defense, 
                   ev_sp_attack, ev_sp_defense, ev_speed
            FROM pokemon
            ORDER BY name
        """)
        pokemon_list = cursor.fetchall()
        return pokemon_list
    finally:
        cursor.close()
        conn.close()

def get_all_zones():
    """Obtiene todas las zonas ordenadas por nombre"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, code, name, region, zone_type
            FROM zones
            ORDER BY name
        """)
        zones_list = cursor.fetchall()
        return zones_list
    finally:
        cursor.close()
        conn.close()

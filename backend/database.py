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
        zones = cursor.fetchall()
        return zones
    finally:
        cursor.close()
        conn.close()

def get_zone_ev_yields(target_stat: str, pokemon_level: int = 50):
    """
    Calcula el EV yield promedio por encuentro para una estadística dada en cada zona.
    Filtra por nivel del pokemon (+- 10 niveles).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Map stat name to column
    stat_map = {
        "HP": "ev_hp",
        "Attack": "ev_attack", 
        "Defense": "ev_defense",
        "Special Attack": "ev_sp_attack",
        "Special Defense": "ev_sp_defense",
        "Speed": "ev_speed"
    }
    col = stat_map.get(target_stat, "ev_speed")
    
    try:
        # Query para calcular yield promedio ponderado por probabilidad de encuentro
        # Se asume que probability_percent suma 100 por zona (o se normaliza)
        query = f"""
            SELECT 
                z.code,
                SUM((e.probability_percent / 100.0) * p.{col}) as avg_yield
            FROM zones z
            JOIN encounters e ON z.id = e.zone_id
            JOIN pokemon p ON e.pokemon_id = p.id
            WHERE e.avg_level BETWEEN %s AND %s
            GROUP BY z.code
            HAVING SUM((e.probability_percent / 100.0) * p.{col}) > 0
        """
        cursor.execute(query, (max(1, pokemon_level - 10), pokemon_level + 10))
        results = cursor.fetchall()
        return {row['code']: float(row['avg_yield']) for row in results}
    finally:
        cursor.close()
        conn.close()

def get_zone_details(zone_code: str, target_stat: str, pokemon_level: int = 50):
    """
    Obtiene detalles de los Pokémon que aparecen en una zona específica,
    filtrados por nivel y ordenados por su aporte a la estadística objetivo.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stat_map = {
        "HP": "ev_hp", "Attack": "ev_attack", "Defense": "ev_defense",
        "Special Attack": "ev_sp_attack", "Special Defense": "ev_sp_defense", "Speed": "ev_speed"
    }
    col = stat_map.get(target_stat, "ev_speed")
    
    try:
        query = f"""
            SELECT 
                p.name,
                p.{col} as ev_yield,
                e.probability_percent,
                e.avg_level
            FROM zones z
            JOIN encounters e ON z.id = e.zone_id
            JOIN pokemon p ON e.pokemon_id = p.id
            WHERE z.code = %s
            AND e.avg_level BETWEEN %s AND %s
            AND p.{col} > 0
            ORDER BY p.{col} DESC, e.probability_percent DESC
        """
        cursor.execute(query, (zone_code, max(1, pokemon_level - 10), pokemon_level + 10))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

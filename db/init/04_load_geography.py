#!/usr/bin/env python3
"""
Script para cargar la geografía (zonas y conexiones) a PostgreSQL
Lee desde db/scrapingNew/geography_graph.json
"""

import os
import json
import psycopg2
from psycopg2.extras import execute_batch
import time
import re

# Configuración de DB (misma que 02_load_data.py)
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'database': os.getenv('POSTGRES_DB', 'pokemon_ev'),
    'user': os.getenv('POSTGRES_USER', 'trainer'),
    'password': os.getenv('POSTGRES_PASSWORD', 'pikachu123'),
    'port': int(os.getenv('POSTGRES_PORT', 5432))
}

# Rutas de archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# En el contenedor, scrapingNew estará montado en /app/scrapingNew
GRAPH_FILE = os.path.join(BASE_DIR, 'scrapingNew/geography_graph.json')
MAPPING_FILE = os.path.join(BASE_DIR, 'scrapingNew/name_mapping.json')

def wait_for_db(max_retries=30):
    """Espera a que la base de datos esté lista"""
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            print("✓ Base de datos lista")
            return True
        except psycopg2.OperationalError:
            print(f"Esperando base de datos... ({i+1}/{max_retries})")
            time.sleep(2)
    return False

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def normalize_name(name, mapping):
    """Normaliza el nombre de la zona usando el mapping y reglas simples"""
    if not name:
        return None
    
    # Quitar paréntesis y espacios extra
    name = re.sub(r'\s*\(.*?\)', '', name).strip()
    
    # Usar mapping si existe
    if name in mapping:
        return mapping[name]
    
    # Reglas comunes
    if name.startswith("Ruta"):
        # Ruta 1 -> Route1
        match = re.match(r'Ruta\s+(\d+)', name, re.IGNORECASE)
        if match:
            return f"Route{match.group(1)}"
    
    return name

def to_db_code(name):
    """Convierte CamelCase (Route1, PalletTown) a formato DB (kanto-route-1, kanto-pallet-town)"""
    # Insertar guión antes de mayúsculas o números, pero no al principio
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
    # Manejar números al final (Route1 -> Route-1)
    s3 = re.sub('([a-z])([0-9]+)', r'\1-\2', s2)
    return f"kanto-{s3.lower()}"

def is_valid_zone(name):
    """Filtra nombres que no son zonas válidas"""
    if not name:
        return False
    invalid_terms = ["Lista de", "WikiDex", "Archivo:", "Imagen", "MediaWiki"]
    for term in invalid_terms:
        if term in name:
            return False
    return True

def load_geography(conn):
    print("\n🗺️  Cargando Geografía...")
    
    graph_data = load_json(GRAPH_FILE)
    mapping = load_json(MAPPING_FILE)
    
    if not graph_data:
        print(f"⚠ No se encontraron datos en {GRAPH_FILE}")
        return

    cursor = conn.cursor()
    
    # 0. Limpiar distancias antiguas (generadas por 02_load_data.py)
    print("  - Limpiando distancias antiguas...")
    cursor.execute("TRUNCATE TABLE zone_distances RESTART IDENTITY CASCADE")
    
    # 1. Recolectar todas las zonas únicas y mapearlas a IDs existentes
    cursor.execute("SELECT id, code, name FROM zones")
    existing_zones = cursor.fetchall()
    
    # Mapas para buscar zonas existentes
    code_to_id = {row[1]: row[0] for row in existing_zones}
    name_to_id = {row[2]: row[0] for row in existing_zones}
    
    unique_zones = set()
    
    # Función auxiliar para resolver ID de zona
    def resolve_zone(raw_name):
        if not is_valid_zone(raw_name):
            return None, None
            
        norm_name = normalize_name(raw_name, mapping)
        if not norm_name:
            return None, None
            
        # Intentar generar código compatible
        db_code = to_db_code(norm_name)
        
        # Buscar en existentes
        if db_code in code_to_id:
            return code_to_id[db_code], db_code
            
        # Si no existe, devolver datos para crearla
        return None, db_code

    # Recolectar zonas nuevas
    zones_to_create = []
    seen_codes = set(code_to_id.keys())
    
    all_nodes = set(graph_data.keys())
    for src in graph_data:
        all_nodes.update(graph_data[src].keys())
        
    for node in all_nodes:
        zone_id, db_code = resolve_zone(node)
        if db_code and db_code not in seen_codes:
            # Crear nombre legible (kanto-route-1 -> Route 1)
            readable_name = db_code.replace('kanto-', '').replace('-', ' ').title()
            zones_to_create.append((db_code, readable_name))
            seen_codes.add(db_code)
            
    # 2. Insertar Zonas Nuevas
    if zones_to_create:
        print(f"  - Creando {len(zones_to_create)} zonas nuevas...")
        execute_batch(cursor, """
            INSERT INTO zones (code, name, region)
            VALUES (%s, %s, 'Kanto')
            ON CONFLICT (code) DO NOTHING
        """, zones_to_create)
        conn.commit()
        
        # Actualizar mapa
        cursor.execute("SELECT id, code FROM zones")
        code_to_id = {row[1]: row[0] for row in cursor.fetchall()}
    
    # 4. Insertar Conexiones
    connections = []
    default_distance = 10 # Valor por defecto si es 0
    
    for src_raw, neighbors in graph_data.items():
        src_id, src_code = resolve_zone(src_raw)
        if not src_id and src_code in code_to_id:
            src_id = code_to_id[src_code]
            
        if not src_id:
            continue
        
        for dst_raw, data in neighbors.items():
            dst_id, dst_code = resolve_zone(dst_raw)
            if not dst_id and dst_code in code_to_id:
                dst_id = code_to_id[dst_code]
                
            if not dst_id:
                continue
            
            # Evitar auto-bucles
            if src_id == dst_id:
                continue
                
            dist = data.get('dist', 0)
            if dist == 0:
                dist = default_distance
                
            connections.append((src_id, dst_id, dist))
            
    print(f"  - Insertando {len(connections)} conexiones...")
    
    insert_dist_query = """
        INSERT INTO zone_distances (from_zone_id, to_zone_id, distance_tiles)
        VALUES (%s, %s, %s)
        ON CONFLICT (from_zone_id, to_zone_id) 
        DO UPDATE SET distance_tiles = EXCLUDED.distance_tiles
    """
    
    execute_batch(cursor, insert_dist_query, connections)
    conn.commit()
    print("✓ Geografía cargada exitosamente.")

if __name__ == "__main__":
    if wait_for_db():
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            load_geography(conn)
            conn.close()
        except Exception as e:
            print(f"❌ Error: {e}")

#!/usr/bin/env python3
"""
Script para cargar todos los datos a PostgreSQL
Ejecutar después de: docker-compose up -d
"""

import os
import csv
import psycopg2
from psycopg2.extras import execute_batch
import time

DB_CONFIG = {
    'host': 'localhost',
    'database': 'pokemon_ev',
    'user': 'trainer',
    'password': 'pikachu123',
    'port': 5432
}

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

def load_pokemon_data(conn):
    """Carga datos de Pokémon desde el CSV"""
    print("\n📦 Cargando Pokémon...")
    
    csv_path = 'Pokedex_Limpiado.csv'
    if not os.path.exists(csv_path):
        print(f"⚠ Archivo no encontrado: {csv_path}")
        return
    
    cursor = conn.cursor()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        pokemon_data = []
        
        for row in reader:
            # Convertir valores vacíos a None
            def clean_val(val):
                return None if val == '' else val
            
            pokemon_data.append((
                int(row['No']),
                row['Name'],
                int(row['Generation']),
                float(row['Height']) if row['Height'] else None,
                float(row['Weight']) if row['Weight'] else None,
                row['Type1'],
                clean_val(row['Type2']),
                clean_val(row['Ability1']),
                clean_val(row['Ability2']),
                clean_val(row['Ability_Hidden']),
                float(row['Gender_Male']) if row['Gender_Male'] else None,
                float(row['Gender_Female']) if row['Gender_Female'] else None,
                float(row['Gender_Unknown']) if row['Gender_Unknown'] else None,
                int(row['Get_Rate']) if row['Get_Rate'] else None,
                int(row['Base_Experience']) if row['Base_Experience'] else None,
                clean_val(row['Experience_Type']),
                clean_val(row['Category']),
                int(row['HP']),
                int(row['Attack']),
                int(row['Defense']),
                int(row['SP_Attack']),
                int(row['SP_Defense']),
                int(row['Speed']),
                int(row['Total']),
                int(row['E_HP']),
                int(row['E_Attack']),
                int(row['E_Defense']),
                int(row['E_SP_Attack']),
                int(row['E_SP_Defense']),
                int(row['E_Speed'])
            ))
    
    insert_query = """
        INSERT INTO pokemon (
            pokedex_number, name, generation, height, weight,
            type1, type2, ability1, ability2, ability_hidden,
            gender_male, gender_female, gender_unknown,
            capture_rate, base_experience, experience_type, category,
            base_hp, base_attack, base_defense, base_sp_attack, base_sp_defense, base_speed, base_total,
            ev_hp, ev_attack, ev_defense, ev_sp_attack, ev_sp_defense, ev_speed
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (pokedex_number) DO NOTHING
    """
    
    execute_batch(cursor, insert_query, pokemon_data)
    conn.commit()
    print(f"✓ {len(pokemon_data)} Pokémon cargados")

def load_zones_and_encounters(conn):
    """Carga zonas y encuentros desde los CSVs de locations"""
    print("\n📍 Cargando zonas y encuentros...")
    
    locations_dir = 'locations/csv'
    if not os.path.exists(locations_dir):
        print(f"⚠ Directorio no encontrado: {locations_dir}")
        return
    
    cursor = conn.cursor()
    zone_id_map = {}
    
    for filename in os.listdir(locations_dir):
        if not filename.endswith('.csv'):
            continue
        
        # Extraer código de zona del nombre del archivo
        zone_code = filename.replace('.csv', '')
        zone_name = zone_code.replace('kanto-', '').replace('-', ' ').title()
        
        # Insertar zona
        cursor.execute("""
            INSERT INTO zones (code, name, region, zone_type)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """, (zone_code, zone_name, 'Kanto', 'Route' if 'route' in zone_code else 'Location'))
        
        zone_id = cursor.fetchone()[0]
        zone_id_map[zone_code] = zone_id
        
        # Leer encuentros
        filepath = os.path.join(locations_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            encounters = []
            
            for row in reader:
                pokemon_name = row['Pokémon'].strip()
                
                # Buscar ID del Pokémon
                cursor.execute("SELECT id FROM pokemon WHERE name = %s", (pokemon_name,))
                result = cursor.fetchone()
                if not result:
                    continue
                
                pokemon_id = result[0]
                
                # Parsear nivel
                nivel_str = row['Nivel'].strip()
                if '-' in nivel_str:
                    min_level, max_level = map(int, nivel_str.split('-'))
                else:
                    min_level = max_level = int(nivel_str)
                
                avg_level = (min_level + max_level) / 2.0
                
                # Mapear rareza a probabilidad aproximada
                rarity_map = {
                    'Common': 40.0,
                    'Uncommon': 20.0,
                    'Rare': 10.0,
                    'Very Rare': 5.0
                }
                
                rarity = row['Rareza'].strip()
                probability = rarity_map.get(rarity, 10.0)
                
                encounters.append((
                    zone_id,
                    pokemon_id,
                    row['Método'].strip(),
                    rarity,
                    min_level,
                    max_level,
                    avg_level,
                    probability,
                    row.get('Generación', 'Generation 3')
                ))
            
            if encounters:
                insert_query = """
                    INSERT INTO encounters (
                        zone_id, pokemon_id, encounter_method, rarity_tier,
                        min_level, max_level, avg_level, probability_percent, generation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                execute_batch(cursor, insert_query, encounters)
    
    conn.commit()
    print(f"✓ {len(zone_id_map)} zonas y sus encuentros cargados")
    return zone_id_map

def calculate_zone_distances(conn, zone_id_map):
    """Calcula distancias entre zonas usando grid_labels.csv"""
    print("\n📏 Calculando distancias entre zonas...")
    
    # Por ahora, crear distancias básicas entre zonas secuenciales
    # En una versión completa, usarías el grid_labels.csv y un algoritmo de pathfinding
    
    cursor = conn.cursor()
    zones_list = list(zone_id_map.items())
    
    distances = []
    for i, (code1, id1) in enumerate(zones_list):
        for j, (code2, id2) in enumerate(zones_list):
            if i != j:
                # Distancia simplificada: diferencia de índices * 50 tiles
                distance = abs(i - j) * 50
                distances.append((id1, id2, distance))
    
    insert_query = """
        INSERT INTO zone_distances (from_zone_id, to_zone_id, distance_tiles)
        VALUES (%s, %s, %s)
        ON CONFLICT (from_zone_id, to_zone_id) DO NOTHING
    """
    
    execute_batch(cursor, insert_query, distances)
    conn.commit()
    print(f"✓ {len(distances)} distancias calculadas")

def main():
    print("🚀 Iniciando carga de datos...")
    
    if not wait_for_db():
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        load_pokemon_data(conn)
        zone_id_map = load_zones_and_encounters(conn)
        
        if zone_id_map:
            calculate_zone_distances(conn, zone_id_map)
        
        conn.close()
        print("\n✅ Carga de datos completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

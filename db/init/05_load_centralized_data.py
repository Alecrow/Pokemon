#!/usr/bin/env python3
import os
import json
import csv
import psycopg2
from psycopg2.extras import execute_batch
import time

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'database': os.getenv('POSTGRES_DB', 'pokemon_ev'),
    'user': os.getenv('POSTGRES_USER', 'trainer'),
    'password': os.getenv('POSTGRES_PASSWORD', 'pikachu123'),
    'port': int(os.getenv('POSTGRES_PORT', 5432))
}

DATA_DIR = '/app/data_sources'

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def load_pokemon(conn):
    print("Loading Pokemon...")
    path = os.path.join(DATA_DIR, 'pokedex.csv')
    if not os.path.exists(path):
        print(f"Skipping Pokemon: {path} not found")
        return

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
            try:
                data.append((
                    int(row['No']), row['Name'], int(row['Generation']),
                    float(row['Height'] or 0), float(row['Weight'] or 0),
                    row['Type1'], row['Type2'] or None,
                    row['Ability1'], row['Ability2'] or None, row['Ability_Hidden'] or None,
                    float(row['Gender_Male'] or -1), float(row['Gender_Female'] or -1), float(row['Gender_Unknown'] or -1),
                    int(row['Get_Rate'] or 0), int(row['Base_Experience'] or 0), row['Experience_Type'],
                    row['Category'],
                    int(row['HP']), int(row['Attack']), int(row['Defense']),
                    int(row['SP_Attack']), int(row['SP_Defense']), int(row['Speed']),
                    int(row['Total']),
                    int(row['E_HP'] or 0), int(row['E_Attack'] or 0), int(row['E_Defense'] or 0),
                    int(row['E_SP_Attack'] or 0), int(row['E_SP_Defense'] or 0), int(row['E_Speed'] or 0)
                ))
            except ValueError as e:
                print(f"Error parsing row {row.get('Name', 'Unknown')}: {e}")

    with conn.cursor() as cur:
        execute_batch(cur, """
            INSERT INTO pokemon (
                pokedex_number, name, generation, height, weight, type1, type2,
                ability1, ability2, ability_hidden, gender_male, gender_female, gender_unknown,
                capture_rate, base_experience, experience_type, category,
                base_hp, base_attack, base_defense, base_sp_attack, base_sp_defense, base_speed, base_total,
                ev_hp, ev_attack, ev_defense, ev_sp_attack, ev_sp_defense, ev_speed
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (pokedex_number) DO NOTHING;
        """, data)
    conn.commit()
    print(f"Loaded {len(data)} pokemon.")

def load_zones_and_distances(conn):
    print("Loading Zones and Distances...")
    path = os.path.join(DATA_DIR, 'adjacency.json')
    if not os.path.exists(path):
        print(f"Skipping Adjacency: {path} not found")
        return

    with open(path, 'r', encoding='utf-8') as f:
        adj = json.load(f)

    zone_names = set(adj.keys())
    for neighbors in adj.values():
        zone_names.update(neighbors.keys())
        for connections in neighbors.values():
            for conn_info in connections:
                zone_names.add(conn_info['to'])

    with conn.cursor() as cur:
        zones_data = [(name, name) for name in zone_names]
        execute_batch(cur, """
            INSERT INTO zones (code, name) VALUES (%s, %s)
            ON CONFLICT (code) DO NOTHING;
        """, zones_data)
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT code, id FROM zones")
        zone_map = {row[0]: row[1] for row in cur.fetchall()}

    distances = []
    for transit_zone, neighbors in adj.items():
        for entry_zone, connections in neighbors.items():
            for conn_info in connections:
                exit_zone = conn_info['to']
                dist = conn_info.get('dist')
                
                if dist is None:
                    print(f"Warning: Missing distance for {entry_zone} -> {exit_zone}. Skipping.")
                    continue

                if entry_zone in zone_map and exit_zone in zone_map:
                    distances.append((zone_map[entry_zone], zone_map[exit_zone], dist))

    with conn.cursor() as cur:
        execute_batch(cur, """
            INSERT INTO zone_distances (from_zone_id, to_zone_id, distance_tiles)
            VALUES (%s, %s, %s)
            ON CONFLICT (from_zone_id, to_zone_id) DO UPDATE 
            SET distance_tiles = EXCLUDED.distance_tiles;
        """, distances)
    conn.commit()
    print(f"Loaded {len(distances)} distances.")

def load_encounters(conn):
    print("Loading Encounters...")
    path = os.path.join(DATA_DIR, 'pokemon_locations.csv')
    if not os.path.exists(path):
        print(f"Skipping Encounters: {path} not found")
        return

    mapping_path = os.path.join(DATA_DIR, 'name_mapping.json')
    name_mapping = {}
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r', encoding='utf-8') as f:
            name_mapping = json.load(f)

    with conn.cursor() as cur:
        cur.execute("SELECT name, id FROM pokemon")
        pokemon_map = {row[0].lower(): row[1] for row in cur.fetchall()}
        cur.execute("SELECT code, id FROM zones")
        zone_map = {row[0].lower(): row[1] for row in cur.fetchall()}

    encounters = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_name = row['Pokemon'].strip().lower()
            z_name = row['Ubicacion'].strip()
            
            if z_name in name_mapping:
                z_code = name_mapping[z_name]
            else:
                z_code = z_name.replace(" ", "")
                if "Ruta" in z_name:
                    z_code = z_code.replace("Ruta", "Route")
            
            p_id = pokemon_map.get(p_name)
            z_id = zone_map.get(z_code.lower())
            
            if p_id and z_id:
                try:
                    rate = float(row['Tasa_Aparicion'])
                except:
                    rate = 0
                encounters.append((
                    z_id, p_id, row['Metodo'], rate, row['Juego']
                ))

    with conn.cursor() as cur:
        execute_batch(cur, """
            INSERT INTO encounters (zone_id, pokemon_id, encounter_method, probability_percent, generation)
            VALUES (%s, %s, %s, %s, %s);
        """, encounters)
    conn.commit()
    print(f"Loaded {len(encounters)} encounters.")

if __name__ == "__main__":
    print("Starting centralized data load...")
    try:
        conn = get_db_connection()
        load_pokemon(conn)
        load_zones_and_distances(conn)
        load_encounters(conn)
        conn.close()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")

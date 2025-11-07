#!/usr/bin/env python3
"""
Script para verificar que la base de datos tiene los datos cargados
"""

import psycopg2
import os

DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'database': os.getenv('PGDATABASE', 'pokemon_ev'),
    'user': os.getenv('PGUSER', 'trainer'),
    'password': os.getenv('PGPASSWORD', 'pikachu123'),
    'port': int(os.getenv('PGPORT', 5432))
}

def verify_data():
    print("🔍 Verificando datos en la base de datos...\n")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Contar Pokémon
        cursor.execute("SELECT COUNT(*) FROM pokemon")
        pokemon_count = cursor.fetchone()[0]
        print(f"✓ Pokémon: {pokemon_count} registros")
        
        # Contar zonas
        cursor.execute("SELECT COUNT(*) FROM zones")
        zones_count = cursor.fetchone()[0]
        print(f"✓ Zonas: {zones_count} registros")
        
        # Contar encuentros
        cursor.execute("SELECT COUNT(*) FROM encounters")
        encounters_count = cursor.fetchone()[0]
        print(f"✓ Encuentros: {encounters_count} registros")
        
        # Contar distancias
        cursor.execute("SELECT COUNT(*) FROM zone_distances")
        distances_count = cursor.fetchone()[0]
        print(f"✓ Distancias: {distances_count} registros")
        
        # Mostrar algunos Pokémon con sus EVs
        print("\n📊 Muestra de Pokémon y sus EVs:")
        cursor.execute("""
            SELECT name, ev_hp, ev_attack, ev_defense, ev_sp_attack, ev_sp_defense, ev_speed
            FROM pokemon
            WHERE ev_attack > 0 OR ev_defense > 0 OR ev_speed > 0
            LIMIT 10
        """)
        
        print("\n{:<15} {:>3} {:>3} {:>3} {:>5} {:>5} {:>5}".format(
            "Pokémon", "HP", "ATK", "DEF", "SP.A", "SP.D", "SPD"))
        print("-" * 50)
        
        for row in cursor.fetchall():
            print("{:<15} {:>3} {:>3} {:>3} {:>5} {:>5} {:>5}".format(
                row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
        
        # Mostrar zonas con mejor tasa de EVs
        print("\n🎯 Top 5 zonas para entrenar Speed:")
        cursor.execute("""
            SELECT zone_name, ROUND(avg_ev_speed::numeric, 2) as speed_rate, pokemon_count
            FROM zone_ev_rates
            WHERE avg_ev_speed > 0
            ORDER BY avg_ev_speed DESC
            LIMIT 5
        """)
        
        print("\n{:<30} {:>10} {:>8}".format("Zona", "EVs/Enc", "Pokémon"))
        print("-" * 50)
        
        for row in cursor.fetchall():
            print("{:<30} {:>10} {:>8}".format(row[0], row[1], row[2]))
        
        conn.close()
        print("\n✅ Base de datos verificada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_data()

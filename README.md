# INSTRUCCIONES DE USO - BASE DE DATOS POKÉMON EV + FRONTEND APP

## Requisitos
- Docker
- Docker Compose

### Librerías para scripts de prueba y visualización (Local)
Si deseas ejecutar los scripts de visualización del grafo (`visualize_graph.py`) o probar la API localmente (`test_api.py`), necesitas instalar:

```bash
pip install networkx pyvis requests
```

## 1. Levantar servicios con docker-compose

```bash
docker-compose up -d
```

Esto creará tres contenedores: 'postgres' con el esquema y la base de datos, 'python_init' con scripts que pueblan la base de datos y 'frontend' con la App

## 2. Para conectarse a la base de datos

**Credenciales:**
- Host: localhost
- Puerto: 5432
- Base de datos: pokemon_ev
- Usuario: trainer
- Password: pikachu123

**Desde la línea de comandos:**
```bash
docker exec -it pokemon_ev_db psql -U trainer -d pokemon_ev
```

**Ejemplo de consultas útiles:**

```sql
-- Ver todos los Pokémon con sus EVs
SELECT name, ev_hp, ev_attack, ev_defense, ev_sp_attack, ev_sp_defense, ev_speed
FROM pokemon
WHERE ev_attack > 0 OR ev_defense > 0 OR ev_speed > 0
LIMIT 20;

-- Ver zonas con mejor tasa de EVs para Speed
SELECT zone_name, avg_ev_speed, pokemon_count
FROM zone_ev_rates
WHERE avg_ev_speed > 0
ORDER BY avg_ev_speed DESC;

-- Ver encuentros en una zona específica
SELECT p.name, e.min_level, e.max_level, e.probability_percent,
       p.ev_hp, p.ev_attack, p.ev_defense, p.ev_sp_attack, p.ev_sp_defense, p.ev_speed
FROM encounters e
JOIN pokemon p ON p.id = e.pokemon_id
JOIN zones z ON z.id = e.zone_id
WHERE z.code = 'kanto-route-1';

-- Ver distancias desde una zona
SELECT z2.name, zd.distance_tiles
FROM zone_distances zd
JOIN zones z1 ON z1.id = zd.from_zone_id
JOIN zones z2 ON z2.id = zd.to_zone_id
WHERE z1.code = 'kanto-pallet-town'
ORDER BY zd.distance_tiles;
```

## 3. Detener los contenedores

```bash
docker-compose down
```

## 4. Eliminar todo (incluidos los datos)

```bash
docker-compose down -v
```

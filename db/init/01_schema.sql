-- ============================================
-- ESQUEMA BASE DE DATOS EV TRAINING OPTIMIZER
-- Pokemon FireRed - Generation III
-- ============================================

-- Tipos de Pokémon
CREATE TYPE pokemon_type AS ENUM (
    'Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice',
    'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 
    'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy'
);

-- Métodos de encuentro
CREATE TYPE encounter_method_type AS ENUM (
    'Walking', 'Surfing', 'Fishing', 'Rock Smash', 'Gift', 'Stationary'
);

-- Tabla de Pokémon
CREATE TABLE pokemon (
    id SERIAL PRIMARY KEY,
    pokedex_number INTEGER NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL UNIQUE,
    generation INTEGER NOT NULL,
    height DECIMAL(3,1),
    weight DECIMAL(5,1),
    type1 VARCHAR(20) NOT NULL,
    type2 VARCHAR(20),
    ability1 VARCHAR(50),
    ability2 VARCHAR(50),
    ability_hidden VARCHAR(50),
    gender_male DECIMAL(4,1),
    gender_female DECIMAL(4,1),
    gender_unknown DECIMAL(4,1),
    capture_rate INTEGER,
    base_experience INTEGER,
    experience_type VARCHAR(20),
    category VARCHAR(50),
    base_hp INTEGER NOT NULL,
    base_attack INTEGER NOT NULL,
    base_defense INTEGER NOT NULL,
    base_sp_attack INTEGER NOT NULL,
    base_sp_defense INTEGER NOT NULL,
    base_speed INTEGER NOT NULL,
    base_total INTEGER,
    ev_hp INTEGER NOT NULL DEFAULT 0,
    ev_attack INTEGER NOT NULL DEFAULT 0,
    ev_defense INTEGER NOT NULL DEFAULT 0,
    ev_sp_attack INTEGER NOT NULL DEFAULT 0,
    ev_sp_defense INTEGER NOT NULL DEFAULT 0,
    ev_speed INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pokemon_name ON pokemon(name);
CREATE INDEX idx_pokemon_pokedex ON pokemon(pokedex_number);

-- Tabla de zonas
CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL DEFAULT 'Kanto',
    zone_type VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_zones_code ON zones(code);

-- Tabla de encuentros
CREATE TABLE encounters (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    pokemon_id INTEGER NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    encounter_method VARCHAR(50) NOT NULL,
    rarity_tier VARCHAR(50),
    min_level INTEGER,
    max_level INTEGER,
    avg_level DECIMAL(4,1),
    probability_percent DECIMAL(5,2),
    generation VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_encounters_zone ON encounters(zone_id);
CREATE INDEX idx_encounters_pokemon ON encounters(pokemon_id);
CREATE INDEX idx_encounters_method ON encounters(encounter_method);

-- Tabla de distancias entre zonas (matriz de adyacencia)
CREATE TABLE zone_distances (
    id SERIAL PRIMARY KEY,
    from_zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    to_zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    distance_tiles INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_zone_id, to_zone_id)
);

CREATE INDEX idx_distances_from ON zone_distances(from_zone_id);
CREATE INDEX idx_distances_to ON zone_distances(to_zone_id);

-- Vista para calcular EVs promedio por zona y estadística
CREATE OR REPLACE VIEW zone_ev_rates AS
SELECT 
    z.id AS zone_id,
    z.code AS zone_code,
    z.name AS zone_name,
    e.encounter_method,
    SUM(p.ev_hp * COALESCE(e.probability_percent, 0) / 100.0) AS avg_ev_hp,
    SUM(p.ev_attack * COALESCE(e.probability_percent, 0) / 100.0) AS avg_ev_attack,
    SUM(p.ev_defense * COALESCE(e.probability_percent, 0) / 100.0) AS avg_ev_defense,
    SUM(p.ev_sp_attack * COALESCE(e.probability_percent, 0) / 100.0) AS avg_ev_sp_attack,
    SUM(p.ev_sp_defense * COALESCE(e.probability_percent, 0) / 100.0) AS avg_ev_sp_defense,
    SUM(p.ev_speed * COALESCE(e.probability_percent, 0) / 100.0) AS avg_ev_speed,
    AVG(e.avg_level) AS zone_avg_level,
    COUNT(DISTINCT e.pokemon_id) AS pokemon_count
FROM zones z
JOIN encounters e ON e.zone_id = z.id
JOIN pokemon p ON p.id = e.pokemon_id
WHERE e.encounter_method = 'Walking'
GROUP BY z.id, z.code, z.name, e.encounter_method;

COMMENT ON TABLE pokemon IS 'Catálogo de Pokémon con estadísticas base y EVs otorgados';
COMMENT ON TABLE zones IS 'Zonas de entrenamiento del mapa (nodos del grafo)';
COMMENT ON TABLE encounters IS 'Encuentros de Pokémon en cada zona con probabilidades';
COMMENT ON TABLE zone_distances IS 'Distancias entre zonas en tiles (aristas del grafo)';
COMMENT ON VIEW zone_ev_rates IS 'Tasa promedio de EVs por encuentro en cada zona';

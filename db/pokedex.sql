-- ============================================
-- ESQUEMA DE BASE DE DATOS PARA EV TRAINING OPTIMIZER
-- Pokemon FireRed - Generation III
-- PostgreSQL Database Schema
-- ============================================

-- ============================================
-- TIPOS ENUMERADOS (ENUMs)
-- ============================================

-- Tipos de Pokémon (17 tipos en Generación III - Fairy no existe aún)
CREATE TYPE pokemon_type AS ENUM (
    'Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice',
    'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 
    'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel'
);

-- Estadísticas base de combate
CREATE TYPE stat_type AS ENUM (
    'HP', 'Attack', 'Defense', 'SpAttack', 'SpDefense', 'Speed'
);

-- Métodos de encuentro de Pokémon
CREATE TYPE encounter_method_type AS ENUM (
    'Walking',      -- Hierba/caminar
    'Surfing',      -- Surf en agua
    'Fishing',      -- Caña (Old Rod, Good Rod, Super Rod)
    'Rock Smash',   -- Golpe Roca
    'Gift',         -- Pokémon regalado
    'Stationary'    -- Pokémon fijo/legendario
);

-- Regiones disponibles en FireRed/LeafGreen
CREATE TYPE region_type AS ENUM (
    'Kanto',
    'Sevii Islands'  -- Islas Sevii exclusivas de FireRed/LeafGreen
);

-- Tipos de ítems que afectan entrenamiento de EVs
CREATE TYPE item_type_enum AS ENUM (
    'Vitamin',      -- Protein, Iron, Carbos, Calcium, Zinc, HP Up
    'Hold Item',    -- Macho Brace (Gen III no tiene Power Items)
    'Status'        -- Pokérus
);

-- ============================================
-- TABLAS MAESTRAS
-- ============================================

-- Tabla de Pokémon con sus estadísticas base y EVs otorgados
CREATE TABLE pokemon (
    id SERIAL PRIMARY KEY,
    pokedex_number INTEGER NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL UNIQUE,
    generation INTEGER NOT NULL,
    
    -- Características físicas
    height DECIMAL(3,1),
    weight DECIMAL(5,1),
    
    -- Tipos
    type1 pokemon_type NOT NULL,
    type2 pokemon_type,
    
    -- Habilidades
    ability1 VARCHAR(50),
    ability2 VARCHAR(50),
    ability_hidden VARCHAR(50),
    
    -- Género (porcentajes)
    gender_male DECIMAL(4,1),
    gender_female DECIMAL(4,1),
    gender_unknown DECIMAL(4,1),
    
    -- Estadísticas de captura
    capture_rate INTEGER,
    base_experience INTEGER,
    experience_type VARCHAR(20),
    category VARCHAR(50),
    
    -- Estadísticas base
    base_hp INTEGER NOT NULL,
    base_attack INTEGER NOT NULL,
    base_defense INTEGER NOT NULL,
    base_sp_attack INTEGER NOT NULL,
    base_sp_defense INTEGER NOT NULL,
    base_speed INTEGER NOT NULL,
    base_total INTEGER GENERATED ALWAYS AS (
        base_hp + base_attack + base_defense + 
        base_sp_attack + base_sp_defense + base_speed
    ) STORED,
    
    -- EVs otorgados al derrotar este Pokémon
    ev_hp INTEGER NOT NULL DEFAULT 0 CHECK (ev_hp >= 0 AND ev_hp <= 3),
    ev_attack INTEGER NOT NULL DEFAULT 0 CHECK (ev_attack >= 0 AND ev_attack <= 3),
    ev_defense INTEGER NOT NULL DEFAULT 0 CHECK (ev_defense >= 0 AND ev_defense <= 3),
    ev_sp_attack INTEGER NOT NULL DEFAULT 0 CHECK (ev_sp_attack >= 0 AND ev_sp_attack <= 3),
    ev_sp_defense INTEGER NOT NULL DEFAULT 0 CHECK (ev_sp_defense >= 0 AND ev_sp_defense <= 3),
    ev_speed INTEGER NOT NULL DEFAULT 0 CHECK (ev_speed >= 0 AND ev_speed <= 3),
    
    -- Metadatos
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint: Total EVs otorgados debe ser <= 3
    CONSTRAINT check_total_evs CHECK (
        ev_hp + ev_attack + ev_defense + 
        ev_sp_attack + ev_sp_defense + ev_speed <= 3
    )
);

-- Índices para búsquedas frecuentes
CREATE INDEX idx_pokemon_name ON pokemon(name);

-- ============================================
-- TABLAS DE UBICACIONES Y GRAFO
-- ============================================

-- Tabla de zonas (nodos del grafo)
CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE, -- 'kanto-route-1', 'kanto-viridian-forest', etc.
    name VARCHAR(100) NOT NULL,
    region region_type NOT NULL DEFAULT 'Kanto',
    zone_type VARCHAR(50), -- 'Route', 'City', 'Cave', 'Forest', etc.
    
    -- Metadata
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de encuentros (relación Zona-Pokémon)
CREATE TABLE encounters (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    pokemon_id INTEGER NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    
    -- Datos del encuentro
    encounter_method encounter_method_type NOT NULL,
    rarity_tier VARCHAR(20), -- 'Common', 'Uncommon', 'Rare', 'Very Rare'
    
    -- Probabilidad de aparición (será actualizada cuando tengas datos precisos)
    probability_percent DECIMAL(5,2), -- NULL hasta tener datos precisos
    
    -- Niveles de los Pokémon en esta zona
    min_level INTEGER NOT NULL,
    max_level INTEGER NOT NULL,
    avg_level DECIMAL(4,1) GENERATED ALWAYS AS ((min_level + max_level) / 2.0) STORED,
    
    -- Generación del encuentro
    generation INTEGER DEFAULT 3,
    
    -- Metadatos
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_zone_pokemon_method UNIQUE(zone_id, pokemon_id, encounter_method),
    CONSTRAINT check_level_range CHECK (min_level <= max_level),
    CONSTRAINT check_level_positive CHECK (min_level > 0 AND max_level > 0),
    CONSTRAINT check_probability CHECK (probability_percent IS NULL OR (probability_percent >= 0 AND probability_percent <= 100))
);

CREATE INDEX idx_encounters_pokemon ON encounters(pokemon_id);
CREATE INDEX idx_encounters_zone ON encounters(zone_id);
CREATE INDEX idx_encounters_avg_level ON encounters(avg_level);
CREATE INDEX idx_encounters_level_range ON encounters(min_level, max_level);

-- ============================================
-- TABLAS AUXILIARES
-- ============================================

-- Tabla de ítems que afectan el entrenamiento de EVs
CREATE TABLE training_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    item_type item_type_enum NOT NULL,
    
    -- Efecto sobre EVs
    ev_multiplier DECIMAL(3,1) DEFAULT 1.0, -- Macho Brace: 2.0, Pokérus: 2.0
    ev_flat_bonus INTEGER DEFAULT 0, -- Vitaminas: 10
    stat_affected stat_type, -- NULL para multiplicadores globales, específico para vitaminas
    
    -- Restricciones
    max_uses_per_pokemon INTEGER, -- NULL = ilimitado
    max_evs_applicable INTEGER DEFAULT 252, -- Vitaminas solo funcionan hasta 100 EVs
    
    -- Disponibilidad
    is_available_gen3 BOOLEAN DEFAULT TRUE,
    description TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de naturalezas
CREATE TABLE natures (
    id SERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE,
    
    -- Estadística aumentada (+10%)
    increased_stat stat_type,
    
    -- Estadística disminuida (-10%)
    decreased_stat stat_type,
    
    -- Naturalezas neutrales (ambas NULL)
    is_neutral BOOLEAN GENERATED ALWAYS AS (
        increased_stat IS NULL AND decreased_stat IS NULL
    ) STORED,
    
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_different_stats CHECK (
        increased_stat IS NULL OR 
        decreased_stat IS NULL OR 
        increased_stat != decreased_stat
    )
);

-- ============================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================

COMMENT ON TABLE pokemon IS 'Catálogo completo de Pokémon con estadísticas base y EVs otorgados al derrotarlos';
COMMENT ON TABLE zones IS 'Zonas de entrenamiento del mapa (nodos del grafo). El usuario define qué zonas son accesibles según su progreso.';
COMMENT ON TABLE encounters IS 'Encuentros de Pokémon en cada zona con probabilidades y rangos de nivel. El nivel promedio de la zona se calcula automáticamente.';
COMMENT ON TABLE training_items IS 'Ítems que modifican la ganancia de EVs (Macho Brace: 2x, Pokérus: 2x, ambos: 4x)';
COMMENT ON TABLE natures IS 'Naturalezas que modifican estadísticas en ±10% (25 naturalezas totales en Gen III)';

COMMENT ON COLUMN encounters.probability_percent IS 'Probabilidad de aparición (NULL hasta obtener datos precisos del scraping). Suma debe ser ≈100% por zona y método.';
COMMENT ON COLUMN encounters.min_level IS 'Nivel mínimo del Pokémon en esta zona';
COMMENT ON COLUMN encounters.max_level IS 'Nivel máximo del Pokémon en esta zona';
COMMENT ON COLUMN encounters.avg_level IS 'Nivel promedio calculado automáticamente. Útil para filtrar zonas según nivel del Pokémon a entrenar.';
COMMENT ON COLUMN pokemon.ev_hp IS 'EVs de HP otorgados al derrotar este Pokémon (0-3)';
COMMENT ON COLUMN training_items.ev_multiplier IS 'Multiplicador de EVs. Macho Brace: 2.0, Pokérus: 2.0, Macho Brace + Pokérus: 4.0';
COMMENT ON COLUMN training_items.stat_affected IS 'Estadística afectada por vitaminas (HP, Attack, etc.). NULL para multiplicadores globales.';

-- ============================================
-- NOTAS DE USO
-- ============================================

-- FILTRADO POR NIVEL:
-- Para entrenar un Pokémon de nivel L, se recomienda filtrar zonas donde:
--   avg_level BETWEEN (L - 5) AND (L + 10)
-- 
-- Ejemplo: Para un Pokémon nivel 15, considerar zonas con avg_level entre 10 y 25
--
-- Query ejemplo:
--   SELECT z.name, AVG(e.avg_level) as zone_avg_level
--   FROM zones z
--   JOIN encounters e ON e.zone_id = z.id
--   WHERE e.encounter_method = 'Walking'
--   GROUP BY z.id, z.name
--   HAVING AVG(e.avg_level) BETWEEN 10 AND 25;

-- RESTRICCIONES DEL USUARIO:
-- El usuario debe proporcionar:
--   1. Zona inicial (posición actual)
--   2. Lista de zonas accesibles (según HMs, medallas, progreso)
--   3. Nivel del Pokémon a entrenar
--   4. Estadística objetivo (HP, Attack, Defense, SpAttack, SpDefense, Speed)
--   5. Multiplicador de EVs (m = 1, 2, o 4)
--   6. Factor lambda (balance encuentros vs distancia)

-- ============================================
-- FIN DEL ESQUEMA
-- ============================================
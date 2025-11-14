import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';

// Constantes de la API
const API_BASE_URL = 'http://localhost:8000';
const API_URL = `${API_BASE_URL}/api/estimate_evs`;

// Simulamos la respuesta de la API de Python para la prueba inicial
const MOCK_SUCCESS_RESPONSE = {
    pokemon_name: "Charizard",
    target_stat: "Ataque Especial y Velocidad",
    total_battles: 15,
    ev_path: [
        { pokemon: "Magikarp", ev_yield: "1 Velocidad", count: 10 },
        { pokemon: "Zubat", ev_yield: "1 Ataque Especial", count: 5 }
    ],
    optimal_route_description: "La ruta óptima requiere derrotar 10 Magikarp y 5 Zubat para maximizar el Ataque Especial y la Velocidad, aprovechando las zonas de agua y cuevas cercanas a Ciudad Plateada."
};

// Componente para seleccionar Pokémon con búsqueda (Autocompletar)
const SelectWithSearch = ({ items, label, selectedItem, onSelectItem }) => {
    const [query, setQuery] = useState(selectedItem || '');
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef(null);

    const filteredItems = useMemo(() => items.filter(item =>
        item.toLowerCase().includes(query.toLowerCase())
    ), [query, items]);

    // Cierra el menú si se hace clic fuera
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSelect = (item) => {
        onSelectItem(item);
        setQuery(item);
        setIsOpen(false);
    };

    return (
        <div className="relative" ref={containerRef}>
            <label className="block text-sm font-bold text-gray-700">{label}</label>
            <input
                type="text"
                value={query}
                onChange={(e) => { setQuery(e.target.value); setIsOpen(true); onSelectItem(e.target.value); }}
                onFocus={() => setIsOpen(true)}
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 sm:text-sm"
                placeholder={`Buscar ${label}...`}
            />
            {isOpen && query.length > 0 && filteredItems.length > 0 && (
                <ul className="absolute z-10 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto mt-1">
                    {filteredItems.slice(0, 10).map(item => (
                        <li
                            key={item}
                            className="px-3 py-2 text-sm cursor-pointer hover:bg-red-500 hover:text-white"
                            onClick={() => handleSelect(item)}
                        >
                            {item}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

// Componente para manejar Zonas Accesibles como etiquetas (Tags)
const TagsInput = ({ items, label, selectedItems, onUpdateItems }) => {
    const [query, setQuery] = useState('');
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef(null);

    const availableItems = useMemo(() => items.filter(
        item => !selectedItems.includes(item)
    ), [items, selectedItems]);

    const filteredItems = useMemo(() => availableItems.filter(item =>
        item.toLowerCase().includes(query.toLowerCase())
    ), [query, availableItems]);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleAddTag = (item) => {
        if (!selectedItems.includes(item)) {
            onUpdateItems([...selectedItems, item]);
        }
        setQuery('');
        setIsOpen(false);
    };

    const handleRemoveTag = (itemToRemove) => {
        onUpdateItems(selectedItems.filter(item => item !== itemToRemove));
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && filteredItems.length > 0) {
            e.preventDefault();
            handleAddTag(filteredItems[0]);
        }
    };

    return (
        <div className="relative" ref={containerRef}>
            <label className="block text-sm font-bold text-gray-700">{label}</label>
            
            {/* Etiquetas Seleccionadas */}
            <div className="flex flex-wrap gap-2 py-2">
                {selectedItems.map(item => (
                    <span key={item} className="inline-flex items-center px-3 py-1 text-sm font-medium bg-red-100 text-red-800 rounded-full">
                        {item}
                        <button
                            type="button"
                            className="ml-2 -mr-1 h-4 w-4 flex items-center justify-center rounded-full hover:bg-red-200"
                            onClick={() => handleRemoveTag(item)}
                        >
                            &times;
                        </button>
                    </span>
                ))}
            </div>

            {/* Input de Búsqueda */}
            <input
                type="text"
                value={query}
                onChange={(e) => { setQuery(e.target.value); setIsOpen(true); }}
                onFocus={() => setIsOpen(true)}
                onKeyDown={handleKeyDown}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 sm:text-sm"
                placeholder="Escribe para buscar y añadir zonas..."
            />

            {/* Resultados de Búsqueda */}
            {isOpen && query.length > 0 && filteredItems.length > 0 && (
                <ul className="absolute z-10 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto mt-1">
                    {filteredItems.slice(0, 10).map(item => (
                        <li
                            key={item}
                            className="px-3 py-2 text-sm cursor-pointer hover:bg-red-500 hover:text-white"
                            onClick={() => handleAddTag(item)}
                        >
                            {item}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

// Componente principal de la aplicación
const App = () => {
    // --- Estados de la Aplicación ---
    const [selectedPokemon, setSelectedPokemon] = useState('Pikachu');
    const [pokemonLevel, setPokemonLevel] = useState(50);
    const [startZone, setStartZone] = useState('Ciudad Plateada');
    const [accessibleZones, setAccessibleZones] = useState(['Ruta 1', 'Bosque Verde', 'Mt. Moon']); // Array de zonas seleccionadas
    const [isZoneFilterEnabled, setIsZoneFilterEnabled] = useState(false); // NUEVO: Control para habilitar/deshabilitar el filtro
    const [targetStat, setTargetStat] = useState('Special Attack');
    const [targetEVs, setTargetEVs] = useState(252);
    const [hasMachoBrace, setHasMachoBrace] = useState(false);
    const [hasPokerus, setHasPokerus] = useState(false);
    const [lambdaPenalty, setLambdaPenalty] = useState(0.1);

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    // Estados para datos cargados desde la API
    const [pokemonList, setPokemonList] = useState([]);
    const [zonesList, setZonesList] = useState([]);
    const [loadingData, setLoadingData] = useState(true);

    // Lista de estadísticas para el selector
    const stats = useMemo(() => [
        "HP", "Attack", "Defense", "Special Attack", "Special Defense", "Speed"
    ], []);

    // Cargar Pokémon y Zonas al montar el componente
    useEffect(() => {
        const fetchInitialData = async () => {
            setLoadingData(true);
            try {
                // Cargar Pokémon
                const pokemonResponse = await fetch(`${API_BASE_URL}/api/pokemon`);
                if (!pokemonResponse.ok) throw new Error('Error al cargar Pokémon');
                const pokemonData = await pokemonResponse.json();
                const pokemonNames = pokemonData.pokemon.map(p => p.name).sort();
                setPokemonList(pokemonNames);

                // Cargar Zonas
                const zonesResponse = await fetch(`${API_BASE_URL}/api/zones`);
                if (!zonesResponse.ok) throw new Error('Error al cargar zonas');
                const zonesData = await zonesResponse.json();
                const zoneNames = zonesData.zones.map(z => z.name).sort();
                setZonesList(zoneNames);

                // Establecer valores por defecto si hay datos
                if (pokemonNames.length > 0 && !pokemonNames.includes(selectedPokemon)) {
                    setSelectedPokemon(pokemonNames[0]);
                }
                if (zoneNames.length > 0 && !zoneNames.includes(startZone)) {
                    setStartZone(zoneNames[0]);
                }
            } catch (err) {
                console.error('Error cargando datos iniciales:', err);
                setError(`Error al cargar datos: ${err.message}`);
            } finally {
                setLoadingData(false);
            }
        };

        fetchInitialData();
    }, []);

    // Simulación de lógica para Potenciadores: Si el Pokémon es inicial o legendario, se asume que se está en el endgame y los objetos están disponibles.
    useEffect(() => {
        const isAdvancedPokemon = ['Charizard', 'Mewtwo', 'Snorlax'].includes(selectedPokemon);
        if (isAdvancedPokemon) {
            // Asumimos que los potenciadores son más probables en fases avanzadas del juego
            setHasMachoBrace(true);
            setHasPokerus(true);
        } else {
            setHasMachoBrace(false);
            setHasPokerus(false);
        }
    }, [selectedPokemon]);

    // Función que simula la llamada a la API de Python
    const callPythonAPI = useCallback(async (data) => {
        // En una aplicación real, usarías 'fetch'
        console.log("Datos enviados al Backend (simulado):", data);

        // Simulación con retardo
        return new Promise((resolve) => {
            setTimeout(() => {
                if (Math.random() > 0.1) { // 90% de éxito en la simulación
                    resolve(MOCK_SUCCESS_RESPONSE);
                } else { // 10% de error
                    resolve({ error: "Error de simulación: el grafo no encontró una ruta óptima." });
                }
            }, 1500);
        });
    }, []);

    // Manejador del envío del formulario
    const handleSubmit = useCallback(async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        setResult(null);

        // Si el filtro está deshabilitado, se envía un array vacío. El backend debe interpretarlo como "todas las zonas accesibles".
        const zonesToSend = isZoneFilterEnabled ? accessibleZones : [];

        const data = {
            pokemon_name: selectedPokemon,
            pokemon_level: pokemonLevel,
            start_zone: startZone,
            accessible_zones: zonesToSend, // Usa el valor condicional
            target_stat: targetStat,
            target_evs: targetEVs,
            has_macho_brace: hasMachoBrace,
            has_pokerus: hasPokerus,
            lambda_penalty: lambdaPenalty,
        };

        try {
            const apiResult = await callPythonAPI(data);

            if (apiResult.error) {
                setError(apiResult.error);
            } else {
                setResult(apiResult);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    }, [selectedPokemon, pokemonLevel, startZone, isZoneFilterEnabled, accessibleZones, targetStat, targetEVs, hasMachoBrace, hasPokerus, lambdaPenalty, callPythonAPI]);

    // Icono de Pokebola (SVG inline para evitar dependencias)
    const PokeballIcon = ({ className }) => (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
            <path fill="currentColor" d="M256 8C119.033 8 8 119.033 8 256s111.033 248 248 248 248-111.033 248-248S392.967 8 256 8zm0 448c-110.532 0-200-89.467-200-200 0-38.354 10.741-75.143 31.543-107.411L359.411 408.457C327.143 429.259 290.354 440 256 440zM256 72c34.354 0 71.143 10.741 103.411 31.543L152.589 359.411C120.321 338.608 109.579 301.819 109.579 256c0-110.533 89.467-200 200-200zm0 184c-22.091 0-40 17.909-40 40s17.909 40 40 40 40-17.909 40-40-17.909-40-40-40z"/>
        </svg>
    );

    // Icono de flecha derecha (simulando un paso en la ruta)
    const ArrowRightIcon = (props) => (
        <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-arrow-right"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
    );

    // --- Renderizado ---
    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4 font-['Inter']">
            {loadingData ? (
                <div className="flex flex-col items-center justify-center p-10">
                    <PokeballIcon className="animate-spin w-12 h-12 text-red-600 mb-4"/>
                    <p className="text-lg font-semibold text-gray-700">Cargando datos desde la base de datos...</p>
                    <p className="text-sm text-gray-500 mt-2">Conectando con el backend</p>
                </div>
            ) : (
            <div className="w-full max-w-5xl bg-white shadow-2xl rounded-xl overflow-hidden grid md:grid-cols-3 gap-8 p-6 lg:p-10 border-t-8 border-red-500">
                
                {/* Columna 1: Título y Formulario Principal */}
                <div className="md:col-span-1 space-y-6">
                    <h1 className="text-3xl font-extrabold text-red-600 flex items-center">
                        <PokeballIcon className="w-8 h-8 mr-3 text-red-500"/>
                        Planificador de EVs
                    </h1>
                    <p className="text-gray-600">
                        Configura los parámetros de tu partida de Pokémon Fire Red para que el algoritmo de grafos halle la ruta más corta.
                    </p>

                    <form onSubmit={handleSubmit} className="space-y-4" id="ev-form">
                        
                        {/* INPUT: Pokémon (Select with Search) */}
                        <SelectWithSearch
                            label="Pokémon"
                            items={pokemonList}
                            selectedItem={selectedPokemon}
                            onSelectItem={setSelectedPokemon}
                        />

                        {/* INPUT: Nivel del Pokémon */}
                        <div>
                            <label htmlFor="pokemonLevel" className="block text-sm font-bold text-gray-700">Nivel del Pokémon</label>
                            <input
                                type="number"
                                id="pokemonLevel"
                                value={pokemonLevel}
                                onChange={(e) => setPokemonLevel(Math.max(1, Math.min(100, parseInt(e.target.value) || 1)))}
                                min="1"
                                max="100"
                                required
                                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 sm:text-sm"
                            />
                        </div>

                        {/* INPUT: Estadística Objetivo */}
                        <div>
                            <label htmlFor="targetStat" className="block text-sm font-bold text-gray-700">Estadística a Entrenar</label>
                            <select
                                id="targetStat"
                                value={targetStat}
                                onChange={(e) => setTargetStat(e.target.value)}
                                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm rounded-md shadow-sm"
                            >
                                {stats.map(stat => (
                                    <option key={stat} value={stat}>{stat}</option>
                                ))}
                            </select>
                        </div>
                        
                        {/* INPUT: Puntos de Esfuerzo Objetivo */}
                        <div>
                            <label htmlFor="targetEVs" className="block text-sm font-bold text-gray-700">EVs Deseados (en esta estadística)</label>
                            <input
                                type="number"
                                id="targetEVs"
                                value={targetEVs}
                                onChange={(e) => setTargetEVs(Math.max(1, Math.min(255, parseInt(e.target.value) || 1)))}
                                min="1" // Mínimo 1 EV
                                max="255" // Máximo 255 solicitado (aunque el máximo jugable es 252)
                                required
                                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 sm:text-sm"
                                placeholder="Máximo 252"
                            />
                            <p className="mt-1 text-xs text-gray-500">
                                (Máx. 252 en la práctica, Máx. Total 510).
                            </p>
                        </div>
                    </form>
                </div>

                {/* Columna 2: Parámetros del Grafo */}
                <div className="md:col-span-1 space-y-6 bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h2 className="text-xl font-bold text-red-600">
                        Parámetros del Mapa y Costos
                    </h2>

                    {/* INPUT: Zona Inicial (Select Box) */}
                    <div>
                        <label htmlFor="startZone" className="block text-sm font-bold text-gray-700">Zona Inicial (Posición Actual)</label>
                        <select
                            id="startZone"
                            value={startZone}
                            onChange={(e) => setStartZone(e.target.value)}
                            required
                            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm rounded-md shadow-sm"
                        >
                            {zonesList.map(zone => (
                                <option key={zone} value={zone}>{zone}</option>
                            ))}
                        </select>
                    </div>

                    {/* CONTROL Y INPUT: Zonas Accesibles */}
                    <div className="pt-2 border-t border-gray-200">
                        {/* Checkbox/Toggle para habilitar el filtro */}
                        <div className="flex items-center justify-between mb-2">
                            <label htmlFor="enableZoneFilter" className="block text-sm font-bold text-gray-700 items-center">
                                Habilitar Filtro de Zonas Accesibles
                            </label>
                            <input
                                id="enableZoneFilter"
                                type="checkbox"
                                checked={isZoneFilterEnabled}
                                onChange={(e) => setIsZoneFilterEnabled(e.target.checked)}
                                className="h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                            />
                        </div>
                        <p className="mt-1 text-xs text-gray-500 mb-4">
                            Este es un multiparámetro opcional. Si está desactivado, se asume que todas las zonas son accesibles.
                        </p>

                        {/* INPUT: Zonas Accesibles (Tags Input) - Habilitado/Deshabilitado */}
                        <div className={!isZoneFilterEnabled ? 'opacity-50 pointer-events-none' : ''}>
                            <TagsInput
                                label="Zonas Accesibles"
                                items={zonesList}
                                selectedItems={accessibleZones}
                                onUpdateItems={setAccessibleZones}
                            />
                        </div>
                    </div>
                    
                    {/* INPUT: Factor de Penalización Lambda */}
                    <div>
                        <label htmlFor="lambdaPenalty" className="block text-sm font-bold text-gray-700">Factor de Penalización λ (Desplazamiento)</label>
                        <input
                            type="number"
                            id="lambdaPenalty"
                            value={lambdaPenalty}
                            onChange={(e) => setLambdaPenalty(parseFloat(e.target.value) || 0)}
                            min="0"
                            step="0.01"
                            required
                            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 sm:text-sm"
                        />
                        <p className="mt-1 text-xs text-gray-500">
                            Coste de viajar entre zonas (λ * distancia). Típicamente entre 0.0 y 1.0.
                        </p>
                    </div>

                    {/* INPUTS: Objetos/Estado (Potenciadores) */}
                    <div className="pt-2 border-t border-gray-200 space-y-2">
                        <label className="block text-sm font-bold text-gray-700">Potenciadores Disponibles</label>
                        <p className="text-xs text-red-700 font-semibold mb-2">
                            Ajuste dinámico basado en Pokémon:
                        </p>
                        <div className="flex items-center">
                            <input
                                id="hasMachoBrace"
                                type="checkbox"
                                checked={hasMachoBrace}
                                onChange={(e) => setHasMachoBrace(e.target.checked)}
                                className="h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                            />
                            <label htmlFor="hasMachoBrace" className="ml-2 block text-sm text-gray-700">
                                Brazal Firme (Macho Brace)
                            </label>
                        </div>
                        <div className="flex items-center">
                            <input
                                id="hasPokerus"
                                type="checkbox"
                                checked={hasPokerus}
                                onChange={(e) => setHasPokerus(e.target.checked)}
                                className="h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                            />
                            <label htmlFor="hasPokerus" className="ml-2 block text-sm text-gray-700">
                                Pokérus (Doble EVs)
                            </label>
                        </div>
                    </div>

                    {/* Botón de Cálculo (Repetido para visibilidad) */}
                    <button
                        type="submit"
                        disabled={isLoading}
                        form="ev-form"
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-lg text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition duration-150"
                    >
                        {isLoading ? 'Calculando Ruta Óptima...' : 'Calcular Ruta de Entrenamiento'}
                    </button>
                </div>


                {/* Columna 3: Resultados */}
                <div className="md:col-span-1 bg-gray-100 p-6 rounded-lg shadow-inner space-y-6">
                    <h2 className="text-xl font-bold text-gray-800 border-b pb-2 border-gray-300">
                        {result ? `Ruta de Entrenamiento para ${result.pokemon_name}` : 'Resultados del Algoritmo'}
                    </h2>
                    
                    {/* Mensajes de estado */}
                    {isLoading && (
                        <div className="flex items-center justify-center p-10 text-red-600 font-semibold">
                            <PokeballIcon className="animate-spin w-6 h-6 mr-2"/>
                            El algoritmo de grafos está trabajando...
                        </div>
                    )}

                    {error && (
                        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-lg" role="alert">
                            <p className="font-bold">Error de Cálculo</p>
                            <p>{error}</p>
                        </div>
                    )}

                    {/* Contenido de Resultados (Mock) */}
                    {result && (
                        <div className="space-y-4">
                            
                            {/* Resumen del Cálculo */}
                            <div className="bg-white p-4 rounded-lg shadow">
                                <p className="text-sm font-medium text-gray-600">Estadísticas Maximizadas:</p>
                                <p className="text-lg font-bold text-red-700">{result.target_stat}</p>
                                <p className="text-sm mt-2 text-gray-600">Batallas Totales Necesarias:</p>
                                <p className="text-2xl font-extrabold text-red-500">{result.total_battles}</p>
                            </div>

                            {/* Descripción de la Ruta */}
                            <div className="text-sm text-gray-700">
                                <p className="font-semibold mb-2">Descripción Detallada (Salida del Algoritmo):</p>
                                <p>{result.optimal_route_description}</p>
                            </div>

                            {/* Visualización de la Ruta (Simulación de Grafo) */}
                            <div className="pt-2">
                                <p className="font-semibold text-gray-800 mb-3">Pasos de la Ruta Óptima:</p>
                                <div className="space-y-2">
                                    {result.ev_path.map((step, index) => (
                                        <div key={index} className="flex items-center space-x-2 p-3 bg-white rounded-md shadow-sm border border-gray-200">
                                            <div className="text-center font-bold text-red-500 min-w-12">
                                                {step.count}x
                                            </div>
                                            <div className="flex-1">
                                                <p className="text-sm font-medium">{step.pokemon}</p>
                                                <p className="text-xs text-gray-500">Da: {step.ev_yield}</p>
                                            </div>
                                            {index < result.ev_path.length - 1 && (
                                                <ArrowRightIcon className="w-5 h-5 text-gray-400" />
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
            )}
        </div>
    );
};

export default App;
import React, { useState, useEffect, useCallback } from 'react';
import OptimizationForm from './components/OptimizationForm';
import ResultsDisplay from './components/ResultsDisplay';
import MapVisualization from './components/MapVisualization';

const API_BASE_URL = 'http://localhost:8000';

const App = () => {
    const [pokemonList, setPokemonList] = useState([]);
    const [zonesList, setZonesList] = useState([]);
    const [loadingData, setLoadingData] = useState(true);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [showMap, setShowMap] = useState(false);

    // Fetch initial data
    useEffect(() => {
        const fetchInitialData = async () => {
            setLoadingData(true);
            try {
                // Fetch Pokemon
                const pokemonResponse = await fetch(`${API_BASE_URL}/api/pokemon`);
                if (!pokemonResponse.ok) throw new Error('Error loading Pokemon data');
                const pokemonData = await pokemonResponse.json();
                setPokemonList(pokemonData.pokemon.map(p => p.name).sort());

                // Fetch Zones
                const zonesResponse = await fetch(`${API_BASE_URL}/api/zones`);
                if (!zonesResponse.ok) throw new Error('Error loading zones data');
                const zonesData = await zonesResponse.json();
                setZonesList(zonesData.zones.map(z => z.name).sort());

            } catch (err) {
                console.error('Error loading initial data:', err);
                setError(`Failed to load data: ${err.message}`);
            } finally {
                setLoadingData(false);
            }
        };

        fetchInitialData();
    }, []);

    const handleOptimizationSubmit = useCallback(async (formData) => {
        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch(`${API_BASE_URL}/api/optimize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Optimization failed');
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            console.error('Optimization error:', err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Icono de Pokebola (SVG inline)
    const PokeballIcon = ({ className }) => (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
            <path fill="currentColor" d="M256 8C119.033 8 8 119.033 8 256s111.033 248 248 248 248-111.033 248-248S392.967 8 256 8zm0 448c-110.532 0-200-89.467-200-200 0-38.354 10.741-75.143 31.543-107.411L359.411 408.457C327.143 429.259 290.354 440 256 440zM256 72c34.354 0 71.143 10.741 103.411 31.543L152.589 359.411C120.321 338.608 109.579 301.819 109.579 256c0-110.533 89.467-200 200-200zm0 184c-22.091 0-40 17.909-40 40s17.909 40 40 40 40-17.909 40-40-17.909-40-40-40z"/>
        </svg>
    );

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4 font-['Inter']">
            {loadingData ? (
                <div className="flex flex-col items-center justify-center p-10">
                    <PokeballIcon className="animate-spin w-12 h-12 text-red-600 mb-4"/>
                    <p className="text-lg font-semibold text-gray-700">Loading game data...</p>
                </div>
            ) : (
                <div className="w-full max-w-6xl bg-white shadow-2xl rounded-xl grid md:grid-cols-3 gap-8 p-6 lg:p-10 border-t-8 border-red-500">
                    
                    {/* Header & Form Column */}
                    <div className="md:col-span-2 space-y-6">
                        <div className="flex justify-between items-center">
                            <h1 className="text-3xl font-extrabold text-red-600 flex items-center">
                                <PokeballIcon className="w-8 h-8 mr-3 text-red-500"/>
                                EV Optimization Planner
                            </h1>
                            <button
                                onClick={() => setShowMap(!showMap)}
                                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                            >
                                {showMap ? 'Hide Map' : 'Show Map'}
                            </button>
                        </div>
                        
                        {showMap ? (
                            <MapVisualization />
                        ) : (
                            <>
                                <p className="text-gray-600">
                                    Configure your Pokemon and training goals to find the optimal EV training route.
                                </p>

                                <OptimizationForm 
                                    pokemonList={pokemonList}
                                    zonesList={zonesList}
                                    onSubmit={handleOptimizationSubmit}
                                    isLoading={isLoading}
                                />
                            </>
                        )}
                    </div>

                    {/* Results Column */}
                    {!showMap && (
                        <div className="md:col-span-1">
                            <ResultsDisplay 
                                result={result}
                                isLoading={isLoading}
                                error={error}
                            />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default App;
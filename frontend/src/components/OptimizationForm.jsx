import React, { useState, useEffect } from 'react';
import SelectWithSearch from './SelectWithSearch';

const STATS = ["HP", "Attack", "Defense", "Special Attack", "Special Defense", "Speed"];

const OptimizationForm = ({ pokemonList, zoneList, onSubmit, isLoading }) => {
    const [selectedPokemon, setSelectedPokemon] = useState(null);
    const [startZone, setStartZone] = useState(null);
    const [level, setLevel] = useState(50);
    const [lambda, setLambda] = useState(0.5);
    const [heldItem, setHeldItem] = useState("");
    const [hasPokerus, setHasPokerus] = useState(false);
    
    const [currentEvs, setCurrentEvs] = useState({
        "HP": 0, "Attack": 0, "Defense": 0, 
        "Special Attack": 0, "Special Defense": 0, "Speed": 0
    });
    
    const [targetEvs, setTargetEvs] = useState({
        "HP": 0, "Attack": 0, "Defense": 0, 
        "Special Attack": 0, "Special Defense": 0, "Speed": 0
    });

    // Auto-fill current EVs when pokemon is selected (base stats are not EVs, but maybe we want to show them?)
    // For now, just keep 0.

    const handleStatChange = (stat, value, isTarget) => {
        const val = Math.max(0, Math.min(252, parseInt(value) || 0));
        if (isTarget) {
            setTargetEvs(prev => ({ ...prev, [stat]: val }));
        } else {
            setCurrentEvs(prev => ({ ...prev, [stat]: val }));
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!selectedPokemon) {
            alert("Por favor selecciona o escribe un Pokémon.");
            return;
        }
        if (!startZone) {
            alert("Por favor selecciona o escribe una zona de inicio.");
            return;
        }
        
        onSubmit({
            pokemon_name: selectedPokemon,
            start_zone: startZone,
            current_evs: currentEvs,
            target_evs: targetEvs,
            pokemon_level: level,
            lambda_penalty: lambda,
            held_item: heldItem || null,
            has_pokerus: hasPokerus
        });
    };

    return (
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Configuración de Entrenamiento</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Selección de Pokemon y Zona */}
                <div>
                    <SelectWithSearch 
                        items={pokemonList} 
                        label="Pokémon" 
                        selectedItem={selectedPokemon} 
                        onSelectItem={setSelectedPokemon}
                        placeholder="Ej: Charmander"
                    />
                    
                    <SelectWithSearch 
                        items={zoneList} 
                        label="Zona de Inicio" 
                        selectedItem={startZone} 
                        onSelectItem={setStartZone}
                        placeholder="Ej: Pallet Town"
                    />
                    
                    <div className="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-1">Nivel</label>
                            <input 
                                type="number" 
                                value={level} 
                                onChange={(e) => setLevel(parseInt(e.target.value))}
                                className="w-full p-2 border border-gray-300 rounded"
                                min="1" max="100"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-1">Objeto</label>
                            <select 
                                value={heldItem} 
                                onChange={(e) => setHeldItem(e.target.value)}
                                className="w-full p-2 border border-gray-300 rounded"
                            >
                                <option value="">Ninguno</option>
                                <option value="Macho Brace">Macho Brace (x2)</option>
                                <option value="Power Weight">Power Weight (HP)</option>
                                <option value="Power Bracer">Power Bracer (Atk)</option>
                                <option value="Power Belt">Power Belt (Def)</option>
                                <option value="Power Lens">Power Lens (SpA)</option>
                                <option value="Power Band">Power Band (SpD)</option>
                                <option value="Power Anklet">Power Anklet (Spe)</option>
                            </select>
                        </div>
                    </div>

                    <div className="mb-4 flex items-center">
                        <input 
                            type="checkbox" 
                            id="pokerus"
                            checked={hasPokerus}
                            onChange={(e) => setHasPokerus(e.target.checked)}
                            className="mr-2 h-4 w-4 text-blue-600"
                        />
                        <label htmlFor="pokerus" className="text-sm font-bold text-gray-700">Tiene Pokérus</label>
                    </div>

                    <div className="mb-4">
                        <label className="block text-sm font-bold text-gray-700 mb-1">
                            Preferencia (Lambda): {lambda}
                        </label>
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                            <span>Más Encuentros</span>
                            <span>Más Distancia</span>
                        </div>
                        <input 
                            type="range" 
                            min="0" max="1" step="0.1" 
                            value={lambda} 
                            onChange={(e) => setLambda(parseFloat(e.target.value))}
                            className="w-full"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            0 = Minimizar Encuentros (Viajar más)<br/>
                            1 = Minimizar Distancia (Pelear más cerca)
                        </p>
                    </div>
                </div>

                {/* Stats */}
                <div>
                    <h3 className="font-bold text-lg mb-3">EVs Actuales vs Objetivo</h3>
                    <div className="space-y-3">
                        {STATS.map(stat => (
                            <div key={stat} className="flex items-center space-x-2">
                                <span className="w-24 text-sm font-medium">{stat}</span>
                                <input 
                                    type="number" 
                                    placeholder="Actual"
                                    value={currentEvs[stat]}
                                    onChange={(e) => handleStatChange(stat, e.target.value, false)}
                                    className="w-20 p-1 border rounded text-sm"
                                />
                                <span className="text-gray-400">→</span>
                                <input 
                                    type="number" 
                                    placeholder="Meta"
                                    value={targetEvs[stat]}
                                    onChange={(e) => handleStatChange(stat, e.target.value, true)}
                                    className="w-20 p-1 border rounded text-sm"
                                />
                            </div>
                        ))}
                    </div>
                    
                    <div className="mt-4 text-sm text-gray-600">
                        Total Objetivo: {Object.values(targetEvs).reduce((a,b)=>a+b, 0)} / 510
                    </div>
                </div>
            </div>

            <div className="mt-8">
                <button 
                    type="submit" 
                    disabled={isLoading}
                    className={`w-full py-3 px-4 rounded font-bold text-white transition-colors ${
                        isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                >
                    {isLoading ? 'Calculando Ruta Óptima...' : 'Calcular Ruta de Entrenamiento'}
                </button>
            </div>
        </form>
    );
};

export default OptimizationForm;

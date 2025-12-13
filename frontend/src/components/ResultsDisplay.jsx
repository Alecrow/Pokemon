import React from 'react';

const ResultsDisplay = ({ result }) => {
    if (!result) return null;

    const { path, total_distance, total_encounters, final_stats } = result;

    return (
        <div className="bg-white p-6 rounded-lg shadow-md mt-8">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">Plan de Entrenamiento Óptimo</h2>
            
            {/* Resumen */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div className="bg-blue-50 p-4 rounded border border-blue-100">
                    <div className="text-sm text-blue-600 font-bold uppercase">Distancia Total</div>
                    <div className="text-2xl font-bold text-blue-800">{total_distance} tiles</div>
                </div>
                <div className="bg-red-50 p-4 rounded border border-red-100">
                    <div className="text-sm text-red-600 font-bold uppercase">Encuentros Totales</div>
                    <div className="text-2xl font-bold text-red-800">{total_encounters} batallas</div>
                </div>
                <div className="bg-green-50 p-4 rounded border border-green-100">
                    <div className="text-sm text-green-600 font-bold uppercase">Pasos del Plan</div>
                    <div className="text-2xl font-bold text-green-800">{path.length} pasos</div>
                </div>
            </div>

            {/* Ruta Paso a Paso */}
            <div className="space-y-4">
                <h3 className="font-bold text-lg text-gray-700">Ruta Detallada</h3>
                {path.map((step, index) => (
                    <div key={index} className="flex items-start p-4 border rounded-lg hover:shadow-sm transition-shadow">
                        <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-gray-200 rounded-full font-bold text-gray-600 mr-4">
                            {index + 1}
                        </div>
                        <div className="flex-grow">
                            {step.type === 'travel' ? (
                                <div>
                                    <h4 className="font-bold text-blue-600">Viajar a {step.to}</h4>
                                    <p className="text-sm text-gray-600">Distancia: {step.distance} tiles</p>
                                </div>
                            ) : (
                                <div>
                                    <h4 className="font-bold text-red-600">Entrenar en {step.zone}</h4>
                                    <div className="mt-2 bg-gray-50 p-3 rounded text-sm">
                                        <p className="font-medium">Objetivo: <span className="text-red-700">{step.count}x {step.target_pokemon}</span></p>
                                        <p className="text-gray-500">Foco: {step.stat_focus}</p>
                                        <div className="mt-1 text-xs text-gray-400">
                                            Ganancia estimada: {Object.entries(step.gained_evs).map(([k,v]) => v > 0 ? `${k}: +${v} ` : '').join(', ')}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Stats Finales */}
            <div className="mt-8 pt-6 border-t">
                <h3 className="font-bold text-lg text-gray-700 mb-3">Estadísticas Finales Estimadas</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {Object.entries(final_stats).map(([stat, val]) => (
                        <div key={stat} className="flex justify-between bg-gray-50 p-2 rounded text-sm">
                            <span className="font-medium">{stat}</span>
                            <span className={`font-bold ${val >= 252 ? 'text-green-600' : 'text-gray-800'}`}>{val}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ResultsDisplay;

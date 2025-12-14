import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';

const MapVisualization = () => {
    const containerRef = useRef(null);
    const [graphData, setGraphData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchGraph = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/graph');
                if (!response.ok) {
                    throw new Error('Failed to fetch graph data');
                }
                const data = await response.json();
                setGraphData(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchGraph();
    }, []);

    useEffect(() => {
        if (graphData && containerRef.current) {
            const nodes = [];
            const edges = [];
            const addedNodes = new Set();

            // Process adjacency list into nodes and edges
            Object.entries(graphData).forEach(([sourceZone, connections]) => {
                if (!addedNodes.has(sourceZone)) {
                    nodes.push({
                        id: sourceZone,
                        label: sourceZone,
                        title: sourceZone,
                        group: 'Zone',
                        shape: 'dot',
                        size: 10,
                        font: { color: 'white' }
                    });
                    addedNodes.add(sourceZone);
                }

                Object.entries(connections).forEach(([targetLabel, paths]) => {
                    paths.forEach(path => {
                        const targetZone = path.to;
                        const dist = path.dist;

                        if (targetZone) {
                            if (!addedNodes.has(targetZone)) {
                                nodes.push({
                                    id: targetZone,
                                    label: targetZone,
                                    title: targetZone,
                                    group: 'Zone',
                                    shape: 'dot',
                                    size: 10,
                                    font: { color: 'white' }
                                });
                                addedNodes.add(targetZone);
                            }

                            edges.push({
                                from: sourceZone,
                                to: targetZone,
                                label: String(dist),
                                title: `Dist: ${dist} tiles`,
                                arrows: 'to',
                                color: { inherit: true }
                            });
                        }
                    });
                });
            });

            const data = { nodes, edges };
            const options = {
                height: '750px',
                width: '100%',
                nodes: {
                    font: { size: 16 },
                    borderWidth: 2,
                    shadow: true
                },
                edges: {
                    smooth: { type: 'continuous' },
                    color: { color: '#848484', highlight: '#848484', hover: '#848484', opacity: 1.0 }
                },
                physics: {
                    forceAtlas2Based: {
                        gravitationalConstant: -50,
                        centralGravity: 0.01,
                        springLength: 100,
                        springConstant: 0.08
                    },
                    maxVelocity: 50,
                    solver: 'forceAtlas2Based',
                    timestep: 0.35,
                    stabilization: { enabled: true, iterations: 1000 }
                },
                interaction: { hover: true }
            };

            new Network(containerRef.current, data, options);
        }
    }, [graphData]);

    if (loading) return <div className="text-white text-center p-4">Loading map...</div>;
    if (error) return <div className="text-red-500 text-center p-4">Error: {error}</div>;

    return (
        <div className="w-full h-[800px] bg-[#222222] border border-gray-600 rounded-lg overflow-hidden">
            <div ref={containerRef} className="w-full h-full" />
        </div>
    );
};

export default MapVisualization;

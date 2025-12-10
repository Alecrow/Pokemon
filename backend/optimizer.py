import heapq
import math
import re
from typing import Dict, List, Tuple, Optional, Any
from graph import PokemonGraph
from database import get_zone_ev_yields, get_zone_details

class EVOptimizer:
    def __init__(self, graph: PokemonGraph):
        self.graph = graph

    def _get_db_code(self, graph_zone: str) -> str:
        """
        Maps Graph Zone Name (e.g. 'Route16_East') to DB Code (e.g. 'kanto-route-16').
        """
        # 1. Convert CamelCase to kebab-case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', graph_zone)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
        s2 = s2.replace("_", "-")
        
        # 2. Construct candidate
        candidate = f"kanto-{s2}"
        return candidate

    def _match_yield(self, graph_zone: str, yields_map: Dict[str, float]) -> float:
        """
        Tries to find the yield for a graph zone in the yields map.
        Handles suffix mismatches (e.g. Route16_East vs kanto-route-16).
        """
        db_code = self._get_db_code(graph_zone)
        
        # Exact match
        if db_code in yields_map:
            return yields_map[db_code]
        
        # Prefix match (remove -east, -west, -north, -south)
        # Try removing last part
        if "-" in db_code:
            prefix = db_code.rsplit("-", 1)[0]
            if prefix in yields_map:
                return yields_map[prefix]
            
            # Try removing last two parts? (e.g. route-2-viridian-forest-north-entrance)
            # This is getting hacky.
            
        return 0.0

    def _calculate_distances(self, start_zone: str) -> Dict[str, int]:
        """
        Calculates min distances from start_zone to all other zones using Dijkstra.
        Returns {zone_name: distance_in_tiles}
        """
        pq = []
        min_dists = {} # (Zone, Label) -> distance
        
        # Initial states: All labels in start_zone
        start_labels = self.graph.adjacency_data.get(start_zone, {}).keys()
        for lbl in start_labels:
            state = (start_zone, lbl)
            min_dists[state] = 0
            heapq.heappush(pq, (0, start_zone, lbl))
            
        # Also track min distance to a Zone (ignoring label)
        zone_min_dists = {start_zone: 0}

        while pq:
            d, zone, label = heapq.heappop(pq)
            
            if d > min_dists.get((zone, label), float('inf')):
                continue
            
            # Update zone min dist
            if d < zone_min_dists.get(zone, float('inf')):
                zone_min_dists[zone] = d
            
            # Neighbors (Intra-zone)
            intra_neighbors = self.graph.get_intra_zone_neighbors(zone, label)
            for target_lbl, dist in intra_neighbors:
                new_dist = d + dist
                if new_dist < min_dists.get((zone, target_lbl), float('inf')):
                    min_dists[(zone, target_lbl)] = new_dist
                    heapq.heappush(pq, (new_dist, zone, target_lbl))
            
            # Neighbors (Inter-zone)
            target_zone = self.graph.get_inter_zone_neighbor(zone, label)
            if target_zone:
                # Target label in target_zone is usually current_zone name
                target_lbl = zone
                # Verify
                if target_zone in self.graph.adjacency_data and target_lbl in self.graph.adjacency_data[target_zone]:
                    new_dist = d # 0 cost to cross
                    if new_dist < min_dists.get((target_zone, target_lbl), float('inf')):
                        min_dists[(target_zone, target_lbl)] = new_dist
                        heapq.heappush(pq, (new_dist, target_zone, target_lbl))
        
        return zone_min_dists

    def find_optimal_zone(self, start_zone: str, target_evs: int, target_stat: str, lambda_val: float, pokemon_level: int = 50) -> Dict[str, Any]:
        """
        Finds the optimal zone to grind EVs, minimizing Z = Encounters + lambda * Distance.
        """
        # 1. Get Yields for all zones
        yields_map = get_zone_ev_yields(target_stat, pokemon_level)
        
        # 2. Calculate Distances from StartZone to ALL reachable (Zone, Label)
        zone_min_dists = self._calculate_distances(start_zone)

        # 3. Evaluate Objective Function for each Zone

        # 3. Evaluate Objective Function for each Zone
        best_zone = None
        min_Z = float('inf')
        
        results = []
        
        for zone, dist in zone_min_dists.items():
            ev_yield = self._match_yield(zone, yields_map)
            if ev_yield <= 0:
                continue
                
            # x_i: Encounters needed
            encounters = math.ceil(target_evs / ev_yield)
            
            # Z = x_i + lambda * d_ij
            # Note: dist is in "tiles". lambda scales tiles to "encounter equivalents".
            Z = encounters + (lambda_val * dist)
            
            if Z < min_Z:
                min_Z = Z
                
                # Obtener detalles de los Pokémon en la zona óptima
                db_code = self._get_db_code(zone)
                # Intentar match exacto o prefijo si no encuentra
                if db_code not in yields_map and "-" in db_code:
                     prefix = db_code.rsplit("-", 1)[0]
                     if prefix in yields_map:
                         db_code = prefix
                
                pokemon_details = get_zone_details(db_code, target_stat, pokemon_level)
                
                best_zone = {
                    "zone": zone,
                    "ev_yield": ev_yield,
                    "encounters": encounters,
                    "distance": dist,
                    "total_cost": Z,
                    "pokemon_list": [
                        {
                            "name": p['name'],
                            "ev_yield": p['ev_yield'],
                            "probability": f"{p['probability_percent']}%",
                            "level": int(p['avg_level'])
                        } for p in pokemon_details
                    ]
                }
        
        return best_zone

    def find_optimal_multistat_route(self, start_zone: str, targets: Dict[str, int], lambda_val: float, pokemon_level: int = 50) -> Dict[str, Any]:
        """
        Finds the optimal sequence of zones to grind multiple stats.
        targets: {"Attack": 252, "Speed": 252, ...}
        """
        import itertools

        # 1. Filter stats with > 0 EVs
        active_targets = [(stat, evs) for stat, evs in targets.items() if evs > 0]
        if not active_targets:
            print("DEBUG: No active targets.")
            return None

        # 2. Pre-calculate yields for all active stats for all zones
        # yields_cache[stat] = {zone: yield}
        yields_cache = {}
        for stat, _ in active_targets:
            yields_cache[stat] = get_zone_ev_yields(stat, pokemon_level)
            print(f"DEBUG: Yields for {stat} (Level {pokemon_level}): Found {len(yields_cache[stat])} zones.")
            # print(f"DEBUG: Sample yields for {stat}: {list(yields_cache[stat].items())[:3]}")

        # Check if graph is loaded
        if not self.graph.adjacency_data:
            print("DEBUG: Graph adjacency data is empty!")
            return None
        else:
            print(f"DEBUG: Graph has {len(self.graph.adjacency_data)} zones.")

        # 3. Try all permutations of stats
        best_route = None
        min_total_cost = float('inf')

        for perm in itertools.permutations(active_targets):
            print(f"DEBUG: Testing permutation: {[p[0] for p in perm]}")
            # perm is a tuple of (stat, evs)
            
            # We use a greedy approach for each step in the permutation for simplicity,
            # or a Viterbi-like approach if we want true optimality.
            # Given the graph size, let's do a simplified Viterbi (Layered Graph Search).
            
            # Layer 0: Start Node
            # current_layer = { zone_name: (cumulative_cost, path_list) }
            current_layer = {start_zone: (0, [])}
            
            for stat, target_evs in perm:
                next_layer = {}
                
                # Identify candidate zones for this stat (yield > 0)
                # Optimization: Only consider top N zones or all valid zones?
                # Let's take all valid zones to be safe.
                # valid_zones = [z for z, y in yields_cache[stat].items() if y > 0]
                
                # We need to map DB codes back to Graph Zones?
                # yields_cache keys are DB codes (kanto-route-1).
                # We need to know which Graph Zone corresponds to kanto-route-1.
                # This reverse mapping is tricky because _get_db_code is one-way heuristic.
                # Let's iterate over Graph Zones and check match.
                
                graph_candidates = []
                for g_zone in self.graph.adjacency_data.keys():
                    y = self._match_yield(g_zone, yields_cache[stat])
                    if y > 0:
                        graph_candidates.append((g_zone, y))
                
                print(f"DEBUG: Stat {stat} has {len(graph_candidates)} graph candidates.")

                if not graph_candidates:
                    # Cannot fulfill this stat
                    print(f"DEBUG: No candidates for {stat}. Breaking permutation.")
                    current_layer = {}
                    break

                # For each candidate zone in this layer
                for cand_zone, yield_val in graph_candidates:
                    encounters = math.ceil(target_evs / yield_val)
                    
                    # Find best previous zone to come from
                    best_prev_cost = float('inf')
                    best_prev_path = []
                    
                    # We need distances from ALL nodes in current_layer to cand_zone.
                    # This is expensive if we run Dijkstra for each pair.
                    # Optimization: Run Dijkstra from cand_zone backwards? Or just run from all current_layer nodes?
                    # If current_layer has 1 node (start), it's 1 Dijkstra.
                    # If current_layer has 20 nodes, it's 20 Dijkstras.
                    # Better: Run Dijkstra from cand_zone (as source) to find distances TO it?
                    # Since graph is undirected for movement (mostly), dist(A,B) ~ dist(B,A).
                    # But our graph is directed.
                    # Let's assume we run Dijkstra from each unique node in current_layer.
                    # To avoid re-running, we can cache distances.
                    
                    # Actually, let's just pick the "Best" 3 candidates per stat to limit branching factor.
                    pass

                # Simplified Greedy Approach for Performance:
                # Instead of full Viterbi, just pick the best zone for the current stat
                # considering the distance from the *current best* location.
                # But "current best" might be a local optimum.
                
                # Let's stick to Viterbi but limit candidates to Top 5 by Yield.
                graph_candidates.sort(key=lambda x: x[1], reverse=True)
                top_candidates = graph_candidates[:5]
                
                # If no candidates found for this stat, break this permutation
                if not top_candidates:
                    current_layer = {}
                    break

                # Calculate distances from all unique zones in current_layer
                # We can optimize by grouping:
                # For each `prev_zone` in `current_layer`, we need `dist(prev_zone, cand_zone)`.
                # We can compute `dists = _calculate_distances(prev_zone)` once per prev_zone.
                
                unique_prev_zones = list(current_layer.keys())
                
                # Optimization: If current_layer has too many nodes, prune to top K best paths so far
                if len(unique_prev_zones) > 5:
                    unique_prev_zones.sort(key=lambda z: current_layer[z][0])
                    unique_prev_zones = unique_prev_zones[:5]

                for prev_zone in unique_prev_zones:
                    prev_cost, prev_path = current_layer[prev_zone]
                    
                    # Calculate distances from this prev_zone to all top_candidates
                    # We run Dijkstra once from prev_zone
                    dists_from_prev = self._calculate_distances(prev_zone)
                    
                    for cand_zone, yield_val in top_candidates:
                        # If cand_zone is not reachable, skip
                        if cand_zone not in dists_from_prev:
                            # print(f"DEBUG: {cand_zone} unreachable from {prev_zone}")
                            continue 
                            
                        dist = dists_from_prev[cand_zone]
                        encounters = math.ceil(target_evs / yield_val)
                        step_cost = encounters + (lambda_val * dist)
                        total_cost = prev_cost + step_cost
                        
                        # Update next_layer
                        if cand_zone not in next_layer or total_cost < next_layer[cand_zone][0]:
                            # Get pokemon details for this step
                            db_code = self._get_db_code(cand_zone)
                            # Fix prefix matching logic duplication
                            if db_code not in yields_cache[stat] and "-" in db_code:
                                prefix = db_code.rsplit("-", 1)[0]
                                if prefix in yields_cache[stat]:
                                    db_code = prefix
                                    
                            pkmn_details = get_zone_details(db_code, stat, pokemon_level)
                            
                            step_info = {
                                "stat": stat,
                                "zone": cand_zone,
                                "ev_yield": yield_val,
                                "encounters": encounters,
                                "distance": dist,
                                "step_cost": step_cost,
                                "pokemon_list": [
                                    {
                                        "name": p['name'],
                                        "ev_yield": p['ev_yield'],
                                        "probability": f"{p['probability_percent']}%",
                                        "level": int(p['avg_level'])
                                    } for p in pkmn_details
                                ]
                            }
                            
                            next_layer[cand_zone] = (total_cost, prev_path + [step_info])
                
                current_layer = next_layer
                if not current_layer:
                    print(f"DEBUG: Dead end for permutation at stat {stat}. No reachable candidates.")
                    break # Dead end for this permutation
            
            # End of permutation
            if current_layer:
                # Find best end state
                for end_zone, (cost, path) in current_layer.items():
                    if cost < min_total_cost:
                        min_total_cost = cost
                        best_route = path

        if best_route:
            return {
                "total_cost": min_total_cost,
                "route": best_route
            }
        return None

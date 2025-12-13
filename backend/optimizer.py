import heapq
import math
import re
from typing import Dict, List, Tuple, Optional, Any
from graph import PokemonGraph
from database import get_all_zone_yields, get_zone_encounters

class EVOptimizer:
    def __init__(self, graph: PokemonGraph):
        self.graph = graph
        # Cache yields to avoid DB hits on every step
        self.zone_yields_cache = {} 

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

    def _match_yield(self, graph_zone: str, yields_map: Dict[str, Dict[str, float]]) -> Optional[Dict[str, float]]:
        """
        Tries to find the yield dict for a graph zone in the yields map.
        """
        db_code = self._get_db_code(graph_zone)
        
        if db_code in yields_map:
            return yields_map[db_code]
        
        if "-" in db_code:
            prefix = db_code.rsplit("-", 1)[0]
            if prefix in yields_map:
                return yields_map[prefix]
            
        return None

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
                target_lbl = zone # Assuming symmetry
                if target_zone in self.graph.adjacency_data:
                    new_dist = d # 0 cost to cross
                    if new_dist < min_dists.get((target_zone, target_lbl), float('inf')):
                        min_dists[(target_zone, target_lbl)] = new_dist
                        heapq.heappush(pq, (new_dist, target_zone, target_lbl))
        
        return zone_min_dists

    def _normalize_zone_name(self, zone_name: str) -> str:
        """
        Normalizes DB zone name to Graph zone name.
        e.g. "Route 1" -> "Route1", "Mt. Moon" -> "MtMoon"
        """
        # Remove spaces, dots, underscores
        normalized = re.sub(r'[\s\._]', '', zone_name)
        
        # Check if this normalized name exists in the graph
        if normalized in self.graph.adjacency_data:
            return normalized
            
        # Try case-insensitive match
        for key in self.graph.adjacency_data.keys():
            if key.lower() == normalized.lower():
                return key
                
        # If not found, return original (might be already correct)
        return zone_name

    async def find_optimal_path(self, start_zone: str, current_evs: Dict[str, int], target_evs: Dict[str, int], accessible_zones: List[str], has_macho_brace: bool, has_pokerus: bool, lambda_penalty: float, pokemon_level: int = 50) -> Dict[str, Any]:
        """
        Finds a sequence of zones to visit to reach target EVs.
        Uses a greedy heuristic:
        1. Calculate needed EVs.
        2. Find best zone to farm needed EVs (Cost = Lambda*Dist + (1-Lambda)*Encounters).
        3. 'Travel' there, 'Farm' until capped or exhausted.
        4. Repeat.
        """
        # Normalize start_zone
        start_zone = self._normalize_zone_name(start_zone)
        
        # Normalize accessible_zones
        if accessible_zones:
            accessible_zones = [self._normalize_zone_name(z) for z in accessible_zones]

        path = []
        total_distance = 0
        total_encounters = 0
        
        current_location = start_zone
        current_stats = current_evs.copy()
        
        # Multipliers
        multiplier = 1
        if has_pokerus: multiplier *= 2
        # Macho brace adds yield but we need to know base yield. 
        # For simplicity, let's assume it doubles yield (it actually doubles EV gain).
        if has_macho_brace: multiplier *= 2 
        
        # Load yields once
        all_yields = get_all_zone_yields(pokemon_level)
        print(f"DEBUG: Loaded yields for {len(all_yields)} zones.")
        
        # Safety loop limit
        for i in range(10):
            # 1. Calculate Needs
            needs = {}
            has_needs = False
            for stat, target in target_evs.items():
                current = current_stats.get(stat, 0)
                if current < target:
                    needs[stat] = target - current
                    has_needs = True
            
            print(f"DEBUG: Iteration {i}, Needs: {needs}")
            
            if not has_needs:
                break
                
            # 2. Calculate Distances from current location
            distances = self._calculate_distances(current_location)
            print(f"DEBUG: Calculated distances from {current_location}. Reachable: {len(distances)}")
            
            # 3. Score Zones
            best_zone = None
            best_score = float('inf')
            best_stat_to_farm = None
            
            for zone_name in self.graph.adjacency_data.keys():
                # Filter accessible zones if provided
                if accessible_zones and zone_name not in accessible_zones:
                    continue

                dist = distances.get(zone_name, float('inf'))
                if dist == float('inf'):
                    continue
                
                zone_yield_data = self._match_yield(zone_name, all_yields)
                if not zone_yield_data:
                    continue
                
                # Check if this zone provides any needed stat
                for stat, amount_needed in needs.items():
                    avg_yield = zone_yield_data.get(stat, 0) * multiplier
                    if avg_yield > 0.1: # Threshold to consider useful
                        # Estimate encounters needed
                        encounters_needed = amount_needed / avg_yield
                        
                        # Score
                        # Normalize distance (e.g. 100 tiles ~ 1 encounter?)
                        # Let's say 1 tile = 1 unit, 1 encounter = 20 units?
                        # Or just use raw values and let lambda handle it.
                        # Problem: Distance is usually 0-500, Encounters 0-252.
                        # Let's assume user lambda is balanced for raw values.
                        
                        score = (lambda_penalty * dist) + ((1 - lambda_penalty) * encounters_needed * 10) # *10 to weight encounters more?
                        
                        if score < best_score:
                            best_score = score
                            best_zone = zone_name
                            best_stat_to_farm = stat
            
            if not best_zone:
                # Cannot fulfill needs
                break
                
            # 4. Add Travel Step
            dist_to_zone = distances[best_zone]
            if dist_to_zone > 0:
                path.append({
                    "type": "travel",
                    "to": best_zone,
                    "distance": dist_to_zone
                })
                total_distance += dist_to_zone
                current_location = best_zone
            
            # 5. Add Farm Step
            # Calculate exact encounters needed for the chosen stat
            # We need to know WHICH pokemon to kill.
            # Simple approach: Kill everything that gives the stat? Or just the best one?
            # For now, let's simulate "farming the zone" generally.
            
            db_code = self._get_db_code(best_zone)
            encounters = get_zone_encounters(db_code, pokemon_level)
            
            # Filter for pokemon that give the target stat
            useful_encounters = [e for e in encounters if e[f'ev_{best_stat_to_farm.lower().replace(" ", "_")}'] > 0]
            
            if not useful_encounters:
                # Should not happen given logic above
                break
                
            # Sort by yield/prob?
            # Let's pick the most common one that gives the stat
            target_pokemon = sorted(useful_encounters, key=lambda x: x['probability_percent'], reverse=True)[0]
            
            stat_key = f'ev_{best_stat_to_farm.lower().replace(" ", "_")}'
            yield_per_kill = target_pokemon[stat_key] * multiplier
            needed = needs[best_stat_to_farm]
            
            kills = math.ceil(needed / yield_per_kill)
            
            # Update stats
            # Note: This is a simplification. We might get other EVs too.
            # For a robust solution, we should simulate the side effects.
            
            gained_evs = {}
            for k in ['ev_hp', 'ev_attack', 'ev_defense', 'ev_sp_attack', 'ev_sp_defense', 'ev_speed']:
                stat_name = k.replace('ev_', '').replace('_', ' ').title()
                if stat_name == 'Hp': stat_name = 'HP'
                if stat_name == 'Sp Attack': stat_name = 'Special Attack'
                if stat_name == 'Sp Defense': stat_name = 'Special Defense'
                
                gain = kills * target_pokemon[k] * multiplier
                current_stats[stat_name] = current_stats.get(stat_name, 0) + gain
                gained_evs[stat_name] = gain

            path.append({
                "type": "farm",
                "zone": best_zone,
                "target_pokemon": target_pokemon['name'],
                "count": kills,
                "stat_focus": best_stat_to_farm,
                "gained_evs": gained_evs
            })
            
            total_encounters += kills
            
            # Check if we overshot caps (252)
            for s in current_stats:
                if current_stats[s] > 252:
                    current_stats[s] = 252 # Cap it
                    
        return {
            "path": path,
            "total_distance": total_distance,
            "total_encounters": total_encounters,
            "final_stats": current_stats
        }

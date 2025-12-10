import json
import os
from typing import Dict, List, Tuple, Optional

class PokemonGraph:
    def __init__(self, adjacency_file: str):
        self.adjacency_data = self._load_adjacency(adjacency_file)
        # Cache for inter-zone connections: (Zone, Label) -> TargetZone
        self.inter_zone_connections = self._build_inter_zone_connections()

    def _load_adjacency(self, path: str) -> Dict:
        if not os.path.exists(path):
            # Fallback or error
            print(f"Warning: Adjacency file not found at {path}")
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_inter_zone_connections(self) -> Dict[Tuple[str, str], str]:
        """
        Infers connections between zones based on label names.
        Assumption: A label in ZoneA named 'ZoneB' connects to ZoneB.
        """
        connections = {}
        zones = self.adjacency_data.keys()
        
        for zone in zones:
            # Get all labels in this zone
            labels = self.adjacency_data[zone].keys()
            for label in labels:
                # Heuristic: If label matches another zone name, it's a connection
                # We might need exact match or partial match. 
                # Based on file names, it seems exact match is intended (e.g. "CeladonCity" in Route16_East)
                if label in zones:
                    connections[(zone, label)] = label
                else:
                    # Handle cases like "Route16_NorthEntrance" -> "Route16_East"?
                    # For now, we assume the label IS the target zone name.
                    # If not found, we might check if it's a known alias or just ignore.
                    pass
        return connections

    def get_intra_zone_neighbors(self, zone: str, current_label: str) -> List[Tuple[str, int]]:
        """
        Returns list of (TargetLabel, Distance) within the same zone.
        """
        if zone not in self.adjacency_data:
            return []
        
        neighbors = []
        # adjacency_data[zone][current_label] is a list of {to: ..., dist: ...}
        paths = self.adjacency_data[zone].get(current_label, [])
        for p in paths:
            if p['dist'] is not None:
                neighbors.append((p['to'], p['dist']))
        return neighbors

    def get_inter_zone_neighbor(self, zone: str, current_label: str) -> Optional[str]:
        """
        Returns the TargetZone if the current label connects to it.
        Cost is 0.
        """
        # If the label is a zone name, we cross to that zone.
        # We need to find the corresponding label in the target zone.
        # Usually, the label in TargetZone pointing back to CurrentZone is named CurrentZone.
        target_zone = current_label
        if target_zone in self.adjacency_data:
            # Check if target_zone has a label named 'zone' (CurrentZone)
            # This confirms the bidirectional link
            if zone in self.adjacency_data[target_zone]:
                return target_zone
            
            # Fallback: Maybe the label in target zone is named differently?
            # For now, assume symmetry: Label A in Z1 -> Z2 implies Label Z1 in Z2 exists.
            return target_zone
        return None

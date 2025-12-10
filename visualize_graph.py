import json
import os
import networkx as nx
from pyvis.network import Network
import webbrowser

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Intentar usar GRAFO_KANTOOOOO.json si adjacency.json no existe
ADJ_PATH = os.path.join(BASE_DIR, "map", "adjacency.json")
if not os.path.exists(ADJ_PATH):
    ADJ_PATH = os.path.join(BASE_DIR, "map", "GRAFO_KANTOOOOO.json")

OUTPUT_HTML = os.path.join(BASE_DIR, "graph_visualization.html")

def load_graph_data():
    if not os.path.exists(ADJ_PATH):
        print(f"❌ Error: No se encontró el archivo {ADJ_PATH}")
        print("Asegúrate de ejecutar 'python map/build_adjacency.py' primero.")
        return None
    
    with open(ADJ_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_visualization():
    data = load_graph_data()
    if not data:
        return

    # Crear grafo dirigido
    G = nx.DiGraph()
    
    print("🔍 Construyendo grafo...")
    
    # Añadir nodos y aristas
    for source_zone, connections in data.items():
        G.add_node(source_zone, title=source_zone, group="Zone")
        
        for target_label, paths in connections.items():
            # En tu estructura, 'paths' es una lista de dicts: [{"to": "TargetZone", "dist": 123}, ...]
            # A veces el label es el nombre de la zona destino, a veces es una puerta.
            
            for path in paths:
                target_zone = path.get("to")
                dist = path.get("dist")
                
                if target_zone and dist is not None:
                    # Añadir arista
                    # Usamos el peso como distancia
                    G.add_edge(source_zone, target_zone, value=1, title=f"Dist: {dist} tiles", label=str(dist))

    print(f"✅ Grafo construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} conexiones.")

    # Configurar visualización con PyVis
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", directed=True)
    net.from_nx(G)
    
    # Opciones de física para que se acomode bonito
    net.set_options("""
    var options = {
      "nodes": {
        "font": {
          "size": 16
        },
        "borderWidth": 2,
        "shadow": true
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "smooth": {
          "type": "continuous"
        },
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        }
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": {
          "enabled": true,
          "iterations": 1000
        }
      }
    }
    """)

    print(f"💾 Guardando visualización en: {OUTPUT_HTML}")
    net.save_graph(OUTPUT_HTML)
    
    print("🚀 Abriendo en el navegador...")
    webbrowser.open('file://' + OUTPUT_HTML)

if __name__ == "__main__":
    create_visualization()

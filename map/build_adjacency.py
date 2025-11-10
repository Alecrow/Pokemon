import os
import csv
import json
from collections import deque

MATRICES_DIR = os.path.join(os.path.dirname(__file__), "matrices")
ADJ_PATH = os.path.join(os.path.dirname(__file__), "adjacency.json")
VISITED_PATH = os.path.join(os.path.dirname(__file__), "visited_files.json")


def read_csv_grid(path):
    grid = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # mantener celdas tal cual (strip espacios)
            cells = [cell.strip() for cell in row if cell is not None]
            if cells:
                grid.append(cells)
    return grid


def build_passable_and_labels(grid):
    R = len(grid)
    C = max((len(r) for r in grid), default=0)
    passable = [[0]*C for _ in range(R)]
    labels = {}  # label -> list of (r,c)
    for r in range(R):
        for c in range(len(grid[r])):
            val = grid[r][c]
            if val == "1":
                passable[r][c] = 1
            elif val == "0" or val == "":
                passable[r][c] = 0
            else:
                # cualquier token no 0/1 lo tratamos como etiqueta y como casilla transitables
                labels.setdefault(val, []).append((r, c))
                passable[r][c] = 1
    return passable, labels


def bfs_min_distance(passable, sources, targets_set):
    """BFS multi-source que devuelve distancia mínima en pasos desde cualquiera de sources a cualquiera de targets_set.
       Si no se alcanza, devuelve None.
    """
    R = len(passable)
    C = len(passable[0]) if R>0 else 0
    q = deque()
    seen = [[False]*C for _ in range(R)]
    for (r,c) in sources:
        if 0 <= r < R and 0 <= c < C and passable[r][c]:
            q.append((r,c,0))
            seen[r][c] = True
    while q:
        r,c,d = q.popleft()
        if (r,c) in targets_set:
            return d
        for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr,nc = r+dr, c+dc
            if 0 <= nr < R and 0 <= nc < C and not seen[nr][nc] and passable[nr][nc]:
                seen[nr][nc] = True
                q.append((nr,nc,d+1))
    return None


def load_visited():
    if os.path.exists(VISITED_PATH):
        with open(VISITED_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_visited(s):
    with open(VISITED_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(list(s)), f, indent=2, ensure_ascii=False)


def load_adj():
    if os.path.exists(ADJ_PATH):
        with open(ADJ_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_adj(adj):
    with open(ADJ_PATH, "w", encoding="utf-8") as f:
        json.dump(adj, f, indent=2, ensure_ascii=False)


def process_all():
    visited = load_visited()
    adj = load_adj()

    for fname in sorted(os.listdir(MATRICES_DIR)):
        if not fname.lower().endswith(".csv"):
            continue
        fpath = os.path.join(MATRICES_DIR, fname)
        zone_key = os.path.splitext(fname)[0]  # e.g. CeruleanCity
        if fpath in visited or zone_key in visited:
            # permitir ambas formas en visited
            print(f"Saltando (ya procesado): {fname}")
            continue

        grid = read_csv_grid(fpath)
        passable, labels = build_passable_and_labels(grid)

        if not labels:
            print(f"No hay etiquetas en {fname}; marcado como visitado.")
            visited.add(zone_key)
            save_visited(visited)
            continue

        # crear estructura para este archivo
        adj.setdefault(zone_key, {})

        label_names = sorted(labels.keys())
        # calcular distancia mínima entre cada par (A->B), usando BFS multi-source desde A
        for a in label_names:
            adj[zone_key].setdefault(a, [])
            for b in label_names:
                if a == b:
                    continue
                # evitar duplicar si ya calculado en sentido opuesto dentro de este archivo:
                # pero el usuario pidió "viceversa" así que guardamos ambos sentidos (simétricos)
                dist = bfs_min_distance(passable, labels[a], set(labels[b]))
                if dist is None:
                    # inalcanzable: guardar null
                    entry = {"to": b, "dist": None}
                else:
                    entry = {"to": b, "dist": int(dist)}
                adj[zone_key][a].append(entry)

        # guardar como visitado
        visited.add(zone_key)
        save_adj(adj)
        save_visited(visited)
        print(f"Procesado {fname}: etiquetas={len(label_names)}")

    print("Terminado. Adjacency guardado en:", ADJ_PATH)
    print("Visited guardado en:", VISITED_PATH)


if __name__ == "__main__":
    process_all()
import csv
from collections import deque
import numpy as np

def load_csv_matrix(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        mat = [ [int(x.strip()) for x in row if x.strip()!=''] for row in reader if row ]
    return np.array(mat, dtype=int)

def save_csv_matrix(mat, path, sep=", "):
    with open(path, "w", encoding="utf-8") as f:
        for r in range(mat.shape[0]):
            f.write(sep.join(str(int(v)) for v in mat[r,:]) + "\n")

def detect_edge_exits(mat, edge="top", passable_value=1):
    exits = []
    if edge == "top":
        r = 0
        for c in range(mat.shape[1]):
            if mat[r, c] == passable_value:
                exits.append((r, c))
    elif edge == "bottom":
        r = mat.shape[0]-1
        for c in range(mat.shape[1]):
            if mat[r, c] == passable_value:
                exits.append((r, c))
    elif edge == "left":
        c = 0
        for r in range(mat.shape[0]):
            if mat[r, c] == passable_value:
                exits.append((r, c))
    elif edge == "right":
        c = mat.shape[1]-1
        for r in range(mat.shape[0]):
            if mat[r, c] == passable_value:
                exits.append((r, c))
    return exits

def relabel_coords(mat, coords, new_value):
    for (r,c) in coords:
        mat[r,c] = new_value
    return mat

def bfs_shortest_path(mat, sources, targets, passable_value=1):
    """
    sources: iterable de (r,c)
    targets: set de (r,c)
    Devuelve lista de celdas desde un source hasta target (inclusive) o None.
    """
    R, C = mat.shape
    q = deque()
    prev = {}
    seen = set()
    for s in sources:
        if mat[s] != passable_value and s not in targets:
            continue
        q.append(s); seen.add(s); prev[s] = None
    while q:
        u = q.popleft()
        if u in targets:
            # reconstruir camino
            path = []
            cur = u
            while cur is not None:
                path.append(cur)
                cur = prev[cur]
            return list(reversed(path))
        r,c = u
        for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr,nc = r+dr, c+dc
            if 0 <= nr < R and 0 <= nc < C:
                if (nr,nc) not in seen and (mat[nr,nc] == passable_value or (nr,nc) in targets):
                    seen.add((nr,nc))
                    prev[(nr,nc)] = u
                    q.append((nr,nc))
    return None

# ejemplo de uso (no se ejecuta al importar):
if __name__ == "__main__":
    mat = load_csv_matrix("PalletTown.csv")
    # detectar salidas en la fila superior que son 1
    exits_top = detect_edge_exits(mat, edge="top", passable_value=1)
    # relabel: ponerles 2 para identificador "lleva a route1"
    mat = relabel_coords(mat, exits_top, new_value=2)
    save_csv_matrix(mat, "PalletTown_relabel.csv")

    # ejemplo de ruta: buscar camino entre primer exit y un objetivo (ejemplo coordenada)
    if exits_top:
        src = [exits_top[0]]            # punto de partida (puede ser lista de múltiples celdas)
        target_set = {(10,12)}          # ejemplo: celda objetivo (coloca tu destino real)
        path = bfs_shortest_path(mat, src, target_set, passable_value=1)
        print("path:", path)
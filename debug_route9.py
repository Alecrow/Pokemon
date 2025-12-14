import csv
import os
from collections import deque

def read_csv_grid(path):
    grid = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            cells = [cell.strip() for cell in row if cell is not None]
            if cells:
                grid.append(cells)
    return grid

def build_passable_and_labels(grid):
    R = len(grid)
    C = max((len(r) for r in grid), default=0)
    passable = [[0]*C for _ in range(R)]
    labels = {}
    for r in range(R):
        for c in range(len(grid[r])):
            val = grid[r][c]
            if val == "1":
                passable[r][c] = 1
            elif val == "0" or val == "":
                passable[r][c] = 0
            else:
                labels.setdefault(val, []).append((r, c))
                passable[r][c] = 1
    return passable, labels

def bfs_debug(passable, start, target_label):
    R = len(passable)
    C = len(passable[0])
    q = deque()
    seen = [[False]*C for _ in range(R)]
    parent = {}
    
    r, c = start
    q.append((r, c))
    seen[r][c] = True
    parent[(r,c)] = None
    
    print(f"Starting BFS from {start}")
    
    max_dist = 0
    furthest_node = start
    
    while q:
        curr_r, curr_c = q.popleft()
        
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = curr_r+dr, curr_c+dc
            if 0 <= nr < R and 0 <= nc < C and not seen[nr][nc] and passable[nr][nc]:
                seen[nr][nc] = True
                q.append((nr, nc))
                parent[(nr,nc)] = (curr_r, curr_c)
                furthest_node = (nr, nc)

    return seen, parent

path = r"e:\universidad\grafos\Pokemon\map\matrices\Route9.csv"
grid = read_csv_grid(path)
passable, labels = build_passable_and_labels(grid)

print("Labels found:", labels.keys())

if "CeruleanCity" in labels and "Route10_North" in labels:
    start = labels["CeruleanCity"][0]
    targets = labels["Route10_North"]
    print(f"CeruleanCity at: {start}")
    print(f"Route10_North at: {targets}")
    
    seen, parent = bfs_debug(passable, start, "Route10_North")
    
    reached = False
    for t in targets:
        if seen[t[0]][t[1]]:
            reached = True
            print(f"Target {t} reached!")
            break
    
    if not reached:
        print("Target NOT reached.")
        # Print column headers
        header = "    "
        for c in range(len(passable[0])):
            header += str(c % 10)
        print(header)
        
        for r in range(len(passable)):
            row_str = ""
            for c in range(len(passable[r])):
                if (r,c) == start:
                    row_str += "S"
                elif (r,c) in targets:
                    row_str += "T"
                elif seen[r][c]:
                    row_str += "."
                elif passable[r][c]:
                    row_str += "#" # Passable but not reached
                else:
                    row_str += " " # Blocked
            print(f"{r:02d}: {row_str}")
else:
    print("Missing labels")

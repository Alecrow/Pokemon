import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import json
import time
import os
import re

BASE_URL = "https://www.wikidex.net"
KANTO_URL = "https://www.wikidex.net/wiki/Kanto"
OUTPUT_FILE = r"c:\Users\lexis\OneDrive\Desktop\grafos\Pokemon\db\scrapingNew\geography_graph.json"
MAPPING_FILE = r"c:\Users\lexis\OneDrive\Desktop\grafos\Pokemon\db\scrapingNew\name_mapping.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def load_mapping():
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

NAME_MAPPING = load_mapping()

def normalize_name(name):
    if not name:
        return ""
    
    # Remove (Kanto) or other suffixes
    name = re.sub(r'\s*\(.*?\)', '', name).strip()
    
    # Check explicit mapping
    if name in NAME_MAPPING:
        return NAME_MAPPING[name]
    
    # Handle "Ruta X" -> "RouteX"
    route_match = re.match(r'Ruta\s+(\d+)', name, re.IGNORECASE)
    if route_match:
        return f"Route{route_match.group(1)}"
    
    return name

def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_kanto_locations():
    soup = get_soup(KANTO_URL)
    if not soup:
        return []

    locations = set()
    
    tables = soup.find_all('table')
    target_table = None
    for table in tables:
        if "Región de Kanto" in table.get_text():
            target_table = table
            break
    
    if not target_table:
        print("Could not find 'Región de Kanto' table")
        return []

    rows = target_table.find_all('tr')
    for row in rows:
        header = row.find('th') or row.find('td')
        if not header:
            continue
        
        header_text = header.get_text().strip()
        valid_categories = ["Ciudades", "Pueblos", "Rutas", "Cuevas y montañas", "Bosques", "Islas", "Otros lugares"]
        
        is_valid = False
        for cat in valid_categories:
            if cat in header_text:
                is_valid = True
                break
        
        if is_valid:
            links = row.find_all('a')
            for link in links:
                href = link.get('href')
                title = link.get('title')
                
                if not href or href.startswith('#') or "Medalla" in str(title) or "Archivo:" in href or "WikiDex" in str(title):
                    continue
                
                full_url = BASE_URL + href
                locations.add((title, full_url))

    return list(locations)

def parse_connections(soup, location_name):
    connections = []
    
    tables = soup.find_all('table')
    target_row = None
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            text = row.get_text(" ", strip=True)
            if "Lugares" in text and "colindantes" in text:
                target_row = row
                break
        if target_row:
            break
            
    if not target_row:
        return []

    cells = target_row.find_all(['th', 'td'])
    content_cell = None
    
    for i, cell in enumerate(cells):
        text = cell.get_text(" ", strip=True)
        if "Lugares" in text and "colindantes" in text:
            if i + 1 < len(cells):
                content_cell = cells[i+1]
            break
            
    if not content_cell:
        return []

    current_target = None
    
    for child in content_cell.contents:
        if isinstance(child, Tag):
            if child.name == 'a':
                raw_name = child.get_text().strip()
                current_target = {
                    "raw_name": raw_name,
                    "name": normalize_name(raw_name),
                    "url": BASE_URL + child.get('href')
                }
            elif child.name == 'br':
                pass
        elif isinstance(child, NavigableString):
            text = str(child).strip()
            if text and current_target:
                direction_match = re.search(r'\((.*?)\)', text)
                if direction_match:
                    direction = direction_match.group(1).lower()
                    connections.append({
                        "target": current_target["name"],
                        "target_raw": current_target["raw_name"],
                        "direction": direction
                    })
                    current_target = None
                else:
                    # Try to capture direction without parens if it's simple text
                    clean = text.replace(',', '').replace('.', '').strip().lower()
                    if clean in ['norte', 'sur', 'este', 'oeste']:
                         connections.append({
                            "target": current_target["name"],
                            "target_raw": current_target["raw_name"],
                            "direction": clean
                        })
                         current_target = None

    return connections

def main():
    print("Fetching Kanto locations...")
    locations = get_kanto_locations()
    print(f"Found {len(locations)} locations.")
    
    graph = {}
    
    for name, url in locations:
        if not name: continue
        
        normalized_name = normalize_name(name)
        print(f"Processing {name} -> {normalized_name}...")
        
        soup = get_soup(url)
        if soup:
            connections = parse_connections(soup, name)
            
            graph[normalized_name] = {}
            for conn in connections:
                target = conn["target"]
                graph[normalized_name][target] = {
                    "dist": 0,
                    "direction": conn["direction"]
                }
                
        time.sleep(0.2) 
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=4, ensure_ascii=False)
    
    print(f"Graph saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

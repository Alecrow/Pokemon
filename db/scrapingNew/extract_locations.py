import os
import csv
import re
from bs4 import BeautifulSoup

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES = [
    "Lista de localizaciones de Pokémon de Rojo Fuego y Verde Hoja_Primera generación - WikiDex, la enciclopedia Pokémon.htm",
    "Lista de localizaciones de Pokémon de Rojo Fuego y Verde Hoja_Segunda generación - WikiDex, la enciclopedia Pokémon.htm",
    "Lista de localizaciones de Pokémon de Rojo Fuego y Verde Hoja_Tercera generación - WikiDex, la enciclopedia Pokémon.htm"
]
OUTPUT_FILE = os.path.join(BASE_DIR, "pokemon_locations.csv")

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def parse_location_entry(text):
    # Expected format: "Location - Percentage" or "Location" (if nested)
    # But sometimes "Location / Location - Percentage"
    
    # Check for percentage at the end
    match = re.search(r'-\s*(\d+)%$', text)
    if match:
        percentage = match.group(1)
        locations_part = text[:match.start()].strip()
        locations = [l.strip() for l in locations_part.split('/')]
        return locations, percentage
    
    return None, None

def extract_locations_from_ul(ul, current_method, parent_location=None):
    entries = []
    for li in ul.find_all('li', recursive=False):
        # Check if this li defines a new method
        b_tag = li.find('b')
        if b_tag:
            b_text = clean_text(b_tag.get_text())
            if "Caminar" in b_text:
                nested_ul = li.find('ul')
                if nested_ul:
                    entries.extend(extract_locations_from_ul(nested_ul, "Caminar"))
                continue
            elif "Surf" in b_text:
                nested_ul = li.find('ul')
                if nested_ul:
                    entries.extend(extract_locations_from_ul(nested_ul, "Surf"))
                continue
            elif "Golpe Roca" in b_text or "Golpe roca" in b_text:
                nested_ul = li.find('ul')
                if nested_ul:
                    entries.extend(extract_locations_from_ul(nested_ul, "Golpe Roca"))
                continue
            elif "Caña" in b_text or "Supercaña" in b_text:
                method_name = f"Pesca ({b_text.replace(':', '').strip()})"
                nested_ul = li.find('ul')
                if nested_ul:
                    entries.extend(extract_locations_from_ul(nested_ul, method_name))
                continue
            elif "Canje" in b_text:
                li_text = clean_text(li.get_text())
                cost = li_text.replace("Canje:", "").strip()
                entries.append({
                    "Location": "Casino (Ciudad Azulona)", 
                    "Method": "Canje",
                    "Rate": cost 
                })
                continue

        
        # Text processing for location
        li_text = ""
        for child in li.children:
            if child.name == 'ul':
                break
            if child.name == 'a' or isinstance(child, str) or child.name == 'b':
                li_text += child.get_text() if child.name else str(child)
        
        li_text = clean_text(li_text)
        
        # Check if there is a nested UL which implies this LI is a parent location
        nested_ul = li.find('ul')
        if nested_ul:
            this_location = li_text.strip()
            entries.extend(extract_locations_from_ul(nested_ul, current_method, parent_location=this_location))
        else:
            # Leaf node
            locations, percentage = parse_location_entry(li_text)
            if locations and percentage:
                for loc in locations:
                    full_loc = f"{parent_location} ({loc})" if parent_location else loc
                    entries.append({
                        "Location": full_loc,
                        "Method": current_method,
                        "Rate": percentage
                    })
            elif parent_location and li_text:
                 # Maybe the sub-location doesn't have a percentage?
                 pass

    return entries

def parse_cell(cell):
    data = []
    
    # Check for Intercambio Interno (In-game trade)
    cell_text = clean_text(cell.get_text())
    if "Intercambio Interno" in cell_text:
        match = re.search(r'en (?:el |la )?([^.]+)', cell_text)
        location = match.group(1).strip() if match else "Desconocido"
        data.append({
            "Location": location,
            "Method": "Intercambio Interno",
            "Rate": "100%"
        })
    
    for child in cell.children:
        if child.name == 'ul':
            for li in child.find_all('li', recursive=False):
                li_text = clean_text(li.get_text())
                
                method = None
                if "Caminar" in li_text:
                    method = "Caminar"
                elif "Surf" in li_text:
                    method = "Surf"
                elif "Golpe Roca" in li_text or "Golpe roca" in li_text:
                    method = "Golpe Roca"
                elif "Caña" in li_text or "Supercaña" in li_text:
                    match = re.search(r'(Supercaña|Caña [Bb]uena|Caña [Vv]ieja)', li_text)
                    if match:
                        method = f"Pesca ({match.group(1)})"
                    else:
                        method = "Pesca"
                elif "Canje" in li_text:
                    cost = li_text.replace("Canje:", "").strip()
                    data.append({
                        "Location": "Casino (Ciudad Azulona)",
                        "Method": "Canje",
                        "Rate": cost
                    })
                    continue
                
                if method:
                    nested_ul = li.find('ul')
                    if nested_ul:
                        data.extend(extract_locations_from_ul(nested_ul, method))
                    
    return data

def process_file(filepath, writer):
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        
        if len(cells) < 5:
            continue
            
        dex_num = clean_text(cells[0].get_text())
        if not re.match(r'^\d+$', dex_num):
            continue
            
        pokemon_name = clean_text(cells[1].get_text())
        
        fr_cell = cells[3]
        lg_cell = cells[4]
        
        fr_data = parse_cell(fr_cell)
        lg_data = parse_cell(lg_cell)
        
        for entry in fr_data:
            writer.writerow([pokemon_name, entry['Location'], entry['Rate'], entry['Method'], "Rojo Fuego"])
            
        for entry in lg_data:
            writer.writerow([pokemon_name, entry['Location'], entry['Rate'], entry['Method'], "Verde Hoja"])

def main():
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Pokemon", "Ubicacion", "Tasa_Aparicion", "Metodo", "Juego"])
        
        for filename in FILES:
            filepath = os.path.join(BASE_DIR, filename)
            if os.path.exists(filepath):
                process_file(filepath, writer)
            else:
                print(f"File not found: {filepath}")

if __name__ == "__main__":
    main()

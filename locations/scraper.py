#!/usr/bin/env python3
import os
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import csv
import re

BASE = "https://pokemondb.net"
targets = [
    "/location/kanto-berry-forest",
    "/location/kanto-bond-bridge",
    "/location/kanto-canyon-entrance",
    "/location/kanto-cape-brink",
    "/location/kanto-celadon-city",
    "/location/kanto-cerulean-cave",
    "/location/kanto-cerulean-city",
    "/location/kanto-cinnabar-island",
    "/location/kanto-digletts-cave",
    "/location/kanto-five-island",
    "/location/kanto-five-isle-meadow",
    "/location/kanto-four-island",
    "/location/kanto-fuchsia-city",
    "/location/kanto-green-path",
    "/location/kanto-icefall-cave",
    "/location/kanto-indigo-plateau",
    "/location/kanto-kindle-road",
    "/location/kanto-lavender-town",
    "/location/kanto-lost-cave",
    "/location/kanto-memorial-pillar",
    "/location/kanto-mt-ember",
    "/location/kanto-mt-moon",
    "/location/kanto-navel-rock",
    "/location/kanto-one-island",
    "/location/kanto-outcast-island",
    "/location/kanto-pallet-town",
    "/location/kanto-pattern-bush",
    "/location/kanto-pewter-city",
    "/location/kanto-pokemon-mansion",
    "/location/kanto-pokemon-tower",
    "/location/kanto-power-plant",
    "/location/kanto-resort-gorgeous",
    "/location/kanto-roaming",
    "/location/kanto-rock-tunnel",
    "/location/kanto-route-1",
    "/location/kanto-route-10",
    "/location/kanto-route-11",
    "/location/kanto-route-12",
    "/location/kanto-route-13",
    "/location/kanto-route-14",
    "/location/kanto-route-15",
    "/location/kanto-route-16",
    "/location/kanto-route-17",
    "/location/kanto-route-18",
    "/location/kanto-route-19",
    "/location/kanto-route-2",
    "/location/kanto-route-20",
    "/location/kanto-route-21",
    "/location/kanto-route-22",
    "/location/kanto-route-23",
    "/location/kanto-route-24",
    "/location/kanto-route-25",
    "/location/kanto-route-26",
    "/location/kanto-route-27",
    "/location/kanto-route-28",
    "/location/kanto-route-3",
    "/location/kanto-route-4",
    "/location/kanto-route-5",
    "/location/kanto-route-6",
    "/location/kanto-route-7",
    "/location/kanto-route-8",
    "/location/kanto-route-9",
    "/location/kanto-ruin-valley",
    "/location/kanto-safari-zone",
    "/location/kanto-saffron-city",
    "/location/kanto-seafoam-islands",
    "/location/kanto-sevault-canyon",
    "/location/kanto-silph-co",
    "/location/kanto-tanoby-ruins",
    "/location/kanto-three-isle-port",
    "/location/kanto-tohjo-falls",
    "/location/kanto-trainer-tower",
    "/location/kanto-treasure-beach",
    "/location/kanto-underground-path-5-6",
    "/location/kanto-vermilion-city",
    "/location/kanto-victory-road",
    "/location/kanto-viridian-city",
    "/location/kanto-viridian-forest",
    "/location/kanto-water-labyrinth",
    "/location/kanto-water-path"
]
DELAY = 5.0

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_request(path: str, idx: int):
    url = urljoin(BASE, path)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        print(f"[{idx}] ERROR al conectar {url}: {e}")
        return False

    if resp.status_code != 200:
        print(f"[{idx}] ERROR STATUS {resp.status_code} para {url}")
        return False

    print(f"[{idx}] STATUS {resp.status_code} para {url}")

    soup = BeautifulSoup(resp.text, "html.parser")

    h2_gen3_list = soup.find_all("h2", id=re.compile(r"^gen3"))

    if not h2_gen3_list:
        print(f"[{idx}] No se encontró ningún <h2 id='gen3...'> en {url}")
        return

    results = []
    for h2_gen3 in h2_gen3_list:
        header = h2_gen3.get_text(strip=True)
        for sibling in h2_gen3.find_all_next():
            if sibling.name == "h2":
                break
            if sibling.name == "h3":
                h3_text = sibling.get_text(strip=True)
                next_table = sibling.find_next("table", {"class": "data-table"})
                if next_table:
                    table_data = []
                    for row in next_table.find_all("tr"):
                        cols = []
                        element = row.find("td", class_="cell-loc-game-FR3")
                        if element:
                            for col in row.find_all(["td", "th"]):
                                if col.has_attr("class"):
                                    clas = col["class"]
                                    if "cell-loc-game-LG3" not in clas:
                                        if "cell-loc-game-blank" not in clas:
                                            if "cell-loc-game-FR3" not in clas:
                                                text = col.get_text(strip=True)
                                                cell_data = {"text": text or None}
                                                cols.append(cell_data)
                                else:
                                    imgs = col.find_all("img")
                                    if imgs:
                                        alt = imgs[0].get("alt", "")
                                        cell_data = {"text": alt or None}
                                        cols.append(cell_data)
                            if cols:
                                table_data.append(cols)
                    results.append({"h3": h3_text, "table": table_data, "generation": header})
                else:
                    results.append({"h3": h3_text, "table": None, "generation": header})
        print(results)
    return results

def main():
    os.makedirs("csv", exist_ok=True)
    all_results = []
    for i, t in enumerate(targets, start=1):
        data = fetch_request(t, i)
        if data:
            all_results.append({"url": urljoin(BASE, t), "data": data})
        time.sleep(DELAY)
    
    for result in all_results:
        rows = []
        data = result['data']
        for section in data:
            metodo = section['h3']
            generation = section['generation']
            if section['table'] is None:
                continue
            for row in section['table']:
                pokemon = row[0]['text']
                rareza = row[1]['text']
                nivel = row[2]['text']
                rows.append({
                        'Pokémon': pokemon,
                        'Rareza': rareza,
                        'Nivel': nivel,
                        'Método': metodo,
                        'Generación': generation
                    })
        csv_filename = os.path.join("csv", f"{result['url'].rstrip('/').split('/')[-1]}.csv")
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Pokémon', 'Rareza', 'Nivel', 'Método', 'Generación'])
            writer.writeheader()
            writer.writerows(rows)

if __name__ == "__main__":
    main()
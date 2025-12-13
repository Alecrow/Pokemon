import requests
import json

API_URL = "http://localhost:8000/api/optimize"

def test_optimize_endpoint():
    payload = {
        "pokemon_name": "Pikachu",
        "pokemon_level": 50,
        "start_zone": "Pallet Town", # Need to check valid zone name
        "accessible_zones": [],
        "target_stat": "Speed",
        "target_evs": 10,
        "has_macho_brace": False,
        "has_pokerus": False,
        "lambda_penalty": 0.1
    }
    
    # First, let's get a valid zone name from the API
    try:
        zones_resp = requests.get("http://localhost:8000/api/zones")
        if zones_resp.status_code == 200:
            zones = zones_resp.json()['zones']
            if zones:
                print("Available zones (first 5):", [z['name'] for z in zones[:5]])
                # Try to find Route 1
                route_1 = next((z for z in zones if "Route 1" in z['name']), None)
                if route_1:
                    payload['start_zone'] = route_1['name']
                else:
                    payload['start_zone'] = zones[0]['name']
                print(f"Using start zone: {payload['start_zone']}")
    except Exception as e:
        print(f"Failed to fetch zones: {e}")

    print(f"Sending request to {API_URL}...")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(API_URL, json=payload)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Error Response:")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_optimize_endpoint()

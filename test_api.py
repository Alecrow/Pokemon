import requests
import json

API_URL = "http://localhost:8000/api/optimize"

def test_optimization():
    # Ejemplo de distribución de 510 EVs
    payload = {
        "pokemon_name": "Charmander",
        "start_zone": "PalletTown",
        "target_evs": {
            "Attack": 100,
            "Speed": 100,
            "HP": 6
        },
        "current_evs": {
            "HP": 0, "Attack": 0, "Defense": 0, 
            "Special Attack": 0, "Special Defense": 0, "Speed": 0
        },
        "pokemon_level": 10,
        "lambda_penalty": 0.1,
        "held_item": "Macho Brace",
        "has_pokerus": False
    }

    print(f"Enviando petición a {API_URL}...")
    print(f"Datos: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ ¡Éxito! Resultado de optimización:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if "path" in data:
                print(f"\n--- PLAN DE ENTRENAMIENTO ---")
                for i, step in enumerate(data["path"], 1):
                    if step['type'] == 'travel':
                        print(f"PASO {i}: Viajar a {step['to']} ({step['distance']} tiles)")
                    else:
                        print(f"PASO {i}: Entrenar en {step['zone']}")
                        print(f"   - Objetivo: {step['count']}x {step['target_pokemon']}")
                        print(f"   - Foco: {step['stat_focus']}")
        else:
            print(f"\n❌ Error {response.status_code}:")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("\n❌ No se pudo conectar al backend. Asegúrate de que Docker esté corriendo en el puerto 8000.")

if __name__ == "__main__":
    test_optimization()

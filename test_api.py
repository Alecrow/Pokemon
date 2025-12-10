import requests
import json

API_URL = "http://localhost:8000/api/optimize"

def test_optimization():
    # Ejemplo de distribución de 510 EVs
    payload = {
        "start_zone": "PalletTown",
        "targets": {
            "Attack": 100,
            "Speed": 100,
            "HP": 6
        },
        "pokemon_level": 10,
        "lambda_val": 0.1
    }

    print(f"Enviando petición a {API_URL}...")
    print(f"Datos: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ ¡Éxito! Resultado de optimización:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if "optimal_route" in data:
                print(f"\n--- PLAN DE ENTRENAMIENTO (Costo Total: {data['total_cost']:.2f}) ---")
                for i, step in enumerate(data["optimal_route"], 1):
                    print(f"\nPASO {i}: Entrenar {step['stat']}")
                    print(f"📍 Viajar a: {step['zone']} (Distancia: {step['distance']} tiles)")
                    print(f"⚔️ Combates necesarios: {step['encounters']}")
                    print(f"🎯 Objetivos:")
                    for p in step["pokemon_list"]:
                        print(f"   - {p['name']} (Nv {p['level']}): {p['ev_yield']} EVs ({p['probability']})")
        else:
            print(f"\n❌ Error {response.status_code}:")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("\n❌ No se pudo conectar al backend. Asegúrate de que Docker esté corriendo en el puerto 8000.")

if __name__ == "__main__":
    test_optimization()

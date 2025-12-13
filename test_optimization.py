import sys
import os
import asyncio

# Add backend to path
backend_path = os.path.join(os.getcwd(), 'backend')
sys.path.append(backend_path)
print(f"Added {backend_path} to sys.path")

try:
    import graph
    print("Successfully imported graph")
except ImportError as e:
    print(f"Failed to import graph: {e}")

from backend.optimizer import EVOptimizer
from backend.database import get_db_connection

async def test_optimization():
    print("Testing EV Optimization Logic...")
    
    try:
        conn = get_db_connection()
        optimizer = EVOptimizer(conn)
        
        # Test case
        start_zone = "Pallet Town" # Assuming English names or whatever is in DB. Let's check DB or just try one.
        # Actually, let's check what zones are in the DB first to be safe, or just handle the error.
        
        # Let's try to fetch zones first
        cur = conn.cursor()
        cur.execute("SELECT name FROM locations LIMIT 1")
        zone = cur.fetchone()
        if zone:
            start_zone = zone[0]
            print(f"Using start zone: {start_zone}")
        
        target_evs = {"Speed": 10}
        current_evs = {"Speed": 0}
        
        print(f"Optimizing for {target_evs} starting at {start_zone}...")
        
        result = await optimizer.find_optimal_path(
            start_zone=start_zone,
            target_evs=target_evs,
            current_evs=current_evs,
            accessible_zones=[], # All
            has_macho_brace=False,
            has_pokerus=False,
            lambda_penalty=0.1
        )
        
        print("Optimization Result:")
        print(result)
        
        conn.close()
        print("Test Passed!")
        
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_optimization())

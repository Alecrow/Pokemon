import pandas as pd

# Cargar el dataset original
input_filename = 'Pokedex_Ver_SV2.csv'
output_filename = 'Pokedex_Limpiado.csv'

try:
    df = pd.read_csv(input_filename)
except FileNotFoundError:
    print(f"Error: El archivo '{input_filename}' no se encontró.")
    exit()

# --- Limpieza 1: Filtrar por número de Pokémon ---

# Convertir la columna 'No' a tipo numérico, manejando errores
df['No'] = pd.to_numeric(df['No'], errors='coerce')
df.dropna(subset=['No'], inplace=True)
df['No'] = df['No'].astype(int)

# Filtrar para incluir solo Pokémon hasta el No 386
df_limpio = df[df['No'] <= 386]

# --- Limpieza 2: Filtrar por Branch_Code ---

# Asegurarse de que la columna 'Branch_Code' sea de tipo string
df_limpio['Branch_Code'] = df_limpio['Branch_Code'].astype(str)

# Mantener solo las filas donde Branch_Code termina en '_0'
df_filtrado = df_limpio[df_limpio['Branch_Code'].str.endswith('_0')].copy()

# --- Limpieza 3: Eliminar columnas innecesarias ---
columnas_a_eliminar = [
    'Branch_Code', 'Original_Name', 'Color', 'Egg_Steps', 'Egg_Group1', 
    'Egg_Group2', 'Mega_Evolution_Flag', 'Region_Form'
]
df_final = df_filtrado.drop(columns=columnas_a_eliminar)

# Guardar el DataFrame final, sobreescribiendo el archivo existente
df_final.to_csv(output_filename, index=False)

print(f"Dataset limpiado y guardado como '{output_filename}'")
print(f"El dataset ahora contiene {len(df_final)} registros después de la limpieza completa.")


FROM python:3.12-alpine

# Instala dependencias del sistema necesarias para compilar psycopg2
RUN apk add --no-cache gcc musl-dev postgresql-dev

# Instala psycopg2 (la versión completa, no binary, para compatibilidad)
RUN pip install psycopg2

# Establece el directorio de trabajo
WORKDIR /app

# Copia ficheros al contenedor
COPY 02_load_data.py 03_verify_data.py 04_load_geography.py Pokedex_Limpiado.csv /app
COPY ./locations/csv /app/locations/csv

CMD ["python3"]
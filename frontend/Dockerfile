# Etapa de build (opcional, si quieres servir con un servidor Node)
FROM node:20-alpine AS build

WORKDIR /app

# Instala dependencias
COPY package*.json ./
RUN npm install

# Copia el resto del código
COPY . .

# Construye la app para producción
RUN npm run build

# Etapa de desarrollo (puedes elegir entre dev o servir estático)
FROM node:20-alpine

WORKDIR /app

# Copia dependencias y código fuente
COPY --from=build /app /app

EXPOSE 5173

# Por defecto corre el servidor de desarrollo de Vite
CMD ["npm", "run", "dev", "--", "--host"]

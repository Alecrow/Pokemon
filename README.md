# Node.js:

```bash

# Crea un contenedor de Node.js:
docker pull node:22-alpine

# Inicia una sesión shell
docker run -it --rm -p 5173:5173 -v "${PWD}/pokemon-map:/app" -w /app node:22-alpine sh

#levantar node
npm install
npm run dev -- --host

```

---

### 1. Crear Entorno Virtual

Para mantener las dependencias del proyecto aisladas, crea un entorno virtual:1

```bash
python -m venv .venv
```

### 2. Activar Entorno Virtual

Una vez creado, activa el entorno.

**En Windows (CMD):**

```bash
.\.venv\Scripts\activate
```

**En Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

_Nota: Si tienes problemas en PowerShell, puede que necesites cambiar la política de ejecución con `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`._

**En macOS/Linux:**

```bash
source .venv/bin/activate
```

### 3. Instalar Dependencias

Con el entorno activado, instala las librerías necesarias desde `requirements.txt`:

```bash
pip install -r requirements.txt
```

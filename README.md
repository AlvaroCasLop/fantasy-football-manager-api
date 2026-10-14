# Fantasy Football API 🏈

Backend moderno y desacoplado para la gestión de ligas, equipos, torneos y actas de partido de **Fantasy Football / Blood Bowl Manager**.

Diseñado con **FastAPI**, **SQLAlchemy 2.0 (Async)**, **Pydantic v2** y **PostgreSQL (Supabase)**, optimizado para despliegue directo en **Railway** o Docker.

---

## 🛠️ Stack Tecnológico

* **FastAPI**: Endpoints HTTP de alto rendimiento con validación y documentación interactiva automática (`/docs` y `/redoc`).
* **Pydantic v2**: Validación estricta y tipado de esquemas de entrada y salida (`pydantic-settings` para configuración).
* **SQLAlchemy 2.0**: ORM moderno asíncrono con pool de conexiones de alto rendimiento (`QueuePool`).
* **Supabase**: Base de datos PostgreSQL en la nube con soporte para Connection Pooler (puerto 6543) y autenticación JWT.
* **Alembic**: Migraciones de esquema versionadas y asíncronas, aisladas estrictamente para el esquema `public`.
* **Ruff**: Linter y formateador ultrarrápido todo en uno (reemplaza Black, Flake8 e Isort).
* **pytest**: Pruebas automatizadas unitarias y de integración asíncronas con `pytest-asyncio` y `httpx`.
* **Railway / Docker**: Despliegue en contenedor persistente 24/7 con soporte nativo para WebSockets y migraciones automáticas al desplegar.

---

## 📂 Estructura del Proyecto

```text
fantasy-football-api/
├── alembic/                      # Migraciones de base de datos
│   ├── versions/                 # Revisiones generadas
│   ├── env.py                    # Configuración asíncrona aislada para Supabase (esquema public)
│   └── script.py.mako            # Plantilla de migración
├── src/
│   └── app/
│       ├── core/                 # Infraestructura base
│       │   ├── config.py         # Configuración y variables de entorno tipadas
│       │   ├── database.py       # AsyncEngine, pool de conexiones, Base y mixins
│       │   ├── security.py       # Validador de tokens JWT de Supabase Auth
│       │   └── exceptions.py     # Manejo global de excepciones de dominio
│       ├── modules/              # Dominios de negocio desacoplados
│       │   ├── health/           # Endpoints de diagnóstico y estado
│       │   ├── coaches/          # Perfiles de entrenador vinculados a Supabase Auth
│       │   ├── reference_data/   # Catálogos oficiales (razas, posicionales base, costes)
│       │   ├── teams/            # Equipos, gestión de tesorería, TV y staff
│       │   ├── players/          # Jugadores, atributos (MA/ST/AG/PA/AV), SPP y lesiones
│       │   └── matches/          # Actas de partido y eventos en directo
│       └── main.py               # Instancia de FastAPI, middlewares CORS y enrutamiento
├── tests/                        # Suite de pruebas automatizadas
│   ├── conftest.py               # Fixtures asíncronos y cliente httpx
│   ├── test_health.py            # Tests de endpoint de salud
│   └── test_security.py          # Tests de validación de tokens
├── Dockerfile                    # Multi-stage build para despliegue en producción
├── railway.json                  # Configuración de despliegue y healthcheck para Railway
├── Procfile                      # Comando de arranque para plataformas PaaS
├── pyproject.toml                # Dependencias, configuración de Ruff y pytest
├── requirements.txt              # Dependencias del proyecto
└── .env.example                  # Plantilla de variables de entorno
```

---

## 🚀 Puesta en Marcha Local

### 1. Requisitos
* Python 3.11 o 3.12 (o Docker)
* Conexión a Supabase o PostgreSQL local

### 2. Configurar el entorno virtual
```bash
# Crear entorno virtual
python -m venv .venv

# Activar en Windows PowerShell:
.venv\Scripts\Activate.ps1

# O en Linux/macOS:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 3. Configurar variables de entorno
Copia el archivo `.env.example` a `.env` y configura tus credenciales de Supabase:
```bash
cp .env.example .env
```

### 4. Ejecutar el servidor de desarrollo
```bash
uvicorn src.app.main:app --reload --port 8000
```
Visita la documentación interactiva en:
* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* Health check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🗄️ Base de Datos y Migraciones con Alembic

Alembic está configurado para conectarse usando `asyncpg` y **filtrar automáticamente los esquemas internos de Supabase** (`auth`, `storage`, etc.), gestionando únicamente tus tablas en `public`.

```bash
# Crear una nueva migración automática tras añadir o modificar modelos SQLAlchemy:
alembic revision --autogenerate -m "create teams and players tables"

# Aplicar migraciones pendientes:
alembic upgrade head

# Revertir la última migración:
alembic downgrade -1
```

---

## 🧪 Pruebas Automatizadas y Análisis Estático

```bash
# Ejecutar suite de pruebas con pytest:
pytest

# Analizar código con Ruff (linter):
ruff check .

# Formatear código automáticamente con Ruff:
ruff format .
```

---

## 🚢 Despliegue en Railway

1. Crea un nuevo proyecto en [Railway.app](https://railway.app).
2. Conecta este repositorio de GitHub.
3. Railway detectará automáticamente el archivo `railway.json` y el `Dockerfile`.
4. En la pestaña **Variables** de tu servicio en Railway, añade las variables de tu archivo `.env`:
   * `DATABASE_URL`: Tu cadena de conexión de Supabase (puerto 6543 Transaction Pooler o puerto 5432).
   * `SUPABASE_URL`: URL de tu proyecto Supabase.
   * `SUPABASE_JWT_SECRET`: Clave secreta JWT de Supabase.
   * `CORS_ORIGINS`: URLs permitidas de tu frontend (ej. `["https://tu-frontend.vercel.app"]`).
5. Al hacer `git push`, Railway compilará el contenedor, ejecutará las migraciones (`alembic upgrade head`) y levantará la API automáticamente.

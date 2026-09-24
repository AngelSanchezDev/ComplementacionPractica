# JSConnect Win Coverage — Proyecto escolar

Aplicación de escritorio (Python + Tkinter) que simula la validación de clientes de
un proveedor de internet:

1. **Inicio de sesión**: los usuarios se autentican contra una base de datos
   **SQLite local** (contraseñas guardadas con hash PBKDF2).
2. **Cobertura**: se ingresan coordenadas (latitud, longitud); la cobertura es
   simulada y **siempre responde "SI"**.
3. **Score crediticio**: se ingresa un **DNI de 8 dígitos** y se muestra el score,
   nivel de riesgo y nombre registrados en la base de datos.

No necesita internet ni dependencias externas: solo la librería estándar de Python.

## Requisitos
- Python 3.12+ en Windows.

## Instalación
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## Uso
```powershell
python main.py
```
La primera vez se crea `datos/jsconnect.db` con datos de prueba:

| Usuario | Contraseña |
|---------|------------|
| admin   | admin123   |

| DNI      | Nombre       | Score | Riesgo   |
|----------|--------------|-------|----------|
| 12345678 | Juan Perez   | 720   | BAJO     |
| 87654321 | Maria Lopez  | 580   | MEDIO    |
| 11111111 | Carlos Ramos | 423   | MUY ALTO |
| 22222222 | Ana Torres   | 650   | BAJO     |
| 33333333 | Luis Quispe  | 480   | ALTO     |

Para usar otra base de datos, define la variable de entorno `JSCONNECT_DB` con su ruta.

### Cargar más datos
```powershell
python tools/seed.py usuario <usuario> <contraseña> [nombre]
python tools/seed.py cliente <dni> <score> [riesgo] [nombre]
```

## Estructura
```
main.py                      punto de entrada
validator_app/core/db.py     base de datos SQLite: usuarios, clientes, validaciones
validator_app/gui/           ventana principal, login y validación de entradas
tools/seed.py                CLI para agregar usuarios y clientes
tests/                       pruebas con pytest
build.ps1                    genera el .exe con PyInstaller
```

## Desarrollo
- Tests: `pytest`
- Lint: `ruff check .`
- Ejecutable: `powershell -ExecutionPolicy Bypass -File build.ps1`

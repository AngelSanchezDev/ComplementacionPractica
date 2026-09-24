# JSConnect Win Coverage — Proyecto escolar

Aplicación de escritorio (Python + CustomTkinter) que simula la validación de
clientes de un proveedor de internet:

1. **Inicio de sesión**: los usuarios se autentican contra una base de datos
   **SQLite local** (contraseñas guardadas con hash PBKDF2).
2. **Cobertura**: se ingresan coordenadas (latitud, longitud); la cobertura es
   simulada y **siempre responde "SI"**.
3. **Score crediticio**: se ingresa un **DNI de 8 dígitos** y se muestra el
   score, nivel de riesgo y nombre registrados en la base de datos, con una
   tarjeta de resultado (color según riesgo, barra de progreso 0–1000).
4. **Clientes (CRUD)**: explorador con búsqueda y paginación para crear,
   editar y eliminar clientes, con validación de DNI único, nombre y score.
5. **Historial**: registro de las validaciones hechas por cada usuario.

No necesita internet ni dependencias del sistema operativo: solo la librería
estándar de Python más `customtkinter` para la interfaz.

## Rangos de riesgo

| Score | Riesgo | Calificación |
|---|---|---|
| 0 – 299 | Muy Alto | Malo |
| 300 – 549 | Alto | Regular |
| 550 – 749 | Medio | Bueno |
| 750 – 899 | Bajo | Muy Bueno |
| 900 – 1000 | Muy Bajo | Excelente |

Esta tabla vive en la propia base de datos (`rangos_riesgo`), no en el código:
ver `docs/base-de-datos.md`.

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

...y **1 000 clientes** generados automáticamente (más 5 clientes fijos, entre
ellos el DNI `12345678`), repartidos entre los cinco rangos de riesgo.

Para usar otra base de datos, define la variable de entorno `JSCONNECT_DB` con
su ruta.

### Cargar más datos desde la línea de comandos
```powershell
python tools/seed.py usuario <usuario> <contraseña> [nombre]
python tools/seed.py cliente <dni> <score> <nombre>
python tools/seed.py generar <cantidad>
```

## Estructura
```
main.py                              punto de entrada
validator_app/core/db.py             base de datos SQLite: usuarios, clientes,
                                      rangos de riesgo, historial de consultas
validator_app/gui/
  theme.py                           colores y fuentes compartidos
  login.py                           pantalla de inicio de sesion
  main_window.py                     ventana principal + barra lateral
  validar_view.py                    validar cobertura/score + tarjeta de resultado
  clientes_view.py                   explorador de clientes (buscar, paginar, CRUD)
  cliente_form.py                    formulario crear/editar cliente
  historial_view.py                  historial de consultas
  fields.py                          validacion de coordenadas, DNI, nombre, score
tools/seed.py                        CLI para agregar usuarios y clientes
tests/                                pruebas con pytest
docs/
  proceso-elaboracion.md             bitacora del desarrollo, por etapas
  base-de-datos.md                   diagrama, diccionario de datos, SQL de ejemplo
  manual-usuario.md                  guia de uso paso a paso
build.ps1                            genera el .exe con PyInstaller
```

## Documentación
- [`docs/proceso-elaboracion.md`](docs/proceso-elaboracion.md) — cómo se
  construyó el proyecto, etapa por etapa.
- [`docs/base-de-datos.md`](docs/base-de-datos.md) — diagrama
  entidad-relación, diccionario de datos y consultas SQL de ejemplo.
- [`docs/manual-usuario.md`](docs/manual-usuario.md) — guía de uso de la
  aplicación.

## Desarrollo
- Tests: `pytest`
- Lint: `ruff check .`
- Ejecutable: `powershell -ExecutionPolicy Bypass -File build.ps1`

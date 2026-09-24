# Proceso de elaboración del sistema

Este documento resume, en orden, cómo se construyó **JSConnect Win Coverage** a
partir de un proyecto empresarial de escritorio, hasta convertirlo en el sistema
escolar actual: login local, validación de cobertura y de score crediticio con
base de datos SQLite propia.

## Etapa 1 — Punto de partida

El proyecto original (`JSConnect-Win-Coverage`, repositorio de la empresa) era un
cliente de escritorio para un call center de un proveedor de internet. Validaba
dos cosas contra un sistema externo real (WinForce):

- **Cobertura de servicio**, por coordenadas geográficas.
- **Score crediticio**, por DNI/RUC/Carnet de Extranjería, contra un reporte de
  Equifax.

Para no depender de que cada PC iniciara sesión (el sistema exigía 2FA de
Microsoft), la arquitectura usaba un **proxy local** (FastAPI) instalado en una
PC de oficina: mantenía viva una única sesión y los agentes (los `.exe` de cada
puesto) le pedían las validaciones por HTTP con un token. Además tenía una
extensión de Chrome para renovar la sesión con un clic, activación por licencia
RSA por PC, un actualizador automático desde GitHub Releases y una consola
aparte para el "owner" del sistema.

**Objetivo de esta etapa:** entender qué hacía el proyecto y qué partes eran
específicas de la empresa (seguridad, credenciales, infraestructura) frente a
las que eran el flujo de negocio en sí (validar cobertura y score).

## Etapa 2 — Preparación del entorno

- Se clonó el repositorio original.
- El proyecto exigía **Python 3.12+**; la PC solo tenía 3.10 y 3.11, así que se
  instaló Python 3.12 con `winget`.
- Se creó un entorno virtual (`.venv`) y se instalaron las dependencias de
  desarrollo (`requirements-dev.txt`), que en ese momento incluían `requests`,
  `keyring`, `cryptography`, `httpx`, `fastapi`, `uvicorn`, `pydantic`,
  `playwright`, `pytest`, `ruff` y `pyinstaller`.
- Se corrieron los tests originales (193 casos) para confirmar que el proyecto
  de partida estaba sano antes de modificarlo.

**Problema encontrado:** la versión de Python del sistema no alcanzaba el
mínimo del proyecto. **Solución:** instalar la versión requerida en vez de
rebajar el `pyproject.toml`, para no arrastrar incompatibilidades más
adelante.

## Etapa 3 — Simplificación: quitar la infraestructura de seguridad

Se decidió usar el proyecto como base para un trabajo escolar, manteniendo el
flujo de negocio (validar cobertura y score) pero **sin conectarse a ningún
sistema externo real**. Se eliminó todo lo que existía solo por razones de
seguridad o de operación de la empresa:

| Eliminado | Por qué |
|---|---|
| `validator_app/proxy/` (servidor FastAPI, extensión de Chrome, `.bat` de servicio) | Dependía de una sesión real contra WinForce y de credenciales de la empresa. |
| `validator_app/activation/` (licencias RSA por huella de PC) | Control de licencias comercial, no aplica a un proyecto escolar. |
| `validator_app/updater/` (auto-actualización desde GitHub Releases) | Innecesario sin releases propios que mantener. |
| `generator/` (consola del "owner": generaba códigos de activación) | Dejó de tener sentido sin activación por licencia. |
| `tools/` (captura de tráfico, medición de sesión, pruebas contra el sistema real) | Herramientas de ingeniería inversa contra un sistema que ya no se usa. |
| Documentación interna (`AGENTS.md`, `Roadmap.md`, `PlanesAprobados.md`, bitácoras diarias, etc.) | Contexto operativo de la empresa, no del proyecto escolar. |

## Etapa 4 — Base de datos SQLite local (primera versión)

Se reemplazó el núcleo que llamaba a la API real (`core/api.py`,
`core/session.py`) por un módulo nuevo, `validator_app/core/db.py`, que solo usa
la librería estándar de Python (`sqlite3`, `hashlib`):

- **Login:** contra una tabla `usuarios`, con la contraseña protegida con
  `hashlib.pbkdf2_hmac` (100 000 iteraciones) y un salt aleatorio por usuario —
  nunca en texto plano.
- **Cobertura:** ya no consulta nada externo; siempre responde `"SI"`
  (cobertura simulada), porque lo que importa para el ejercicio es el flujo, no
  un dato geográfico real.
- **Score:** se consulta por **DNI de 8 dígitos** contra una tabla `clientes`
  con un score y un nivel de riesgo precargados.

La interfaz (Tkinter/ttk) se simplificó: un diálogo de login al iniciar y una
ventana con el formulario de validación.

## Etapa 5 — Publicación en un repositorio propio

- Se creó un commit único (con historial limpio, sin el historial de la
  empresa) y se subió a un repositorio nuevo en GitHub, propiedad del alumno.
- Se generó el ejecutable (`build.ps1` + PyInstaller): un solo `.exe` portable
  que no necesita Python instalado.

**Problema encontrado:** GitHub rechazó el primer intento de `push` porque la
cuenta tiene activada la protección de correo privado (rechaza commits con el
correo real si no coincide con el `noreply` de GitHub). **Solución:** usar el
correo `noreply` que GitHub genera para la cuenta
(`<id>+<usuario>@users.noreply.github.com`).

## Etapa 6 — Rediseño de UX/UI, tabla de riesgos, CRUD y datos masivos

Esta es la versión actual del sistema. Se amplió el proyecto en cuatro frentes:

1. **Interfaz nueva con CustomTkinter**, en vez de Tkinter/ttk puro: pantalla de
   login con tarjeta centrada, una barra lateral de navegación (Validar /
   Clientes / Historial), modo claro/oscuro y una **tarjeta de resultado** que
   muestra el score en grande, una barra de progreso de 0 a 1000 y el color
   correspondiente a su nivel de riesgo.
2. **Tabla de rangos de riesgo dentro de la base de datos** (`rangos_riesgo`),
   en vez de un valor fijo por cliente:

   | Rango de score | Riesgo | Calificación |
   |---|---|---|
   | 0 – 299 | Muy Alto | Malo |
   | 300 – 549 | Alto | Regular |
   | 550 – 749 | Medio | Bueno |
   | 750 – 899 | Bajo | Muy Bueno |
   | 900 – 1000 | Muy Bajo | Excelente |

   El riesgo de un cliente ya no se guarda como texto suelto: se calcula con un
   `JOIN` entre `clientes.score` y esta tabla, así que cambiar un rango en un
   solo lugar actualiza la calificación de todos los clientes que caen en él.
3. **CRUD completo de clientes**, con las validaciones pedidas: el DNI debe
   tener exactamente 8 dígitos numéricos, el nombre solo letras y espacios, el
   score entre 0 y 1000, y **el DNI no puede repetirse** — el formulario avisa
   "El DNI ya está registrado" apenas se completan los 8 dígitos, antes incluso
   de intentar guardar.
4. **1 000 clientes de prueba**, generados de forma determinista (misma semilla
   → mismos datos) y repartidos entre los cinco rangos de riesgo, para que el
   explorador de clientes (con búsqueda y paginación) tenga volumen real que
   mostrar.

También se agregó un **historial de consultas** por usuario (tabla `consultas`,
ligada a `usuarios` por clave foránea) y un script de línea de comandos
(`tools/seed.py`) para cargar usuarios o clientes nuevos sin abrir la interfaz.

**Migración de datos:** como ya existían bases de datos de la Etapa 4 (con la
columna `riesgo` escrita a mano), `db.py` detecta ese esquema viejo al conectar
y migra los clientes existentes al esquema nuevo automáticamente, sin perder
datos.

**Cómo se verificó cada etapa:** además de los tests automáticos (`pytest`),
cada entrega se probó abriendo la aplicación real (o el `.exe` construido) y
ejercitando el flujo completo: iniciar sesión, validar un DNI conocido y uno
desconocido, crear/editar/eliminar un cliente de prueba y revisar que quedara
en el historial.

## Etapa 7 — Usabilidad, dashboard y consultas con JOIN

A partir de comentarios de uso real sobre la Etapa 6, se afinó la interfaz y
se agregaron dos pantallas nuevas orientadas a sustentar el proyecto de base
de datos:

- **Usabilidad:** los botones de acción (Guardar, Nuevo, Editar, Eliminar…)
  tenían tamaño y tipografía por defecto de Tk, casi invisibles junto al
  resto de la interfaz; se homogeneizaron con una altura y fuente comunes
  (`theme.ALTO_BOTON`, `theme.FUENTE_BOTON`). La tabla de clientes ganó una
  barra de desplazamiento vertical.
- **Copiar DNI:** botón dedicado en el explorador de clientes (más clic
  derecho sobre la tabla) y en la tarjeta de resultado de Validar, para no
  tener que transcribir el número a mano.
- **Filtro por nivel de riesgo:** el explorador de clientes ganó un
  desplegable para quedarse solo con un nivel; `buscar_clientes()` en
  `core/db.py` se amplió para aceptar ese filtro además del texto libre.
- **Dashboard (matplotlib):** una vista nueva con el porcentaje de clientes
  en cada nivel de riesgo (tarjetas + gráfico de barras horizontales), donde
  un clic en cualquier nivel lleva al explorador de clientes ya filtrado por
  ese riesgo — conectando el punto anterior con este.
- **Consultas SQL (catálogo de JOIN):** una vista nueva con 5 consultas
  predefinidas sobre las tablas del proyecto, cada una mostrando un tipo de
  `JOIN` distinto (INNER simple, LEFT, INNER múltiple sobre 3 tablas, LEFT
  como antijoin, e INNER con agregación), con el SQL visible junto al
  resultado — pensada para poder explicar, con ejemplos reales corriendo
  contra la base, las distintas formas de unir tablas.

**Problema encontrado:** al ejecutar el dashboard, la aplicación fallaba con
`AttributeError: 'FigureCanvasTkAgg' object has no attribute 'winfo_exists'`
al cambiar el tamaño de la ventana. La causa: `DashboardView` hereda de
`ctk.CTkFrame`, que ya usa internamente un atributo de instancia llamado
`self._canvas` para su propio dibujo (el canvas que pinta las esquinas
redondeadas); al guardar el gráfico de matplotlib en `self._canvas` se pisaba
ese atributo interno de CustomTkinter. **Solución:** renombrar el atributo
propio a `self._canvas_grafico`, dejando intacto el uso interno de
CustomTkinter. Queda como aviso para cualquier widget nuevo que herede de un
widget de CustomTkinter: evitar nombres de atributo genéricos como `_canvas`,
`_frame` o `_label` que puedan chocar con la implementación interna de la
librería.

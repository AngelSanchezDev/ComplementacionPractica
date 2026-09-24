# Base de datos

La aplicación usa **SQLite** (un solo archivo, sin servidor) a través del
módulo estándar `sqlite3`. El archivo vive en `datos/jsconnect.db` (o donde
apunte la variable de entorno `JSCONNECT_DB`) y se crea solo, con datos de
ejemplo, la primera vez que se ejecuta la app.

## Diagrama entidad-relación

```mermaid
erDiagram
    usuarios ||--o{ consultas : "realiza"
    rangos_riesgo ||--o{ clientes : "clasifica (por score)"
    rangos_riesgo ||--o{ consultas : "clasifica (por score)"

    usuarios {
        integer id PK
        text usuario UK
        text password_hash
        text salt
        text nombre
    }
    clientes {
        text dni PK "8 digitos"
        text nombre
        integer score "0 a 1000"
    }
    rangos_riesgo {
        integer id PK
        integer score_min
        integer score_max
        text riesgo UK
        text calificacion
        text color
    }
    consultas {
        integer id PK
        integer usuario_id FK
        text dni
        real lat
        real lon
        text cobertura
        integer score
        text fecha
    }
```

La relación entre `clientes`/`consultas` y `rangos_riesgo` no es una clave
foránea: es un `JOIN` por rango (`score BETWEEN score_min AND score_max`), así
que un cliente nunca "guarda" su riesgo — se calcula en el momento a partir de
su score.

## Diccionario de datos

### `usuarios`
Cuentas que pueden iniciar sesión en la aplicación.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | Identificador interno. |
| `usuario` | TEXT UNIQUE NOT NULL | Nombre de usuario para el login. |
| `password_hash` | TEXT NOT NULL | Hash PBKDF2-SHA256 de la contraseña (100 000 iteraciones). |
| `salt` | TEXT NOT NULL | Salt aleatorio (16 bytes, en hexadecimal) usado al calcular el hash. |
| `nombre` | TEXT | Nombre para mostrar. |

La contraseña **nunca se guarda en texto plano**: se calcula
`PBKDF2(password, salt)` y se compara ese hash contra el guardado.

### `clientes`
Las personas que se pueden consultar por DNI.

| Columna | Tipo | Descripción |
|---|---|---|
| `dni` | TEXT PK | Exactamente 8 dígitos numéricos (`CHECK`). |
| `nombre` | TEXT NOT NULL | Nombre completo. |
| `score` | INTEGER NOT NULL | Entre 0 y 1000 (`CHECK`). |

Índice `idx_clientes_nombre` sobre `nombre`, para que la búsqueda por nombre en
el explorador de clientes no recorra la tabla completa.

### `rangos_riesgo`
La tabla de clasificación de riesgo por score, editable sin tocar código.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | Identificador interno. |
| `score_min` | INTEGER NOT NULL | Límite inferior del rango (incluido). |
| `score_max` | INTEGER NOT NULL | Límite superior del rango (incluido). |
| `riesgo` | TEXT UNIQUE NOT NULL | Nivel de riesgo ("Muy Alto"… "Muy Bajo"). |
| `calificacion` | TEXT NOT NULL | Calificación en palabras ("Malo"… "Excelente"). |
| `color` | TEXT NOT NULL | Color hexadecimal usado en la interfaz. |

`CHECK (score_min <= score_max)`. Se llena una sola vez, al crear la base, con
los 5 rangos oficiales del proyecto.

### `consultas`
El historial de validaciones hechas por cada usuario.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | Identificador interno. |
| `usuario_id` | INTEGER FK → `usuarios.id` | Quién hizo la consulta (`ON DELETE SET NULL`). |
| `dni` | TEXT NOT NULL | DNI consultado (no valida que exista en `clientes`: se puede consultar un DNI que no está registrado). |
| `lat`, `lon` | REAL NOT NULL | Coordenadas usadas en la validación de cobertura. |
| `cobertura` | TEXT NOT NULL | Resultado de cobertura ("SI"). |
| `score` | INTEGER | Score encontrado, o `NULL` si el DNI no estaba registrado. |
| `fecha` | TEXT | Fecha y hora local, puesta automáticamente por SQLite. |

## Consultas de ejemplo

**Riesgo de un cliente (el JOIN que usa la aplicación):**
```sql
SELECT c.dni, c.nombre, c.score, r.riesgo, r.calificacion
FROM clientes c
LEFT JOIN rangos_riesgo r ON c.score BETWEEN r.score_min AND r.score_max
WHERE c.dni = '12345678';
```

**Cuántos clientes hay en cada nivel de riesgo:**
```sql
SELECT r.riesgo, COUNT(*) AS total
FROM clientes c
JOIN rangos_riesgo r ON c.score BETWEEN r.score_min AND r.score_max
GROUP BY r.riesgo
ORDER BY r.score_min DESC;
```

**Últimas 20 consultas de un usuario:**
```sql
SELECT fecha, dni, cobertura, score
FROM consultas
WHERE usuario_id = 1
ORDER BY id DESC
LIMIT 20;
```

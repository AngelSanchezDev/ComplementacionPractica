# Manual de usuario

## 1. Iniciar sesión

Al abrir la aplicación aparece una tarjeta con **Usuario** y **Contraseña**.

- Usuario de prueba: `admin` / `admin123`.
- La casilla **"Mostrar contraseña"** revela el texto escrito.
- Si los datos son incorrectos, aparece en rojo: *"Usuario o contraseña
  incorrectos."* — la contraseña escrita se borra y hay que intentar de nuevo.

## 2. Validar un cliente

Es la pantalla que aparece al entrar (menú lateral, opción **Validar**).

1. Escribe las **coordenadas** como `latitud, longitud`, por ejemplo
   `-11.956037, -77.040653`. Si el formato no es válido (falta la coma, no son
   números, o están fuera de rango), aparece el motivo debajo del campo.
2. Escribe el **DNI** (8 dígitos). El campo solo acepta números y no deja
   escribir más de 8 caracteres.
3. Presiona **VALIDAR** (o Enter).

**Resultado con cobertura y DNI registrado:** la tarjeta de resultado muestra
"Cobertura: SI", el score en grande con el color de su riesgo, una barra de
progreso de 0 a 1000, el nivel de riesgo con su calificación (por ejemplo
"Riesgo Medio · Bueno") y el nombre del cliente.

**Resultado con un DNI no registrado:** la tarjeta muestra "DNI no registrado"
y un botón **"Registrar cliente"** que abre el formulario de creación con ese
DNI ya escrito.

En ambos casos aparece un botón **"Copiar DNI"** para copiar al portapapeles
el DNI que acabas de consultar.

Cada validación (tenga o no cobertura, exista o no el DNI) queda guardada en el
**Historial**.

## 3. Dashboard

Menú lateral, opción **Dashboard**. Muestra, para cada nivel de riesgo, una
tarjeta con su porcentaje y su conteo de clientes, y debajo un gráfico de
barras con los mismos datos. **Haz clic en una tarjeta o en una barra** para
ir directo al explorador de Clientes, ya filtrado por ese nivel de riesgo.

## 4. Explorador de clientes (CRUD)

Menú lateral, opción **Clientes**.

- **Buscar:** escribe un número para buscar por DNI (coincidencia desde el
  inicio) o un texto para buscar por nombre. La búsqueda se actualiza sola
  mientras escribes.
- **Filtrar por riesgo:** el menú desplegable junto al buscador limita la
  lista a un solo nivel ("Todos" lo quita). Se combina con la búsqueda por
  texto. Al llegar desde el Dashboard, el filtro ya viene puesto.
- **Paginación y barra de desplazamiento:** la tabla muestra 50 clientes a la
  vez, con una barra de desplazamiento vertical; los botones "< Anterior" /
  "Siguiente >" cambian de página, y el contador ("1–50 de 1000") indica dónde
  estás.
- **Copiar DNI:** selecciona una fila y presiona el botón, o haz clic derecho
  sobre la fila y elige "Copiar DNI" en el menú.
- **Nuevo:** abre el formulario en blanco.
- **Editar:** selecciona una fila (o haz doble clic) y presiona Editar. El DNI
  no se puede cambiar al editar.
- **Eliminar:** selecciona una fila, presiona Eliminar y confirma. La acción no
  se puede deshacer.

### Formulario de cliente

- **DNI:** 8 dígitos numéricos. Mientras escribes, si ya existe un cliente con
  ese DNI aparece de inmediato: *"El DNI ya está registrado."* — no se puede
  guardar hasta usar un DNI distinto.
- **Nombre completo:** solo letras y espacios, mínimo 3 caracteres.
- **Score:** un número entre 0 y 1000. Mientras escribes, debajo aparece en
  vivo a qué nivel de riesgo corresponde (por ejemplo "Riesgo Bajo · Muy
  Bueno"), con el mismo color que se ve en la tabla y en el resultado de
  validación.
- Cualquier error de validación aparece en rojo antes de intentar guardar.

## 5. Historial

Menú lateral, opción **Historial**. Muestra, de la más reciente a la más
antigua, cada validación hecha por el usuario que tiene la sesión abierta:
fecha, DNI consultado, cobertura, score (si el DNI estaba registrado) y su
riesgo.

## 6. Consultas SQL

Menú lateral, opción **Consultas SQL**. Pensada para explicar cómo está
armada la base de datos: un menú desplegable con 5 consultas ya escritas,
cada una usando un tipo distinto de `JOIN` (INNER, LEFT, antijoin, múltiple
sobre 3 tablas, y con agregación). Al elegir una, se ve su tipo de JOIN, una
explicación breve, el SQL exacto y, al presionar **Ejecutar**, el resultado
en una tabla. El detalle de cada consulta está en
[`docs/base-de-datos.md`](base-de-datos.md).

## 7. Otras opciones

- **Modo oscuro:** interruptor en la parte inferior del menú lateral.
- **Cerrar sesión:** vuelve a la pantalla de login sin cerrar la aplicación.

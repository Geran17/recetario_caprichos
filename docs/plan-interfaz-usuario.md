# Plan por etapas para la interfaz de usuario

Este documento propone una ruta incremental para construir la interfaz gráfica
del recetario con Tkinter. El objetivo es entregar una aplicación de escritorio
que permita mantener catálogos, definir menús y registrar la planificación y
producción diaria sin acceder directamente a SQL desde las pantallas.

**Estado:** están implementadas la estructura visual y la navegación, y las
secciones de catálogos, menús base, planificación, producción y reportes están
conectadas a controladores y servicios. Se puede consultar y persistir la
información, así como previsualizar y exportar reportes a CSV/PDF. La impresión
envía el PDF a `lp`/`lpr` y requiere configurar el servicio de impresión del
sistema. El panel principal muestra únicamente los totales de menús base
registrados, planificaciones del día y producciones de la fecha actual. Las
pruebas automatizadas de controlador usan bases temporales.

## Alcance funcional

La aplicación cubrirá el flujo de trabajo que representa la base de datos:

1. Administrar unidades, cocineros e ingredientes.
2. Definir menús base y asociarles responsables e ingredientes.
3. Planificar menús base por fecha y registrar porciones.
4. Registrar los ingredientes realmente utilizados en cada preparación.
5. Registrar la cantidad producida y las porciones obtenidas.
6. Consultar, imprimir y exportar reportes de menús, planificación/consumos y
   producción.

La interfaz inicial será para uso local en un comedor. No contempla por ahora
usuarios, inicio de sesión, permisos ni sincronización entre equipos.

## Arquitectura acordada

Mantener las responsabilidades separadas:

```text
src/main.py
    └── src/vista/          Tkinter: widgets, ventanas y presentación
          ↕ eventos / datos de presentación
        src/controlador/    acciones, coordinación y flujo de usuario
          └── src/modelo/services.py
                └── src/modelo/daos.py
                      └── src/modelo/consultas.py
                            └── SQLite
```

- `vista` contiene únicamente la presentación Tkinter: ventanas, frames,
  formularios, tablas, estilos y diálogos. Puede exponer métodos para mostrar
  datos y registrar callbacks, pero no valida reglas de negocio, llama servicios,
  abre conexiones ni construye SQL.
- `controlador` recibe acciones de la vista, valida los datos de entrada para el
  flujo de la aplicación, llama a los servicios y decide qué datos o mensajes
  devolver a la vista. No crea ni modifica widgets directamente.
- `services.py` ofrece las operaciones de las entidades al controlador, por
  ejemplo `Cocinero.listar()` o `Cocinero.insertar()`.
- `daos.py` coordina la persistencia y convierte filas en DTOs/entidades.
- `consultas.py` es el lugar central para generar sentencias SQL, incluidas
  futuras consultas específicas requeridas por la interfaz.
- `scripts/database.sql` define el esquema de la base de datos.

La dirección de las dependencias debe ser unidireccional desde la interfaz al
dominio: `vista → controlador → services → DAO → consultas → SQLite`. Para
actualizar la interfaz, el controlador invoca métodos de presentación o actualiza
un modelo de vista sencillo; la vista no importa controladores concretos ni
servicios. La composición en `main.py` conecta la vista con su controlador e
inyecta las dependencias.

Las rutas de la base de datos y las dependencias se deben poder inyectar para
probar controladores con una base temporal. Las vistas no deben depender de una
ruta escrita directamente en cada pantalla.

## Etapa 0: preparación de la aplicación

**Objetivo:** tener un punto de entrada y una base lista para que la interfaz
pueda operar.

**Trabajo:**

- Definir la ventana raíz Tkinter y el módulo de arranque en `src/main.py`.
- Configurar título, tamaño inicial, comportamiento al cerrar y tema visual
  básico.
- Definir una única configuración de la ruta de base de datos y compartirla
  con los servicios/DAO.
- Crear el punto de composición que instancia servicios, controladores y vistas
  y los conecta sin mezclar sus responsabilidades.
- Preparar una inicialización explícita de esquema antes de mostrar la ventana.
- Revisar el contenido de `scripts/database.sql`: además del DDL incluye datos
  de ejemplo con identificadores fijos. No se debe ejecutar repetidamente como
  inicializador de cada arranque; separar el esquema de las semillas, o controlar
  que estas se apliquen una sola vez.
- Si la base ya existe, no asumir que `CREATE TABLE IF NOT EXISTS` la migra.
  Informar de manera clara si el esquema requiere una migración.

**Criterios de aceptación:**

- La aplicación inicia y se cierra sin errores.
- Si falta la base, la inicialización del esquema ocurre antes de usar servicios.
- Un fallo al preparar la base se informa; no se presenta una ventana funcional
  con datos que no pueden guardarse.

## Etapa 1: estructura visual y navegación

**Objetivo:** establecer una experiencia consistente antes de añadir todos los
formularios.

**Trabajo:**

- Crear una ventana principal con navegación clara para **Inicio**,
  **Catálogos**, **Menús base** y **Planificación diaria**.
- Reservar un área de contenido para mostrar cada vista sin abrir ventanas
  innecesarias.
- Crear componentes compartidos: formulario etiquetado, botones de acción,
  tabla/listado, estados vacíos, cuadros de confirmación y mensajes de error.
- Hacer que los controles publiquen eventos mediante callbacks que conectará
  el controlador; no asociar en la vista lógica de persistencia.
- Añadir **Reportes** a la navegación para mostrar informes y exportaciones.
- En la primera maqueta, permitir que el menú lateral cambie entre páginas
  vacías solo para revisar la presentación. Al implementar el controlador, esa
  navegación podrá conectarse desde el punto de composición sin añadir
  operaciones de negocio a la vista.
- Mantener textos, validaciones y nombres del dominio en español.
- Permitir cerrar o cancelar formularios sin guardar cambios accidentalmente.

**Criterios de aceptación:**

- Se puede navegar entre las secciones principales.
- Los controles mantienen tamaño y alineación razonables al redimensionar la
  ventana.
- La navegación no abre conexiones a la base por sí sola ni ejecuta SQL desde
  Tkinter.

## Etapa 2: catálogos

**Objetivo:** gestionar los datos que se reutilizan en las demás etapas.

**Pantallas:**

- **Unidades de medida:** nombre y abreviatura.
- **Cocineros:** código, nombre y estado activo.
- **Ingredientes:** código, nombre, descripción y unidad base.

**Implementación actual:** cada catálogo muestra sus registros y ofrece alta,
edición y eliminación mediante callbacks. El controlador delega en servicios y
DAO, comunica errores de integridad/validación y refresca la lista después de
operaciones exitosas.

**Comportamiento común:**

- Mostrar listados y formularios; conectar las acciones crear, editar y
  eliminar con callbacks.
- Delegar la consulta y persistencia al controlador.
- Mostrar códigos y nombres en los selectores de otras pantallas.
- Validar formato de entrada en la vista solo para dar retroalimentación
  inmediata; el controlador aplica las validaciones de flujo antes de llamar al
  servicio.
- Pedir confirmación visual para eliminar y dejar al controlador ejecutar la
  operación y tratar errores de integridad referencial.

**Criterios de aceptación:**

- Las altas, modificaciones y eliminaciones persisten al reiniciar la aplicación.
- Un código o nombre duplicado se informa como error sin perder lo ingresado.
- Las listas se refrescan después de una operación exitosa.

## Etapa 3: menús base

**Objetivo:** definir el catálogo de recetas/menús y sus relaciones.

**Pantalla:**

- Datos del menú: código, nombre, porción, unidad y descripción.
- Selección de uno o varios cocineros responsables.
- Selección de los ingredientes que componen el menú.

`MenuBase_Ingrediente` es una asociación: aquí se eligen ingredientes, pero no
se ingresa cantidad ni unidad. Las cantidades de una preparación concreta se
registran en la etapa diaria.

En el formulario de menú, el usuario agrega ingredientes desde los registrados
en Catálogos y puede quitar los seleccionados. Para guardar se requiere al menos
un ingrediente; modificar la composición de un menú consiste en agregar o quitar
ingredientes al editarlo.

**Implementación actual:** listado y formulario con datos del menú, selectores
de unidades y listas de selección múltiple para responsables e ingredientes.
El controlador carga las opciones y guarda el menú junto con sus relaciones en
una misma transacción.

**Criterios de aceptación:**

- Se puede crear y editar un menú con su porción y unidad.
- Las relaciones de responsables e ingredientes se guardan y se muestran al
  volver a abrir el menú.
- No se permiten asociaciones duplicadas.
- La búsqueda/selección de entidades muestra nombres legibles, no solo claves
  numéricas.

## Etapa 4: planificación y preparación diaria

**Objetivo:** registrar lo que se preparará y los insumos que efectivamente se
utilizan.

**Pantalla:**

- Mostrar selectores de fecha y menú base conectados al controlador.
- Mostrar la porción y su unidad como valores de solo lectura, tomados del menú
  base seleccionado. La planificación copia esos valores a su registro diario.
- Presentar los ingredientes utilizados con cantidad y unidad en una tabla
  editable.
- Facilitar la selección a partir de los ingredientes asociados al menú base;
  permitir decidir si se admitirán ingredientes extraordinarios.
- El controlador coordina la lectura y escritura de la planificación y los
  ingredientes diarios mediante los servicios.

La última decisión requiere validar el comportamiento esperado del comedor
antes de implementarla. En cualquier caso, `MenuDiario_Ingrediente` registra
consumos diarios y no reemplaza la asociación de ingredientes del menú base.

**Implementación actual:** formulario de fecha y menú con porción y unidad de
solo lectura tomadas del menú base seleccionado, captura
de ingredientes realmente utilizados, consulta por fecha y persistencia. La
planificación y sus detalles de ingredientes se guardan en una misma transacción.
Al agregar un ingrediente utilizado, la lista se filtra según los ingredientes
asociados al menú base seleccionado; al cambiar de menú se confirma antes de
limpiar los ingredientes pendientes del borrador. Además, el usuario puede
cargar varios ingredientes en un diálogo tabular; la unidad de cada ingrediente
se preselecciona según la unidad configurada en el catálogo de ingredientes.

**Criterios de aceptación:**

- El usuario puede consultar la planificación por fecha desde la vista.
- El controlador y la base respetan la unicidad fecha/menú y las cantidades
  mayores que cero.
- Errores de validación comunicados por el controlador preservan los datos del
  formulario para corregirlos.

## Etapa 5: registro de producción

**Objetivo:** cerrar el registro de una preparación.

**Pantalla:**

- Presentar preparaciones diarias para seleccionar o abrir.
- Capturar cantidad producida, unidad y cantidad de porciones.
- Mostrar la porción planificada como referencia para el cálculo.
- Explicar claramente los errores si la unidad no coincide con la unidad de la
  porción o si la relación cantidad/porciones no es válida; el controlador
  recibe los errores y solicita mostrarlos.
- Presentar las salidas registradas por fecha y menú.

Las reglas finales ya se aplican en SQLite mediante triggers; la interfaz puede
anticipar errores para mejorar la experiencia, pero la base sigue siendo la
fuente de verdad.

La navegación incluye la sección «Acerca de», donde se identifica a German
Cespedes como autor del sistema.

**Implementación actual:** formulario de producción con selectores de menú
diario y unidad, campos de cantidad/porciones y filtro por fecha para el menú
planificado y el historial. Ambos filtros comienzan en la fecha actual. El
historial permite editar o eliminar la salida seleccionada. El controlador
registra y actualiza las salidas, y presenta errores devueltos por las reglas de
la base. Las porciones se calculan automáticamente y el campo es de solo
lectura. Convierte unidades compatibles de masa, volumen y conteo; por ejemplo,
6 litros equivalen a 6000 ml. La cantidad puede ingresarse como número con
unidad opcional (`6000 ml`); al seleccionar el menú planificado se completa la
fecha y hora actual. No se hacen conversiones entre masa y volumen sin datos de
densidad.

**Criterios de aceptación:**

- Una salida válida se guarda mediante el controlador y aparece en el historial.
- El selector de menú planificado muestra solo los menús de la fecha filtrada,
  inicialmente la fecha actual.
- Una salida seleccionada puede editarse o eliminarse y el historial se
  actualiza después de cada operación.
- Las restricciones de unidad y cálculo se explican al usuario si SQLite
  rechaza el registro y el controlador presenta el error.

## Etapa 6: reportes e impresión/exportación

**Objetivo:** consultar datos del recetario en formato legible y permitir
imprimirlos o exportarlos.

**Reportes iniciales:**

- Menús base con porciones, unidades, responsables e ingredientes asociados.
- Planificación por período, incluyendo los ingredientes y cantidades
  registrados en cada preparación diaria.
- Producción por período, con menú, cantidad producida, unidad y porciones.

**Implementación actual:** el área Reportes permite generar vista previa,
imprimir y exportar los tres informes a PDF/CSV. Las consultas permanecen en
`src/modelo/consultas.py`; CSV usa UTF-8 con BOM para compatibilidad con hojas
de cálculo y PDF se genera con ReportLab. Para que esta dependencia esté
disponible, instala el entorno y ejecuta la aplicación con
`pipenv install` y `pipenv run python src/main.py` (en VS Code, selecciona el
intérprete Pipenv del proyecto). La impresión se realiza en un hilo secundario
mediante `lp`/`lpr`; su funcionamiento depende de la configuración del sistema
operativo.

**Criterios de aceptación:**

- Los filtros de período y tipo llegan al controlador sin que la vista acceda
  directamente a datos.
- La vista previa muestra las mismas filas que se exportan.
- CSV y PDF pueden abrirse con sus lectores habituales y conservan encabezados,
  datos y período seleccionado.
- La exportación PDF/CSV se prueba con archivos temporales; la impresión real
  requiere una cola de impresión configurada y debe verificarse en el equipo de
  despliegue.
- Cancelar el diálogo de guardado no ejecuta exportación.
- Un error de impresión o exportación no se presenta como éxito.

## Etapa 7: integración y calidad

**Objetivo:** verificar el flujo completo y preparar el uso cotidiano.

**Trabajo:**

- Recorrer el flujo desde catálogos hasta producción usando una base temporal.
- Probar creación/edición de menús y planificación con relaciones inválidas y
  comprobar que la transacción revierte todas las escrituras.
- Probar campos vacíos, duplicados, valores fuera de rango, cancelaciones y
  errores de claves foráneas.
- Comprobar el formato y la validación de fechas y cantidades.
- Verificar que el cierre de la ventana no deje recursos abiertos.
- Revisar navegación por teclado, foco inicial y etiquetas accesibles.
- Probar con el entorno Tkinter de destino; la disponibilidad del módulo Python
  no garantiza que el sistema operativo tenga servidor gráfico configurado.

**Criterios de aceptación:**

- Las acciones siguen `vista → controlador → services → DAO`; no hay reglas de
  negocio ni acceso a servicios o SQL en `vista`.
- Las pruebas de vista verifican presentación y eventos; las pruebas del
  controlador verifican coordinación, validación y respuesta ante errores.
- Las pruebas de persistencia no modifican la base de datos real.
- La aplicación informa éxitos y errores, sin ocultar excepciones de escritura.

## Organización sugerida

Mantener módulos de vista y controlador separados, haciendo crecer cada paquete
a medida que se implemente cada etapa:

```text
src/vista/
    __init__.py
    aplicacion.py             # ventana raíz y navegación visual
    componentes.py            # widgets reutilizables, sin lógica de negocio
    catalogos.py              # pantallas de unidades, cocineros e ingredientes
    menus_base.py             # presentación de menús y relaciones
    planificacion_diaria.py   # presentación de planificación y consumos
    produccion.py             # presentación de salidas e historial

src/controlador/
    __init__.py
    controlador_principal.py  # navegación y coordinación de pantallas
    catalogos.py              # acciones y flujo de los catálogos
    menus_base.py             # acciones y flujo de menús
    planificacion_diaria.py   # acciones y flujo de planificación
    produccion.py             # acciones y flujo de producción
```

Las vistas exponen operaciones de presentación como `mostrar_cocineros`,
`mostrar_error` o `obtener_datos_formulario`, y reciben callbacks para acciones
como guardar o eliminar. Los controladores enlazan esos callbacks, invocan los
servicios y llaman los métodos de presentación para refrescar la pantalla. Las
vistas no importan servicios ni DAOs y los controladores no manipulan widgets
internos directamente.

Se recomienda agregar solo los módulos necesarios en cada etapa y mantener los
formularios pequeños y enfocados. `main.py` construye y conecta las vistas y
controladores, e inyecta sus servicios y dependencias.

## Orden sugerido de implementación

La estructura visual y los controladores de las etapas 1 a 6 ya están conectados.
Las pruebas automatizadas verifican CRUD, relaciones, planificación, producción,
reportes y exportaciones sobre una base temporal. El trabajo restante es validar
la experiencia gráfica en el entorno de despliegue, comprobar la impresión real
y definir una estrategia de migración para bases creadas con versiones previas
del esquema. La inicialización actual solo prepara una base nueva; no migra una
base existente.

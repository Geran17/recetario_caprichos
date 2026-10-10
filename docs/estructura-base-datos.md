# Estructura de la base de datos

La base de datos del recetario está implementada en SQLite y definida en
[`scripts/database.sql`](../scripts/database.sql). Organiza la información en
catálogos, menús base, planificación diaria y registro de producción de cocina.
Al comenzar el script se activa la validación de claves foráneas.

## Vista general

```text
UnidadMedida ──< Ingrediente
      │
      ├────────< MenuBase
      │              ├──< MenuBase_Responsable >── Cocinero
      │              ├──< MenuBase_Ingrediente >── Ingrediente
      │              └──< MenuDiario
      │                       ├──< MenuDiario_Ingrediente >── Ingrediente
      │                       └──< SalidaMenuCocina
      └───────────────────────┘
```

Las relaciones marcadas con `──<` son de uno a muchos. Las tablas de unión
`MenuBase_Responsable` y `MenuBase_Ingrediente` resuelven relaciones de muchos
a muchos.

## Catálogos

### `UnidadMedida`

Catálogo de unidades que se reutilizan en los ingredientes, porciones y
cantidades de producción.

| Columna | Descripción |
| --- | --- |
| `id_unidad` | Clave primaria autoincremental. |
| `nombre` | Nombre de la unidad; obligatorio y único. |
| `abreviatura` | Abreviatura; obligatoria y única. |

### `Cocinero`

Personas responsables de preparar los menús base.

| Columna | Descripción |
| --- | --- |
| `id_cocinero` | Clave primaria autoincremental. |
| `codigo` | Código identificador; obligatorio y único. |
| `nombre` | Nombre del cocinero; obligatorio. |
| `activo` | Estado del cocinero (`1` activo, `0` inactivo); por defecto `1`. |

El valor de `activo` está limitado a `0` o `1`.

### `Ingrediente`

Catálogo de insumos. Cada ingrediente tiene una unidad base que se usa para
interpretar las cantidades registradas.

| Columna | Descripción |
| --- | --- |
| `id_ingrediente` | Clave primaria autoincremental. |
| `codigo` | Código identificador; obligatorio y único. |
| `nombre` | Nombre del ingrediente; obligatorio y único. |
| `descripcion` | Descripción opcional. |
| `id_unidad` | Unidad base; referencia a `UnidadMedida`. |

La unidad referenciada no se puede eliminar mientras esté en uso (`ON DELETE
RESTRICT`).

## Menús base y sus relaciones

### `MenuBase`

Define un menú reutilizable y el tamaño de una porción estándar.

| Columna | Descripción |
| --- | --- |
| `id_menu_base` | Clave primaria autoincremental. |
| `codigo` | Código identificador; obligatorio y único. |
| `nombre` | Nombre del menú; obligatorio y único. |
| `porcion` | Tamaño de la porción; debe ser mayor que cero. |
| `id_unidad` | Unidad de la porción; referencia a `UnidadMedida`. |
| `descripcion` | Descripción opcional. |

La porción y su unidad describen la ración estándar del menú.

### `MenuBase_Responsable`

Asocia menús base con cocineros responsables. Su clave primaria compuesta por
`id_menu_base` e `id_cocinero` impide repetir la misma asignación. Ambas
columnas son claves foráneas; al eliminar un menú o cocinero relacionado, la
asignación se elimina en cascada (`ON DELETE CASCADE`).

### `MenuBase_Ingrediente`

Indica qué ingredientes forman parte de cada menú base. Tiene una clave
primaria compuesta (`id_menu_base`, `id_ingrediente`) y claves foráneas a
`MenuBase` e `Ingrediente`.

Esta tabla **no almacena cantidades ni unidades**: representa únicamente la
composición del menú. Las cantidades realmente utilizadas y sus unidades se
registran por fecha en `MenuDiario_Ingrediente`. Al eliminar un menú base se
eliminan sus asociaciones a ingredientes; un ingrediente no puede eliminarse
mientras una asociación lo utilice (`ON DELETE RESTRICT`).

## Planificación diaria

### `MenuDiario`

Representa la planificación de un menú base para una fecha determinada.

| Columna | Descripción |
| --- | --- |
| `id_menu_diario` | Clave primaria autoincremental. |
| `id_menu_base` | Menú planificado; referencia a `MenuBase`. |
| `fecha` | Fecha de planificación; obligatoria. |
| `porcion` | Copia del tamaño de porción aplicable ese día; debe ser mayor que cero. |
| `id_unidad_porcion` | Unidad de la porción de ese día; referencia a `UnidadMedida`. |

La combinación de `fecha` e `id_menu_base` es única, por lo que un mismo menú
base no se puede planificar dos veces en la misma fecha. La porción y su unidad
se guardan como una copia de la planificación diaria, independiente de futuros
cambios en la definición del menú. El menú base y la unidad no se pueden
eliminar mientras estén referenciados (`ON DELETE RESTRICT`).

### `MenuDiario_Ingrediente`

Registra los ingredientes y cantidades utilizadas en la preparación de un
menú diario. Su clave primaria compuesta (`id_menu_diario`, `id_ingrediente`)
permite una sola fila por ingrediente y menú diario.

| Columna | Descripción |
| --- | --- |
| `id_menu_diario` | Menú diario preparado; referencia a `MenuDiario`. |
| `id_ingrediente` | Ingrediente utilizado; referencia a `Ingrediente`. |
| `cantidad` | Cantidad utilizada; debe ser mayor que cero. |
| `id_unidad` | Unidad de la cantidad; referencia a `UnidadMedida`. |

Las referencias al menú diario se eliminan en cascada; los ingredientes y
unidades usados no se pueden eliminar mientras estén referenciados.

## Producción de cocina

### `SalidaMenuCocina`

Registra la producción resultante de un menú diario.

| Columna | Descripción |
| --- | --- |
| `id_salida` | Clave primaria autoincremental. |
| `id_menu_diario` | Menú diario producido; referencia a `MenuDiario`. |
| `fecha_hora` | Momento de la producción; por defecto, la fecha y hora actuales. |
| `cantidad_producida` | Cantidad total producida; debe ser mayor que cero. |
| `id_unidad` | Unidad de producción; referencia a `UnidadMedida`. |
| `cantidad_porciones` | Porciones resultantes; debe ser mayor que cero. |

Si se elimina el menú diario, sus salidas se eliminan en cascada.

## Reglas de integridad

Además de las claves foráneas, restricciones `UNIQUE` y verificaciones
`CHECK`, el script define triggers para validar las salidas tanto al insertar
como al actualizar:

1. La unidad de producción debe coincidir con `MenuDiario.id_unidad_porcion`.
2. `cantidad_porciones` debe coincidir con
   `cantidad_producida / MenuDiario.porcion`, con una tolerancia de `0.0001`.

Si una regla no se cumple, SQLite cancela la operación con un error.

## Índices

El script crea índices para facilitar consultas habituales por:

- fecha del menú diario (`idx_menu_diario_fecha`);
- fecha y hora de producción (`idx_salida_fecha`);
- nombre del ingrediente (`idx_ingrediente_nombre`);
- menú base de una planificación diaria (`idx_menu_diario_base`);
- ingrediente incluido en un menú base (`idx_menu_base_ingrediente`);
- ingrediente registrado en una preparación diaria (`idx_menu_diario_ingrediente`).

Las claves primarias y restricciones de unicidad también cuentan con los
índices que SQLite necesita para aplicarlas.

## Flujo de uso

1. Registrar unidades, cocineros e ingredientes.
2. Crear menús base con su porción y unidad.
3. Asociar responsables e ingredientes mediante las tablas de relación.
4. Planificar el menú base para una fecha en `MenuDiario`.
5. Registrar en `MenuDiario_Ingrediente` las cantidades y unidades realmente
   usadas.
6. Registrar el resultado producido en `SalidaMenuCocina`.

Así se separa la composición estable del menú (qué ingredientes incluye) de
los consumos efectivos de cada preparación (qué cantidad se utilizó ese día).

## Aplicar cambios a una base existente

El archivo SQL define tablas con `CREATE TABLE IF NOT EXISTS`; ejecutarlo sobre
una base ya creada no modifica automáticamente las tablas existentes. Si la
base contiene el esquema anterior, se necesita una migración explícita para
agregar `codigo` a `Ingrediente`, `MenuBase` y `Cocinero` y para reconstruir
`MenuBase_Ingrediente` sin `cantidad` ni `id_unidad`. Los registros existentes
deben recibir códigos únicos antes de aplicar las restricciones `NOT NULL` y
`UNIQUE`.

## Acceso a datos desde Python

El acceso está separado en dos capas:

- [`src/modelo/consultas.py`](../src/modelo/consultas.py) centraliza la
  generación de las consultas SQL CRUD y de activación de claves foráneas.
  Las consultas específicas nuevas también deben definirse allí.
- [`src/modelo/daos.py`](../src/modelo/daos.py) contiene `SQLiteDAO`, la clase
  abstracta genérica que gestiona conexiones, ejecución y transacciones, y un
  DAO concreto por tabla. Los DAO obtienen sus sentencias SQL desde
  `consultas.py`; cada uno declara el nombre de la tabla, el DTO que representa
  sus filas y sus claves primarias.
- [`src/modelo/services.py`](../src/modelo/services.py) contiene servicios
  como `Cocinero`, `Ingrediente` y `MenuBase`. Cada clase hereda de su DTO y
  delega `insertar`, `actualizar`, `eliminar`, `obtener` y `listar` en el DAO
  correspondiente. Los controladores de la interfaz consumen estos servicios;
  las vistas no deben acceder a ellos directamente.

Los DAO aceptan una ruta de base de datos opcional. Por defecto se usa
`data/recetario.db` en la raíz del proyecto. La conexión activa las claves
foráneas en cada operación, parametriza los valores SQL, confirma los cambios
correctos y revierte una operación si ocurre una excepción. El archivo SQL de
esquema se debe ejecutar en esa base antes de usar los servicios; los DAO no
crean ni migran tablas automáticamente.

Ejemplo de uso después de inicializar la base desde `scripts/database.sql`:

```python
from src.modelo.daos import CocineroDAO
from src.modelo.services import Cocinero

dao = CocineroDAO("data/recetario.db")
cocinero = Cocinero(codigo="COC-003", nombre="Luis", dao=dao)
cocinero.insertar()

cocinero = Cocinero.obtener(cocinero.id_cocinero, dao=dao)
if cocinero is not None:
    cocinero.nombre = "Luis Pérez"
    cocinero.actualizar()
```

`obtener` devuelve `None` si la clave no existe. `actualizar` y `eliminar`
devuelven `True` si SQLite encontró y modificó o eliminó la fila; de lo
contrario devuelven `False`. En las tablas de relación con clave compuesta,
`obtener` recibe cada componente de la clave en el orden declarado por el DAO.

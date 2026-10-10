# Recetario Caprichos

Aplicación de escritorio para gestionar un comedor: permite mantener
catálogos, definir menús base, planificar preparaciones diarias, registrar
ingredientes utilizados y controlar la producción de cocina. También genera
reportes exportables a CSV y PDF.

La interfaz está desarrollada con Tkinter y los datos se almacenan localmente
en SQLite.

La navegación usa un set opcional de emojis. Se muestran cuando Tk detecta una
fuente emoji conocida para el sistema (Segoe UI Emoji en Windows, Noto/Twemoji/
JoyPixels en Linux o Apple Color Emoji en macOS); de lo contrario, la interfaz
presenta las etiquetas de texto sin iconos.

## Funcionalidades

- Gestión de unidades, cocineros e ingredientes.
- Creación de menús base y asociación de responsables e ingredientes.
- Planificación diaria y registro de ingredientes utilizados.
- Registro, consulta, edición y eliminación de producción.
- Reportes de menús, planificación y producción con exportación a CSV/PDF.
- Resumen de actividad del día y sección «Acerca de».

## Requisitos

- Python 3.14.
- [Pipenv](https://pipenv.pypa.io/).
- Tkinter instalado y disponible en la distribución de Python.
- Para imprimir directamente, un servicio de impresión configurado y el
  comando `lp` o `lpr`.

En algunas distribuciones Linux, Tkinter se instala por separado (por ejemplo,
con el paquete `python3-tk`).

## Instalación y ejecución

Desde la raíz del proyecto:

```bash
pipenv install --dev
pipenv run python src/main.py
```

Al iniciar por primera vez, la aplicación crea `data/recetario.db` y carga el
esquema y los datos de ejemplo definidos en [`scripts/database.sql`](scripts/database.sql).
La base local se conserva entre ejecuciones.

## Pruebas

```bash
pipenv run pytest -q
```

Las pruebas de controlador utilizan bases de datos temporales.

## Estructura

```text
src/
  controlador/  Coordinación de acciones y reglas del flujo
  modelo/       Entidades, servicios, DAO y consultas SQLite
  vista/        Interfaz gráfica Tkinter
  main.py       Punto de entrada
scripts/
  database.sql  Esquema y datos iniciales
tests/          Pruebas automatizadas
docs/           Documentación funcional y del modelo de datos
```

Más detalles sobre la interfaz y el esquema están en [`docs/`](docs/).

## Autor

German Cespedes

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo
[`LICENSE`](LICENSE).

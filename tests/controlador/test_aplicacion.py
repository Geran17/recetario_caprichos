import csv
from datetime import date, datetime
from pathlib import Path

from src.controlador.aplicacion import (
    ControladorAplicacion,
    ControladorCatalogos,
    ControladorMenusBase,
    ControladorPlanificacion,
    ControladorProduccion,
    ControladorReportes,
    inicializar_base_si_no_existe,
)
from src.modelo.daos import (
    CocineroDAO,
    MenuBaseDAO,
    MenuDiarioDAO,
    SalidaMenuCocinaDAO,
)
from src.modelo.services import Cocinero, MenuBase, MenuDiario, SalidaMenuCocina
from src.vista.planificacion_diaria import PlanificacionDiariaVista


RUTA_ESQUEMA = Path(__file__).resolve().parents[2] / "scripts" / "database.sql"


class VistaPrueba:
    def __init__(self):
        self.registros = []
        self.opciones = {}
        self.planificaciones = []
        self.salidas = []
        self.resultados = None
        self.errores = []
        self.mensajes = []
        self.callbacks = {}
        self.resumen_inicio = None
        self.opciones_formulario = {}

    def mostrar_registros(self, registros):
        self.registros = registros

    def mostrar_menus(self, registros):
        self.registros = registros

    def mostrar_planificaciones(self, registros):
        self.planificaciones = registros

    def mostrar_salidas(self, registros):
        self.salidas = registros

    def mostrar_resultados(self, columnas, filas):
        self.resultados = (tuple(columnas), list(filas))

    def mostrar_resumen_inicio(self, resumen):
        self.resumen_inicio = resumen

    def establecer_opciones(self, **opciones):
        self.opciones = opciones

    def establecer_opciones_formulario(self, campo, opciones):
        self.opciones_formulario[campo] = list(opciones)

    def establecer_callbacks(self, **callbacks):
        self.callbacks = callbacks

    def finalizar_edicion(self):
        pass

    def cerrar_formulario(self):
        pass

    def mostrar_error(self, mensaje):
        self.errores.append(mensaje)

    def mostrar_mensaje(self, mensaje):
        self.mensajes.append(mensaje)


def crear_base(ruta_db: Path) -> None:
    inicializar_base_si_no_existe(ruta_db, RUTA_ESQUEMA)


class AplicacionPrueba:
    def establecer_callback_navegacion(self, callback):
        self.callback_navegacion = callback


def test_inicializador_crea_esquema_una_sola_vez(tmp_path):
    ruta_db = tmp_path / "db" / "recetario.db"
    crear_base(ruta_db)
    Cocinero(nombre="Otra", codigo="COC-999", dao=CocineroDAO(ruta_db)).insertar()

    inicializar_base_si_no_existe(ruta_db, RUTA_ESQUEMA)

    assert len(Cocinero.listar(dao=CocineroDAO(ruta_db))) == 3


def test_panel_principal_resume_menus_planificacion_y_produccion_de_hoy(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    hoy = date.today()
    diario = MenuDiario(
        id_menu_base=1,
        fecha=hoy,
        porcion=200,
        id_unidad_porcion=1,
        dao=MenuDiarioDAO(ruta_db),
    )
    diario.insertar()
    SalidaMenuCocina(
        id_menu_diario=diario.id_menu_diario,
        fecha_hora=datetime.now(),
        cantidad_producida=4000,
        id_unidad=1,
        cantidad_porciones=20,
        dao=SalidaMenuCocinaDAO(ruta_db),
    ).insertar()
    controlador = ControladorAplicacion(AplicacionPrueba(), ruta_db)
    vista = VistaPrueba()

    controlador.refrescar_inicio(vista)

    assert vista.resumen_inicio is not None
    assert vista.resumen_inicio == {
        "menus": 2,
        "planificaciones": 1,
        "producciones": 1,
    }


def test_controlador_catalogos_cubre_crud(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    controlador = ControladorCatalogos(ruta_db)
    vista = VistaPrueba()

    controlador.conectar("cocineros", vista)
    controlador.crear(
        "cocineros",
        vista,
        {"codigo": "COC-901", "nombre": "Eva", "activo": "1"},
    )
    nuevo = next(item for item in vista.registros if item["codigo"] == "COC-901")
    assert nuevo["nombre"] == "Eva"

    controlador.actualizar(
        "cocineros",
        vista,
        {
            "id_cocinero": str(nuevo["id_cocinero"]),
            "codigo": "COC-901",
            "nombre": "Eva Ruiz",
            "activo": "0",
        },
    )
    actualizado = next(item for item in vista.registros if item["codigo"] == "COC-901")
    assert actualizado["nombre"] == "Eva Ruiz"
    assert actualizado["activo"] == 0

    controlador.eliminar(
        "cocineros",
        vista,
        {
            "id_cocinero": str(actualizado["id_cocinero"]),
            "codigo": "COC-901",
            "nombre": "Eva Ruiz",
            "activo": "0",
        },
    )
    assert all(item["codigo"] != "COC-901" for item in vista.registros)
    assert not vista.errores


def test_formulario_ingrediente_ofrece_nombres_de_unidad_y_guarda_id(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    controlador = ControladorCatalogos(ruta_db)
    vista = VistaPrueba()

    controlador.conectar("ingredientes", vista)

    assert vista.opciones_formulario["id_unidad"][0] == (1, "gramo (g)")
    controlador.crear(
        "ingredientes",
        vista,
        {
            "codigo": "ING-901",
            "nombre": "Harina de prueba",
            "descripcion": "",
            "id_unidad": "gramo (g)",
        },
    )
    ingrediente = next(
        item for item in vista.registros if item["codigo"] == "ING-901"
    )
    assert ingrediente["id_unidad"] == 1
    assert not vista.errores


def test_controlador_menu_guarda_relaciones_y_refresca(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    controlador = ControladorMenusBase(ruta_db)
    vista = VistaPrueba()

    controlador.conectar(vista)
    controlador.crear(
        vista,
        {
            "codigo": "MEN-901",
            "nombre": "Menú de prueba",
            "porcion": "220",
            "id_unidad": "1 — gramo (g)",
            "descripcion": "Ejemplo",
            "responsables": [1],
            "ingredientes": [1, 2],
        },
    )

    menu = next(item for item in vista.registros if item["codigo"] == "MEN-901")
    assert menu["unidad"] == "gramo"
    assert menu["responsables"] == [1]
    assert menu["ingredientes"] == [1, 2]
    assert not vista.errores

    controlador.actualizar(
        vista,
        {
            "id_menu_base": str(menu["id_menu_base"]),
            "codigo": "MEN-901",
            "nombre": "Cambio que debe revertirse",
            "porcion": "220",
            "id_unidad": "1 — gramo (g)",
            "responsables": [999999],
            "ingredientes": [2],
        },
    )
    controlador.refrescar(vista)
    menu_persistido = next(
        item for item in vista.registros if item["codigo"] == "MEN-901"
    )
    assert menu_persistido["nombre"] == "Menú de prueba"
    assert menu_persistido["responsables"] == [1]
    assert menu_persistido["ingredientes"] == [1, 2]
    assert vista.errores

    controlador.actualizar(
        vista,
        {
            "id_menu_base": str(menu["id_menu_base"]),
            "codigo": "MEN-901",
            "nombre": "Menú de prueba",
            "porcion": "220",
            "id_unidad": "1 — gramo (g)",
            "responsables": [1],
            "ingredientes": [2],
        },
    )
    menu_persistido = next(
        item for item in vista.registros if item["codigo"] == "MEN-901"
    )
    assert menu_persistido["ingredientes"] == [2]


def test_controlador_requiere_ingrediente_al_crear_menu(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    controlador = ControladorMenusBase(ruta_db)
    vista = VistaPrueba()
    controlador.conectar(vista)

    controlador.crear(
        vista,
        {
            "codigo": "MEN-SIN-INGREDIENTES",
            "nombre": "Menú incompleto",
            "porcion": "220",
            "id_unidad": "1 — gramo (g)",
            "responsables": [],
            "ingredientes": [],
        },
    )

    assert "al menos un ingrediente" in vista.errores[0]
    assert all(
        menu.codigo != "MEN-SIN-INGREDIENTES"
        for menu in MenuBase.listar(dao=MenuBaseDAO(ruta_db))
    )


def test_controlador_revierte_menu_y_relaciones_si_falla_un_detalle(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    controlador = ControladorMenusBase(ruta_db)
    vista = VistaPrueba()
    controlador.conectar(vista)

    controlador.crear(
        vista,
        {
            "codigo": "MEN-ROLLBACK",
            "nombre": "Menú no persistido",
            "porcion": "220",
            "id_unidad": "1 — gramo (g)",
            "responsables": [999999],
            "ingredientes": [],
        },
    )

    assert vista.errores
    assert all(
        menu.codigo != "MEN-ROLLBACK"
        for menu in MenuBase.listar(dao=MenuBaseDAO(ruta_db))
    )


def test_controladores_planificacion_y_produccion(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    planificador = ControladorPlanificacion(ruta_db)
    vista_plan = VistaPrueba()
    planificador.conectar(vista_plan)
    planificador.guardar(
        vista_plan,
        {
            "id_menu_base": 1,
            "fecha": "2026-11-02",
            "porcion": "999",
            "id_unidad_porcion": 3,
            "ingredientes": [
                {
                    "id_ingrediente": 1,
                    "cantidad": "3000",
                    "id_unidad": 1,
                }
            ],
        },
    )
    assert len(vista_plan.planificaciones) == 1
    assert vista_plan.planificaciones[0]["fecha"] == date(2026, 11, 2)
    menu_base = MenuBase.obtener(1, dao=MenuBaseDAO(ruta_db))
    assert vista_plan.planificaciones[0]["porcion"] == menu_base.porcion
    assert vista_plan.planificaciones[0]["id_unidad_porcion"] == menu_base.id_unidad
    assert not vista_plan.errores

    produccion = ControladorProduccion(ruta_db)
    vista_produccion = VistaPrueba()
    produccion.conectar(vista_produccion)
    produccion.registrar(
        vista_produccion,
        {
            "id_menu_diario": "2",
            "fecha_hora": "2026-11-02 12:00:00",
            "cantidad_producida": "5000",
            "id_unidad": "1",
            "cantidad_porciones": "25",
        },
    )
    assert len(vista_produccion.salidas) == 1
    assert vista_produccion.salidas[0]["menu"] == "Arroz con pollo"
    assert not vista_produccion.errores


def test_planificacion_limita_ingredientes_al_menu_seleccionado():
    ingredientes = [
        {"id_ingrediente": 1, "nombre": "Arroz"},
        {"id_ingrediente": 2, "nombre": "Pollo"},
        {"id_ingrediente": 3, "nombre": "Leche"},
    ]

    resultado = PlanificacionDiariaVista._ingredientes_del_menu(
        {"id_menu_base": 1, "ingredientes": [1, 2]},
        ingredientes,
    )

    assert [item["id_ingrediente"] for item in resultado] == [1, 2]


def test_produccion_convierte_litros_a_porciones_de_mililitros(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    dao_diario = MenuDiarioDAO(ruta_db)
    menu_diario = MenuDiario(
        id_menu_base=2,
        fecha=date(2026, 11, 4),
        porcion=250,
        id_unidad_porcion=2,
        dao=dao_diario,
    )
    menu_diario.insertar()
    controlador = ControladorProduccion(ruta_db)
    vista = VistaPrueba()

    resultado_calculo = controlador.calcular_porciones(
        {
            "id_menu_diario": str(menu_diario.id_menu_diario),
            "cantidad_producida": "6 l",
            "id_unidad": "5",
        }
    )
    assert float(resultado_calculo) == 24
    assert float(
        controlador.calcular_porciones(
            {
                "id_menu_diario": str(menu_diario.id_menu_diario),
                "cantidad_producida": "6000 ml",
                "id_unidad": "2",
            }
        )
    ) == 24

    controlador.registrar(
        vista,
        {
            "id_menu_diario": str(menu_diario.id_menu_diario),
            "fecha_hora": "2026-11-04 12:30:00",
            "cantidad_producida": "6 l",
            "id_unidad": "5",
            "cantidad_porciones": "dato ignorado: se calcula",
        },
    )

    assert not vista.errores
    salida = SalidaMenuCocina.listar(
        dao=SalidaMenuCocinaDAO(ruta_db)
    )[-1]
    assert salida.cantidad_producida == 6000
    assert salida.id_unidad == 2
    assert salida.cantidad_porciones == 24


def test_produccion_actualiza_y_elimina_salidas(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    hoy = date.today()
    diario = MenuDiario(
        id_menu_base=2,
        fecha=hoy,
        porcion=250,
        id_unidad_porcion=2,
        dao=MenuDiarioDAO(ruta_db),
    )
    diario.insertar()
    salida = SalidaMenuCocina(
        id_menu_diario=diario.id_menu_diario,
        fecha_hora=datetime.combine(hoy, datetime.min.time()),
        cantidad_producida=2500,
        id_unidad=2,
        cantidad_porciones=10,
        dao=SalidaMenuCocinaDAO(ruta_db),
    )
    salida.insertar()
    controlador = ControladorProduccion(ruta_db)
    vista = VistaPrueba()
    controlador.conectar(vista)

    assert [registro["id_salida"] for registro in vista.salidas] == [
        salida.id_salida
    ]
    assert vista.salidas[0]["fecha_planificacion"] == hoy.isoformat()

    controlador.actualizar(
        vista,
        {
            "id_salida": str(salida.id_salida),
            "id_menu_diario": str(diario.id_menu_diario),
            "fecha_hora": f"{hoy.isoformat()} 12:30:00",
            "cantidad_producida": "5000 ml",
            "id_unidad": "2",
            "fecha_consulta": hoy.isoformat(),
        },
    )

    actualizado = SalidaMenuCocina.obtener(
        salida.id_salida,
        dao=SalidaMenuCocinaDAO(ruta_db),
    )
    assert actualizado is not None
    assert actualizado.cantidad_producida == 5000
    assert actualizado.cantidad_porciones == 20
    assert not vista.errores

    controlador.eliminar(
        vista,
        {
            "id_salida": str(salida.id_salida),
            "fecha_planificacion": hoy.isoformat(),
        },
    )

    assert SalidaMenuCocina.obtener(
        salida.id_salida,
        dao=SalidaMenuCocinaDAO(ruta_db),
    ) is None
    assert vista.salidas == []
    assert not vista.errores


def test_produccion_rechaza_conversion_entre_dimensiones(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    dao_diario = MenuDiarioDAO(ruta_db)
    menu_diario = MenuDiario(
        id_menu_base=2,
        fecha=date(2026, 11, 4),
        porcion=250,
        id_unidad_porcion=2,
        dao=dao_diario,
    )
    menu_diario.insertar()
    controlador = ControladorProduccion(ruta_db)
    vista = VistaPrueba()

    controlador.registrar(
        vista,
        {
            "id_menu_diario": str(menu_diario.id_menu_diario),
            "fecha_hora": "2026-11-04 12:30:00",
            "cantidad_producida": "2",
            "id_unidad": "4",
            "cantidad_porciones": "",
        },
    )

    assert vista.errores
    assert "dimensiones distintas" in vista.errores[0]


def test_controlador_revierte_planificacion_si_falla_un_ingrediente(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    controlador = ControladorPlanificacion(ruta_db)
    vista = VistaPrueba()

    controlador.guardar(
        vista,
        {
            "id_menu_base": 1,
            "fecha": "2026-11-03",
            "porcion": "200",
            "id_unidad_porcion": 1,
            "ingredientes": [
                {
                    "id_ingrediente": 999999,
                    "cantidad": "3000",
                    "id_unidad": 1,
                }
            ],
        },
    )

    assert vista.errores
    assert all(
        item.fecha != date(2026, 11, 3)
        for item in MenuDiario.listar(dao=MenuDiarioDAO(ruta_db))
    )


def test_controlador_reportes_consulta_y_exporta_csv_pdf(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    controlador = ControladorReportes(ruta_db)
    vista = VistaPrueba()
    filtros = {
        "tipo_reporte": "Planificación e ingredientes utilizados",
        "fecha_desde": "2026-10-07",
        "fecha_hasta": "2026-10-07",
    }

    controlador.generar(vista, filtros)
    assert vista.resultados is not None
    assert vista.resultados[1]

    ruta_csv = tmp_path / "planificacion.csv"
    controlador.exportar(vista, {**filtros, "formato": "csv", "ruta": str(ruta_csv)})
    with ruta_csv.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.reader(archivo))
    assert filas[0][0] == "Fecha"
    assert len(filas) > 1

    ruta_pdf = tmp_path / "planificacion.pdf"
    controlador.exportar(vista, {**filtros, "formato": "pdf", "ruta": str(ruta_pdf)})
    assert ruta_pdf.read_bytes().startswith(b"%PDF")
    assert not vista.errores


def test_registro_produccion_invalido_informa_error(tmp_path):
    ruta_db = tmp_path / "recetario.db"
    crear_base(ruta_db)
    controlador = ControladorProduccion(ruta_db)
    vista = VistaPrueba()

    controlador.registrar(
        vista,
        {
            "id_menu_diario": "1",
            "fecha_hora": "2026-10-07 12:00:00",
            "cantidad_producida": "5000",
            "id_unidad": "2",
            "cantidad_porciones": "25",
        },
    )

    assert vista.errores
    assert "unidad" in vista.errores[0].lower()

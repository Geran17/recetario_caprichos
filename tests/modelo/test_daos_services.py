import sqlite3
from datetime import date, datetime
from pathlib import Path

from src.modelo.daos import (
    CocineroDAO,
    IngredienteDAO,
    MenuBaseDAO,
    MenuBaseIngredienteDAO,
    MenuBaseResponsableDAO,
    MenuDiarioDAO,
    MenuDiarioIngredienteDAO,
    SalidaMenuCocinaDAO,
    UnidadMedidaDAO,
)
from src.modelo.dtos import (
    CocineroDTO,
    MenuBaseIngredienteDTO,
    MenuDiarioDTO,
    SalidaMenuCocinaDTO,
)
from src.modelo.services import Cocinero


DATABASE_SQL = Path(__file__).resolve().parents[2] / "scripts" / "database.sql"


def crear_base_temporal(tmp_path: Path) -> Path:
    ruta_db = tmp_path / "recetario.db"
    conexion = sqlite3.connect(ruta_db)
    try:
        conexion.executescript(DATABASE_SQL.read_text(encoding="utf-8"))
    finally:
        conexion.close()
    return ruta_db


def test_daos_instancian_filas_de_todas_las_tablas(tmp_path):
    ruta_db = crear_base_temporal(tmp_path)
    daos = [
        (UnidadMedidaDAO(ruta_db), (1,), "nombre", "gramo"),
        (CocineroDAO(ruta_db), (1,), "codigo", "COC-001"),
        (IngredienteDAO(ruta_db), (1,), "codigo", "ING-001"),
        (MenuBaseDAO(ruta_db), (1,), "codigo", "MEN-001"),
        (MenuBaseResponsableDAO(ruta_db), (1, 1), "id_cocinero", 1),
        (MenuBaseIngredienteDAO(ruta_db), (1, 1), "id_ingrediente", 1),
        (MenuDiarioDAO(ruta_db), (1,), "fecha", date(2026, 10, 7)),
        (
            MenuDiarioIngredienteDAO(ruta_db),
            (1, 1),
            "cantidad",
            3000.0,
        ),
        (
            SalidaMenuCocinaDAO(ruta_db),
            (1,),
            "fecha_hora",
            datetime(2026, 10, 7, 12, 0),
        ),
    ]

    for dao, clave, atributo, esperado in daos:
        entidad = dao.obtener_por_id(*clave)
        assert entidad is not None
        assert getattr(entidad, atributo) == esperado


def test_cocinero_service_delega_crud_en_dao(tmp_path):
    dao = CocineroDAO(crear_base_temporal(tmp_path))
    cocinero = Cocinero(codigo="COC-003", nombre="Luis", dao=dao)

    clave = cocinero.insertar()
    assert isinstance(clave, int)
    assert cocinero.id_cocinero == clave

    encontrado = Cocinero.obtener(clave, dao=dao)
    assert encontrado is not None
    assert encontrado == Cocinero(
        id_cocinero=clave,
        codigo="COC-003",
        nombre="Luis",
        dao=dao,
    )
    assert isinstance(encontrado, CocineroDTO)

    encontrado.nombre = "Luis Pérez"
    assert encontrado.actualizar()
    assert Cocinero.obtener(clave, dao=dao).nombre == "Luis Pérez"
    assert any(persona.id_cocinero == clave for persona in Cocinero.listar(dao))
    assert encontrado.eliminar()
    assert Cocinero.obtener(clave, dao=dao) is None


def test_instanciar_hidrata_tipos_fecha_y_entidades(tmp_path):
    ruta_db = crear_base_temporal(tmp_path)
    menu_diario = MenuDiarioDAO(ruta_db).obtener_por_id(1)
    salida = SalidaMenuCocinaDAO(ruta_db).obtener_por_id(1)

    assert isinstance(menu_diario, MenuDiarioDTO)
    assert isinstance(menu_diario.fecha, date)
    assert isinstance(salida, SalidaMenuCocinaDTO)
    assert isinstance(salida.fecha_hora, datetime)


def test_daos_insertan_entidades_con_claves_simples_y_compuestas(tmp_path):
    ruta_db = crear_base_temporal(tmp_path)
    relacion_dao = MenuBaseIngredienteDAO(ruta_db)
    relacion = (1, 6)

    assert relacion_dao.insertar(
        MenuBaseIngredienteDTO(
            id_menu_base=relacion[0],
            id_ingrediente=relacion[1],
        )
    ) == relacion
    assert relacion_dao.obtener_por_id(*relacion) is not None
    assert relacion_dao.eliminar(*relacion)

    menu_dao = MenuDiarioDAO(ruta_db)
    menu = MenuDiarioDTO(
        id_menu_base=2,
        fecha=date(2026, 10, 8),
        porcion=250.0,
        id_unidad_porcion=2,
    )
    id_menu = menu_dao.insertar(menu)

    assert isinstance(id_menu, int)
    assert menu_dao.obtener_por_id(id_menu).fecha == date(2026, 10, 8)

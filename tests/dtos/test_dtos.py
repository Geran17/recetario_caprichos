from dataclasses import asdict
from datetime import date, datetime

import pytest

from src.modelo.dtos import (
    CocineroDTO,
    IngredienteDTO,
    MenuBaseDTO,
    MenuBaseIngredienteDTO,
    MenuBaseResponsableDTO,
    MenuDiarioDTO,
    MenuDiarioIngredienteDTO,
    SalidaMenuCocinaDTO,
    UnidadMedidaDTO,
)


@pytest.mark.parametrize(
    ("dto", "expected"),
    [
        (
            UnidadMedidaDTO(
                id_unidad=1,
                nombre="Kilogramo",
                abreviatura="kg",
            ),
            {"id_unidad": 1, "nombre": "Kilogramo", "abreviatura": "kg"},
        ),
        (
            CocineroDTO(id_cocinero=2, codigo="COC-002", nombre="Ana", activo=0),
            {"id_cocinero": 2, "codigo": "COC-002", "nombre": "Ana", "activo": 0},
        ),
        (
            IngredienteDTO(
                id_ingrediente=3,
                codigo="ING-003",
                nombre="Harina",
                descripcion="Harina de trigo",
                id_unidad=1,
            ),
            {
                "id_ingrediente": 3,
                "codigo": "ING-003",
                "nombre": "Harina",
                "descripcion": "Harina de trigo",
                "id_unidad": 1,
            },
        ),
        (
            MenuBaseDTO(
                id_menu_base=4,
                codigo="MEN-004",
                nombre="Pan",
                porcion=2.5,
                id_unidad=1,
                descripcion="Pan casero",
            ),
            {
                "id_menu_base": 4,
                "codigo": "MEN-004",
                "nombre": "Pan",
                "porcion": 2.5,
                "id_unidad": 1,
                "descripcion": "Pan casero",
            },
        ),
        (
            MenuBaseResponsableDTO(id_menu_base=4, id_cocinero=2),
            {"id_menu_base": 4, "id_cocinero": 2},
        ),
        (
            MenuBaseIngredienteDTO(
                id_menu_base=4,
                id_ingrediente=3,
            ),
            {
                "id_menu_base": 4,
                "id_ingrediente": 3,
            },
        ),
        (
            MenuDiarioDTO(
                id_menu_diario=5,
                id_menu_base=4,
                fecha=date(2026, 10, 7),
                porcion=3,
                id_unidad_porcion=1,
            ),
            {
                "id_menu_diario": 5,
                "id_menu_base": 4,
                "fecha": date(2026, 10, 7),
                "porcion": 3,
                "id_unidad_porcion": 1,
            },
        ),
        (
            MenuDiarioIngredienteDTO(
                id_menu_diario=5,
                id_ingrediente=3,
                cantidad=1.25,
                id_unidad=1,
            ),
            {
                "id_menu_diario": 5,
                "id_ingrediente": 3,
                "cantidad": 1.25,
                "id_unidad": 1,
            },
        ),
        (
            SalidaMenuCocinaDTO(
                id_salida=6,
                id_menu_diario=5,
                fecha_hora=datetime(2026, 10, 7, 12, 30),
                cantidad_producida=12.5,
                id_unidad=1,
                cantidad_porciones=5,
            ),
            {
                "id_salida": 6,
                "id_menu_diario": 5,
                "fecha_hora": datetime(2026, 10, 7, 12, 30),
                "cantidad_producida": 12.5,
                "id_unidad": 1,
                "cantidad_porciones": 5,
            },
        ),
    ],
)
def test_dto_stores_provided_values(dto, expected):
    assert asdict(dto) == expected


@pytest.mark.parametrize(
    ("dto", "expected"),
    [
        (
            UnidadMedidaDTO(nombre="Litro", abreviatura="L"),
            {"id_unidad": None, "nombre": "Litro", "abreviatura": "L"},
        ),
        (
            CocineroDTO(codigo="COC-001", nombre="Luis"),
            {"id_cocinero": None, "codigo": "COC-001", "nombre": "Luis", "activo": 1},
        ),
        (
            IngredienteDTO(codigo="ING-001", nombre="Agua", id_unidad=2),
            {
                "id_ingrediente": None,
                "codigo": "ING-001",
                "nombre": "Agua",
                "descripcion": None,
                "id_unidad": 2,
            },
        ),
        (
            MenuBaseDTO(codigo="MEN-001", nombre="Sopa", porcion=1, id_unidad=2),
            {
                "id_menu_base": None,
                "codigo": "MEN-001",
                "nombre": "Sopa",
                "porcion": 1,
                "id_unidad": 2,
                "descripcion": None,
            },
        ),
        (
            MenuDiarioDTO(
                id_menu_base=4,
                fecha=date(2026, 10, 7),
                porcion=1,
                id_unidad_porcion=2,
            ),
            {
                "id_menu_diario": None,
                "id_menu_base": 4,
                "fecha": date(2026, 10, 7),
                "porcion": 1,
                "id_unidad_porcion": 2,
            },
        ),
        (
            SalidaMenuCocinaDTO(
                id_menu_diario=5,
                cantidad_producida=3,
                id_unidad=2,
                cantidad_porciones=3,
            ),
            {
                "id_salida": None,
                "id_menu_diario": 5,
                "fecha_hora": None,
                "cantidad_producida": 3,
                "id_unidad": 2,
                "cantidad_porciones": 3,
            },
        ),
    ],
)
def test_dto_defaults(dto, expected):
    assert asdict(dto) == expected


@pytest.mark.parametrize(
    "dto_type",
    [
        UnidadMedidaDTO,
        CocineroDTO,
        IngredienteDTO,
        MenuBaseDTO,
        MenuBaseResponsableDTO,
        MenuBaseIngredienteDTO,
        MenuDiarioDTO,
        MenuDiarioIngredienteDTO,
        SalidaMenuCocinaDTO,
    ],
)
def test_dtos_require_keyword_arguments(dto_type):
    with pytest.raises(TypeError):
        dto_type(1, 2)

"""DTOs correspondientes a las tablas de la base de datos."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(kw_only=True)
class UnidadMedidaDTO:
    id_unidad: int | None = None
    nombre: str
    abreviatura: str


@dataclass(kw_only=True)
class CocineroDTO:
    id_cocinero: int | None = None
    codigo: str
    nombre: str
    activo: int = 1


@dataclass(kw_only=True)
class IngredienteDTO:
    id_ingrediente: int | None = None
    codigo: str
    nombre: str
    descripcion: str | None = None
    id_unidad: int


@dataclass(kw_only=True)
class MenuBaseDTO:
    id_menu_base: int | None = None
    codigo: str
    nombre: str
    porcion: float
    id_unidad: int
    descripcion: str | None = None


@dataclass(kw_only=True)
class MenuBaseResponsableDTO:
    id_menu_base: int
    id_cocinero: int


@dataclass(kw_only=True)
class MenuBaseIngredienteDTO:
    id_menu_base: int
    id_ingrediente: int


@dataclass(kw_only=True)
class MenuDiarioDTO:
    id_menu_diario: int | None = None
    id_menu_base: int
    fecha: date
    porcion: float
    id_unidad_porcion: int


@dataclass(kw_only=True)
class MenuDiarioIngredienteDTO:
    id_menu_diario: int
    id_ingrediente: int
    cantidad: float
    id_unidad: int


@dataclass(kw_only=True)
class SalidaMenuCocinaDTO:
    id_salida: int | None = None
    id_menu_diario: int
    fecha_hora: datetime | None = None
    cantidad_producida: float
    id_unidad: int
    cantidad_porciones: float

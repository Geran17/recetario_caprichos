"""Servicios de aplicación para las entidades del recetario."""

from dataclasses import InitVar, asdict, dataclass
import sqlite3
from typing import Any, ClassVar

from src.modelo.daos import (
    CocineroDAO,
    IngredienteDAO,
    MenuBaseDAO,
    MenuBaseIngredienteDAO,
    MenuBaseResponsableDAO,
    MenuDiarioDAO,
    MenuDiarioIngredienteDAO,
    SalidaMenuCocinaDAO,
    SQLiteDAO,
    UnidadMedidaDAO,
)
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


class ServicioCRUD:
    """Delegación común de las operaciones de una entidad a su DAO."""

    _tipo_dao: ClassVar[type[SQLiteDAO]]
    _dao: SQLiteDAO

    def __post_init__(self, dao: SQLiteDAO | None = None) -> None:
        self._dao = dao if dao is not None else self._tipo_dao()

    def insertar(self) -> int | tuple[Any, ...]:
        clave = self._dao.insertar(self)
        self._actualizar_clave_generada(clave)
        return clave

    def insertar_en(self, conexion: sqlite3.Connection) -> int | tuple[Any, ...]:
        clave = self._dao.insertar_en(conexion, self)
        self._actualizar_clave_generada(clave)
        return clave

    def _actualizar_clave_generada(self, clave: int | tuple[Any, ...]) -> None:
        if len(self._dao.claves_primarias) == 1:
            nombre_clave = self._dao.claves_primarias[0]
            if getattr(self, nombre_clave) is None:
                setattr(self, nombre_clave, clave)

    def actualizar(self) -> bool:
        return self._dao.actualizar(self)

    def actualizar_en(self, conexion: sqlite3.Connection) -> bool:
        return self._dao.actualizar_en(conexion, self)

    def eliminar(self) -> bool:
        claves = tuple(
            getattr(self, nombre) for nombre in self._dao.claves_primarias
        )
        return self._dao.eliminar(*claves)

    def eliminar_en(self, conexion: sqlite3.Connection) -> bool:
        claves = tuple(
            getattr(self, nombre) for nombre in self._dao.claves_primarias
        )
        return self._dao.eliminar_en(conexion, *claves)

    @classmethod
    def obtener(cls, *claves: Any, dao: SQLiteDAO | None = None):
        repositorio = dao if dao is not None else cls._tipo_dao()
        entidad = repositorio.obtener_por_id(*claves)
        return cls(**asdict(entidad), dao=repositorio) if entidad is not None else None

    @classmethod
    def listar(cls, dao: SQLiteDAO | None = None) -> list:
        repositorio = dao if dao is not None else cls._tipo_dao()
        return [
            cls(**asdict(entidad), dao=repositorio)
            for entidad in repositorio.listar()
        ]


@dataclass(kw_only=True)
class UnidadMedida(ServicioCRUD, UnidadMedidaDTO):
    dao: InitVar[UnidadMedidaDAO | None] = None
    _tipo_dao: ClassVar[type[UnidadMedidaDAO]] = UnidadMedidaDAO


@dataclass(kw_only=True)
class Cocinero(ServicioCRUD, CocineroDTO):
    dao: InitVar[CocineroDAO | None] = None
    _tipo_dao: ClassVar[type[CocineroDAO]] = CocineroDAO


@dataclass(kw_only=True)
class Ingrediente(ServicioCRUD, IngredienteDTO):
    dao: InitVar[IngredienteDAO | None] = None
    _tipo_dao: ClassVar[type[IngredienteDAO]] = IngredienteDAO


@dataclass(kw_only=True)
class MenuBase(ServicioCRUD, MenuBaseDTO):
    dao: InitVar[MenuBaseDAO | None] = None
    _tipo_dao: ClassVar[type[MenuBaseDAO]] = MenuBaseDAO


@dataclass(kw_only=True)
class MenuBaseResponsable(ServicioCRUD, MenuBaseResponsableDTO):
    dao: InitVar[MenuBaseResponsableDAO | None] = None
    _tipo_dao: ClassVar[type[MenuBaseResponsableDAO]] = MenuBaseResponsableDAO


@dataclass(kw_only=True)
class MenuBaseIngrediente(ServicioCRUD, MenuBaseIngredienteDTO):
    dao: InitVar[MenuBaseIngredienteDAO | None] = None
    _tipo_dao: ClassVar[type[MenuBaseIngredienteDAO]] = MenuBaseIngredienteDAO


@dataclass(kw_only=True)
class MenuDiario(ServicioCRUD, MenuDiarioDTO):
    dao: InitVar[MenuDiarioDAO | None] = None
    _tipo_dao: ClassVar[type[MenuDiarioDAO]] = MenuDiarioDAO


@dataclass(kw_only=True)
class MenuDiarioIngrediente(ServicioCRUD, MenuDiarioIngredienteDTO):
    dao: InitVar[MenuDiarioIngredienteDAO | None] = None
    _tipo_dao: ClassVar[type[MenuDiarioIngredienteDAO]] = MenuDiarioIngredienteDAO


@dataclass(kw_only=True)
class SalidaMenuCocina(ServicioCRUD, SalidaMenuCocinaDTO):
    dao: InitVar[SalidaMenuCocinaDAO | None] = None
    _tipo_dao: ClassVar[type[SalidaMenuCocinaDAO]] = SalidaMenuCocinaDAO

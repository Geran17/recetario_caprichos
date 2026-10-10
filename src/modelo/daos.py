"""Acceso a datos SQLite mediante objetos DAO concretos por tabla."""

import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import fields
from datetime import date, datetime
from pathlib import Path
from typing import Any, ClassVar, Generic, Iterator, Mapping, TypeVar

from src.modelo.consultas import Consultas
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

DTO = TypeVar("DTO")
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "recetario.db"


class SQLiteDAO(ABC, Generic[DTO]):
    """Implementa operaciones CRUD comunes para una tabla SQLite."""

    tabla: ClassVar[str]
    tipo_dto: ClassVar[type]
    claves_primarias: ClassVar[tuple[str, ...]]

    def __init__(self, ruta_db: str | Path = DEFAULT_DATABASE_PATH) -> None:
        self.ruta_db = Path(ruta_db)
        self.columnas = tuple(field.name for field in fields(self.tipo_dto))

        if not set(self.claves_primarias).issubset(self.columnas):
            raise ValueError(f"Claves primarias inválidas para la tabla {self.tabla}")

    @contextmanager
    def _conexion(self) -> Iterator[sqlite3.Connection]:
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)
        conexion = sqlite3.connect(self.ruta_db)
        conexion.row_factory = sqlite3.Row
        conexion.execute(Consultas.activar_claves_foraneas())
        try:
            yield conexion
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def _serializar(valor: Any) -> Any:
        if isinstance(valor, (date, datetime)):
            return valor.isoformat(sep=" ") if isinstance(valor, datetime) else valor.isoformat()
        return valor

    def _columnas_insertables(self, entidad: DTO) -> dict[str, Any]:
        if not isinstance(entidad, self.tipo_dto):
            raise TypeError(f"{self.tabla} requiere una instancia de {self.tipo_dto.__name__}")

        valores = {
            field.name: getattr(entidad, field.name)
            for field in fields(self.tipo_dto)
        }
        if len(self.claves_primarias) == 1:
            clave = self.claves_primarias[0]
            if valores[clave] is None:
                del valores[clave]
        return {columna: self._serializar(valor) for columna, valor in valores.items()}

    @contextmanager
    def transaccion(self) -> Iterator[sqlite3.Connection]:
        """Expone una transacción para operaciones coordinadas entre varios DAO."""
        with self._conexion() as conexion:
            yield conexion

    @abstractmethod
    def insertar(self, entidad: DTO) -> int | tuple[Any, ...]:
        """Inserta una entidad y devuelve su clave primaria."""
        with self.transaccion() as conexion:
            return self.insertar_en(conexion, entidad)

    def insertar_en(
        self,
        conexion: sqlite3.Connection,
        entidad: DTO,
    ) -> int | tuple[Any, ...]:
        """Inserta una entidad usando la transacción proporcionada."""
        valores = self._columnas_insertables(entidad)
        consulta = Consultas.insertar(self.tabla, tuple(valores))
        cursor = conexion.execute(consulta, tuple(valores.values()))
        if len(self.claves_primarias) == 1:
            clave = self.claves_primarias[0]
            valor_clave = getattr(entidad, clave)
            if valor_clave is None:
                return int(cursor.lastrowid)
            return valor_clave
        return tuple(getattr(entidad, clave) for clave in self.claves_primarias)

    @abstractmethod
    def instanciar(self, fila: Mapping[str, Any]) -> DTO:
        """Construye el DTO de la tabla a partir de una fila SQLite."""
        return self.tipo_dto(**dict(fila))

    def obtener_por_id(self, *valores_clave: Any) -> DTO | None:
        """Obtiene una fila por su clave primaria, simple o compuesta."""
        if len(valores_clave) != len(self.claves_primarias):
            raise ValueError(
                f"{self.tabla} requiere {len(self.claves_primarias)} valor(es) "
                "para su clave primaria"
            )

        consulta = Consultas.obtener_por_clave(
            self.tabla,
            self.columnas,
            self.claves_primarias,
        )
        with self._conexion() as conexion:
            fila = conexion.execute(consulta, valores_clave).fetchone()
        return self.instanciar(fila) if fila is not None else None

    def listar(self) -> list[DTO]:
        """Devuelve todas las filas ordenadas por clave primaria."""
        consulta = Consultas.listar(
            self.tabla,
            self.columnas,
            self.claves_primarias,
        )
        with self._conexion() as conexion:
            filas = conexion.execute(consulta).fetchall()
        return [self.instanciar(fila) for fila in filas]

    def actualizar(self, entidad: DTO) -> bool:
        """Actualiza las columnas no clave y señala si encontró la fila."""
        with self.transaccion() as conexion:
            return self.actualizar_en(conexion, entidad)

    def actualizar_en(self, conexion: sqlite3.Connection, entidad: DTO) -> bool:
        """Actualiza una entidad usando la transacción proporcionada."""
        valores = self._columnas_insertables(entidad)
        if any(valores.get(clave) is None for clave in self.claves_primarias):
            raise ValueError(f"Se requieren las claves primarias para actualizar {self.tabla}")

        columnas_actualizables = [
            columna for columna in valores if columna not in self.claves_primarias
        ]
        if not columnas_actualizables:
            raise ValueError(f"La tabla {self.tabla} no tiene columnas actualizables")

        parametros = [valores[columna] for columna in columnas_actualizables]
        parametros.extend(valores[clave] for clave in self.claves_primarias)
        consulta = Consultas.actualizar(
            self.tabla,
            tuple(columnas_actualizables),
            self.claves_primarias,
        )

        cursor = conexion.execute(consulta, parametros)
        return cursor.rowcount > 0

    def eliminar(self, *valores_clave: Any) -> bool:
        """Elimina una fila por su clave primaria."""
        with self.transaccion() as conexion:
            return self.eliminar_en(conexion, *valores_clave)

    def eliminar_en(
        self,
        conexion: sqlite3.Connection,
        *valores_clave: Any,
    ) -> bool:
        """Elimina una fila usando la transacción proporcionada."""
        if len(valores_clave) != len(self.claves_primarias):
            raise ValueError(
                f"{self.tabla} requiere {len(self.claves_primarias)} valor(es) "
                "para su clave primaria"
            )

        consulta = Consultas.eliminar(self.tabla, self.claves_primarias)
        cursor = conexion.execute(consulta, valores_clave)
        return cursor.rowcount > 0

    def ejecutar_consulta(
        self,
        consulta: str,
        parametros: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        """Ejecuta un SELECT proporcionado por Consultas y devuelve filas."""
        with self._conexion() as conexion:
            filas = conexion.execute(consulta, parametros).fetchall()
        return [dict(fila) for fila in filas]


class _DAOEntidad(SQLiteDAO[DTO]):
    def insertar(self, entidad: DTO) -> int | tuple[Any, ...]:
        return super().insertar(entidad)

    def instanciar(self, fila: Mapping[str, Any]) -> DTO:
        return super().instanciar(fila)


class UnidadMedidaDAO(_DAOEntidad[UnidadMedidaDTO]):
    tabla = "UnidadMedida"
    tipo_dto = UnidadMedidaDTO
    claves_primarias = ("id_unidad",)


class CocineroDAO(_DAOEntidad[CocineroDTO]):
    tabla = "Cocinero"
    tipo_dto = CocineroDTO
    claves_primarias = ("id_cocinero",)


class IngredienteDAO(_DAOEntidad[IngredienteDTO]):
    tabla = "Ingrediente"
    tipo_dto = IngredienteDTO
    claves_primarias = ("id_ingrediente",)


class MenuBaseDAO(_DAOEntidad[MenuBaseDTO]):
    tabla = "MenuBase"
    tipo_dto = MenuBaseDTO
    claves_primarias = ("id_menu_base",)


class MenuBaseResponsableDAO(_DAOEntidad[MenuBaseResponsableDTO]):
    tabla = "MenuBase_Responsable"
    tipo_dto = MenuBaseResponsableDTO
    claves_primarias = ("id_menu_base", "id_cocinero")


class MenuBaseIngredienteDAO(_DAOEntidad[MenuBaseIngredienteDTO]):
    tabla = "MenuBase_Ingrediente"
    tipo_dto = MenuBaseIngredienteDTO
    claves_primarias = ("id_menu_base", "id_ingrediente")


class MenuDiarioDAO(_DAOEntidad[MenuDiarioDTO]):
    tabla = "MenuDiario"
    tipo_dto = MenuDiarioDTO
    claves_primarias = ("id_menu_diario",)

    def instanciar(self, fila: Mapping[str, Any]) -> MenuDiarioDTO:
        valores = dict(fila)
        if isinstance(valores["fecha"], str):
            valores["fecha"] = date.fromisoformat(valores["fecha"])
        return self.tipo_dto(**valores)


class MenuDiarioIngredienteDAO(_DAOEntidad[MenuDiarioIngredienteDTO]):
    tabla = "MenuDiario_Ingrediente"
    tipo_dto = MenuDiarioIngredienteDTO
    claves_primarias = ("id_menu_diario", "id_ingrediente")


class SalidaMenuCocinaDAO(_DAOEntidad[SalidaMenuCocinaDTO]):
    tabla = "SalidaMenuCocina"
    tipo_dto = SalidaMenuCocinaDTO
    claves_primarias = ("id_salida",)

    def instanciar(self, fila: Mapping[str, Any]) -> SalidaMenuCocinaDTO:
        valores = dict(fila)
        if isinstance(valores["fecha_hora"], str):
            valores["fecha_hora"] = datetime.fromisoformat(valores["fecha_hora"])
        return self.tipo_dto(**valores)
"""Conversión de cantidades entre unidades de medida compatibles."""

import re
import unicodedata
from collections.abc import Mapping
from math import isfinite
from typing import Any


_UNIDADES: dict[str, tuple[str, float]] = {}


def _registrar(dimension: str, factor: float, *alias: str) -> None:
    for elemento in alias:
        _UNIDADES[_normalizar(elemento)] = (dimension, factor)


def _normalizar(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto.strip().lower())
    return "".join(caracter for caracter in normalizado if not unicodedata.combining(caracter))


_registrar("masa", 0.000001, "µg", "μg", "mcg", "microgramo", "microgramos")
_registrar("masa", 0.001, "mg", "miligramo", "miligramos")
_registrar("masa", 1, "g", "gr", "gramo", "gramos")
_registrar("masa", 1000, "kg", "kilogramo", "kilogramos")
_registrar("masa", 1_000_000, "t", "ton", "tonelada", "toneladas")
_registrar("masa", 453.59237, "lb", "lbs", "libra", "libras")
_registrar("masa", 28.349523125, "oz", "onza", "onzas")
_registrar("volumen", 1, "ml", "mililitro", "mililitros", "cc", "cm3", "cm³")
_registrar("volumen", 10, "cl", "centilitro", "centilitros")
_registrar("volumen", 100, "dl", "decilitro", "decilitros")
_registrar("volumen", 1000, "l", "lt", "litro", "litros")
_registrar("volumen", 1_000_000, "m3", "m³", "metro cubico", "metros cubicos")
_registrar("conteo", 1, "u", "unidad", "unidades", "pieza", "piezas")
_registrar("conteo", 12, "docena", "docenas")

_PATRON_CANTIDAD = re.compile(
    r"^\s*([+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?)\s*(.*?)\s*$"
)


def analizar_cantidad(valor: Any) -> tuple[float, str | None]:
    """Lee una cantidad numérica opcionalmente seguida por su unidad."""
    coincidencia = _PATRON_CANTIDAD.fullmatch(str(valor))
    if coincidencia is None:
        raise ValueError("Ingresa una cantidad numérica válida, por ejemplo 6000 o 6 ml.")
    numero, unidad = coincidencia.groups()
    try:
        cantidad = float(numero.replace(",", "."))
    except ValueError as error:
        raise ValueError("La cantidad producida no es un número válido.") from error
    if not isfinite(cantidad) or cantidad <= 0:
        raise ValueError("La cantidad producida debe ser mayor que cero.")
    return cantidad, unidad or None


def resolver_unidad(unidades: list[Mapping[str, Any]], seleccion: Any) -> Mapping[str, Any]:
    """Resuelve un identificador o etiqueta de unidad del catálogo."""
    texto = str(seleccion).strip()
    for unidad in unidades:
        if texto == str(unidad.get("id_unidad", "")):
            return unidad
        etiqueta = (
            f"{unidad.get('id_unidad', '')} — {unidad.get('nombre', '')} "
            f"({unidad.get('abreviatura', '')})"
        )
        if texto == etiqueta:
            return unidad
    raise ValueError(f"La unidad seleccionada no existe: {texto}")


def resolver_unidad_por_sufijo(
    unidades: list[Mapping[str, Any]],
    sufijo: str,
) -> Mapping[str, Any]:
    """Resuelve una unidad escrita junto a la cantidad."""
    clave = _normalizar(sufijo)
    coincidencias = [
        unidad
        for unidad in unidades
        if clave
        in {
            _normalizar(str(unidad.get("nombre", ""))),
            _normalizar(str(unidad.get("abreviatura", ""))),
        }
    ]
    if len(coincidencias) == 1:
        return coincidencias[0]
    if clave in _UNIDADES:
        return {"id_unidad": None, "nombre": sufijo, "abreviatura": sufijo}
    raise ValueError(f"No se reconoce la unidad indicada en la cantidad: {sufijo}")


def convertir_cantidad(
    cantidad: float,
    unidad_origen: Mapping[str, Any],
    unidad_destino: Mapping[str, Any],
) -> float:
    """Convierte entre unidades métricas compatibles, sin asumir densidades."""
    if str(unidad_origen.get("id_unidad")) == str(unidad_destino.get("id_unidad")):
        return cantidad
    dimension_origen = _dimension(unidad_origen)
    dimension_destino = _dimension(unidad_destino)
    if dimension_origen is None or dimension_destino is None:
        raise ValueError("No se puede convertir una unidad desconocida.")
    if dimension_origen[0] != dimension_destino[0]:
        raise ValueError(
            "No se pueden convertir unidades de dimensiones distintas "
            f"({unidad_origen.get('nombre')} y {unidad_destino.get('nombre')})."
        )
    resultado = cantidad * dimension_origen[1] / dimension_destino[1]
    if not isfinite(resultado):
        raise ValueError("La cantidad convertida está fuera del rango permitido.")
    return resultado


def _dimension(unidad: Mapping[str, Any]) -> tuple[str, float] | None:
    for valor in (unidad.get("abreviatura"), unidad.get("nombre")):
        if valor:
            coincidencia = _UNIDADES.get(_normalizar(str(valor)))
            if coincidencia is not None:
                return coincidencia
    return None

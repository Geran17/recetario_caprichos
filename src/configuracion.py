"""Rutas de recursos y datos de la aplicación."""

import os
import sys
from collections.abc import Mapping
from pathlib import Path


def ruta_base_proyecto() -> Path:
    return Path(__file__).resolve().parents[1]


def ruta_base_datos(
    *,
    empaquetada: bool | None = None,
    sistema: str | None = None,
    entorno: Mapping[str, str] | None = None,
) -> Path:
    """Devuelve una ruta escribible, persistente y específica del usuario."""
    es_empaquetada = (
        getattr(sys, "frozen", False) if empaquetada is None else empaquetada
    )
    if not es_empaquetada:
        return ruta_base_proyecto() / "data" / "recetario.db"

    variables = os.environ if entorno is None else entorno
    nombre_sistema = os.name if sistema is None else sistema
    if nombre_sistema == "nt":
        directorio_usuario = variables.get("LOCALAPPDATA")
        base_datos = (
            Path(directorio_usuario)
            if directorio_usuario
            else Path.home() / "AppData" / "Local"
        )
    else:
        directorio_usuario = variables.get("XDG_DATA_HOME")
        base_datos = (
            Path(directorio_usuario)
            if directorio_usuario
            else Path.home() / ".local" / "share"
        )
    return base_datos / "RecetarioCaprichos" / "data" / "recetario.db"


def ruta_esquema() -> Path:
    """Localiza el SQL en fuentes o dentro del bundle de PyInstaller."""
    directorio_bundle = getattr(sys, "_MEIPASS", None)
    raiz = Path(directorio_bundle) if directorio_bundle else ruta_base_proyecto()
    return raiz / "scripts" / "database.sql"

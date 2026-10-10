"""Iconos emoji opcionales para la interfaz Tkinter."""

import platform
from collections.abc import Iterable


ICONOS = {
    "inicio": "🏠",
    "unidades": "📏",
    "cocineros": "🍳",
    "ingredientes": "🥕",
    "menus": "🍽️",
    "planificacion": "📅",
    "produccion": "🥘",
    "reportes": "📊",
    "acerca_de": "ℹ️",
}

FUENTES_EMOJI_POR_SISTEMA = {
    "Windows": {"segoe ui emoji", "segoe ui symbol"},
    "Linux": {
        "noto color emoji",
        "noto emoji",
        "twemoji mozilla",
        "joypixels",
    },
    "Darwin": {"apple color emoji"},
}


def sistema_tiene_fuente_emoji(
    familias: Iterable[str],
    sistema: str | None = None,
) -> bool:
    """Indica si Tk reporta una fuente emoji conocida para el sistema."""
    nombre_sistema = sistema or platform.system()
    fuentes_compatibles = FUENTES_EMOJI_POR_SISTEMA.get(nombre_sistema, set())
    familias_disponibles = {familia.casefold() for familia in familias}
    return bool(fuentes_compatibles & familias_disponibles)


def texto_con_icono(
    clave: str,
    etiqueta: str,
    *,
    emojis_habilitados: bool,
) -> str:
    """Combina una etiqueta con su emoji, o devuelve solo texto como alternativa."""
    if not emojis_habilitados:
        return etiqueta
    return f"{ICONOS[clave]}  {etiqueta}"

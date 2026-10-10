from src.vista.iconos import sistema_tiene_fuente_emoji, texto_con_icono


def test_detecta_fuente_emoji_conocida_por_sistema():
    assert sistema_tiene_fuente_emoji(["Arial", "Segoe UI Emoji"], "Windows")
    assert sistema_tiene_fuente_emoji(["DejaVu Sans", "Noto Color Emoji"], "Linux")
    assert sistema_tiene_fuente_emoji(["Apple Color Emoji"], "Darwin")


def test_no_habilita_emojis_sin_fuente_compatible():
    assert not sistema_tiene_fuente_emoji(["Arial"], "Windows")
    assert not sistema_tiene_fuente_emoji(["Noto Color Emoji"], "Windows")
    assert not sistema_tiene_fuente_emoji(["Segoe UI Emoji"], "Linux")
    assert not sistema_tiene_fuente_emoji(["Noto Color Emoji"], "FreeBSD")


def test_etiqueta_oculta_icono_si_emojis_no_estan_habilitados():
    assert texto_con_icono(
        "menus",
        "Menús base",
        emojis_habilitados=False,
    ) == "Menús base"


def test_etiqueta_incluye_icono_registrado_si_estan_habilitados():
    assert texto_con_icono(
        "menus",
        "Menús base",
        emojis_habilitados=True,
    ) == "🍽️  Menús base"

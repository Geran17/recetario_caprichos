from pathlib import Path

from src.configuracion import ruta_base_datos, ruta_esquema


def test_ruta_base_datos_de_desarrollo_usa_directorio_del_proyecto():
    assert ruta_base_datos(empaquetada=False) == (
        Path(__file__).resolve().parents[1] / "data" / "recetario.db"
    )


def test_ruta_base_datos_empaquetada_usa_local_app_data_de_windows():
    assert ruta_base_datos(
        empaquetada=True,
        sistema="nt",
        entorno={"LOCALAPPDATA": "C:/Users/demo/AppData/Local"},
    ) == Path(
        "C:/Users/demo/AppData/Local/RecetarioCaprichos/data/recetario.db"
    )


def test_ruta_base_datos_empaquetada_tiene_fallback_sin_local_app_data():
    ruta = ruta_base_datos(
        empaquetada=True,
        sistema="nt",
        entorno={},
    )

    assert ruta == (
        Path.home()
        / "AppData"
        / "Local"
        / "RecetarioCaprichos"
        / "data"
        / "recetario.db"
    )


def test_ruta_base_datos_empaquetada_usa_xdg_en_linux():
    assert ruta_base_datos(
        empaquetada=True,
        sistema="posix",
        entorno={"XDG_DATA_HOME": "/home/demo/.local/share"},
    ) == Path(
        "/home/demo/.local/share/RecetarioCaprichos/data/recetario.db"
    )


def test_ruta_esquema_usa_bundle_de_pyinstaller(monkeypatch, tmp_path):
    monkeypatch.setattr("src.configuracion.sys._MEIPASS", str(tmp_path), raising=False)

    assert ruta_esquema() == tmp_path / "scripts" / "database.sql"

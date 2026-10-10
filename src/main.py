"""Punto de entrada de la interfaz del recetario."""

import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.controlador.aplicacion import crear_controlador
from src.vista.aplicacion import Aplicacion


def main() -> None:
    aplicacion = Aplicacion()
    crear_controlador(aplicacion)
    aplicacion.mainloop()


if __name__ == "__main__":
    main()
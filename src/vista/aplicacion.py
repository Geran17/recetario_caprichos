"""Ventana y navegación puramente visual de la aplicación."""

import tkinter as tk
from collections.abc import Mapping
from tkinter import font as tkfont
from tkinter import ttk

from .catalogos import CocinerosVista, IngredientesVista, UnidadesVista
from .iconos import sistema_tiene_fuente_emoji, texto_con_icono
from .menus_base import MenusBaseVista
from .planificacion_diaria import PlanificacionDiariaVista
from .produccion import ProduccionVista
from .reportes import ReportesVista


class Aplicacion(tk.Tk):
    """Maqueta principal del recetario, sin acceso al modelo ni a la base."""

    COLOR_FONDO = "#F5F4EF"
    COLOR_PANEL = "#FFFFFF"
    COLOR_PRIMARIO = "#234B3B"
    COLOR_PRIMARIO_OSCURO = "#18372B"
    COLOR_ACENTO = "#D89550"
    COLOR_TEXTO = "#26332C"
    COLOR_SECUNDARIO = "#778179"
    COLOR_BORDE = "#E5E8E2"

    SECCIONES = (
        ("inicio", "Inicio"),
        ("unidades", "Unidades"),
        ("cocineros", "Cocineros"),
        ("ingredientes", "Ingredientes"),
        ("menus", "Menús base"),
        ("planificacion", "Planificación diaria"),
        ("produccion", "Producción"),
        ("reportes", "Reportes"),
        ("acerca_de", "Acerca de"),
    )
    AUTOR = "German Cespedes"

    DESCRIPCIONES = {
        "unidades": "Administra las unidades de medida utilizadas por el comedor.",
        "cocineros": "Consulta y administra las personas responsables de cocina.",
        "ingredientes": "Organiza los ingredientes y sus unidades base.",
        "menus": "Define los menús, sus porciones, responsables e ingredientes.",
        "planificacion": "Consulta la planificación y preparación de cada día.",
        "produccion": "Registra y consulta la producción de cocina.",
        "reportes": "Consulta y exporta información del recetario.",
    }

    def __init__(self) -> None:
        super().__init__()
        self.title("Recetario | Gestión de comedor")
        self.geometry("1180x760")
        self.minsize(900, 620)
        self.configure(bg=self.COLOR_FONDO)

        self._configurar_estilos()
        self._emojis_habilitados = sistema_tiene_fuente_emoji(
            tkfont.families(self)
        )
        self._botones_navegacion: dict[str, tk.Button] = {}
        self._paginas: dict[str, tk.Frame] = {}
        self._vistas_seccion: dict[str, tk.Frame] = {}
        self._callback_navegacion = None
        self._pagina_actual = "inicio"
        self._crear_estructura()
        self.mostrar_seccion("inicio")

    def _configurar_estilos(self) -> None:
        estilos = ttk.Style(self)
        if "clam" in estilos.theme_names():
            estilos.theme_use("clam")
        estilos.configure(
            "App.TFrame",
            background=self.COLOR_FONDO,
        )
        estilos.configure(
            "Panel.TFrame",
            background=self.COLOR_PANEL,
        )
        estilos.configure(
            "Titulo.TLabel",
            background=self.COLOR_FONDO,
            foreground=self.COLOR_TEXTO,
            font=("TkDefaultFont", 22, "bold"),
        )
        estilos.configure(
            "Subtitulo.TLabel",
            background=self.COLOR_FONDO,
            foreground=self.COLOR_SECUNDARIO,
            font=("TkDefaultFont", 10),
        )
        estilos.configure(
            "Tarjeta.TLabel",
            background=self.COLOR_PANEL,
            foreground=self.COLOR_TEXTO,
            font=("TkDefaultFont", 11, "bold"),
        )
        estilos.configure(
            "TextoPanel.TLabel",
            background=self.COLOR_PANEL,
            foreground=self.COLOR_SECUNDARIO,
            font=("TkDefaultFont", 10),
        )
        estilos.configure(
            "App.Treeview",
            rowheight=32,
            font=("TkDefaultFont", 9),
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground=self.COLOR_TEXTO,
            borderwidth=0,
        )
        estilos.configure(
            "App.Treeview.Heading",
            background="#E8F0EB",
            foreground=self.COLOR_PRIMARIO,
            font=("TkDefaultFont", 9, "bold"),
            borderwidth=0,
            relief="flat",
            padding=(10, 8),
        )
        estilos.map(
            "App.Treeview",
            background=[("selected", "#E3ECE6"), ("active", "#D7E8DE")],
            foreground=[("selected", self.COLOR_TEXTO), ("active", self.COLOR_TEXTO)],
        )
        estilos.configure(
            "TEntry",
            padding=(10, 8),
            fieldbackground=self.COLOR_PANEL,
            foreground=self.COLOR_TEXTO,
            bordercolor=self.COLOR_BORDE,
            lightcolor=self.COLOR_BORDE,
            darkcolor=self.COLOR_BORDE,
            relief="flat",
        )
        estilos.map(
            "TEntry",
            fieldbackground=[("disabled", "#F0F2EF")],
            foreground=[("disabled", self.COLOR_SECUNDARIO)],
            bordercolor=[("focus", self.COLOR_PRIMARIO)],
            lightcolor=[("focus", self.COLOR_PRIMARIO)],
            darkcolor=[("focus", self.COLOR_PRIMARIO)],
        )
        estilos.configure(
            "TCombobox",
            padding=(10, 7),
            fieldbackground=self.COLOR_PANEL,
            foreground=self.COLOR_TEXTO,
            background=self.COLOR_PANEL,
            bordercolor=self.COLOR_BORDE,
            lightcolor=self.COLOR_BORDE,
            darkcolor=self.COLOR_BORDE,
            arrowcolor=self.COLOR_PRIMARIO,
            relief="flat",
        )
        estilos.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", self.COLOR_PANEL),
                ("disabled", "#F0F2EF"),
            ],
            foreground=[
                ("disabled", self.COLOR_SECUNDARIO),
                ("readonly", self.COLOR_TEXTO),
            ],
            bordercolor=[("focus", self.COLOR_PRIMARIO)],
            lightcolor=[("focus", self.COLOR_PRIMARIO)],
            darkcolor=[("focus", self.COLOR_PRIMARIO)],
            arrowcolor=[("disabled", self.COLOR_SECUNDARIO)],
        )

    def _crear_estructura(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._crear_barra_lateral()

        self.contenido = ttk.Frame(self, style="App.TFrame", padding=(32, 26))
        self.contenido.grid(row=0, column=1, sticky="nsew")
        self.contenido.columnconfigure(0, weight=1)
        self.contenido.rowconfigure(1, weight=1)

        self.encabezado = ttk.Frame(self.contenido, style="App.TFrame")
        self.encabezado.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        self.encabezado.columnconfigure(0, weight=1)

        self.titulo = ttk.Label(
            self.encabezado,
            text="",
            style="Titulo.TLabel",
        )
        self.titulo.grid(row=0, column=0, sticky="w")

        self.subtitulo = ttk.Label(
            self.encabezado,
            text="",
            style="Subtitulo.TLabel",
        )
        self.subtitulo.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.panel = ttk.Frame(self.contenido, style="App.TFrame")
        self.panel.grid(row=1, column=0, sticky="nsew")
        self.panel.columnconfigure(0, weight=1)
        self.panel.rowconfigure(0, weight=1)

    def _crear_barra_lateral(self) -> None:
        lateral = tk.Frame(self, bg=self.COLOR_PRIMARIO, width=244)
        lateral.grid(row=0, column=0, sticky="ns")
        lateral.grid_propagate(False)
        lateral.columnconfigure(0, weight=1)
        lateral.rowconfigure(len(self.SECCIONES) + 2, weight=1)

        marca = tk.Frame(lateral, bg=self.COLOR_PRIMARIO)
        marca.grid(row=0, column=0, sticky="ew", padx=22, pady=(27, 34))
        tk.Label(
            marca,
            text="RECETARIO",
            bg=self.COLOR_PRIMARIO,
            fg="#FFFFFF",
            font=("TkDefaultFont", 17, "bold"),
        ).pack(anchor="w")
        tk.Label(
            marca,
            text="GESTIÓN DE COMEDOR",
            bg=self.COLOR_PRIMARIO,
            fg="#C9D9CE",
            font=("TkDefaultFont", 8, "bold"),
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            lateral,
            text="MENÚ PRINCIPAL",
            bg=self.COLOR_PRIMARIO,
            fg="#AFC3B5",
            font=("TkDefaultFont", 8, "bold"),
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 10))

        for indice, (clave, etiqueta) in enumerate(self.SECCIONES, start=2):
            boton = tk.Button(
                lateral,
                text=(
                    "  "
                    + texto_con_icono(
                        clave,
                        etiqueta,
                        emojis_habilitados=self._emojis_habilitados,
                    )
                ),
                anchor="w",
                relief="flat",
                borderwidth=0,
                padx=14,
                pady=11,
                bg=self.COLOR_PRIMARIO,
                fg="#E9F0EB",
                activebackground=self.COLOR_PRIMARIO_OSCURO,
                activeforeground="#FFFFFF",
                font=("TkDefaultFont", 10),
                cursor="hand2",
                command=lambda seccion=clave: self.mostrar_seccion(seccion),
            )
            boton.grid(row=indice, column=0, sticky="ew", padx=12, pady=2)
            self._botones_navegacion[clave] = boton

        pie = tk.Frame(lateral, bg=self.COLOR_PRIMARIO)
        pie.grid(
            row=len(self.SECCIONES) + 3,
            column=0,
            sticky="sew",
            padx=22,
            pady=20,
        )
        tk.Frame(pie, bg="#52715F", height=1).pack(fill="x", pady=(0, 12))
        tk.Label(
            pie,
            text="Aplicación local",
            bg=self.COLOR_PRIMARIO,
            fg="#C9D9CE",
            font=("TkDefaultFont", 9),
        ).pack(anchor="w")

    def mostrar_seccion(self, seccion: str) -> None:
        """Muestra el contenido visual de una sección."""
        if seccion not in dict(self.SECCIONES):
            raise ValueError(f"Sección desconocida: {seccion}")

        self._pagina_actual = seccion
        if seccion != "inicio":
            self.encabezado.grid_remove()
        else:
            self.encabezado.grid()

        for clave, boton in self._botones_navegacion.items():
            seleccionado = clave == seccion
            boton.configure(
                bg=self.COLOR_PRIMARIO_OSCURO if seleccionado else self.COLOR_PRIMARIO,
                fg="#FFFFFF" if seleccionado else "#E9F0EB",
                font=("TkDefaultFont", 10, "bold" if seleccionado else "normal"),
            )

        if seccion not in self._paginas:
            self._paginas[seccion] = self._crear_pagina(seccion)

        for pagina in self._paginas.values():
            pagina.grid_remove()
        self._paginas[seccion].grid(row=0, column=0, sticky="nsew")
        if self._callback_navegacion is not None:
            self._callback_navegacion(seccion)

    def _crear_pagina(self, seccion: str) -> tk.Frame:
        vistas = {
            "unidades": UnidadesVista,
            "cocineros": CocinerosVista,
            "ingredientes": IngredientesVista,
            "menus": MenusBaseVista,
            "planificacion": PlanificacionDiariaVista,
            "produccion": ProduccionVista,
            "reportes": ReportesVista,
        }
        if seccion in vistas:
            vista = vistas[seccion](
                self.panel,
                color_fondo=self.COLOR_FONDO,
                color_panel=self.COLOR_PANEL,
                color_primario=self.COLOR_PRIMARIO,
                color_texto=self.COLOR_TEXTO,
                color_secundario=self.COLOR_SECUNDARIO,
                color_borde=self.COLOR_BORDE,
            )
            self._vistas_seccion[seccion] = vista
            return vista

        if seccion == "inicio":
            pagina = self._crear_pagina_inicio()
            self._vistas_seccion[seccion] = self
            return pagina

        if seccion == "acerca_de":
            pagina = self._crear_pagina_acerca_de()
            self._vistas_seccion[seccion] = pagina
            return pagina

        etiqueta = dict(self.SECCIONES)[seccion]
        return self._crear_pagina_vacia(etiqueta)

    def _crear_pagina_acerca_de(self) -> tk.Frame:
        pagina = ttk.Frame(self.panel, style="App.TFrame", padding=24)
        pagina.columnconfigure(0, weight=1)
        pagina.rowconfigure(0, weight=1)

        tarjeta = tk.Frame(
            pagina,
            bg=self.COLOR_PANEL,
            highlightbackground=self.COLOR_BORDE,
            highlightthickness=1,
            padx=40,
            pady=36,
        )
        tarjeta.grid(row=0, column=0, sticky="nsew")

        contenido = tk.Frame(tarjeta, bg=self.COLOR_PANEL)
        contenido.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(
            contenido,
            text="RECETARIO",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_PRIMARIO,
            font=("TkDefaultFont", 22, "bold"),
        ).pack()
        tk.Label(
            contenido,
            text="Gestión de comedor",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_SECUNDARIO,
            font=("TkDefaultFont", 11),
        ).pack(pady=(5, 26))
        tk.Frame(contenido, bg=self.COLOR_BORDE, height=1, width=280).pack()
        tk.Label(
            contenido,
            text="Autor del sistema",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_SECUNDARIO,
            font=("TkDefaultFont", 9),
        ).pack(pady=(22, 5))
        tk.Label(
            contenido,
            text=self.AUTOR,
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXTO,
            font=("TkDefaultFont", 14, "bold"),
        ).pack()
        return pagina

    def _crear_pagina_inicio(self) -> tk.Frame:
        pagina = ttk.Frame(self.panel, style="App.TFrame")
        pagina.columnconfigure(0, weight=1)
        self.titulo.configure(text="Panel principal")
        self.subtitulo.configure(
            text="Menús registrados, planificación y producción del día."
        )

        contenedor = ttk.Frame(pagina, style="App.TFrame")
        contenedor.grid(row=0, column=0, sticky="nsew")
        pagina.rowconfigure(0, weight=1)
        for columna in range(3):
            contenedor.columnconfigure(columna, weight=1, uniform="tarjetas")

        tarjetas = (
            ("menus", "MENÚS BASE", "Recetas y porciones"),
            ("planificaciones", "PLANIFICACIÓN", "Preparaciones por fecha"),
            ("producciones", "PRODUCCIÓN", "Registro de cocina"),
        )
        self._indicadores_inicio = {}
        for columna, (clave, titulo, detalle) in enumerate(tarjetas):
            tarjeta = tk.Frame(
                contenedor,
                bg=self.COLOR_PANEL,
                highlightbackground=self.COLOR_BORDE,
                highlightthickness=1,
                padx=20,
                pady=18,
            )
            tarjeta.grid(
                row=0,
                column=columna,
                sticky="ew",
                padx=(0 if columna == 0 else 8, 8 if columna < 2 else 0),
            )
            tk.Label(
                tarjeta,
                text=titulo,
                bg=self.COLOR_PANEL,
                fg=self.COLOR_SECUNDARIO,
                font=("TkDefaultFont", 8, "bold"),
            ).pack(anchor="w")
            indicador = tk.Label(
                tarjeta,
                text="0",
                bg=self.COLOR_PANEL,
                fg=self.COLOR_PRIMARIO,
                font=("TkDefaultFont", 24, "bold"),
            )
            indicador.pack(anchor="w", pady=(10, 2))
            tk.Label(
                tarjeta,
                text=detalle,
                bg=self.COLOR_PANEL,
                fg=self.COLOR_SECUNDARIO,
                font=("TkDefaultFont", 9),
            ).pack(anchor="w")
            self._indicadores_inicio[clave] = indicador

        return pagina

    def mostrar_resumen_inicio(
        self,
        resumen: Mapping[str, int],
    ) -> None:
        """Actualiza las tarjetas de totales del panel principal."""
        for clave, indicador in self._indicadores_inicio.items():
            indicador.configure(text=str(resumen.get(clave, 0)))

    def _crear_pagina_vacia(self, seccion: str) -> tk.Frame:
        pagina = ttk.Frame(self.panel, style="App.TFrame")
        pagina.columnconfigure(0, weight=1)
        pagina.rowconfigure(0, weight=1)
        estado = tk.Frame(
            pagina,
            bg=self.COLOR_PANEL,
            highlightbackground=self.COLOR_BORDE,
            highlightthickness=1,
            padx=30,
            pady=36,
        )
        estado.grid(row=0, column=0, sticky="nsew")
        estado.columnconfigure(0, weight=1)
        for fila in range(3):
            estado.rowconfigure(fila, weight=1)

        centro = tk.Frame(estado, bg=self.COLOR_PANEL)
        centro.grid(row=1, column=0)
        tk.Label(
            centro,
            text=seccion,
            bg=self.COLOR_PANEL,
            fg=self.COLOR_PRIMARIO,
            font=("TkDefaultFont", 17, "bold"),
        ).pack(pady=(0, 9))
        tk.Label(
            centro,
            text="Esta sección estará disponible en una próxima etapa.",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_SECUNDARIO,
            font=("TkDefaultFont", 10),
        ).pack()
        return pagina

    def obtener_vista_catalogo(self, seccion: str) -> tk.Frame:
        """Devuelve la vista de catálogo para que el punto de composición la conecte."""
        vistas_catalogo = {"unidades", "cocineros", "ingredientes"}
        if seccion not in vistas_catalogo or seccion not in self._vistas_seccion:
            raise ValueError(f"La vista de catálogo '{seccion}' todavía no fue creada")
        return self._vistas_seccion[seccion]

    def obtener_vista(self, seccion: str) -> tk.Frame:
        """Devuelve la vista de una sección ya visitada, para conectar callbacks."""
        if seccion not in self._vistas_seccion:
            raise ValueError(f"La vista de '{seccion}' todavía no fue creada")
        return self._vistas_seccion[seccion]

    def establecer_callback_navegacion(self, callback) -> None:
        """Registra el callback de navegación para el controlador."""
        self._callback_navegacion = callback
        callback(self._pagina_actual)

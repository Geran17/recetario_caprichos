"""Presentación Tkinter para consulta, impresión y exportación de reportes."""

import tkinter as tk
from collections.abc import Callable, Mapping, Sequence
from tkinter import filedialog, messagebox, ttk
from typing import Any


Registro = Mapping[str, Any]
Filtros = dict[str, str]
Exportacion = dict[str, str]


class ReportesVista(tk.Frame):
    """Filtros y vista previa; delega generación y salida al controlador."""

    TIPOS_REPORTE = (
        "Menús base",
        "Planificación e ingredientes utilizados",
        "Producción de cocina",
    )

    def __init__(
        self,
        master: tk.Misc,
        *,
        color_fondo: str,
        color_panel: str,
        color_primario: str,
        color_texto: str,
        color_secundario: str,
        color_borde: str,
        on_generar: Callable[[Filtros], None] | None = None,
        on_imprimir: Callable[[Filtros], None] | None = None,
        on_exportar: Callable[[Exportacion], None] | None = None,
    ) -> None:
        super().__init__(master, bg=color_fondo)
        self._colores = {
            "fondo": color_fondo,
            "panel": color_panel,
            "primario": color_primario,
            "texto": color_texto,
            "secundario": color_secundario,
            "borde": color_borde,
        }
        self._on_generar = on_generar
        self._on_imprimir = on_imprimir
        self._on_exportar = on_exportar
        self._columnas: tuple[str, ...] = ()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._crear_encabezado()
        self._crear_filtros()
        self._crear_vista_previa()

    def _crear_encabezado(self) -> None:
        c = self._colores
        tk.Label(
            self,
            text="Reportes",
            bg=c["fondo"],
            fg=c["texto"],
            font=("TkDefaultFont", 15, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            self,
            text="Consulta, revisa e imprime o exporta la información del recetario.",
            bg=c["fondo"],
            fg=c["secundario"],
            font=("TkDefaultFont", 9),
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

    def _crear_filtros(self) -> None:
        c = self._colores
        panel = tk.Frame(
            self,
            bg=c["panel"],
            highlightbackground=c["borde"],
            highlightthickness=1,
            padx=18,
            pady=14,
        )
        panel.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        panel.columnconfigure(0, weight=2)
        panel.columnconfigure(1, weight=1)
        panel.columnconfigure(2, weight=1)

        tk.Label(
            panel,
            text="Selecciona el reporte y los filtros",
            bg=c["panel"],
            fg=c["texto"],
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self.tipo_reporte = tk.StringVar(value=self.TIPOS_REPORTE[0])
        self.fecha_desde = tk.StringVar()
        self.fecha_hasta = tk.StringVar()
        self._selector(
            panel,
            1,
            0,
            "Tipo de reporte",
            self.tipo_reporte,
            self.TIPOS_REPORTE,
        )
        self._entrada(panel, 1, 1, "Desde (AAAA-MM-DD)", self.fecha_desde)
        self._entrada(panel, 1, 2, "Hasta (AAAA-MM-DD)", self.fecha_hasta)

        acciones = tk.Frame(panel, bg=c["panel"])
        acciones.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        tk.Button(
            acciones,
            text="Generar vista previa",
            command=self._generar,
            cursor="hand2",
            relief="flat",
            padx=14,
            pady=8,
            bg=c["primario"],
            fg="#FFFFFF",
        ).pack(side="left")
        tk.Button(
            acciones,
            text="Imprimir",
            command=self._imprimir,
            cursor="hand2",
            relief="flat",
            padx=13,
            pady=8,
            bg="#EEF0EC",
            fg=c["texto"],
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            acciones,
            text="Exportar PDF",
            command=lambda: self._exportar("pdf"),
            cursor="hand2",
            relief="flat",
            padx=13,
            pady=8,
            bg="#EEF0EC",
            fg=c["texto"],
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            acciones,
            text="Exportar CSV",
            command=lambda: self._exportar("csv"),
            cursor="hand2",
            relief="flat",
            padx=13,
            pady=8,
            bg="#EEF0EC",
            fg=c["texto"],
        ).pack(side="right")

    def _crear_vista_previa(self) -> None:
        c = self._colores
        panel = tk.Frame(
            self,
            bg=c["panel"],
            highlightbackground=c["borde"],
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        panel.grid(row=3, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)
        barra = tk.Frame(panel, bg=c["panel"])
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        barra.columnconfigure(0, weight=1)
        tk.Label(
            barra,
            text="Vista previa",
            bg=c["panel"],
            fg=c["texto"],
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")
        self._cantidad = tk.Label(
            barra,
            text="Sin datos",
            bg=c["panel"],
            fg=c["secundario"],
            font=("TkDefaultFont", 9),
        )
        self._cantidad.grid(row=0, column=1, sticky="e")
        tabla_contenedor = tk.Frame(panel, bg=c["panel"])
        tabla_contenedor.grid(row=1, column=0, sticky="nsew")
        tabla_contenedor.columnconfigure(0, weight=1)
        tabla_contenedor.rowconfigure(0, weight=1)
        estilo = ttk.Style(self)
        estilo.configure(
            "Reportes.Treeview",
            rowheight=32,
            font=("TkDefaultFont", 9),
            background=c["panel"],
            fieldbackground=c["panel"],
            foreground=c["texto"],
        )
        estilo.configure(
            "Reportes.Treeview.Heading",
            background="#E8F0EB",
            foreground=c["primario"],
            font=("TkDefaultFont", 9, "bold"),
            relief="flat",
            padding=(10, 8),
        )
        estilo.map(
            "Reportes.Treeview",
            background=[("selected", "#E3ECE6"), ("active", "#D7E8DE")],
            foreground=[("selected", c["texto"]), ("active", c["texto"])],
        )
        self._tabla = ttk.Treeview(
            tabla_contenedor,
            show="headings",
            style="Reportes.Treeview",
        )
        self._tabla.tag_configure("fila-par", background="#F8FAF8")
        self._tabla.tag_configure("fila-impar", background="#FFFFFF")
        self._tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y = ttk.Scrollbar(
            tabla_contenedor,
            orient="vertical",
            command=self._tabla.yview,
        )
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x = ttk.Scrollbar(
            tabla_contenedor,
            orient="horizontal",
            command=self._tabla.xview,
        )
        scroll_x.grid(row=1, column=0, sticky="ew")
        self._tabla.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )
        self._estado = tk.Label(
            tabla_contenedor,
            text="Genera una vista previa para mostrar resultados.",
            bg=c["panel"],
            fg=c["secundario"],
        )
        self._estado.place(relx=0.5, rely=0.5, anchor="center")

    def _entrada(
        self,
        master: tk.Misc,
        fila: int,
        columna: int,
        etiqueta: str,
        variable: tk.StringVar,
    ) -> None:
        c = self._colores
        celda = tk.Frame(master, bg=c["panel"])
        celda.grid(row=fila, column=columna, sticky="ew", padx=(0, 12))
        tk.Label(
            celda,
            text=etiqueta,
            bg=c["panel"],
            fg=c["secundario"],
            font=("TkDefaultFont", 8),
        ).pack(anchor="w", pady=(0, 4))
        ttk.Entry(celda, textvariable=variable).pack(fill="x")

    def _selector(
        self,
        master: tk.Misc,
        fila: int,
        columna: int,
        etiqueta: str,
        variable: tk.StringVar,
        opciones: Sequence[str],
    ) -> None:
        c = self._colores
        celda = tk.Frame(master, bg=c["panel"])
        celda.grid(row=fila, column=columna, sticky="ew", padx=(0, 12))
        tk.Label(
            celda,
            text=etiqueta,
            bg=c["panel"],
            fg=c["secundario"],
            font=("TkDefaultFont", 8),
        ).pack(anchor="w", pady=(0, 4))
        ttk.Combobox(
            celda,
            textvariable=variable,
            values=opciones,
            state="readonly",
        ).pack(fill="x")

    def establecer_callbacks(
        self,
        *,
        on_generar: Callable[[Filtros], None] | None = None,
        on_imprimir: Callable[[Filtros], None] | None = None,
        on_exportar: Callable[[Exportacion], None] | None = None,
    ) -> None:
        """Conecta las acciones de la vista a las operaciones del controlador."""
        self._on_generar = on_generar
        self._on_imprimir = on_imprimir
        self._on_exportar = on_exportar

    def obtener_filtros(self) -> Filtros:
        return {
            "tipo_reporte": self.tipo_reporte.get(),
            "fecha_desde": self.fecha_desde.get(),
            "fecha_hasta": self.fecha_hasta.get(),
        }

    def mostrar_resultados(
        self,
        columnas: Sequence[str],
        filas: Sequence[Sequence[Any]],
    ) -> None:
        """Muestra filas preparadas por el controlador en la vista previa."""
        self._columnas = tuple(columnas)
        self._tabla.configure(columns=self._columnas)
        self._tabla["show"] = "headings"
        for columna in self._columnas:
            self._tabla.heading(columna, text=columna.replace("_", " ").title())
            self._tabla.column(columna, width=150, minwidth=90, anchor="w")
        for item in self._tabla.get_children():
            self._tabla.delete(item)
        for indice, fila in enumerate(filas):
            if len(fila) != len(self._columnas):
                raise ValueError("Cada fila debe tener un valor por columna del reporte")
            self._tabla.insert(
                "",
                "end",
                values=tuple(str(valor) for valor in fila),
                tags=("fila-par" if indice % 2 == 0 else "fila-impar",),
            )
        cantidad = len(filas)
        self._cantidad.configure(
            text=f"{cantidad} registro" + ("" if cantidad == 1 else "s")
        )
        if cantidad:
            self._estado.place_forget()
        else:
            self._estado.configure(text="No hay resultados para los filtros seleccionados.")
            self._estado.place(relx=0.5, rely=0.5, anchor="center")

    def mostrar_error(self, mensaje: str) -> None:
        messagebox.showerror("No se pudo generar el reporte", mensaje, parent=self)

    def mostrar_mensaje(self, mensaje: str) -> None:
        messagebox.showinfo("Reportes", mensaje, parent=self)

    def _generar(self) -> None:
        if self._on_generar is None:
            self._pendiente()
            return
        self._on_generar(self.obtener_filtros())

    def _imprimir(self) -> None:
        if self._on_imprimir is None:
            self._pendiente()
            return
        self._on_imprimir(self.obtener_filtros())

    def _exportar(self, formato: str) -> None:
        if self._on_exportar is None:
            self._pendiente()
            return
        extension = ".pdf" if formato == "pdf" else ".csv"
        ruta = filedialog.asksaveasfilename(
            parent=self,
            title=f"Exportar reporte a {formato.upper()}",
            defaultextension=extension,
            filetypes=(
                (f"Archivo {formato.upper()}", f"*{extension}"),
                ("Todos los archivos", "*.*"),
            ),
        )
        if not ruta:
            return
        self._on_exportar(
            {
                **self.obtener_filtros(),
                "formato": formato,
                "ruta": ruta,
            }
        )

    def _pendiente(self) -> None:
        messagebox.showinfo(
            "Acción pendiente",
            "La generación y exportación estarán disponibles al conectar el controlador.",
            parent=self,
        )

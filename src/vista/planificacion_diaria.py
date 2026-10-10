"""Presentación Tkinter de la planificación y preparación diaria."""

import math
import tkinter as tk
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from tkinter import messagebox, ttk
from typing import Any


Registro = Mapping[str, Any]


class PlanificacionDiariaVista(tk.Frame):
    """Formulario y listado diario; deja las operaciones al controlador."""

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
        on_consultar: Callable[[dict[str, str]], None] | None = None,
        on_guardar: Callable[[dict[str, Any]], None] | None = None,
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
        self._on_consultar = on_consultar
        self._on_guardar = on_guardar
        self._menus: list[Registro] = []
        self._unidades: list[Registro] = []
        self._ingredientes: list[Registro] = []
        self._items_borrador: list[dict[str, str]] = []
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._crear_encabezado()
        self._crear_formulario()
        self._crear_listado()

    def _crear_encabezado(self) -> None:
        c = self._colores
        tk.Label(
            self,
            text="Planificación diaria",
            bg=c["fondo"],
            fg=c["texto"],
            font=("TkDefaultFont", 15, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            self,
            text="Planifica un menú y registra los ingredientes realmente utilizados.",
            bg=c["fondo"],
            fg=c["secundario"],
            font=("TkDefaultFont", 9),
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

    def _crear_formulario(self) -> None:
        c = self._colores
        panel = tk.Frame(
            self,
            bg=c["panel"],
            highlightbackground=c["borde"],
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        panel.grid(row=2, column=0, sticky="nsew", pady=(0, 14))
        panel.columnconfigure(0, weight=1)

        tk.Label(
            panel,
            text="Datos de la preparación",
            bg=c["panel"],
            fg=c["texto"],
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        campos = tk.Frame(panel, bg=c["panel"])
        campos.grid(row=1, column=0, sticky="ew")
        for columna in range(4):
            campos.columnconfigure(columna, weight=1)

        self.fecha = tk.StringVar(value=date.today().isoformat())
        self.menu = tk.StringVar()
        self.porcion = tk.StringVar()
        self.unidad_porcion = tk.StringVar()
        self._entrada(
            campos, 0, 0, "Fecha (AAAA-MM-DD)", self.fecha, ancho=18
        )
        self._menu_selector = self._selector(
            campos, 0, 1, "Menú base", self.menu, ()
        )
        self._menu_selector.bind("<<ComboboxSelected>>", self._cambio_menu)
        self._menu_planificacion_actual = self.menu.get()
        self._entrada(
            campos,
            0,
            2,
            "Porción (del menú base)",
            self.porcion,
            readonly=True,
        )
        self._entrada(
            campos,
            0,
            3,
            "Unidad porción (del menú base)",
            self.unidad_porcion,
            readonly=True,
        )

        acciones = tk.Frame(panel, bg=c["panel"])
        acciones.grid(row=2, column=0, sticky="ew", pady=(10, 14))
        tk.Button(
            acciones,
            text="Consultar fecha",
            command=self._consultar,
            cursor="hand2",
            relief="flat",
            padx=13,
            pady=7,
            bg="#EEF0EC",
            fg=c["texto"],
        ).pack(side="left")
        tk.Button(
            acciones,
            text="＋  Agregar ingrediente utilizado",
            command=self._agregar_ingrediente,
            cursor="hand2",
            relief="flat",
            padx=13,
            pady=7,
            bg="#EEF0EC",
            fg=c["texto"],
        ).pack(side="left", padx=8)
        tk.Button(
            acciones,
            text="＋  Agregar ingredientes en tabla",
            command=self._agregar_ingredientes_en_tabla,
            cursor="hand2",
            relief="flat",
            padx=13,
            pady=7,
            bg="#EEF0EC",
            fg=c["texto"],
        ).pack(side="left")
        tk.Button(
            acciones,
            text="Guardar planificación",
            command=self._guardar,
            cursor="hand2",
            relief="flat",
            padx=15,
            pady=7,
            bg=c["primario"],
            fg="#FFFFFF",
        ).pack(side="right")

        tk.Label(
            panel,
            text="Ingredientes utilizados",
            bg=c["panel"],
            fg=c["texto"],
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=3, column=0, sticky="w", pady=(0, 7))

        columnas = ("id_ingrediente", "ingrediente", "cantidad", "unidad")
        estilo = ttk.Style(self)
        estilo.configure(
            "Planificacion.Treeview",
            rowheight=30,
            font=("TkDefaultFont", 9),
            background=c["panel"],
            fieldbackground=c["panel"],
            foreground=c["texto"],
        )
        estilo.configure(
            "Planificacion.Treeview.Heading",
            background="#E8F0EB",
            foreground=c["primario"],
            font=("TkDefaultFont", 9, "bold"),
            relief="flat",
            padding=(10, 8),
        )
        estilo.map(
            "Planificacion.Treeview",
            background=[("selected", "#E3ECE6"), ("active", "#D7E8DE")],
            foreground=[("selected", c["texto"]), ("active", c["texto"])],
        )
        self._tabla_ingredientes = ttk.Treeview(
            panel,
            columns=columnas,
            show="headings",
            height=4,
            style="Planificacion.Treeview",
            selectmode="browse",
        )
        self._tabla_ingredientes.tag_configure("fila-par", background="#F8FAF8")
        self._tabla_ingredientes.tag_configure("fila-impar", background="#FFFFFF")
        for clave, etiqueta, ancho in (
            ("id_ingrediente", "ID", 55),
            ("ingrediente", "Ingrediente", 230),
            ("cantidad", "Cantidad", 120),
            ("unidad", "Unidad", 120),
        ):
            self._tabla_ingredientes.heading(clave, text=etiqueta, anchor="w")
            self._tabla_ingredientes.column(clave, width=ancho, anchor="w")
        self._tabla_ingredientes.grid(row=4, column=0, sticky="ew")
        self._tabla_ingredientes.bind("<Delete>", lambda _event: self._quitar_ingrediente())

        pie = tk.Frame(panel, bg=c["panel"])
        pie.grid(row=5, column=0, sticky="ew", pady=(5, 0))
        tk.Label(
            pie,
            text="Selecciona una fila y presiona Supr para quitarla del borrador.",
            bg=c["panel"],
            fg=c["secundario"],
            font=("TkDefaultFont", 8),
        ).pack(side="left")
        tk.Button(
            pie,
            text="Quitar seleccionado",
            command=self._quitar_ingrediente,
            relief="flat",
            bg=c["panel"],
            fg=c["secundario"],
        ).pack(side="right")

    def _crear_listado(self) -> None:
        c = self._colores
        panel = tk.Frame(
            self,
            bg=c["panel"],
            highlightbackground=c["borde"],
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        panel.grid(row=3, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)
        tk.Label(
            panel,
            text="Planificaciones de la fecha",
            bg=c["panel"],
            fg=c["texto"],
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        estilo = ttk.Style(self)
        estilo.configure(
            "Planificaciones.Treeview",
            rowheight=32,
            font=("TkDefaultFont", 9),
            background=c["panel"],
            fieldbackground=c["panel"],
            foreground=c["texto"],
        )
        estilo.configure(
            "Planificaciones.Treeview.Heading",
            background="#E8F0EB",
            foreground=c["primario"],
            font=("TkDefaultFont", 9, "bold"),
            relief="flat",
            padding=(10, 8),
        )
        estilo.map(
            "Planificaciones.Treeview",
            background=[("selected", "#E3ECE6"), ("active", "#D7E8DE")],
            foreground=[("selected", c["texto"]), ("active", c["texto"])],
        )
        self._tabla_planificaciones = ttk.Treeview(
            panel,
            columns=("id", "menu", "fecha", "porcion", "unidad"),
            show="headings",
            height=5,
            style="Planificaciones.Treeview",
        )
        self._tabla_planificaciones.tag_configure("fila-par", background="#F8FAF8")
        self._tabla_planificaciones.tag_configure("fila-impar", background="#FFFFFF")
        for clave, etiqueta, ancho in (
            ("id", "ID", 55),
            ("menu", "Menú base", 240),
            ("fecha", "Fecha", 120),
            ("porcion", "Porción", 110),
            ("unidad", "Unidad", 110),
        ):
            self._tabla_planificaciones.heading(clave, text=etiqueta, anchor="w")
            self._tabla_planificaciones.column(clave, width=ancho, anchor="w")
        self._tabla_planificaciones.grid(row=1, column=0, sticky="nsew")
        self._estado = tk.Label(
            panel,
            text="Consulta una fecha para mostrar sus planificaciones.",
            bg=c["panel"],
            fg=c["secundario"],
        )
        self._estado.place(relx=0.5, rely=0.67, anchor="center")

    def _entrada(
        self,
        master: tk.Misc,
        fila: int,
        columna: int,
        etiqueta: str,
        variable: tk.StringVar,
        *,
        ancho: int = 16,
        readonly: bool = False,
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
        ttk.Entry(
            celda,
            textvariable=variable,
            width=ancho,
            state="readonly" if readonly else "normal",
        ).pack(fill="x")

    def _selector(
        self,
        master: tk.Misc,
        fila: int,
        columna: int,
        etiqueta: str,
        variable: tk.StringVar,
        opciones: Sequence[str],
    ) -> ttk.Combobox:
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
        selector = ttk.Combobox(
            celda,
            textvariable=variable,
            values=opciones,
            state="readonly" if opciones else "normal",
        )
        selector.pack(fill="x")
        return selector

    def establecer_opciones(
        self,
        *,
        menus: Sequence[Registro] = (),
        unidades: Sequence[Registro] = (),
        ingredientes: Sequence[Registro] = (),
    ) -> None:
        self._menus = list(menus)
        self._unidades = list(unidades)
        self._ingredientes = list(ingredientes)
        self._menu_selector.configure(
            values=[
                f"{item.get('id_menu_base', '')} — {item.get('nombre', '')}"
                for item in self._menus
            ],
            state="readonly" if self._menus else "normal",
        )
        self._actualizar_datos_menu()

    def establecer_callbacks(
        self,
        *,
        on_consultar: Callable[[dict[str, str]], None] | None = None,
        on_guardar: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self._on_consultar = on_consultar
        self._on_guardar = on_guardar

    def _consultar(self) -> None:
        if self._on_consultar is None:
            self._pendiente()
            return
        self._on_consultar({"fecha": self.fecha.get()})

    def _agregar_ingrediente(self) -> None:
        ingredientes_menu = self._ingredientes_disponibles()
        if not ingredientes_menu:
            return

        dialogo = tk.Toplevel(self)
        dialogo.title("Agregar ingrediente utilizado")
        dialogo.transient(self.winfo_toplevel())
        dialogo.resizable(False, False)
        dialogo.columnconfigure(1, weight=1)
        dialogo.protocol("WM_DELETE_WINDOW", dialogo.destroy)
        c = self._colores
        tk.Label(
            dialogo,
            text="Ingrediente",
            bg=c["panel"],
            fg=c["texto"],
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 6))
        opciones_ingredientes = [
            f"{item.get('id_ingrediente', '')} — {item.get('nombre', '')}"
            for item in ingredientes_menu
        ]
        ingrediente = tk.StringVar(value=opciones_ingredientes[0])
        selector_ingrediente = ttk.Combobox(
            dialogo,
            textvariable=ingrediente,
            values=opciones_ingredientes,
            state="readonly",
            width=32,
        )
        selector_ingrediente.grid(
            row=0, column=1, padx=(0, 18), pady=(18, 6)
        )
        cantidad = tk.StringVar()
        self._dialogo_campo(dialogo, 1, "Cantidad", cantidad)
        unidades = [
            f"{item.get('id_unidad', '')} — {item.get('nombre', '')} ({item.get('abreviatura', '')})"
            for item in self._unidades
        ]
        unidad_predeterminada = str(ingredientes_menu[0].get("id_unidad", ""))
        indice_unidad = next(
            (
                indice
                for indice, item in enumerate(self._unidades)
                if str(item.get("id_unidad", "")) == unidad_predeterminada
            ),
            0,
        )
        unidad = tk.StringVar(value=unidades[indice_unidad] if unidades else "")
        tk.Label(
            dialogo,
            text="Unidad",
            bg=c["panel"],
            fg=c["texto"],
        ).grid(row=2, column=0, sticky="w", padx=18, pady=6)
        ttk.Combobox(
            dialogo,
            textvariable=unidad,
            values=unidades,
            state="readonly" if unidades else "normal",
            width=32,
        ).grid(row=2, column=1, padx=(0, 18), pady=6)

        def actualizar_unidad(_evento: tk.Event | None = None) -> None:
            indice = opciones_ingredientes.index(ingrediente.get())
            unidad_base = str(ingredientes_menu[indice].get("id_unidad", ""))
            indice_base = next(
                (
                    indice_unidad
                    for indice_unidad, registro in enumerate(self._unidades)
                    if str(registro.get("id_unidad", "")) == unidad_base
                ),
                0,
            )
            unidad.set(unidades[indice_base] if unidades else "")

        selector_ingrediente.bind("<<ComboboxSelected>>", actualizar_unidad)

        def agregar() -> None:
            indice = opciones_ingredientes.index(ingrediente.get())
            item = ingredientes_menu[indice]
            unidad_item = self._unidades[unidades.index(unidad.get())] if unidades else {}
            registro = {
                "id_ingrediente": str(item.get("id_ingrediente", "")),
                "ingrediente": str(item.get("nombre", "")),
                "cantidad": cantidad.get(),
                "id_unidad": str(unidad_item.get("id_unidad", "")),
                "unidad": str(unidad_item.get("nombre", "")),
            }
            self._agregar_al_borrador(registro)
            dialogo.destroy()

        tk.Button(
            dialogo,
            text="Agregar al borrador",
            command=agregar,
            bg=c["primario"],
            fg="#FFFFFF",
            padx=12,
            pady=7,
        ).grid(row=3, column=0, columnspan=2, sticky="e", padx=18, pady=(12, 18))
        dialogo.grab_set()

    def _agregar_ingredientes_en_tabla(self) -> None:
        menu = self._registro_seleccionado(
            self.menu.get(),
            self._menus,
            "id_menu_base",
        )
        if not menu:
            messagebox.showinfo(
                "Selecciona un menú",
                "Primero selecciona un menú base para ver sus ingredientes.",
                parent=self,
            )
            return
        ingredientes_menu = self._ingredientes_del_menu(menu, self._ingredientes)
        if not ingredientes_menu:
            messagebox.showinfo(
                "Ingredientes",
                "El menú seleccionado no tiene ingredientes asociados.",
                parent=self,
            )
            return
        borrador_por_ingrediente = {
            item["id_ingrediente"]: item for item in self._items_borrador
        }

        dialogo = tk.Toplevel(self)
        dialogo.title("Agregar ingredientes utilizados")
        dialogo.transient(self.winfo_toplevel())
        dialogo.geometry("760x500")
        dialogo.minsize(600, 300)
        dialogo.columnconfigure(0, weight=1)
        dialogo.rowconfigure(1, weight=1)
        dialogo.protocol("WM_DELETE_WINDOW", dialogo.destroy)
        c = self._colores

        tk.Label(
            dialogo,
            text=(
                "Ingresa las cantidades. Deja en blanco lo que no agregarás; "
                "los ingredientes del borrador aparecen con sus valores actuales."
            ),
            bg=c["panel"],
            fg=c["secundario"],
            anchor="w",
            wraplength=720,
            padx=16,
            pady=12,
        ).grid(row=0, column=0, sticky="ew")

        contenedor = tk.Frame(dialogo, bg=c["panel"])
        contenedor.grid(row=1, column=0, sticky="nsew", padx=16)
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)

        lienzo = tk.Canvas(contenedor, highlightthickness=0, bg=c["panel"])
        barra = ttk.Scrollbar(contenedor, orient="vertical", command=lienzo.yview)
        lienzo.configure(yscrollcommand=barra.set)
        lienzo.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        filas = tk.Frame(lienzo, bg=c["panel"])
        ventana = lienzo.create_window((0, 0), window=filas, anchor="nw")
        filas.bind(
            "<Configure>",
            lambda _evento: lienzo.configure(scrollregion=lienzo.bbox("all")),
        )
        lienzo.bind(
            "<Configure>",
            lambda evento: lienzo.itemconfigure(ventana, width=evento.width),
        )
        for columna, (etiqueta, peso) in enumerate(
            (("Ingrediente", 3), ("Cantidad utilizada", 1), ("Unidad", 2))
        ):
            filas.columnconfigure(columna, weight=peso)
            tk.Label(
                filas,
                text=etiqueta,
                bg="#E8F0EB",
                fg=c["primario"],
                font=("TkDefaultFont", 9, "bold"),
                anchor="w",
                padx=8,
                pady=8,
            ).grid(row=0, column=columna, sticky="ew", padx=(0, 1))

        opciones_unidades = [
            f"{item.get('id_unidad', '')} — {item.get('nombre', '')} ({item.get('abreviatura', '')})"
            for item in self._unidades
        ]
        entradas: list[tuple[Registro, tk.StringVar, tk.StringVar]] = []
        for fila, ingrediente in enumerate(ingredientes_menu, start=1):
            id_ingrediente = str(ingrediente.get("id_ingrediente", ""))
            existente = borrador_por_ingrediente.get(id_ingrediente)
            fondo = "#F8FAF8" if fila % 2 else "#FFFFFF"
            tk.Label(
                filas,
                text=str(ingrediente.get("nombre", "")),
                bg=fondo,
                fg=c["texto"],
                anchor="w",
                padx=8,
                pady=6,
            ).grid(row=fila, column=0, sticky="ew", padx=(0, 1), pady=1)
            cantidad = tk.StringVar(
                value=existente.get("cantidad", "") if existente else ""
            )
            ttk.Entry(filas, textvariable=cantidad).grid(
                row=fila, column=1, sticky="ew", padx=(0, 1), pady=1
            )
            id_unidad_base = str(
                existente.get("id_unidad", ingrediente.get("id_unidad", ""))
                if existente
                else ingrediente.get("id_unidad", "")
            )
            indice_unidad = next(
                (
                    indice
                    for indice, unidad in enumerate(self._unidades)
                    if str(unidad.get("id_unidad", "")) == id_unidad_base
                ),
                0,
            )
            unidad = tk.StringVar(
                value=opciones_unidades[indice_unidad] if opciones_unidades else ""
            )
            ttk.Combobox(
                filas,
                textvariable=unidad,
                values=opciones_unidades,
                state="readonly" if opciones_unidades else "normal",
            ).grid(row=fila, column=2, sticky="ew", padx=(0, 1), pady=1)
            entradas.append((ingrediente, cantidad, unidad))

        def agregar() -> None:
            registros: list[dict[str, str]] = []
            for ingrediente, cantidad, unidad in entradas:
                valor_cantidad = cantidad.get().strip()
                if not valor_cantidad:
                    continue
                try:
                    cantidad_numerica = float(valor_cantidad)
                except ValueError:
                    messagebox.showerror(
                        "Cantidad inválida",
                        f"La cantidad de {ingrediente.get('nombre', 'un ingrediente')} debe ser numérica.",
                        parent=dialogo,
                    )
                    return
                if not math.isfinite(cantidad_numerica) or cantidad_numerica <= 0:
                    messagebox.showerror(
                        "Cantidad inválida",
                        "Las cantidades utilizadas deben ser mayores que cero.",
                        parent=dialogo,
                    )
                    return
                if not opciones_unidades or unidad.get() not in opciones_unidades:
                    messagebox.showerror(
                        "Unidad requerida",
                        f"Selecciona una unidad para {ingrediente.get('nombre', 'cada ingrediente')}.",
                        parent=dialogo,
                    )
                    return
                unidad_item = self._unidades[opciones_unidades.index(unidad.get())]
                registros.append(
                    {
                        "id_ingrediente": str(ingrediente.get("id_ingrediente", "")),
                        "ingrediente": str(ingrediente.get("nombre", "")),
                        "cantidad": valor_cantidad,
                        "id_unidad": str(unidad_item.get("id_unidad", "")),
                        "unidad": str(unidad_item.get("nombre", "")),
                    }
                )
            if not registros:
                messagebox.showinfo(
                    "Sin cantidades",
                    "Ingresa al menos una cantidad para agregar ingredientes.",
                    parent=dialogo,
                )
                return
            for registro in registros:
                self._agregar_al_borrador(registro)
            dialogo.destroy()

        tk.Button(
            dialogo,
            text="Agregar al borrador",
            command=agregar,
            bg=c["primario"],
            fg="#FFFFFF",
            padx=12,
            pady=7,
        ).grid(row=2, column=0, sticky="e", padx=16, pady=12)
        dialogo.grab_set()

    def _ingredientes_disponibles(self) -> list[Registro]:
        menu = self._registro_seleccionado(
            self.menu.get(),
            self._menus,
            "id_menu_base",
        )
        if not menu:
            messagebox.showinfo(
                "Selecciona un menú",
                "Primero selecciona un menú base para ver sus ingredientes.",
                parent=self,
            )
            return []
        ingredientes_menu = self._ingredientes_del_menu(menu, self._ingredientes)
        ids_en_borrador = {
            str(item["id_ingrediente"]) for item in self._items_borrador
        }
        disponibles = [
            item
            for item in ingredientes_menu
            if str(item.get("id_ingrediente", "")) not in ids_en_borrador
        ]
        if not disponibles:
            messagebox.showinfo(
                "Ingredientes",
                "El menú seleccionado no tiene ingredientes disponibles para agregar.",
                parent=self,
            )
        return disponibles

    def _agregar_al_borrador(self, registro: dict[str, str]) -> None:
        for indice, existente in enumerate(self._items_borrador):
            if existente["id_ingrediente"] != registro["id_ingrediente"]:
                continue
            self._items_borrador[indice] = registro
            fila = self._tabla_ingredientes.get_children()[indice]
            self._tabla_ingredientes.item(
                fila,
                values=(
                    registro["id_ingrediente"],
                    registro["ingrediente"],
                    registro["cantidad"],
                    registro["unidad"],
                ),
            )
            return
        self._items_borrador.append(registro)
        indice = len(self._tabla_ingredientes.get_children())
        etiqueta_fila = "fila-par" if indice % 2 == 0 else "fila-impar"
        self._tabla_ingredientes.insert(
            "",
            "end",
            values=(
                registro["id_ingrediente"],
                registro["ingrediente"],
                registro["cantidad"],
                registro["unidad"],
            ),
            tags=(etiqueta_fila,),
        )

    @staticmethod
    def _ingredientes_del_menu(
        menu: Registro,
        ingredientes: Sequence[Registro],
    ) -> list[Registro]:
        identificadores_menu = {
            str(identificador) for identificador in menu.get("ingredientes", [])
        }
        return [
            ingrediente
            for ingrediente in ingredientes
            if str(ingrediente.get("id_ingrediente", "")) in identificadores_menu
        ]

    def _cambio_menu(self, _evento: tk.Event | None = None) -> None:
        menu_seleccionado = self.menu.get()
        if menu_seleccionado == self._menu_planificacion_actual:
            self._actualizar_datos_menu()
            return
        if self._items_borrador:
            confirmar = messagebox.askyesno(
                "Cambiar menú base",
                "Cambiar el menú quitará los ingredientes agregados al borrador. ¿Continuar?",
                parent=self,
            )
            if not confirmar:
                self.menu.set(self._menu_planificacion_actual)
                self._actualizar_datos_menu()
                return
            self._items_borrador.clear()
            for fila in self._tabla_ingredientes.get_children():
                self._tabla_ingredientes.delete(fila)
        self._menu_planificacion_actual = menu_seleccionado
        self._actualizar_datos_menu()

    def _actualizar_datos_menu(self) -> None:
        menu = self._registro_seleccionado(
            self.menu.get(),
            self._menus,
            "id_menu_base",
        )
        if not menu:
            self.porcion.set("")
            self.unidad_porcion.set("")
            return
        self.porcion.set(str(menu.get("porcion", "")))
        unidad = next(
            (
                item
                for item in self._unidades
                if str(item.get("id_unidad", "")) == str(menu.get("id_unidad", ""))
            ),
            None,
        )
        if unidad is None:
            self.unidad_porcion.set("")
            return
        self.unidad_porcion.set(
            f"{unidad.get('id_unidad', '')} — {unidad.get('nombre', '')} "
            f"({unidad.get('abreviatura', '')})"
        )

    def _dialogo_campo(
        self,
        master: tk.Misc,
        fila: int,
        etiqueta: str,
        variable: tk.StringVar,
    ) -> None:
        c = self._colores
        tk.Label(
            master,
            text=etiqueta,
            bg=c["panel"],
            fg=c["texto"],
        ).grid(row=fila, column=0, sticky="w", padx=18, pady=6)
        ttk.Entry(master, textvariable=variable, width=35).grid(
            row=fila, column=1, padx=(0, 18), pady=6
        )

    def _quitar_ingrediente(self) -> None:
        seleccion = self._tabla_ingredientes.selection()
        if not seleccion:
            return
        indice = self._tabla_ingredientes.index(seleccion[0])
        self._tabla_ingredientes.delete(seleccion[0])
        if indice < len(self._items_borrador):
            self._items_borrador.pop(indice)

    def _guardar(self) -> None:
        if self._on_guardar is None:
            self._pendiente()
            return
        menu = self._registro_seleccionado(self.menu.get(), self._menus, "id_menu_base")
        if not menu:
            messagebox.showerror(
                "Menú requerido",
                "Selecciona un menú base antes de guardar la planificación.",
                parent=self,
            )
            return
        self._on_guardar(
            {
                "fecha": self.fecha.get(),
                "id_menu_base": menu["id_menu_base"],
                "ingredientes": list(self._items_borrador),
            }
        )

    @staticmethod
    def _registro_seleccionado(
        seleccion: str,
        registros: Sequence[Registro],
        clave_id: str,
    ) -> Registro:
        for registro in registros:
            etiqueta = f"{registro.get(clave_id, '')} — {registro.get('nombre', '')}"
            if clave_id == "id_unidad":
                etiqueta += f" ({registro.get('abreviatura', '')})"
            if seleccion == etiqueta:
                return registro
        return {}

    def mostrar_planificaciones(self, registros: Sequence[Registro]) -> None:
        for item in self._tabla_planificaciones.get_children():
            self._tabla_planificaciones.delete(item)
        for indice, registro in enumerate(registros):
            etiqueta_fila = "fila-par" if indice % 2 == 0 else "fila-impar"
            self._tabla_planificaciones.insert(
                "",
                "end",
                values=(
                    registro.get("id_menu_diario", ""),
                    registro.get("menu", registro.get("id_menu_base", "")),
                    registro.get("fecha", ""),
                    registro.get("porcion", ""),
                    registro.get("unidad", registro.get("id_unidad_porcion", "")),
                ),
                tags=(etiqueta_fila,),
            )
        if registros:
            self._estado.place_forget()
        else:
            self._estado.configure(text="No hay planificaciones para esta fecha.")
            self._estado.place(relx=0.5, rely=0.67, anchor="center")

    def mostrar_error(self, mensaje: str) -> None:
        messagebox.showerror("No se pudo completar la operación", mensaje, parent=self)

    def mostrar_mensaje(self, mensaje: str) -> None:
        messagebox.showinfo("Recetario", mensaje, parent=self)

    def _pendiente(self) -> None:
        messagebox.showinfo(
            "Acción pendiente",
            "Esta acción estará disponible cuando se conecte el controlador.",
            parent=self,
        )

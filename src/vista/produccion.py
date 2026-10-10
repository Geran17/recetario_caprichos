"""Presentación Tkinter del registro de producción de cocina."""

import tkinter as tk
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime
from tkinter import messagebox, ttk
from typing import Any


Registro = Mapping[str, Any]


class ProduccionVista(tk.Frame):
    """Formulario de producción e historial suministrado por el controlador."""

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
        on_registrar: Callable[[dict[str, str]], None] | None = None,
        on_consultar: Callable[[dict[str, str]], None] | None = None,
        on_actualizar: Callable[[dict[str, str]], None] | None = None,
        on_eliminar: Callable[[dict[str, Any]], None] | None = None,
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
        self._on_registrar = on_registrar
        self._on_consultar = on_consultar
        self._on_actualizar = on_actualizar
        self._on_eliminar = on_eliminar
        self._on_calcular_porciones: Callable[[dict[str, str]], str] | None = None
        self._menus_diarios: list[Registro] = []
        self._unidades: list[Registro] = []
        self._salidas_por_fila: dict[str, dict[str, Any]] = {}
        self._id_salida_edicion: int | None = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._crear_encabezado()
        self._crear_formulario()
        self._crear_historial()

    def _crear_encabezado(self) -> None:
        c = self._colores
        tk.Label(
            self,
            text="Producción de cocina",
            bg=c["fondo"],
            fg=c["texto"],
            font=("TkDefaultFont", 15, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            self,
            text="Registra el resultado de una preparación diaria.",
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
            padx=20,
            pady=18,
        )
        self._panel = panel
        panel.grid(row=2, column=0, sticky="new", pady=(0, 16))
        for columna in range(3):
            panel.columnconfigure(columna, weight=1)
        self._titulo_formulario = tk.Label(
            panel,
            text="Nueva salida de cocina",
            bg=c["panel"],
            fg=c["texto"],
            font=("TkDefaultFont", 10, "bold"),
        )
        self._titulo_formulario.grid(row=0, column=0, sticky="w", pady=(0, 14))

        self.fecha_menu = tk.StringVar(value=date.today().isoformat())
        tk.Label(
            panel,
            text="Fecha de planificación",
            bg=c["panel"],
            fg=c["secundario"],
            font=("TkDefaultFont", 8),
        ).grid(row=0, column=1, sticky="e", padx=(0, 8), pady=(0, 14))
        filtro_menu = tk.Frame(panel, bg=c["panel"])
        filtro_menu.grid(row=0, column=2, sticky="ew", pady=(0, 14))
        filtro_menu.columnconfigure(0, weight=1)
        entrada_fecha_menu = ttk.Entry(
            filtro_menu,
            textvariable=self.fecha_menu,
            width=12,
        )
        entrada_fecha_menu.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        entrada_fecha_menu.bind("<Return>", self._filtrar_menus)
        tk.Button(
            filtro_menu,
            text="Filtrar",
            command=self._filtrar_menus,
            cursor="hand2",
            relief="flat",
            padx=10,
            pady=5,
            bg="#EEF0EC",
            fg=c["texto"],
        ).grid(row=0, column=1)

        self.fecha = tk.StringVar(value=date.today().isoformat())
        self.fecha_hora = tk.StringVar()
        self.menu_diario = tk.StringVar()
        self.cantidad_producida = tk.StringVar()
        self.unidad = tk.StringVar()
        self.cantidad_porciones = tk.StringVar()
        self._menu_selector = self._selector(
            panel, 1, 0, "Menú planificado", self.menu_diario, ()
        )
        self._menu_selector.bind("<<ComboboxSelected>>", self._menu_seleccionado)
        self._entrada(
            panel,
            1,
            1,
            "Cantidad producida (puede incluir unidad)",
            self.cantidad_producida,
        )
        self.cantidad_producida.trace_add("write", self._recalcular_porciones)
        self._unidad_selector = self._selector(
            panel, 1, 2, "Unidad de producción", self.unidad, ()
        )
        self._unidad_selector.bind("<<ComboboxSelected>>", self._recalcular_porciones)
        self._entrada(
            panel,
            2,
            0,
            "Porciones obtenidas (calculado)",
            self.cantidad_porciones,
            readonly=True,
        )
        self._entrada(panel, 2, 1, "Fecha y hora (opcional)", self.fecha_hora)

        ayuda = tk.Label(
            panel,
            text=(
                "La unidad y el cálculo de porciones se contrastan con la "
                "planificación seleccionada."
            ),
            bg=c["panel"],
            fg=c["secundario"],
            font=("TkDefaultFont", 8),
            wraplength=480,
            justify="left",
        )
        ayuda.grid(row=2, column=2, sticky="w", padx=(0, 12), pady=(12, 0))

        acciones = tk.Frame(panel, bg=c["panel"])
        acciones.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        self._boton_guardar = tk.Button(
            acciones,
            text="Registrar producción",
            command=self._registrar,
            cursor="hand2",
            relief="flat",
            padx=15,
            pady=8,
            bg=c["primario"],
            fg="#FFFFFF",
        )
        self._boton_guardar.pack(side="right")
        self._boton_cancelar_edicion = tk.Button(
            acciones,
            text="Cancelar edición",
            command=self._cancelar_edicion,
            cursor="hand2",
            relief="flat",
            padx=12,
            pady=8,
            bg="#EEF0EC",
            fg=c["texto"],
        )

    def _crear_historial(self) -> None:
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
        filtros = tk.Frame(panel, bg=c["panel"])
        filtros.grid(row=0, column=0, sticky="ew", pady=(0, 9))
        filtros.columnconfigure(0, weight=1)
        tk.Label(
            filtros,
            text="Historial de producción",
            bg=c["panel"],
            fg=c["texto"],
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Entry(
            filtros,
            textvariable=self.fecha,
            width=16,
        ).grid(row=0, column=1, padx=(8, 6))
        filtros.grid_columnconfigure(0, weight=1)
        tk.Button(
            filtros,
            text="Consultar fecha",
            command=self._consultar,
            relief="flat",
            padx=10,
            pady=5,
            bg="#EEF0EC",
            fg=c["texto"],
        ).grid(row=0, column=2)
        tk.Button(
            filtros,
            text="Editar",
            command=self._editar_seleccionado,
            relief="flat",
            padx=10,
            pady=5,
            bg="#EEF0EC",
            fg=c["texto"],
        ).grid(row=0, column=3, padx=(8, 0))
        tk.Button(
            filtros,
            text="Eliminar",
            command=self._eliminar_seleccionado,
            relief="flat",
            padx=10,
            pady=5,
            bg="#F8ECE8",
            fg="#8B3F32",
        ).grid(row=0, column=4, padx=(6, 0))
        estilo = ttk.Style(self)
        estilo.configure(
            "Produccion.Treeview",
            rowheight=32,
            font=("TkDefaultFont", 9),
            background=c["panel"],
            fieldbackground=c["panel"],
            foreground=c["texto"],
        )
        estilo.configure(
            "Produccion.Treeview.Heading",
            background="#E8F0EB",
            foreground=c["primario"],
            font=("TkDefaultFont", 9, "bold"),
            relief="flat",
            padding=(10, 8),
        )
        estilo.map(
            "Produccion.Treeview",
            background=[("selected", "#E3ECE6"), ("active", "#D7E8DE")],
            foreground=[("selected", c["texto"]), ("active", c["texto"])],
        )
        self._tabla = ttk.Treeview(
            panel,
            columns=("fecha_hora", "menu", "cantidad", "unidad", "porciones"),
            show="headings",
            height=8,
            style="Produccion.Treeview",
        )
        self._tabla.tag_configure("fila-par", background="#F8FAF8")
        self._tabla.tag_configure("fila-impar", background="#FFFFFF")
        for clave, etiqueta, ancho in (
            ("fecha_hora", "Fecha y hora", 155),
            ("menu", "Menú", 220),
            ("cantidad", "Cantidad producida", 150),
            ("unidad", "Unidad", 110),
            ("porciones", "Porciones", 110),
        ):
            self._tabla.heading(clave, text=etiqueta, anchor="w")
            self._tabla.column(clave, width=ancho, anchor="w")
        self._tabla.grid(row=1, column=0, sticky="nsew")
        self._tabla.bind("<Double-1>", self._editar_seleccionado)
        self._estado = tk.Label(
            panel,
            text="No hay salidas para mostrar.",
            bg=c["panel"],
            fg=c["secundario"],
        )
        self._estado.place(relx=0.5, rely=0.65, anchor="center")

    def _entrada(
        self,
        master: tk.Misc,
        fila: int,
        columna: int,
        etiqueta: str,
        variable: tk.StringVar,
        *,
        readonly: bool = False,
    ) -> None:
        c = self._colores
        celda = tk.Frame(master, bg=c["panel"])
        celda.grid(row=fila, column=columna, sticky="ew", padx=(0, 14), pady=5)
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
        celda.grid(row=fila, column=columna, sticky="ew", padx=(0, 14), pady=5)
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
        menus_diarios: Sequence[Registro] = (),
        unidades: Sequence[Registro] = (),
    ) -> None:
        self._menus_diarios = list(menus_diarios)
        self._unidades = list(unidades)
        self._actualizar_menus_fecha()
        self._unidad_selector.configure(
            values=[
                self._etiqueta_unidad(item)
                for item in self._unidades
            ],
            state="readonly",
        )
        self._recalcular_porciones()

    def _actualizar_menus_fecha(self) -> None:
        fecha = self.fecha_menu.get()
        menus = [
            item
            for item in self._menus_diarios
            if str(item.get("fecha", "")) == fecha
        ]
        opciones = [self._etiqueta_menu(item) for item in menus]
        self._menu_selector.configure(values=opciones, state="readonly")
        if self.menu_diario.get() not in opciones:
            self.menu_diario.set("")
        self._recalcular_porciones()

    @staticmethod
    def _etiqueta_menu(opcion: Registro) -> str:
        return (
            f"{opcion.get('id_menu_diario', '')} — {opcion.get('fecha', '')} — "
            f"{opcion.get('menu', opcion.get('id_menu_base', ''))}"
        )

    @staticmethod
    def _etiqueta_unidad(opcion: Registro) -> str:
        return (
            f"{opcion.get('id_unidad', '')} — {opcion.get('nombre', '')} "
            f"({opcion.get('abreviatura', '')})"
        )

    def establecer_callbacks(
        self,
        *,
        on_registrar: Callable[[dict[str, str]], None] | None = None,
        on_consultar: Callable[[dict[str, str]], None] | None = None,
        on_actualizar: Callable[[dict[str, str]], None] | None = None,
        on_eliminar: Callable[[dict[str, Any]], None] | None = None,
        on_calcular_porciones: Callable[[dict[str, str]], str] | None = None,
    ) -> None:
        self._on_registrar = on_registrar
        self._on_consultar = on_consultar
        self._on_actualizar = on_actualizar
        self._on_eliminar = on_eliminar
        self._on_calcular_porciones = on_calcular_porciones
        self._recalcular_porciones()

    def mostrar_salidas(self, registros: Sequence[Registro]) -> None:
        self._salidas_por_fila.clear()
        for item in self._tabla.get_children():
            self._tabla.delete(item)
        for indice, registro in enumerate(registros):
            etiqueta_fila = "fila-par" if indice % 2 == 0 else "fila-impar"
            fila = self._tabla.insert(
                "",
                "end",
                values=(
                    registro.get("fecha_hora", ""),
                    registro.get("menu", registro.get("id_menu_diario", "")),
                    registro.get("cantidad_producida", ""),
                    registro.get("unidad", registro.get("id_unidad", "")),
                    registro.get("cantidad_porciones", ""),
                ),
                tags=(etiqueta_fila,),
            )
            self._salidas_por_fila[fila] = dict(registro)
        if registros:
            self._estado.place_forget()
        else:
            self._estado.place(relx=0.5, rely=0.65, anchor="center")

    def mostrar_error(self, mensaje: str) -> None:
        messagebox.showerror("No se pudo completar la operación", mensaje, parent=self)

    def mostrar_mensaje(self, mensaje: str) -> None:
        messagebox.showinfo("Recetario", mensaje, parent=self)

    def _consultar(self) -> None:
        if self._on_consultar is None:
            self._pendiente()
            return
        self._on_consultar(
            {
                "fecha": self.fecha.get(),
            }
        )

    def _filtrar_menus(self, _evento: tk.Event | None = None) -> None:
        try:
            fecha = date.fromisoformat(self.fecha_menu.get())
        except ValueError:
            messagebox.showerror(
                "Fecha inválida",
                "Ingresa la fecha con el formato AAAA-MM-DD.",
                parent=self,
            )
            return
        self.fecha_menu.set(fecha.isoformat())
        self._actualizar_menus_fecha()

    def _registrar(self) -> None:
        callback = (
            self._on_actualizar
            if self._id_salida_edicion is not None
            else self._on_registrar
        )
        if callback is None:
            self._pendiente()
            return
        menu = self._buscar_opcion(
            self.menu_diario.get(),
            self._menus_diarios,
            "id_menu_diario",
            incluir_fecha=True,
        )
        unidad = self._buscar_opcion(
            self.unidad.get(),
            self._unidades,
            "id_unidad",
        )
        valores = {
            "fecha_hora": self.fecha_hora.get(),
            "id_menu_diario": str(
                menu.get("id_menu_diario", self.menu_diario.get())
            ),
            "cantidad_producida": self.cantidad_producida.get(),
            "id_unidad": str(unidad.get("id_unidad", self.unidad.get())),
            "cantidad_porciones": self.cantidad_porciones.get(),
        }
        if self._id_salida_edicion is not None:
            valores["id_salida"] = str(self._id_salida_edicion)
            valores["fecha_consulta"] = str(menu.get("fecha", self.fecha.get()))
            callback(valores)
        else:
            callback(valores)

    def _editar_seleccionado(self, _evento: tk.Event | None = None) -> None:
        seleccion = self._tabla.selection()
        if not seleccion:
            return
        registro = self._salidas_por_fila[seleccion[0]]
        self._id_salida_edicion = int(registro["id_salida"])
        fecha_planificacion = str(registro.get("fecha_planificacion", ""))
        if fecha_planificacion:
            self.fecha_menu.set(fecha_planificacion)
            self._actualizar_menus_fecha()
        menu = next(
            (
                item
                for item in self._menus_diarios
                if str(item.get("id_menu_diario", ""))
                == str(registro.get("id_menu_diario", ""))
            ),
            None,
        )
        self.menu_diario.set(self._etiqueta_menu(menu) if menu else "")
        self.cantidad_producida.set(str(registro.get("cantidad_producida", "")))
        unidad = next(
            (
                item
                for item in self._unidades
                if str(item.get("id_unidad", ""))
                == str(registro.get("id_unidad", ""))
            ),
            None,
        )
        self.unidad.set(self._etiqueta_unidad(unidad) if unidad else "")
        self.fecha_hora.set(str(registro.get("fecha_hora", "")))
        self._titulo_formulario.configure(text="Editar salida de cocina")
        self._boton_guardar.configure(text="Guardar cambios")
        self._boton_cancelar_edicion.pack(side="left")
        self._recalcular_porciones()

    def _cancelar_edicion(self) -> None:
        self._id_salida_edicion = None
        self.menu_diario.set("")
        self.cantidad_producida.set("")
        self.unidad.set("")
        self.fecha_hora.set("")
        self._titulo_formulario.configure(text="Nueva salida de cocina")
        self._boton_guardar.configure(text="Registrar producción")
        self._boton_cancelar_edicion.pack_forget()
        self._recalcular_porciones()

    def finalizar_edicion(self) -> None:
        self._cancelar_edicion()

    def _eliminar_seleccionado(self) -> None:
        seleccion = self._tabla.selection()
        if not seleccion:
            return
        if self._on_eliminar is None:
            self._pendiente()
            return
        registro = self._salidas_por_fila[seleccion[0]]
        confirmado = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Deseas eliminar el registro de producción seleccionado?",
            parent=self,
        )
        if confirmado:
            if self._id_salida_edicion == int(registro["id_salida"]):
                self._cancelar_edicion()
            self._on_eliminar(dict(registro))

    def _menu_seleccionado(self, _evento: tk.Event | None = None) -> None:
        if self._id_salida_edicion is None:
            self.fecha_hora.set(datetime.now().isoformat(sep=" ", timespec="seconds"))
        self._recalcular_porciones()

    def _recalcular_porciones(self, *_args: Any) -> None:
        if self._on_calcular_porciones is None:
            self.cantidad_porciones.set("")
            return
        menu = self._buscar_opcion(
            self.menu_diario.get(),
            self._menus_diarios,
            "id_menu_diario",
            incluir_fecha=True,
        )
        unidad = self._buscar_opcion(self.unidad.get(), self._unidades, "id_unidad")
        try:
            resultado = self._on_calcular_porciones(
                {
                    "id_menu_diario": str(menu.get("id_menu_diario", "")),
                    "cantidad_producida": self.cantidad_producida.get(),
                    "id_unidad": str(unidad.get("id_unidad", "")),
                }
            )
        except (TypeError, ValueError):
            resultado = ""
        self.cantidad_porciones.set(resultado)

    @staticmethod
    def _buscar_opcion(
        seleccion: str,
        opciones: Sequence[Registro],
        id_clave: str,
        *,
        incluir_fecha: bool = False,
    ) -> Registro:
        for opcion in opciones:
            etiqueta = f"{opcion.get(id_clave, '')} — "
            if incluir_fecha:
                etiqueta += f"{opcion.get('fecha', '')} — "
                etiqueta += str(opcion.get("menu", opcion.get("id_menu_base", "")))
            else:
                etiqueta += (
                    f"{opcion.get('nombre', '')} "
                    f"({opcion.get('abreviatura', '')})"
                )
            if seleccion == etiqueta:
                return opcion
        return {}

    def _pendiente(self) -> None:
        messagebox.showinfo(
            "Acción pendiente",
            "Esta acción estará disponible cuando se conecte el controlador.",
            parent=self,
        )

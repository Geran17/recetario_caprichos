"""Presentación Tkinter del catálogo de menús base."""

import tkinter as tk
from collections.abc import Callable, Mapping, Sequence
from tkinter import messagebox, ttk
from typing import Any


Registro = Mapping[str, Any]
Guardar = Callable[[dict[str, Any]], None]


class MenusBaseVista(tk.Frame):
    """Lista y formulario visual de menús base, sin acceso a servicios."""

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
        on_crear: Guardar | None = None,
        on_actualizar: Guardar | None = None,
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
        self._on_crear = on_crear
        self._on_actualizar = on_actualizar
        self._on_eliminar = on_eliminar
        self._unidades: list[Registro] = []
        self._cocineros: list[Registro] = []
        self._ingredientes: list[Registro] = []
        self._registros_por_fila: dict[str, dict[str, Any]] = {}
        self._formulario: tk.Toplevel | None = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._crear_encabezado()
        self._crear_tabla()

    def _crear_encabezado(self) -> None:
        c = self._colores
        encabezado = tk.Frame(self, bg=c["fondo"])
        encabezado.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        encabezado.columnconfigure(0, weight=1)
        tk.Label(
            encabezado,
            text="Menús base",
            bg=c["fondo"],
            fg=c["texto"],
            font=("TkDefaultFont", 15, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            encabezado,
            text="Define las porciones y la composición de cada menú.",
            bg=c["fondo"],
            fg=c["secundario"],
            font=("TkDefaultFont", 9),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        acciones = tk.Frame(encabezado, bg=c["fondo"])
        acciones.grid(row=0, column=1, rowspan=2, sticky="e")
        self._boton(acciones, "＋  Nuevo menú", self._nuevo, primario=True).pack(
            side="left", padx=(0, 8)
        )
        self._boton(acciones, "Editar", self._editar).pack(side="left", padx=(0, 8))
        self._boton(acciones, "Eliminar", self._eliminar).pack(side="left")

    def _crear_tabla(self) -> None:
        c = self._colores
        panel = tk.Frame(
            self,
            bg=c["panel"],
            highlightbackground=c["borde"],
            highlightthickness=1,
        )
        panel.grid(row=1, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)
        barra = tk.Frame(panel, bg=c["panel"])
        barra.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        barra.columnconfigure(0, weight=1)
        tk.Label(
            barra,
            text="Menús registrados",
            bg=c["panel"],
            fg=c["texto"],
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")
        self._cantidad = tk.Label(
            barra,
            text="0 registros",
            bg=c["panel"],
            fg=c["secundario"],
            font=("TkDefaultFont", 9),
        )
        self._cantidad.grid(row=0, column=1, sticky="e")
        tabla_frame = tk.Frame(panel, bg=c["panel"])
        tabla_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        tabla_frame.rowconfigure(0, weight=1)
        tabla_frame.columnconfigure(0, weight=1)
        estilo = ttk.Style(self)
        estilo.configure(
            "MenusBase.Treeview",
            rowheight=32,
            font=("TkDefaultFont", 9),
            background=c["panel"],
            fieldbackground=c["panel"],
            foreground=c["texto"],
        )
        estilo.configure(
            "MenusBase.Treeview.Heading",
            background="#E8F0EB",
            foreground=c["primario"],
            font=("TkDefaultFont", 9, "bold"),
            relief="flat",
            padding=(10, 8),
        )
        estilo.map(
            "MenusBase.Treeview",
            background=[("selected", "#E3ECE6"), ("active", "#D7E8DE")],
            foreground=[("selected", c["texto"]), ("active", c["texto"])],
        )
        self._tabla = ttk.Treeview(
            tabla_frame,
            columns=(
                "id_menu_base",
                "codigo",
                "nombre",
                "porcion",
                "unidad",
                "responsables",
                "ingredientes",
            ),
            show="headings",
            style="MenusBase.Treeview",
            selectmode="browse",
        )
        self._tabla.tag_configure("fila-par", background="#F8FAF8")
        self._tabla.tag_configure("fila-impar", background="#FFFFFF")
        for clave, texto, ancho in (
            ("id_menu_base", "ID", 55),
            ("codigo", "Código", 105),
            ("nombre", "Nombre", 180),
            ("porcion", "Porción", 90),
            ("unidad", "Unidad", 90),
            ("responsables", "Responsables", 170),
            ("ingredientes", "Ingredientes", 220),
        ):
            self._tabla.heading(clave, text=texto, anchor="w")
            self._tabla.column(clave, width=ancho, minwidth=ancho, anchor="w")
        self._tabla.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(tabla_frame, orient="vertical", command=self._tabla.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self._tabla.configure(yscrollcommand=scroll.set)
        self._tabla.bind("<Double-1>", self._editar)
        self._estado = tk.Label(
            tabla_frame,
            text="Todavía no hay menús para mostrar.",
            bg=c["panel"],
            fg=c["secundario"],
        )
        self._estado.place(relx=0.5, rely=0.53, anchor="center")

    def _boton(
        self,
        master: tk.Misc,
        texto: str,
        comando: Callable[[], None],
        *,
        primario: bool = False,
    ) -> tk.Button:
        c = self._colores
        return tk.Button(
            master,
            text=texto,
            command=comando,
            cursor="hand2",
            relief="flat",
            padx=13,
            pady=8,
            bg=c["primario"] if primario else c["panel"],
            fg="#FFFFFF" if primario else c["texto"],
        )

    def mostrar_menus(self, menus: Sequence[Registro]) -> None:
        self._registros_por_fila.clear()
        for item in self._tabla.get_children():
            self._tabla.delete(item)
        for indice, menu in enumerate(menus):
            etiqueta_fila = "fila-par" if indice % 2 == 0 else "fila-impar"
            fila = self._tabla.insert(
                "",
                "end",
                values=(
                    menu.get("id_menu_base", ""),
                    menu.get("codigo", ""),
                    menu.get("nombre", ""),
                    menu.get("porcion", ""),
                    menu.get("unidad", menu.get("id_unidad", "")),
                    menu.get("responsables_texto", ""),
                    menu.get("ingredientes_texto", ""),
                ),
                tags=(etiqueta_fila,),
            )
            self._registros_por_fila[fila] = dict(menu)
        if menus:
            self._estado.place_forget()
        else:
            self._estado.place(relx=0.5, rely=0.53, anchor="center")
        self._cantidad.configure(
            text=f"{len(menus)} registro" + ("" if len(menus) == 1 else "s")
        )

    def establecer_opciones(
        self,
        *,
        unidades: Sequence[Registro] = (),
        cocineros: Sequence[Registro] = (),
        ingredientes: Sequence[Registro] = (),
    ) -> None:
        self._unidades = list(unidades)
        self._cocineros = list(cocineros)
        self._ingredientes = list(ingredientes)

    def establecer_callbacks(
        self,
        *,
        on_crear: Guardar | None = None,
        on_actualizar: Guardar | None = None,
        on_eliminar: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self._on_crear = on_crear
        self._on_actualizar = on_actualizar
        self._on_eliminar = on_eliminar

    def _seleccionado(self) -> dict[str, Any] | None:
        seleccion = self._tabla.selection()
        if not seleccion:
            return None
        return self._registros_por_fila[seleccion[0]].copy()

    def _nuevo(self) -> None:
        self._abrir_formulario()

    def _editar(self, _evento: tk.Event | None = None) -> None:
        registro = self._seleccionado()
        if registro is not None:
            self._abrir_formulario(registro)

    def _eliminar(self) -> None:
        registro = self._seleccionado()
        if registro is None:
            return
        if not messagebox.askyesno(
            "Confirmar eliminación",
            "¿Deseas eliminar el menú seleccionado?",
            parent=self,
        ):
            return
        if self._on_eliminar is not None:
            self._on_eliminar(registro)
        else:
            self._pendiente()

    def _abrir_formulario(self, registro: Registro | None = None) -> None:
        if self._formulario is not None and self._formulario.winfo_exists():
            self._formulario.lift()
            return
        c = self._colores
        formulario = tk.Toplevel(self)
        self._formulario = formulario
        self._registro_en_edicion = None if registro is None else dict(registro)
        formulario.title("Editar menú base" if registro else "Nuevo menú base")
        formulario.transient(self.winfo_toplevel())
        formulario.configure(bg=c["panel"])
        formulario.resizable(False, False)
        formulario.columnconfigure(1, weight=1)
        formulario.protocol("WM_DELETE_WINDOW", self.cerrar_formulario)
        tk.Label(
            formulario,
            text="Datos del menú",
            bg=c["panel"],
            fg=c["texto"],
            font=("TkDefaultFont", 14, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=22, pady=(20, 14))

        self._variables: dict[str, tk.StringVar] = {}
        campos = (
            ("codigo", "Código"),
            ("nombre", "Nombre"),
            ("porcion", "Porción estándar"),
            ("id_unidad", "Unidad de porción"),
            ("descripcion", "Descripción"),
        )
        for fila, (clave, etiqueta) in enumerate(campos, start=1):
            tk.Label(
                formulario,
                text=etiqueta,
                bg=c["panel"],
                fg=c["texto"],
            ).grid(row=fila, column=0, sticky="w", padx=(22, 14), pady=5)
            inicial = "" if registro is None else str(registro.get(clave, ""))
            variable = tk.StringVar(value=inicial)
            self._variables[clave] = variable
            if clave == "id_unidad":
                nombres = [
                    f"{item.get('id_unidad', '')} — {item.get('nombre', '')} ({item.get('abreviatura', '')})"
                    for item in self._unidades
                ]
                widget = ttk.Combobox(
                    formulario,
                    textvariable=variable,
                    values=nombres,
                    state="readonly" if nombres else "normal",
                    width=34,
                )
                if registro is not None:
                    actual = str(registro.get("id_unidad", registro.get("unidad", "")))
                    for item, nombre in zip(self._unidades, nombres, strict=True):
                        if str(item.get("id_unidad", "")) == actual or nombre == actual:
                            variable.set(nombre)
                            break
            else:
                widget = ttk.Entry(formulario, textvariable=variable, width=37)
            widget.grid(row=fila, column=1, sticky="ew", padx=(0, 22), pady=5)
            if clave == "id_unidad" and registro is None and self._unidades:
                variable.set(nombres[0])

        fila_seleccion = len(campos) + 1
        self._crear_selector(
            formulario,
            fila_seleccion,
            "Cocineros responsables",
            self._cocineros,
            "id_cocinero",
            "codigo",
            "nombre",
            () if registro is None else registro.get("responsables", ()),
            "responsables",
        )
        self._crear_selector_ingredientes(
            formulario,
            fila_seleccion + 1,
            () if registro is None else registro.get("ingredientes", ()),
        )
        acciones = tk.Frame(formulario, bg=c["panel"])
        acciones.grid(
            row=fila_seleccion + 3,
            column=0,
            columnspan=2,
            sticky="e",
            padx=22,
            pady=(16, 20),
        )
        tk.Button(
            acciones,
            text="Cancelar",
            command=self.cerrar_formulario,
            padx=12,
            pady=7,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            acciones,
            text="Guardar",
            command=lambda: self._guardar(registro is not None),
            bg=c["primario"],
            fg="#FFFFFF",
            padx=14,
            pady=7,
        ).pack(side="right")
        formulario.update_idletasks()
        formulario.grab_set()
        formulario.focus_set()

    def _crear_selector_ingredientes(
        self,
        master: tk.Misc,
        fila: int,
        seleccionados: Sequence[Any],
    ) -> None:
        c = self._colores
        tk.Label(
            master,
            text="Ingredientes del menú",
            bg=c["panel"],
            fg=c["texto"],
        ).grid(row=fila, column=0, sticky="nw", padx=(22, 14), pady=5)

        panel = tk.Frame(master, bg=c["panel"])
        panel.grid(row=fila, column=1, sticky="ew", padx=(0, 22), pady=5)
        panel.columnconfigure(0, weight=1)

        etiquetas_por_id = {
            opcion.get("id_ingrediente"): (
                f"{opcion.get('codigo', '')} — {opcion.get('nombre', '')}"
            )
            for opcion in self._ingredientes
        }
        ingredientes_por_id_texto = {
            str(identificador): identificador for identificador in etiquetas_por_id
        }
        self._ingredientes_seleccionados = [
            ingredientes_por_id_texto[str(identificador)]
            for identificador in seleccionados
            if str(identificador) in ingredientes_por_id_texto
        ]
        self._etiquetas_ingredientes = etiquetas_por_id

        self._ingrediente_disponible = tk.StringVar()
        combo = ttk.Combobox(
            panel,
            textvariable=self._ingrediente_disponible,
            values=[
                etiquetas_por_id[opcion.get("id_ingrediente")]
                for opcion in self._ingredientes
                if opcion.get("id_ingrediente") not in self._ingredientes_seleccionados
            ],
            state="readonly",
        )
        combo.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._combo_ingredientes = combo
        self._boton(
            panel,
            "Agregar",
            self._agregar_ingrediente,
            primario=True,
        ).grid(row=0, column=1)

        self._ingredientes_lista = tk.Listbox(
            panel,
            selectmode="browse",
            height=4,
            exportselection=False,
            width=38,
        )
        self._ingredientes_lista.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(6, 0),
        )
        self._actualizar_lista_ingredientes()
        self._boton(
            panel,
            "Quitar ingrediente seleccionado",
            self._quitar_ingrediente,
        ).grid(row=2, column=0, columnspan=2, sticky="e", pady=(5, 0))

        if not self._ingredientes:
            tk.Label(
                panel,
                text="No hay ingredientes disponibles. Primero registra ingredientes en Catálogos.",
                bg=c["panel"],
                fg=c["secundario"],
                anchor="w",
            ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))

    def _actualizar_lista_ingredientes(self) -> None:
        self._ingredientes_lista.delete(0, "end")
        for identificador in self._ingredientes_seleccionados:
            self._ingredientes_lista.insert(
                "end",
                self._etiquetas_ingredientes[identificador],
            )
        disponibles = [
            opcion
            for opcion in self._ingredientes
            if opcion.get("id_ingrediente") not in self._ingredientes_seleccionados
        ]
        self._combo_ingredientes.configure(
            values=[
                self._etiquetas_ingredientes[opcion.get("id_ingrediente")]
                for opcion in disponibles
            ]
        )
        if (
            self._ingrediente_disponible.get()
            not in self._combo_ingredientes.cget("values")
        ):
            self._ingrediente_disponible.set("")

    def _agregar_ingrediente(self) -> None:
        etiqueta = self._ingrediente_disponible.get()
        identificador = next(
            (
                clave
                for clave, texto in self._etiquetas_ingredientes.items()
                if texto == etiqueta
            ),
            None,
        )
        if identificador is None or identificador in self._ingredientes_seleccionados:
            return
        self._ingredientes_seleccionados.append(identificador)
        self._actualizar_lista_ingredientes()

    def _quitar_ingrediente(self) -> None:
        seleccion = self._ingredientes_lista.curselection()
        if not seleccion:
            return
        del self._ingredientes_seleccionados[seleccion[0]]
        self._actualizar_lista_ingredientes()

    def _crear_selector(
        self,
        master: tk.Misc,
        fila: int,
        titulo: str,
        opciones: Sequence[Registro],
        id_clave: str,
        codigo_clave: str,
        nombre_clave: str,
        seleccionados: Sequence[Any],
        variable_clave: str,
    ) -> None:
        c = self._colores
        if not hasattr(self, "_listas"):
            self._listas: dict[str, tuple[tk.Listbox, list[Any]]] = {}
        tk.Label(
            master,
            text=titulo,
            bg=c["panel"],
            fg=c["texto"],
        ).grid(row=fila, column=0, sticky="nw", padx=(22, 14), pady=5)
        lista = tk.Listbox(
            master,
            selectmode="multiple",
            height=4,
            exportselection=False,
            width=38,
        )
        lista.grid(row=fila, column=1, sticky="ew", padx=(0, 22), pady=5)
        ids = []
        for opcion in opciones:
            identificador = opcion.get(id_clave)
            ids.append(identificador)
            lista.insert(
                "end",
                f"{opcion.get(codigo_clave, '')} — {opcion.get(nombre_clave, '')}",
            )
        for indice, identificador in enumerate(ids):
            if identificador in seleccionados or str(identificador) in seleccionados:
                lista.selection_set(indice)
        if variable_clave == "responsables":
            self._listas[variable_clave] = (lista, ids)

    def _guardar(self, es_edicion: bool) -> None:
        valores: dict[str, Any] = {
            clave: variable.get() for clave, variable in self._variables.items()
        }
        unidad_seleccionada = valores.get("id_unidad", "")
        for unidad in self._unidades:
            etiqueta = (
                f"{unidad.get('id_unidad', '')} — {unidad.get('nombre', '')} "
                f"({unidad.get('abreviatura', '')})"
            )
            if unidad_seleccionada == etiqueta:
                valores["id_unidad"] = unidad.get("id_unidad")
                break
        for clave, (lista, ids) in self._listas.items():
            valores[clave] = [ids[indice] for indice in lista.curselection()]
        valores["ingredientes"] = self._ingredientes_seleccionados.copy()
        registro = self._registro_en_edicion if es_edicion else None
        if registro is not None:
            valores["id_menu_base"] = registro.get("id_menu_base")
        callback = self._on_actualizar if es_edicion else self._on_crear
        if callback is None:
            self._pendiente()
            return
        callback(valores)

    def cerrar_formulario(self) -> None:
        if self._formulario is not None and self._formulario.winfo_exists():
            self._formulario.grab_release()
            self._formulario.destroy()
        self._formulario = None
        self._variables = {}
        self._listas = {}
        self._registro_en_edicion = None

    def _pendiente(self) -> None:
        messagebox.showinfo(
            "Acción pendiente",
            "Esta acción estará disponible cuando se conecte el controlador.",
            parent=self,
        )

    def mostrar_error(self, mensaje: str) -> None:
        messagebox.showerror("No se pudo completar la operación", mensaje, parent=self)

    def mostrar_mensaje(self, mensaje: str) -> None:
        messagebox.showinfo("Recetario", mensaje, parent=self)

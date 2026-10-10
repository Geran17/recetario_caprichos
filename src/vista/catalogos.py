"""Componentes Tkinter de presentación para los catálogos."""

import tkinter as tk
from collections.abc import Callable, Mapping, Sequence
from tkinter import messagebox, ttk
from typing import Any


Campo = tuple[str, str]
Registro = Mapping[str, Any]
Accion = Callable[[dict[str, str]], None]


class CatalogoFrame(tk.Frame):
    """Lista y formularios genéricos; delega las acciones en callbacks."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        titulo: str,
        descripcion: str,
        columnas: Sequence[Campo],
        campos: Sequence[Campo],
        color_fondo: str,
        color_panel: str,
        color_primario: str,
        color_texto: str,
        color_secundario: str,
        color_borde: str,
        on_crear: Accion | None = None,
        on_actualizar: Accion | None = None,
        on_eliminar: Callable[[dict[str, str]], None] | None = None,
    ) -> None:
        super().__init__(master, bg=color_fondo)
        self._columnas = tuple(columnas)
        self._campos = tuple(campos)
        self._color_fondo = color_fondo
        self._color_panel = color_panel
        self._color_primario = color_primario
        self._color_texto = color_texto
        self._color_secundario = color_secundario
        self._color_borde = color_borde
        self._on_crear = on_crear
        self._on_actualizar = on_actualizar
        self._on_eliminar = on_eliminar
        self._formulario: tk.Toplevel | None = None
        self._variables_formulario: dict[str, tk.StringVar] = {}
        self._opciones_formulario: dict[str, list[tuple[str, str]]] = {}
        self._registros_por_fila: dict[str, dict[str, Any]] = {}
        self._id_edicion: Any = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._crear_encabezado(titulo, descripcion)
        self._crear_lista()

    def _crear_encabezado(self, titulo: str, descripcion: str) -> None:
        encabezado = tk.Frame(self, bg=self._color_fondo)
        encabezado.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        encabezado.columnconfigure(0, weight=1)

        tk.Label(
            encabezado,
            text=titulo,
            bg=self._color_fondo,
            fg=self._color_texto,
            font=("TkDefaultFont", 15, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            encabezado,
            text=descripcion,
            bg=self._color_fondo,
            fg=self._color_secundario,
            font=("TkDefaultFont", 9),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        acciones = tk.Frame(encabezado, bg=self._color_fondo)
        acciones.grid(row=0, column=1, rowspan=2, sticky="e")
        self._crear_boton(
            acciones,
            "＋  Nuevo",
            self._abrir_formulario_nuevo,
            primario=True,
        ).pack(side="left", padx=(0, 8))
        self._crear_boton(
            acciones,
            "Editar",
            self._editar_seleccionado,
        ).pack(side="left", padx=(0, 8))
        self._crear_boton(
            acciones,
            "Eliminar",
            self._eliminar_seleccionado,
            secundario=True,
        ).pack(side="left")

    def _crear_lista(self) -> None:
        panel = tk.Frame(
            self,
            bg=self._color_panel,
            highlightbackground=self._color_borde,
            highlightthickness=1,
        )
        panel.grid(row=1, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        barra = tk.Frame(panel, bg=self._color_panel)
        barra.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        barra.columnconfigure(0, weight=1)
        tk.Label(
            barra,
            text="Registros",
            bg=self._color_panel,
            fg=self._color_texto,
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")

        self._cantidad = tk.Label(
            barra,
            text="0 registros",
            bg=self._color_panel,
            fg=self._color_secundario,
            font=("TkDefaultFont", 9),
        )
        self._cantidad.grid(row=0, column=1, sticky="e")

        tabla_frame = tk.Frame(panel, bg=self._color_panel)
        tabla_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        estilo = ttk.Style(self)
        estilo.configure(
            "Catalogo.Treeview",
            rowheight=32,
            font=("TkDefaultFont", 9),
            background=self._color_panel,
            fieldbackground=self._color_panel,
            foreground=self._color_texto,
        )
        estilo.configure(
            "Catalogo.Treeview.Heading",
            background="#E8F0EB",
            foreground=self._color_primario,
            font=("TkDefaultFont", 9, "bold"),
            relief="flat",
            padding=(10, 8),
        )
        estilo.map(
            "Catalogo.Treeview",
            background=[("selected", "#E3ECE6"), ("active", "#D7E8DE")],
            foreground=[("selected", self._color_texto), ("active", self._color_texto)],
        )

        claves = [clave for clave, _ in self._columnas]
        self._tabla = ttk.Treeview(
            tabla_frame,
            columns=claves,
            show="headings",
            style="Catalogo.Treeview",
            selectmode="browse",
        )
        self._tabla.tag_configure("fila-par", background="#F8FAF8")
        self._tabla.tag_configure("fila-impar", background="#FFFFFF")
        for clave, etiqueta in self._columnas:
            self._tabla.heading(clave, text=etiqueta, anchor="w")
            self._tabla.column(clave, width=130, minwidth=90, anchor="w")
        self._tabla.grid(row=0, column=0, sticky="nsew")

        barra_desplazamiento = ttk.Scrollbar(
            tabla_frame,
            orient="vertical",
            command=self._tabla.yview,
        )
        barra_desplazamiento.grid(row=0, column=1, sticky="ns")
        self._tabla.configure(yscrollcommand=barra_desplazamiento.set)
        self._tabla.bind("<Double-1>", self._editar_seleccionado)
        self._mostrar_estado_vacio()

    def _crear_boton(
        self,
        master: tk.Misc,
        texto: str,
        comando: Callable[[], None],
        *,
        primario: bool = False,
        secundario: bool = False,
    ) -> tk.Button:
        fondo = self._color_primario if primario else self._color_panel
        texto_color = "#FFFFFF" if primario else self._color_texto
        return tk.Button(
            master,
            text=texto,
            command=comando,
            cursor="hand2",
            relief="flat",
            borderwidth=0,
            padx=13,
            pady=8,
            bg=fondo,
            fg=texto_color,
            activebackground="#E9EEE9" if secundario else self._color_primario,
            activeforeground=self._color_texto if secundario else "#FFFFFF",
            font=("TkDefaultFont", 9, "bold" if primario else "normal"),
        )

    def _mostrar_estado_vacio(self) -> None:
        if self._tabla.get_children():
            return
        if hasattr(self, "_estado_vacio") and self._estado_vacio.winfo_exists():
            return
        self._estado_vacio = tk.Label(
            self._tabla.master,
            text="Todavía no hay registros para mostrar.",
            bg=self._color_panel,
            fg=self._color_secundario,
            font=("TkDefaultFont", 9),
        )
        self._estado_vacio.place(relx=0.5, rely=0.53, anchor="center")

    def mostrar_registros(self, registros: Sequence[Registro]) -> None:
        """Muestra datos suministrados por el controlador, sin consultarlos."""
        self._registros_por_fila.clear()
        for elemento in self._tabla.get_children():
            self._tabla.delete(elemento)
        if hasattr(self, "_estado_vacio") and self._estado_vacio.winfo_exists():
            self._estado_vacio.destroy()

        claves = [clave for clave, _ in self._columnas]
        for indice, registro in enumerate(registros):
            valores = []
            for clave in claves:
                valor = registro.get(clave, "")
                if clave in self._opciones_formulario:
                    valor = self._etiqueta_opcion(clave, valor)
                valores.append(str(valor))
            etiqueta_fila = "fila-par" if indice % 2 == 0 else "fila-impar"
            fila = self._tabla.insert(
                "",
                "end",
                values=valores,
                tags=(etiqueta_fila,),
            )
            self._registros_por_fila[fila] = dict(registro)

        cantidad = len(registros)
        self._cantidad.configure(
            text=f"{cantidad} registro" + ("" if cantidad == 1 else "s")
        )
        self._mostrar_estado_vacio()

    def mostrar_error(self, mensaje: str) -> None:
        messagebox.showerror("No se pudo completar la operación", mensaje, parent=self)

    def mostrar_mensaje(self, mensaje: str) -> None:
        messagebox.showinfo("Recetario", mensaje, parent=self)

    def establecer_callbacks(
        self,
        *,
        on_crear: Accion | None = None,
        on_actualizar: Accion | None = None,
        on_eliminar: Callable[[dict[str, str]], None] | None = None,
    ) -> None:
        """Conecta los eventos visuales con las acciones del controlador."""
        self._on_crear = on_crear
        self._on_actualizar = on_actualizar
        self._on_eliminar = on_eliminar

    def establecer_opciones_formulario(
        self,
        campo: str,
        opciones: Sequence[tuple[Any, str]],
    ) -> None:
        self._opciones_formulario[campo] = [
            (str(identificador), etiqueta)
            for identificador, etiqueta in opciones
        ]

    def _etiqueta_opcion(self, campo: str, valor: Any) -> str:
        valor_texto = str(valor)
        return next(
            (
                etiqueta
                for identificador, etiqueta in self._opciones_formulario[campo]
                if identificador == valor_texto
            ),
            valor_texto,
        )

    def _abrir_formulario_nuevo(self) -> None:
        self._abrir_formulario("Nuevo registro")

    def _editar_seleccionado(self, _evento: tk.Event | None = None) -> None:
        seleccion = self._tabla.selection()
        if not seleccion:
            return
        registro = self._registros_por_fila[seleccion[0]].copy()
        self._id_edicion = registro.get(self._columnas[0][0])
        self._abrir_formulario("Editar registro", registro)

    def _eliminar_seleccionado(self) -> None:
        seleccion = self._tabla.selection()
        if not seleccion:
            return
        registro = self._registros_por_fila[seleccion[0]].copy()
        confirmado = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Deseas eliminar el registro seleccionado?",
            parent=self,
        )
        if not confirmado:
            return
        if self._on_eliminar is None:
            self._avisar_controlador_pendiente()
            return
        self._on_eliminar(registro)

    def _abrir_formulario(
        self,
        titulo: str,
        registro: Registro | None = None,
    ) -> None:
        if self._formulario is not None and self._formulario.winfo_exists():
            self._formulario.lift()
            return

        self._formulario = tk.Toplevel(self)
        formulario = self._formulario
        formulario.title(titulo)
        formulario.transient(self.winfo_toplevel())
        formulario.resizable(False, False)
        formulario.configure(bg=self._color_panel)
        formulario.columnconfigure(1, weight=1)
        formulario.protocol("WM_DELETE_WINDOW", self.cerrar_formulario)

        tk.Label(
            formulario,
            text=titulo,
            bg=self._color_panel,
            fg=self._color_texto,
            font=("TkDefaultFont", 14, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=24, pady=(22, 5))
        tk.Label(
            formulario,
            text="Completa los datos del catálogo.",
            bg=self._color_panel,
            fg=self._color_secundario,
            font=("TkDefaultFont", 9),
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=24, pady=(0, 16))

        self._variables_formulario = {}
        for fila, (clave, etiqueta) in enumerate(self._campos, start=2):
            tk.Label(
                formulario,
                text=etiqueta,
                bg=self._color_panel,
                fg=self._color_texto,
                font=("TkDefaultFont", 9),
            ).grid(row=fila, column=0, sticky="w", padx=(24, 12), pady=6)
            variable = tk.StringVar(
                value=(
                    ""
                    if registro is None
                    else self._etiqueta_opcion(clave, registro.get(clave, ""))
                    if clave in self._opciones_formulario
                    else str(registro.get(clave, ""))
                )
            )
            self._variables_formulario[clave] = variable
            if clave in self._opciones_formulario:
                widget = ttk.Combobox(
                    formulario,
                    textvariable=variable,
                    values=[
                        etiqueta
                        for _, etiqueta in self._opciones_formulario[clave]
                    ],
                    state="readonly",
                    width=36,
                )
            else:
                widget = ttk.Entry(
                    formulario,
                    textvariable=variable,
                    width=38,
                )
            widget.grid(row=fila, column=1, sticky="ew", padx=(0, 24), pady=6)

        barra = tk.Frame(formulario, bg=self._color_panel)
        barra.grid(
            row=len(self._campos) + 2,
            column=0,
            columnspan=2,
            sticky="e",
            padx=24,
            pady=(18, 22),
        )
        tk.Button(
            barra,
            text="Cancelar",
            command=self.cerrar_formulario,
            cursor="hand2",
            relief="flat",
            padx=14,
            pady=8,
            bg="#EEF0EC",
            fg=self._color_texto,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            barra,
            text="Guardar",
            command=lambda: self._enviar_formulario(registro is not None),
            cursor="hand2",
            relief="flat",
            padx=16,
            pady=8,
            bg=self._color_primario,
            fg="#FFFFFF",
        ).pack(side="right")

        formulario.update_idletasks()
        formulario.grab_set()
        formulario.focus_set()

    def _enviar_formulario(self, es_edicion: bool) -> None:
        valores = {
            clave: variable.get()
            for clave, variable in self._variables_formulario.items()
        }
        for clave, opciones in self._opciones_formulario.items():
            seleccion = valores.get(clave, "")
            identificador = next(
                (
                    identificador
                    for identificador, etiqueta in opciones
                    if etiqueta == seleccion
                ),
                None,
            )
            if identificador is None:
                self.mostrar_error(f"Selecciona un valor válido para {clave}.")
                return
            valores[clave] = identificador
        callback = self._on_actualizar if es_edicion else self._on_crear
        if callback is None:
            self._avisar_controlador_pendiente()
            return
        if es_edicion:
            valores[self._columnas[0][0]] = self._id_edicion
        callback(valores)

    def cerrar_formulario(self) -> None:
        """Cierra el formulario activo, llamado por cancelar o el controlador."""
        if self._formulario is not None and self._formulario.winfo_exists():
            self._formulario.grab_release()
            self._formulario.destroy()
        self._formulario = None
        self._variables_formulario.clear()
        self._id_edicion = None

    def _avisar_controlador_pendiente(self) -> None:
        messagebox.showinfo(
            "Acción pendiente",
            "Esta acción estará disponible cuando se conecte el controlador.",
            parent=self,
        )


class UnidadesVista(CatalogoFrame):
    def __init__(self, master: tk.Misc, **opciones: Any) -> None:
        super().__init__(
            master,
            titulo="Unidades de medida",
            descripcion="Unidades utilizadas para porciones e ingredientes.",
            columnas=(("id_unidad", "ID"), ("nombre", "Nombre"), ("abreviatura", "Abreviatura")),
            campos=(("nombre", "Nombre"), ("abreviatura", "Abreviatura")),
            **opciones,
        )


class CocinerosVista(CatalogoFrame):
    def __init__(self, master: tk.Misc, **opciones: Any) -> None:
        super().__init__(
            master,
            titulo="Cocineros",
            descripcion="Personas responsables de preparar los menús.",
            columnas=(("id_cocinero", "ID"), ("codigo", "Código"), ("nombre", "Nombre"), ("activo", "Estado")),
            campos=(("codigo", "Código"), ("nombre", "Nombre"), ("activo", "Estado (1 activo, 0 inactivo)")),
            **opciones,
        )


class IngredientesVista(CatalogoFrame):
    def __init__(self, master: tk.Misc, **opciones: Any) -> None:
        super().__init__(
            master,
            titulo="Ingredientes",
            descripcion="Insumos disponibles y su unidad base.",
            columnas=(
                ("id_ingrediente", "ID"),
                ("codigo", "Código"),
                ("nombre", "Nombre"),
                ("descripcion", "Descripción"),
                ("id_unidad", "Unidad base"),
            ),
            campos=(
                ("codigo", "Código"),
                ("nombre", "Nombre"),
                ("descripcion", "Descripción"),
                ("id_unidad", "Unidad base"),
            ),
            **opciones,
        )

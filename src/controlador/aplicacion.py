"""Conexión entre navegación, vistas y servicios del recetario."""

import csv
import sqlite3
import shutil
import subprocess
import tempfile
import threading
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox
from typing import Any

from src.configuracion import ruta_base_datos, ruta_esquema
from src.modelo.consultas import Consultas
from src.modelo.conversiones_unidades import (
    analizar_cantidad,
    convertir_cantidad,
    resolver_unidad,
    resolver_unidad_por_sufijo,
)
from src.modelo.daos import (
    CocineroDAO,
    IngredienteDAO,
    MenuBaseDAO,
    MenuBaseIngredienteDAO,
    MenuBaseResponsableDAO,
    MenuDiarioDAO,
    MenuDiarioIngredienteDAO,
    SalidaMenuCocinaDAO,
    UnidadMedidaDAO,
)
from src.modelo.services import (
    Cocinero,
    Ingrediente,
    MenuBase,
    MenuBaseIngrediente,
    MenuBaseResponsable,
    MenuDiario,
    MenuDiarioIngrediente,
    SalidaMenuCocina,
    UnidadMedida,
)
from src.vista.aplicacion import Aplicacion
from src.vista.catalogos import CatalogoFrame
from src.vista.menus_base import MenusBaseVista
from src.vista.planificacion_diaria import PlanificacionDiariaVista
from src.vista.produccion import ProduccionVista
from src.vista.reportes import ReportesVista


RUTA_BASE_DATOS = ruta_base_datos()
RUTA_ESQUEMA = ruta_esquema()


def inicializar_base_si_no_existe(
    ruta_db: str | Path = RUTA_BASE_DATOS,
    ruta_esquema: str | Path = RUTA_ESQUEMA,
) -> None:
    """Crea el esquema y los datos de ejemplo solo al crear una base nueva."""
    destino = Path(ruta_db)
    if destino.exists() and destino.stat().st_size:
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(destino)
    try:
        conexion.executescript(Path(ruta_esquema).read_text(encoding="utf-8"))
        conexion.commit()
    except sqlite3.Error:
        conexion.rollback()
        raise
    finally:
        conexion.close()


class ControladorCatalogos:
    """Coordina operaciones CRUD para unidades, cocineros e ingredientes."""

    CONFIGURACION = {
        "unidades": (UnidadMedida, UnidadMedidaDAO),
        "cocineros": (Cocinero, CocineroDAO),
        "ingredientes": (Ingrediente, IngredienteDAO),
    }

    def __init__(self, ruta_db: str | Path) -> None:
        self._ruta_db = ruta_db
        self._conectadas: set[int] = set()

    def conectar(self, seccion: str, vista: CatalogoFrame) -> None:
        if seccion not in self.CONFIGURACION:
            raise ValueError(f"Catálogo desconocido: {seccion}")
        if seccion == "ingredientes":
            unidades = UnidadMedida.listar(dao=UnidadMedidaDAO(self._ruta_db))
            vista.establecer_opciones_formulario(
                "id_unidad",
                [
                    (
                        unidad.id_unidad,
                        f"{unidad.nombre} ({unidad.abreviatura})",
                    )
                    for unidad in unidades
                ],
            )
        if id(vista) not in self._conectadas:
            vista.establecer_callbacks(
                on_crear=lambda valores: self.crear(seccion, vista, valores),
                on_actualizar=lambda valores: self.actualizar(seccion, vista, valores),
                on_eliminar=lambda valores: self.eliminar(seccion, vista, valores),
            )
            self._conectadas.add(id(vista))
        self.refrescar(seccion, vista)

    def _dependencias(self, seccion: str):
        servicio, tipo_dao = self.CONFIGURACION[seccion]
        return servicio, tipo_dao(self._ruta_db)

    def refrescar(self, seccion: str, vista: CatalogoFrame) -> None:
        servicio, dao = self._dependencias(seccion)
        vista.mostrar_registros([asdict(entidad) for entidad in servicio.listar(dao=dao)])

    def crear(self, seccion: str, vista: CatalogoFrame, valores: dict[str, str]) -> None:
        servicio, dao = self._dependencias(seccion)
        try:
            self._crear_entidad(servicio, valores, dao).insertar()
        except (sqlite3.Error, TypeError, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        vista.cerrar_formulario()
        self.refrescar(seccion, vista)
        vista.mostrar_mensaje("Registro creado correctamente.")

    def actualizar(
        self,
        seccion: str,
        vista: CatalogoFrame,
        valores: dict[str, str],
    ) -> None:
        servicio, dao = self._dependencias(seccion)
        try:
            entidad = self._crear_entidad(servicio, valores, dao)
            if not entidad.actualizar():
                vista.mostrar_error("El registro ya no existe.")
                return
        except (sqlite3.Error, TypeError, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        vista.cerrar_formulario()
        self.refrescar(seccion, vista)
        vista.mostrar_mensaje("Registro actualizado correctamente.")

    def eliminar(
        self,
        seccion: str,
        vista: CatalogoFrame,
        valores: dict[str, str],
    ) -> None:
        servicio, dao = self._dependencias(seccion)
        try:
            if not self._crear_entidad(servicio, valores, dao).eliminar():
                vista.mostrar_error("El registro ya no existe.")
                return
        except (sqlite3.Error, TypeError, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        self.refrescar(seccion, vista)

    def _crear_entidad(self, servicio, valores: dict[str, Any], dao):
        enteros = {"id_unidad", "id_cocinero", "id_ingrediente", "activo"}
        datos = {}
        for clave, valor in valores.items():
            if clave not in enteros or valor in (None, ""):
                datos[clave] = valor
            elif clave == "id_unidad" and servicio is Ingrediente:
                datos[clave] = self._resolver_unidad(valor)
            else:
                datos[clave] = int(valor)
        return servicio(**datos, dao=dao)

    def _resolver_unidad(self, seleccion: Any) -> int:
        texto = str(seleccion).strip()
        for unidad in UnidadMedida.listar(dao=UnidadMedidaDAO(self._ruta_db)):
            if texto in (
                str(unidad.id_unidad),
                unidad.nombre,
                f"{unidad.nombre} ({unidad.abreviatura})",
            ):
                return int(unidad.id_unidad)
        raise ValueError(f"Selecciona una unidad base válida: {texto}")


class ControladorMenusBase:
    """Coordina el menú y las selecciones de responsables e ingredientes."""

    def __init__(self, ruta_db: str | Path) -> None:
        self._dao_menu = MenuBaseDAO(ruta_db)
        self._dao_responsables = MenuBaseResponsableDAO(ruta_db)
        self._dao_ingredientes_menu = MenuBaseIngredienteDAO(ruta_db)
        self._dao_unidades = UnidadMedidaDAO(ruta_db)
        self._dao_cocineros = CocineroDAO(ruta_db)
        self._dao_ingredientes = IngredienteDAO(ruta_db)

    def conectar(self, vista: MenusBaseVista) -> None:
        vista.establecer_callbacks(
            on_crear=lambda valores: self.crear(vista, valores),
            on_actualizar=lambda valores: self.actualizar(vista, valores),
            on_eliminar=lambda valores: self.eliminar(vista, valores),
        )
        self.refrescar(vista)

    def refrescar(self, vista: MenusBaseVista) -> None:
        unidades = [asdict(item) for item in UnidadMedida.listar(dao=self._dao_unidades)]
        cocineros = [asdict(item) for item in Cocinero.listar(dao=self._dao_cocineros)]
        ingredientes = [
            asdict(item) for item in Ingrediente.listar(dao=self._dao_ingredientes)
        ]
        vista.establecer_opciones(
            unidades=unidades,
            cocineros=cocineros,
            ingredientes=ingredientes,
        )
        responsables: dict[int, list[int]] = {}
        for relacion in MenuBaseResponsable.listar(dao=self._dao_responsables):
            responsables.setdefault(relacion.id_menu_base, []).append(relacion.id_cocinero)
        ingredientes_menu: dict[int, list[int]] = {}
        for relacion in MenuBaseIngrediente.listar(
            dao=self._dao_ingredientes_menu
        ):
            ingredientes_menu.setdefault(relacion.id_menu_base, []).append(
                relacion.id_ingrediente
            )
        unidades_por_id = {item["id_unidad"]: item for item in unidades}
        cocineros_por_id = {item["id_cocinero"]: item for item in cocineros}
        ingredientes_por_id = {item["id_ingrediente"]: item for item in ingredientes}
        menus = []
        for menu in MenuBase.listar(dao=self._dao_menu):
            fila = asdict(menu)
            fila["unidad"] = unidades_por_id.get(menu.id_unidad, {}).get("nombre", "")
            fila["responsables"] = responsables.get(menu.id_menu_base, [])
            fila["responsables_texto"] = ", ".join(
                cocineros_por_id.get(key, {}).get("nombre", "")
                for key in fila["responsables"]
            )
            fila["ingredientes"] = ingredientes_menu.get(menu.id_menu_base, [])
            fila["ingredientes_texto"] = ", ".join(
                ingredientes_por_id.get(key, {}).get("nombre", "")
                for key in fila["ingredientes"]
            )
            menus.append(fila)
        vista.mostrar_menus(menus)

    def crear(self, vista: MenusBaseVista, valores: dict[str, Any]) -> None:
        try:
            self._validar_ingredientes(valores)
            menu = self._construir_menu(valores)
            with self._dao_menu.transaccion() as conexion:
                menu.insertar_en(conexion)
                self._guardar_relaciones(menu.id_menu_base, valores, conexion)
        except (sqlite3.Error, TypeError, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        vista.cerrar_formulario()
        self.refrescar(vista)
        vista.mostrar_mensaje("Menú base creado correctamente.")

    def actualizar(self, vista: MenusBaseVista, valores: dict[str, Any]) -> None:
        try:
            self._validar_ingredientes(valores)
            menu = self._construir_menu(valores)
            menu.id_menu_base = int(valores["id_menu_base"])
            with self._dao_menu.transaccion() as conexion:
                if not menu.actualizar_en(conexion):
                    raise ValueError("El menú ya no existe.")
                self._guardar_relaciones(
                    menu.id_menu_base,
                    valores,
                    conexion,
                    reemplazar=True,
                )
        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        vista.cerrar_formulario()
        self.refrescar(vista)
        vista.mostrar_mensaje("Menú base actualizado correctamente.")

    def eliminar(self, vista: MenusBaseVista, valores: dict[str, Any]) -> None:
        try:
            menu = MenuBase(
                id_menu_base=int(valores["id_menu_base"]),
                codigo=str(valores["codigo"]),
                nombre=str(valores["nombre"]),
                porcion=float(valores["porcion"]),
                id_unidad=int(valores["id_unidad"]),
                dao=self._dao_menu,
            )
            if not menu.eliminar():
                vista.mostrar_error("El menú ya no existe.")
                return
        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        self.refrescar(vista)

    def _construir_menu(self, valores: dict[str, Any]) -> MenuBase:
        id_unidad = valores["id_unidad"]
        if not isinstance(id_unidad, int):
            id_unidad = self._resolver_id(
                id_unidad,
                UnidadMedida.listar(dao=self._dao_unidades),
                "id_unidad",
                lambda item: (
                    f"{item.id_unidad} — {item.nombre} ({item.abreviatura})"
                ),
            )
        return MenuBase(
            codigo=str(valores["codigo"]).strip(),
            nombre=str(valores["nombre"]).strip(),
            porcion=float(valores["porcion"]),
            id_unidad=int(id_unidad),
            descripcion=str(valores.get("descripcion", "")).strip() or None,
            dao=self._dao_menu,
        )

    @staticmethod
    def _validar_ingredientes(valores: dict[str, Any]) -> None:
        ingredientes = valores.get("ingredientes", [])
        if not ingredientes:
            raise ValueError("Selecciona al menos un ingrediente para el menú.")
        identificadores = [int(identificador) for identificador in ingredientes]
        if len(identificadores) != len(set(identificadores)):
            raise ValueError("No se puede agregar dos veces el mismo ingrediente.")

    @staticmethod
    def _resolver_id(seleccion: Any, elementos, clave: str, etiqueta) -> int:
        for elemento in elementos:
            if str(seleccion) == etiqueta(elemento):
                return getattr(elemento, clave)
        return int(seleccion)

    def _guardar_relaciones(
        self,
        id_menu: int,
        valores: dict[str, Any],
        conexion: sqlite3.Connection,
        *,
        reemplazar: bool = False,
    ) -> None:
        if reemplazar:
            for servicio, dao in (
                (MenuBaseResponsable, self._dao_responsables),
                (MenuBaseIngrediente, self._dao_ingredientes_menu),
            ):
                for relacion in servicio.listar(dao=dao):
                    if relacion.id_menu_base == id_menu:
                        relacion.eliminar_en(conexion)
        for id_cocinero in valores.get("responsables", []):
            MenuBaseResponsable(
                id_menu_base=id_menu,
                id_cocinero=int(id_cocinero),
                dao=self._dao_responsables,
            ).insertar_en(conexion)
        for id_ingrediente in valores.get("ingredientes", []):
            MenuBaseIngrediente(
                id_menu_base=id_menu,
                id_ingrediente=int(id_ingrediente),
                dao=self._dao_ingredientes_menu,
            ).insertar_en(conexion)


class ControladorPlanificacion:
    def __init__(self, ruta_db: str | Path) -> None:
        self._dao_menu_diario = MenuDiarioDAO(ruta_db)
        self._dao_menu = MenuBaseDAO(ruta_db)
        self._dao_ingredientes_menu = MenuBaseIngredienteDAO(ruta_db)
        self._dao_unidades = UnidadMedidaDAO(ruta_db)
        self._dao_ingredientes = IngredienteDAO(ruta_db)
        self._dao_detalles = MenuDiarioIngredienteDAO(ruta_db)

    def conectar(self, vista: PlanificacionDiariaVista) -> None:
        vista.establecer_callbacks(
            on_consultar=lambda filtros: self.consultar(vista, filtros),
            on_guardar=lambda valores: self.guardar(vista, valores),
        )
        self.refrescar_opciones(vista)

    def refrescar_opciones(self, vista: PlanificacionDiariaVista) -> None:
        ingredientes_por_menu: dict[int, list[int]] = {}
        for relacion in MenuBaseIngrediente.listar(dao=self._dao_ingredientes_menu):
            ingredientes_por_menu.setdefault(relacion.id_menu_base, []).append(
                relacion.id_ingrediente
            )
        menus = [
            {
                **asdict(item),
                "nombre": item.nombre,
                "ingredientes": ingredientes_por_menu.get(item.id_menu_base, []),
            }
            for item in MenuBase.listar(dao=self._dao_menu)
        ]
        unidades = [asdict(item) for item in UnidadMedida.listar(dao=self._dao_unidades)]
        ingredientes = [
            asdict(item) for item in Ingrediente.listar(dao=self._dao_ingredientes)
        ]
        vista.establecer_opciones(
            menus=menus,
            unidades=unidades,
            ingredientes=ingredientes,
        )

    def consultar(self, vista: PlanificacionDiariaVista, filtros: dict[str, str]) -> None:
        try:
            fecha_filtro = date.fromisoformat(filtros["fecha"])
            unidades = {
                item.id_unidad: item.nombre
                for item in UnidadMedida.listar(dao=self._dao_unidades)
            }
            nombres = {
                item.id_menu_base: item.nombre
                for item in MenuBase.listar(dao=self._dao_menu)
            }
            registros = [
                {
                    **asdict(item),
                    "menu": nombres.get(item.id_menu_base, ""),
                    "unidad": unidades.get(item.id_unidad_porcion, ""),
                }
                for item in MenuDiario.listar(dao=self._dao_menu_diario)
                if item.fecha == fecha_filtro
            ]
            vista.mostrar_planificaciones(registros)
        except (sqlite3.Error, ValueError) as error:
            vista.mostrar_error(str(error))

    def guardar(self, vista: PlanificacionDiariaVista, valores: dict[str, Any]) -> None:
        try:
            fecha = date.fromisoformat(str(valores["fecha"]))
            menu_base = MenuBase.obtener(
                int(valores["id_menu_base"]),
                dao=self._dao_menu,
            )
            if menu_base is None:
                raise ValueError("El menú base seleccionado ya no existe.")
            if menu_base.porcion <= 0:
                raise ValueError("La porción del menú base debe ser mayor que cero.")
            detalles = [
                {
                    "id_ingrediente": int(item["id_ingrediente"]),
                    "cantidad": float(item["cantidad"]),
                    "id_unidad": int(item["id_unidad"]),
                }
                for item in valores.get("ingredientes", [])
            ]
            if any(item["cantidad"] <= 0 for item in detalles):
                raise ValueError("Las cantidades utilizadas deben ser mayores que cero.")
            if len({item["id_ingrediente"] for item in detalles}) != len(detalles):
                raise ValueError("No se puede repetir un ingrediente en la preparación.")

            menu = MenuDiario(
                id_menu_base=menu_base.id_menu_base,
                fecha=fecha,
                porcion=menu_base.porcion,
                id_unidad_porcion=menu_base.id_unidad,
                dao=self._dao_menu_diario,
            )
            with self._dao_menu_diario.transaccion() as conexion:
                menu.insertar_en(conexion)
                for detalle in detalles:
                    MenuDiarioIngrediente(
                        id_menu_diario=menu.id_menu_diario,
                        dao=self._dao_detalles,
                        **detalle,
                    ).insertar_en(conexion)
        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        self.refrescar_opciones(vista)
        self.consultar(vista, {"fecha": fecha.isoformat()})
        vista.mostrar_mensaje("Planificación diaria guardada correctamente.")


class ControladorProduccion:
    def __init__(self, ruta_db: str | Path) -> None:
        self._dao_salidas = SalidaMenuCocinaDAO(ruta_db)
        self._dao_diarios = MenuDiarioDAO(ruta_db)
        self._dao_menus = MenuBaseDAO(ruta_db)
        self._dao_unidades = UnidadMedidaDAO(ruta_db)

    def conectar(self, vista: ProduccionVista) -> None:
        vista.establecer_callbacks(
            on_consultar=lambda filtros: self.consultar(vista, filtros),
            on_registrar=lambda valores: self.registrar(vista, valores),
            on_actualizar=lambda valores: self.actualizar(vista, valores),
            on_eliminar=lambda valores: self.eliminar(vista, valores),
            on_calcular_porciones=self.calcular_porciones,
        )
        self.refrescar_opciones(vista)
        self.consultar(vista, {"fecha": date.today().isoformat()})

    def refrescar_opciones(self, vista: ProduccionVista) -> None:
        nombres = {
            item.id_menu_base: item.nombre
            for item in MenuBase.listar(dao=self._dao_menus)
        }
        diarios = [
            {**asdict(item), "menu": nombres.get(item.id_menu_base, "")}
            for item in MenuDiario.listar(dao=self._dao_diarios)
        ]
        unidades = [asdict(item) for item in UnidadMedida.listar(dao=self._dao_unidades)]
        vista.establecer_opciones(menus_diarios=diarios, unidades=unidades)

    def consultar(self, vista: ProduccionVista, filtros: dict[str, str]) -> None:
        try:
            vista.mostrar_salidas(self._salidas_para(filtros.get("fecha", "")))
        except (sqlite3.Error, ValueError) as error:
            vista.mostrar_error(str(error))

    def registrar(self, vista: ProduccionVista, valores: dict[str, str]) -> None:
        try:
            fecha_hora = (
                datetime.fromisoformat(valores["fecha_hora"])
                if valores.get("fecha_hora")
                else datetime.now()
            )
            cantidad, id_unidad, porciones = self._calcular_produccion(valores)
            salida = SalidaMenuCocina(
                id_menu_diario=int(valores["id_menu_diario"]),
                fecha_hora=fecha_hora,
                cantidad_producida=cantidad,
                id_unidad=id_unidad,
                cantidad_porciones=porciones,
                dao=self._dao_salidas,
            )
            salida.insertar()
        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        self.refrescar_opciones(vista)
        self.consultar(vista, {"fecha": fecha_hora.date().isoformat()})
        vista.mostrar_mensaje("Producción registrada correctamente.")

    def actualizar(self, vista: ProduccionVista, valores: dict[str, str]) -> None:
        try:
            fecha_hora = datetime.fromisoformat(valores["fecha_hora"])
            cantidad, id_unidad, porciones = self._calcular_produccion(valores)
            fecha_consulta = valores.get("fecha_consulta", "")
            if not fecha_consulta:
                menu_diario = MenuDiario.obtener(
                    int(valores["id_menu_diario"]),
                    dao=self._dao_diarios,
                )
                if menu_diario is None:
                    raise ValueError("El menú planificado seleccionado ya no existe.")
                fecha_consulta = menu_diario.fecha.isoformat()
            salida = SalidaMenuCocina(
                id_salida=int(valores["id_salida"]),
                id_menu_diario=int(valores["id_menu_diario"]),
                fecha_hora=fecha_hora,
                cantidad_producida=cantidad,
                id_unidad=id_unidad,
                cantidad_porciones=porciones,
                dao=self._dao_salidas,
            )
            if not salida.actualizar():
                vista.mostrar_error("El registro de producción ya no existe.")
                return
        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        vista.finalizar_edicion()
        self.refrescar_opciones(vista)
        self.consultar(vista, {"fecha": fecha_consulta})
        vista.mostrar_mensaje("Producción actualizada correctamente.")

    def eliminar(self, vista: ProduccionVista, valores: dict[str, Any]) -> None:
        try:
            if not self._dao_salidas.eliminar(int(valores["id_salida"])):
                vista.mostrar_error("El registro de producción ya no existe.")
                return
        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        self.consultar(
            vista,
            {
                "fecha": str(
                    valores.get("fecha_filtro")
                    or valores.get("fecha_planificacion")
                    or ""
                )
            },
        )
        vista.mostrar_mensaje("Producción eliminada correctamente.")

    def calcular_porciones(self, valores: dict[str, str]) -> str:
        if not valores.get("id_menu_diario") or not valores.get("cantidad_producida"):
            return ""
        try:
            _, _, porciones = self._calcular_produccion(valores)
        except (sqlite3.Error, KeyError, TypeError, ValueError):
            return ""
        return str(porciones)

    def _calcular_produccion(self, valores: dict[str, str]) -> tuple[float, int, float]:
        id_menu_diario = int(valores["id_menu_diario"])
        menu_diario = MenuDiario.obtener(id_menu_diario, dao=self._dao_diarios)
        if menu_diario is None:
            raise ValueError("El menú planificado seleccionado ya no existe.")

        cantidad, sufijo_unidad = analizar_cantidad(valores["cantidad_producida"])
        unidades = [asdict(item) for item in UnidadMedida.listar(dao=self._dao_unidades)]
        if sufijo_unidad:
            unidad_origen = resolver_unidad_por_sufijo(unidades, sufijo_unidad)
        else:
            unidad_origen = resolver_unidad(unidades, valores["id_unidad"])
        unidad_destino = resolver_unidad(
            unidades,
            menu_diario.id_unidad_porcion,
        )
        cantidad_convertida = convertir_cantidad(
            cantidad,
            unidad_origen,
            unidad_destino,
        )
        porciones = cantidad_convertida / menu_diario.porcion
        if porciones <= 0:
            raise ValueError("La cantidad producida no genera porciones válidas.")
        return cantidad_convertida, int(menu_diario.id_unidad_porcion), porciones

    def _salidas_para(self, filtro_fecha: str) -> list[dict[str, Any]]:
        desde = date.fromisoformat(filtro_fecha) if filtro_fecha else None
        diarios = {
            item.id_menu_diario: item
            for item in MenuDiario.listar(dao=self._dao_diarios)
        }
        menus = {
            item.id_menu_base: item.nombre
            for item in MenuBase.listar(dao=self._dao_menus)
        }
        unidades = {
            item.id_unidad: item.nombre
            for item in UnidadMedida.listar(dao=self._dao_unidades)
        }
        resultado = []
        for salida in SalidaMenuCocina.listar(dao=self._dao_salidas):
            diario = diarios.get(salida.id_menu_diario)
            if diario is None or (desde and diario.fecha != desde):
                continue
            resultado.append(
                {
                    **asdict(salida),
                    "menu": menus.get(diario.id_menu_base, ""),
                    "unidad": unidades.get(salida.id_unidad, ""),
                    "fecha_planificacion": diario.fecha.isoformat(),
                }
            )
        return resultado


class ControladorReportes:
    """Obtiene datos de reportes, muestra vistas previas y exporta resultados."""

    CONFIGURACION = {
        "Menús base": (
            ("Código", "Menú", "Porción", "Unidad", "Descripción", "Responsables", "Ingredientes"),
            Consultas.reporte_menus_base,
            (),
        ),
        "Planificación e ingredientes utilizados": (
            ("Fecha", "Código menú", "Menú", "Porción", "Unidad porción",
             "Código ingrediente", "Ingrediente", "Cantidad utilizada", "Unidad utilizada"),
            Consultas.reporte_planificacion,
            ("fecha_desde", "fecha_hasta", "fecha_desde", "fecha_hasta"),
        ),
        "Producción de cocina": (
            ("Fecha", "Hora", "Código menú", "Menú", "Cantidad producida", "Unidad", "Porciones"),
            Consultas.reporte_produccion,
            ("fecha_desde", "fecha_hasta", "fecha_desde", "fecha_hasta"),
        ),
    }

    def __init__(self, ruta_db: str | Path) -> None:
        self._dao = UnidadMedidaDAO(ruta_db)
        self._resultados: tuple[tuple[str, ...], list[tuple[Any, ...]]] | None = None

    def conectar(self, vista: ReportesVista) -> None:
        vista.establecer_callbacks(
            on_generar=lambda filtros: self.generar(vista, filtros),
            on_imprimir=lambda filtros: self.imprimir(vista, filtros),
            on_exportar=lambda datos: self.exportar(vista, datos),
        )

    def generar(self, vista: ReportesVista, filtros: dict[str, str]) -> None:
        self._resultados = None
        try:
            columnas, consulta_factory, _ = self.CONFIGURACION[filtros["tipo_reporte"]]
            parametros: tuple[Any, ...] = ()
            if filtros["tipo_reporte"] != "Menús base":
                inicio = filtros["fecha_desde"]
                fin = filtros["fecha_hasta"]
                if inicio:
                    date.fromisoformat(inicio)
                if fin:
                    date.fromisoformat(fin)
                if inicio and fin and inicio > fin:
                    raise ValueError("La fecha inicial no puede ser posterior a la fecha final.")
                parametros = (inicio, inicio, fin, fin)
            filas_db = self._dao.ejecutar_consulta(
                consulta_factory(),
                parametros,
            )
        except (KeyError, sqlite3.Error, ValueError) as error:
            vista.mostrar_error(str(error))
            return
        filas = [tuple(fila.values()) for fila in filas_db]
        self._resultados = (columnas, filas)
        vista.mostrar_resultados(columnas, filas)

    def exportar(self, vista: ReportesVista, datos: dict[str, str]) -> None:
        self.generar(vista, datos)
        if self._resultados is None:
            return
        columnas, filas = self._resultados
        try:
            if datos["formato"] == "csv":
                self._exportar_csv(datos["ruta"], columnas, filas)
            elif datos["formato"] == "pdf":
                self._exportar_pdf(datos["ruta"], datos["tipo_reporte"], columnas, filas)
            else:
                raise ValueError(f"Formato no soportado: {datos['formato']}")
        except (OSError, ValueError, ImportError) as error:
            vista.mostrar_error(str(error))
            return
        vista.mostrar_mensaje(f"Reporte exportado correctamente:\n{datos['ruta']}")

    def imprimir(self, vista: ReportesVista, filtros: dict[str, str]) -> None:
        self.generar(vista, filtros)
        if self._resultados is None:
            return
        columnas, filas = self._resultados
        try:
            comando = shutil.which("lp") or shutil.which("lpr")
            if comando is None:
                raise OSError("No se encontró el comando de impresión lp ni lpr.")
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as archivo:
                ruta = Path(archivo.name)
            self._exportar_pdf(
                str(ruta),
                filtros["tipo_reporte"],
                columnas,
                filas,
            )
        except (OSError, ValueError, ImportError) as error:
            vista.mostrar_error(str(error))
            return
        threading.Thread(
            target=self._enviar_a_impresora,
            args=(comando, ruta, vista),
            daemon=True,
        ).start()

    @staticmethod
    def _enviar_a_impresora(
        comando: str,
        ruta: Path,
        vista: ReportesVista,
    ) -> None:
        try:
            resultado = subprocess.run(
                [comando, str(ruta)],
                check=False,
                capture_output=True,
                text=True,
            )
            if resultado.returncode:
                raise OSError(
                    resultado.stderr.strip()
                    or "No se pudo enviar el reporte a la impresora."
                )
            mensaje = ("info", "Reporte enviado a la cola de impresión.")
        except OSError as error:
            mensaje = ("error", str(error))
        finally:
            ruta.unlink(missing_ok=True)

        def mostrar_resultado() -> None:
            if not vista.winfo_exists():
                return
            if mensaje[0] == "info":
                vista.mostrar_mensaje(mensaje[1])
            else:
                vista.mostrar_error(mensaje[1])

        if vista.winfo_exists():
            vista.after(0, mostrar_resultado)

    @staticmethod
    def _exportar_csv(
        ruta: str,
        columnas: tuple[str, ...],
        filas: list[tuple[Any, ...]],
    ) -> None:
        with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(columnas)
            escritor.writerows(filas)

    @staticmethod
    def _exportar_pdf(
        ruta: str,
        titulo: str,
        columnas: tuple[str, ...],
        filas: list[tuple[Any, ...]],
    ) -> None:
        from html import escape

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import landscape, letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except ModuleNotFoundError as error:
            if error.name is None or not error.name.startswith("reportlab"):
                raise
            raise ImportError(
                "No se encontró ReportLab en el intérprete activo. "
                "Instala las dependencias con 'pipenv install' y ejecuta "
                "la aplicación con 'pipenv run python src/main.py'. "
                "En VS Code, selecciona el intérprete del entorno Pipenv."
            ) from error

        estilos = getSampleStyleSheet()
        documento = SimpleDocTemplate(
            ruta,
            pagesize=landscape(letter),
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title=titulo,
        )
        contenido = [
            Paragraph(titulo, estilos["Title"]),
            Paragraph(
                f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                estilos["Normal"],
            ),
            Spacer(1, 8 * mm),
        ]
        contenido_tabla = [
            [Paragraph(escape(columna), estilos["Normal"]) for columna in columnas]
        ]
        contenido_tabla.extend(
            [
                [
                    Paragraph(escape(str(valor)) if valor is not None else "", estilos["Normal"])
                    for valor in fila
                ]
                for fila in filas
            ]
        )
        tabla = Table(
            contenido_tabla,
            repeatRows=1,
            hAlign="LEFT",
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#234B3B")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("LEADING", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9DED9")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5F2")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        contenido.append(tabla)
        documento.build(contenido)


class ControladorAplicacion:
    """Conecta las secciones visuales a los controladores de cada flujo."""

    def __init__(self, aplicacion: Aplicacion, ruta_db: str | Path) -> None:
        self._aplicacion = aplicacion
        self._ruta_db = ruta_db
        self._catalogos = ControladorCatalogos(ruta_db)
        self._menus = ControladorMenusBase(ruta_db)
        self._planificacion = ControladorPlanificacion(ruta_db)
        self._produccion = ControladorProduccion(ruta_db)
        self._reportes = ControladorReportes(ruta_db)
        self._dao_menus_inicio = MenuBaseDAO(ruta_db)
        self._dao_diarios_inicio = MenuDiarioDAO(ruta_db)
        self._dao_salidas_inicio = SalidaMenuCocinaDAO(ruta_db)
        aplicacion.establecer_callback_navegacion(self.al_cambiar_seccion)

    def al_cambiar_seccion(self, seccion: str) -> None:
        try:
            vista = self._aplicacion.obtener_vista(seccion)
        except ValueError:
            return
        if seccion == "inicio":
            try:
                self.refrescar_inicio(vista)
            except sqlite3.Error as error:
                messagebox.showerror(
                    "No se pudo cargar el resumen",
                    str(error),
                    parent=self._aplicacion,
                )
            return
        try:
            if seccion in ControladorCatalogos.CONFIGURACION:
                self._catalogos.conectar(seccion, vista)
            elif seccion == "menus":
                self._menus.conectar(vista)
            elif seccion == "planificacion":
                self._planificacion.conectar(vista)
            elif seccion == "produccion":
                self._produccion.conectar(vista)
            elif seccion == "reportes":
                self._reportes.conectar(vista)
        except sqlite3.Error as error:
            vista.mostrar_error(str(error))

    def refrescar_inicio(self, vista: Aplicacion) -> None:
        hoy = date.today()
        menus_base = MenuBase.listar(dao=self._dao_menus_inicio)
        planificaciones = [
            item
            for item in MenuDiario.listar(dao=self._dao_diarios_inicio)
            if item.fecha == hoy
        ]
        producciones_hoy = [
            salida
            for salida in SalidaMenuCocina.listar(dao=self._dao_salidas_inicio)
            if salida.fecha_hora.date() == hoy
        ]
        vista.mostrar_resumen_inicio(
            {
                "menus": len(menus_base),
                "planificaciones": len(planificaciones),
                "producciones": len(producciones_hoy),
            }
        )


def crear_controlador(
    aplicacion: Aplicacion,
    ruta_db: str | Path = RUTA_BASE_DATOS,
) -> ControladorAplicacion:
    """Prepara una base nueva e instancia los controladores de la aplicación."""
    try:
        inicializar_base_si_no_existe(ruta_db)
    except (OSError, sqlite3.Error) as error:
        messagebox.showerror(
            "Error de base de datos",
            str(error),
            parent=aplicacion,
        )
        raise
    return ControladorAplicacion(aplicacion, ruta_db)

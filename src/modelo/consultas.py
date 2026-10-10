"""Generación centralizada de consultas SQL para los DAO."""


class Consultas:
    """Construye consultas CRUD usando identificadores definidos por los DAO."""

    @staticmethod
    def activar_claves_foraneas() -> str:
        return "PRAGMA foreign_keys = ON"

    @staticmethod
    def insertar(tabla: str, columnas: tuple[str, ...]) -> str:
        nombres_columnas = ", ".join(columnas)
        marcadores = ", ".join("?" for _ in columnas)
        return f"INSERT INTO {tabla} ({nombres_columnas}) VALUES ({marcadores})"

    @staticmethod
    def obtener_por_clave(
        tabla: str,
        columnas: tuple[str, ...],
        claves_primarias: tuple[str, ...],
    ) -> str:
        condicion = " AND ".join(f"{clave} = ?" for clave in claves_primarias)
        return f"SELECT {', '.join(columnas)} FROM {tabla} WHERE {condicion}"

    @staticmethod
    def listar(
        tabla: str,
        columnas: tuple[str, ...],
        claves_primarias: tuple[str, ...],
    ) -> str:
        orden = ", ".join(claves_primarias)
        return f"SELECT {', '.join(columnas)} FROM {tabla} ORDER BY {orden}"

    @staticmethod
    def actualizar(
        tabla: str,
        columnas: tuple[str, ...],
        claves_primarias: tuple[str, ...],
    ) -> str:
        asignaciones = ", ".join(f"{columna} = ?" for columna in columnas)
        condicion = " AND ".join(f"{clave} = ?" for clave in claves_primarias)
        return f"UPDATE {tabla} SET {asignaciones} WHERE {condicion}"

    @staticmethod
    def eliminar(tabla: str, claves_primarias: tuple[str, ...]) -> str:
        condicion = " AND ".join(f"{clave} = ?" for clave in claves_primarias)
        return f"DELETE FROM {tabla} WHERE {condicion}"

    @staticmethod
    def reporte_menus_base() -> str:
        return """
            SELECT
                mb.codigo AS codigo_menu,
                mb.nombre AS menu,
                mb.porcion AS porcion,
                um.abreviatura AS unidad_porcion,
                mb.descripcion AS descripcion,
                COALESCE(GROUP_CONCAT(DISTINCT c.nombre), '') AS responsables,
                COALESCE(GROUP_CONCAT(DISTINCT i.nombre), '') AS ingredientes
            FROM MenuBase AS mb
            JOIN UnidadMedida AS um ON um.id_unidad = mb.id_unidad
            LEFT JOIN MenuBase_Responsable AS mbr
                ON mbr.id_menu_base = mb.id_menu_base
            LEFT JOIN Cocinero AS c ON c.id_cocinero = mbr.id_cocinero
            LEFT JOIN MenuBase_Ingrediente AS mbi
                ON mbi.id_menu_base = mb.id_menu_base
            LEFT JOIN Ingrediente AS i ON i.id_ingrediente = mbi.id_ingrediente
            GROUP BY mb.id_menu_base
            ORDER BY mb.nombre
        """

    @staticmethod
    def reporte_planificacion() -> str:
        return """
            SELECT
                md.fecha AS fecha,
                mb.codigo AS codigo_menu,
                mb.nombre AS menu,
                md.porcion AS porcion,
                ump.abreviatura AS unidad_porcion,
                i.codigo AS codigo_ingrediente,
                i.nombre AS ingrediente,
                mdi.cantidad AS cantidad_utilizada,
                um.abreviatura AS unidad_utilizada
            FROM MenuDiario AS md
            JOIN MenuBase AS mb ON mb.id_menu_base = md.id_menu_base
            JOIN UnidadMedida AS ump ON ump.id_unidad = md.id_unidad_porcion
            LEFT JOIN MenuDiario_Ingrediente AS mdi
                ON mdi.id_menu_diario = md.id_menu_diario
            LEFT JOIN Ingrediente AS i ON i.id_ingrediente = mdi.id_ingrediente
            LEFT JOIN UnidadMedida AS um ON um.id_unidad = mdi.id_unidad
            WHERE (? = '' OR md.fecha >= ?)
              AND (? = '' OR md.fecha <= ?)
            ORDER BY md.fecha, mb.nombre, i.nombre
        """

    @staticmethod
    def reporte_produccion() -> str:
        return """
            SELECT
                date(sm.fecha_hora) AS fecha,
                time(sm.fecha_hora) AS hora,
                mb.codigo AS codigo_menu,
                mb.nombre AS menu,
                sm.cantidad_producida AS cantidad_producida,
                um.abreviatura AS unidad,
                sm.cantidad_porciones AS porciones
            FROM SalidaMenuCocina AS sm
            JOIN MenuDiario AS md ON md.id_menu_diario = sm.id_menu_diario
            JOIN MenuBase AS mb ON mb.id_menu_base = md.id_menu_base
            JOIN UnidadMedida AS um ON um.id_unidad = sm.id_unidad
            WHERE (? = '' OR date(sm.fecha_hora) >= ?)
              AND (? = '' OR date(sm.fecha_hora) <= ?)
            ORDER BY sm.fecha_hora, mb.nombre
        """
-- ============================================================
-- Base de datos para comedor: menús base, planificación diaria
-- y registro de producción en cocina.
-- Motor: SQLite 3
-- ============================================================
PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. TABLAS CATÁLOGO
-- ============================================================
-- ------------------------------------------------------------
-- Tabla: UnidadMedida
-- Catálogo de unidades de medida.
-- Ejemplo: (1, 'gramo', 'g'), (2, 'mililitro', 'ml')
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS
    UnidadMedida (
        id_unidad INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        abreviatura TEXT NOT NULL UNIQUE
    );

-- ------------------------------------------------------------
-- Tabla: Cocinero
-- Personas responsables de preparar los menús base.
-- Ejemplo: (1, 'COC-001', 'Juan Pérez', 1)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS
    Cocinero (
        id_cocinero INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL,
        activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
    );

-- ------------------------------------------------------------
-- Tabla: Ingrediente
-- Insumos usados en las recetas. Cada ingrediente tiene una unidad base.
-- Ejemplo: (1, 'ING-001', 'Arroz', 'Arroz blanco grano largo', 1) -> 1 = gramo
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS
    Ingrediente (
        id_ingrediente INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        id_unidad INTEGER NOT NULL,
        FOREIGN KEY (id_unidad) REFERENCES UnidadMedida (id_unidad) ON DELETE RESTRICT
    );

-- ============================================================
-- 2. ENTIDADES PRINCIPALES
-- ============================================================
-- ------------------------------------------------------------
-- Tabla: MenuBase
-- Define un menú estándar y el tamaño de una porción servida al cliente.
-- Ejemplo: (1, 'MEN-001', 'Arroz con pollo', 200.0, 1, 'Plato fuerte') -> 200 g por porción.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS
    MenuBase (
        id_menu_base INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL UNIQUE,
        porcion REAL NOT NULL CHECK (porcion > 0),
        id_unidad INTEGER NOT NULL,
        descripcion TEXT,
        FOREIGN KEY (id_unidad) REFERENCES UnidadMedida (id_unidad) ON DELETE RESTRICT
    );

-- ------------------------------------------------------------
-- Tabla: MenuBase_Responsable
-- Relación N:M entre menús base y cocineros responsables.
-- Ejemplo: (1,1) -> El menú base 1 es responsabilidad del cocinero 1.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS
    MenuBase_Responsable (
        id_menu_base INTEGER NOT NULL,
        id_cocinero INTEGER NOT NULL,
        PRIMARY KEY (id_menu_base, id_cocinero),
        FOREIGN KEY (id_menu_base) REFERENCES MenuBase (id_menu_base) ON DELETE CASCADE,
        FOREIGN KEY (id_cocinero) REFERENCES Cocinero (id_cocinero) ON DELETE CASCADE
    );

-- ------------------------------------------------------------
-- Tabla: MenuBase_Ingrediente
-- Ingredientes asociados a un menú base; las cantidades reales se registran a diario.
-- Ejemplo: (1,1) -> El menú base 1 incluye el ingrediente 1.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS
    MenuBase_Ingrediente (
        id_menu_base INTEGER NOT NULL,
        id_ingrediente INTEGER NOT NULL,
        PRIMARY KEY (id_menu_base, id_ingrediente),
        FOREIGN KEY (id_menu_base) REFERENCES MenuBase (id_menu_base) ON DELETE CASCADE,
        FOREIGN KEY (id_ingrediente) REFERENCES Ingrediente (id_ingrediente) ON DELETE RESTRICT
    );

-- ============================================================
-- 3. PLANIFICACIÓN DIARIA
-- ============================================================
-- ------------------------------------------------------------
-- Tabla: MenuDiario
-- Planificación diaria de un menú base. Guarda snapshot de la porción usada.
-- Ejemplo: (1, 1, '2026-10-07', 200.0, 1) -> Menú base 1, 200 g por porción.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS
    MenuDiario (
        id_menu_diario INTEGER PRIMARY KEY AUTOINCREMENT,
        id_menu_base INTEGER NOT NULL,
        fecha DATE NOT NULL,
        porcion REAL NOT NULL CHECK (porcion > 0),
        id_unidad_porcion INTEGER NOT NULL,
        FOREIGN KEY (id_menu_base) REFERENCES MenuBase (id_menu_base) ON DELETE RESTRICT,
        FOREIGN KEY (id_unidad_porcion) REFERENCES UnidadMedida (id_unidad) ON DELETE RESTRICT,
        UNIQUE (fecha, id_menu_base)
    );

-- ------------------------------------------------------------
-- Tabla: MenuDiario_Ingrediente
-- Ingredientes realmente utilizados en la preparación diaria.
-- Ejemplo: (1,1,3000.0,1) -> Menú diario 1 usó 3000 g del ingrediente 1.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS
    MenuDiario_Ingrediente (
        id_menu_diario INTEGER NOT NULL,
        id_ingrediente INTEGER NOT NULL,
        cantidad REAL NOT NULL CHECK (cantidad > 0),
        id_unidad INTEGER NOT NULL,
        PRIMARY KEY (id_menu_diario, id_ingrediente),
        FOREIGN KEY (id_menu_diario) REFERENCES MenuDiario (id_menu_diario) ON DELETE CASCADE,
        FOREIGN KEY (id_ingrediente) REFERENCES Ingrediente (id_ingrediente) ON DELETE RESTRICT,
        FOREIGN KEY (id_unidad) REFERENCES UnidadMedida (id_unidad) ON DELETE RESTRICT
    );

-- ============================================================
-- 4. REGISTRO DE SALIDAS DE COCINA
-- ============================================================
-- ------------------------------------------------------------
-- Tabla: SalidaMenuCocina
-- Registra la producción de cocina: cantidad total y porciones resultantes.
-- cantidad_porciones = cantidad_producida / porcion del menú diario.
-- Ejemplo: (1,1,'2026-10-07 12:00:00',5000.0,1,25.0) -> 5000 g = 25 porciones de 200 g.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS
    SalidaMenuCocina (
        id_salida INTEGER PRIMARY KEY AUTOINCREMENT,
        id_menu_diario INTEGER NOT NULL,
        fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        cantidad_producida REAL NOT NULL CHECK (cantidad_producida > 0),
        id_unidad INTEGER NOT NULL,
        cantidad_porciones REAL NOT NULL CHECK (cantidad_porciones > 0),
        FOREIGN KEY (id_menu_diario) REFERENCES MenuDiario (id_menu_diario) ON DELETE CASCADE,
        FOREIGN KEY (id_unidad) REFERENCES UnidadMedida (id_unidad) ON DELETE RESTRICT
    );

-- ============================================================
-- 5. TRIGGERS DE VALIDACIÓN
-- ============================================================
-- Validar que la unidad de producción coincida con la unidad de porción
CREATE TRIGGER trg_salida_validar_unidad_insert BEFORE INSERT ON SalidaMenuCocina FOR EACH ROW WHEN NEW.id_unidad != (
    SELECT
        id_unidad_porcion
    FROM
        MenuDiario
    WHERE
        id_menu_diario = NEW.id_menu_diario
) BEGIN
SELECT
    RAISE (
        ABORT,
        'La unidad de producción debe coincidir con la unidad de porción del menú diario'
    );

END;

-- Validar que cantidad_porciones = cantidad_producida / porcion
CREATE TRIGGER trg_salida_validar_porciones_insert BEFORE INSERT ON SalidaMenuCocina FOR EACH ROW WHEN ABS(
    NEW.cantidad_porciones - (
        NEW.cantidad_producida / (
            SELECT
                porcion
            FROM
                MenuDiario
            WHERE
                id_menu_diario = NEW.id_menu_diario
        )
    )
) > 0.0001 BEGIN
SELECT
    RAISE (
        ABORT,
        'cantidad_porciones no coincide con cantidad_producida / porcion'
    );

END;

-- Mismas validaciones para UPDATE
CREATE TRIGGER trg_salida_validar_unidad_update BEFORE
UPDATE ON SalidaMenuCocina FOR EACH ROW WHEN NEW.id_unidad != (
    SELECT
        id_unidad_porcion
    FROM
        MenuDiario
    WHERE
        id_menu_diario = NEW.id_menu_diario
) BEGIN
SELECT
    RAISE (
        ABORT,
        'La unidad de producción debe coincidir con la unidad de porción del menú diario'
    );

END;

CREATE TRIGGER trg_salida_validar_porciones_update BEFORE
UPDATE ON SalidaMenuCocina FOR EACH ROW WHEN ABS(
    NEW.cantidad_porciones - (
        NEW.cantidad_producida / (
            SELECT
                porcion
            FROM
                MenuDiario
            WHERE
                id_menu_diario = NEW.id_menu_diario
        )
    )
) > 0.0001 BEGIN
SELECT
    RAISE (
        ABORT,
        'cantidad_porciones no coincide con cantidad_producida / porcion'
    );

END;

-- ============================================================
-- 6. ÍNDICES PARA MEJORAR RENDIMIENTO
-- ============================================================
CREATE INDEX idx_menu_diario_fecha ON MenuDiario (fecha);

CREATE INDEX idx_salida_fecha ON SalidaMenuCocina (fecha_hora);

CREATE INDEX idx_ingrediente_nombre ON Ingrediente (nombre);

CREATE INDEX idx_menu_diario_base ON MenuDiario (id_menu_base);

CREATE INDEX idx_menu_base_ingrediente ON MenuBase_Ingrediente (id_ingrediente);

CREATE INDEX idx_menu_diario_ingrediente ON MenuDiario_Ingrediente (id_ingrediente);

-- ============================================================
-- 7. EJEMPLOS DE INSERCIÓN
-- ============================================================
-- Unidades de medida
INSERT INTO
    UnidadMedida (id_unidad, nombre, abreviatura)
VALUES
    (1, 'gramo', 'g'),
    (2, 'mililitro', 'ml'),
    (3, 'unidad', 'u'),
    (4, 'kilogramo', 'kg'),
    (5, 'litro', 'l');

-- Cocinero
INSERT INTO
    Cocinero (id_cocinero, codigo, nombre, activo)
VALUES
    (1, 'COC-001', 'Juan Pérez', 1),
    (2, 'COC-002', 'María López', 1);

-- Ingredientes
INSERT INTO
    Ingrediente (id_ingrediente, codigo, nombre, descripcion, id_unidad)
VALUES
    (1, 'ING-001', 'Arroz', 'Arroz blanco grano largo', 1),
    (2, 'ING-002', 'Pollo', 'Pollo fresco en trozos', 1),
    (3, 'ING-003', 'Aceite', 'Aceite vegetal', 2),
    (4, 'ING-004', 'Sal', 'Sal fina', 1),
    (5, 'ING-005', 'Cebolla', 'Cebolla blanca', 1),
    (6, 'ING-006', 'Tomate', 'Tomate fresco', 1);

-- Menús base
INSERT INTO
    MenuBase (
        id_menu_base,
        codigo,
        nombre,
        porcion,
        id_unidad,
        descripcion
    )
VALUES
    (
        1,
        'MEN-001',
        'Arroz con pollo',
        200.0,
        1,
        'Plato fuerte: 200 g por porción'
    ),
    (
        2,
        'MEN-002',
        'Sopa de verduras',
        250.0,
        2,
        'Entrada: 250 ml por porción'
    );

-- Responsables de menús base
INSERT INTO
    MenuBase_Responsable (id_menu_base, id_cocinero)
VALUES
    (1, 1),
    (2, 2);

-- Ingredientes de menús base
INSERT INTO
    MenuBase_Ingrediente (id_menu_base, id_ingrediente)
VALUES
    (1, 1), -- Arroz
    (1, 2), -- Pollo
    (1, 3), -- Aceite
    (1, 4), -- Sal
    (1, 5), -- Cebolla
    (2, 5), -- Cebolla
    (2, 6); -- Tomate

-- Menú diario planificado
INSERT INTO
    MenuDiario (
        id_menu_diario,
        id_menu_base,
        fecha,
        porcion,
        id_unidad_porcion
    )
VALUES
    (1, 1, '2026-10-07', 200.0, 1);

-- 200 g por porción
-- Ingredientes usados realmente en el día
INSERT INTO
    MenuDiario_Ingrediente (
        id_menu_diario,
        id_ingrediente,
        cantidad,
        id_unidad
    )
VALUES
    (1, 1, 3000.0, 1), -- 3 kg de arroz
    (1, 2, 4000.0, 1), -- 4 kg de pollo
    (1, 3, 200.0, 2), -- 200 ml de aceite
    (1, 4, 100.0, 1), -- 100 g de sal
    (1, 5, 600.0, 1);

-- 600 g de cebolla
-- Salida de cocina: 5000 g producidos = 25 porciones de 200 g
INSERT INTO
    SalidaMenuCocina (
        id_salida,
        id_menu_diario,
        fecha_hora,
        cantidad_producida,
        id_unidad,
        cantidad_porciones
    )
VALUES
    (1, 1, '2026-10-07 12:00:00', 5000.0, 1, 25.0);
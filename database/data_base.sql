-- ===============================
-- ROLES
-- ===============================
CREATE TABLE IF NOT EXISTS roles (
    id_rol INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    activo INTEGER DEFAULT 1,
    fecha_eliminacion TEXT
);

-- ===============================
-- USUARIOS
-- ===============================
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    activo INTEGER DEFAULT 1,
    fecha_eliminacion TEXT,
    rol_id INTEGER NOT NULL,
    FOREIGN KEY (rol_id) REFERENCES roles (id_rol)
);

-- ===============================
-- CIUDADES
-- ===============================
CREATE TABLE IF NOT EXISTS ciudades (
    id_ciudad INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    activo INTEGER DEFAULT 1,
    fecha_eliminación TEXT
);

-- ===============================
-- TIENDAS
-- ===============================
CREATE TABLE IF NOT EXISTS tiendas (
    id_tienda INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    direccion TEXT,
    activo INTEGER DEFAULT 1,
    fecha_eliminacion TEXT,
    ciudad_id INTEGER NOT NULL,
    FOREIGN KEY (ciudad_id) REFERENCES ciudades (id_ciudad)
);

-- ===============================
-- CLIENTES
-- ===============================
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    direccion TEXT,
    telefono TEXT,
    activo INTEGER DEFAULT 1,
    fecha_eliminacion TEXT,
    ciudad_id INTEGER,
    FOREIGN KEY (ciudad_id) REFERENCES ciudades (id_ciudad)
);

-- ===============================
-- PROVEEDORES
-- ===============================
CREATE TABLE IF NOT EXISTS proveedores (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    contacto TEXT,
    activo INTEGER DEFAULT 1,
    fecha_eliminacion TEXT,
    ciudad_id INTEGER,
    FOREIGN KEY (ciudad_id) REFERENCES ciudades (id_ciudad)
);

-- ===============================
-- PERSONAL
-- ===============================
CREATE TABLE IF NOT EXISTS personal (
    id_empleado INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    cargo TEXT,
    salario REAL,
    activo INTEGER DEFAULT 1,
    fecha_eliminacion TEXT,
    ciudad_id INTEGER,
    tienda_id INTEGER,
    FOREIGN KEY (ciudad_id) REFERENCES ciudades (id_ciudad),
    FOREIGN KEY (tienda_id) REFERENCES tiendas (id_tienda)
);

-- ===============================
-- PRODUCTOS
-- ===============================
CREATE TABLE IF NOT EXISTS productos (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    descripcion TEXT,
    precio REAL NOT NULL,
    stock INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1,
    fecha_eliminacion TEXT,
    proveedor_id INTEGER,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores (id_proveedor)
);

-- ===============================
-- VENTAS
-- ===============================
CREATE TABLE IF NOT EXISTS ventas (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    total REAL NOT NULL,
    estado TEXT NOT NULL,
    activo INTEGER DEFAULT 1,
    cliente_id INTEGER,
    empleado_id INTEGER,
    tienda_id INTEGER,
    FOREIGN KEY (cliente_id) REFERENCES clientes (id_cliente),
    FOREIGN KEY (empleado_id) REFERENCES personal (id_empleado),
    FOREIGN KEY (tienda_id) REFERENCES tiendas (id_tienda)
);

-- ===============================
-- FACTURAS
-- ===============================
CREATE TABLE IF NOT EXISTS facturas (
    id_factura INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    total REAL NOT NULL,
    activo INTEGER DEFAULT 1,
    venta_id INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (venta_id) REFERENCES ventas (id_venta) ON DELETE CASCADE
);

-- ===============================
-- ORDENES DE CLIENTE
-- ===============================
CREATE TABLE IF NOT EXISTS ordenes_cliente (
    id_orden_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    cliente_id INTEGER NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes (id_cliente) ON DELETE CASCADE
);

-- ===============================
-- ORDENES DE PROVEEDOR
-- ===============================
CREATE TABLE IF NOT EXISTS ordenes_proveedor (
    id_orden_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    proveedor_id INTEGER NOT NULL,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores (id_proveedor) ON DELETE CASCADE
);

-- ===============================
-- TABLAS DE RELACIÓN (N:M)
-- ===============================
CREATE TABLE IF NOT EXISTS venta_producto (
    id_venta INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    activo INTEGER DEFAULT 1,
    PRIMARY KEY (id_venta, id_producto),
    FOREIGN KEY (id_venta) REFERENCES ventas (id_venta) ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto)
);

CREATE TABLE IF NOT EXISTS ordencliente_producto (
    id_orden_cliente INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    PRIMARY KEY (id_orden_cliente, id_producto),
    FOREIGN KEY (id_orden_cliente) REFERENCES ordenes_cliente (id_orden_cliente) ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto)
);

CREATE TABLE IF NOT EXISTS ordenproveedor_producto (
    id_orden_proveedor INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    PRIMARY KEY (id_orden_proveedor, id_producto),
    FOREIGN KEY (id_orden_proveedor) REFERENCES ordenes_proveedor (id_orden_proveedor) ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto)
);

-- Insertar rol de Administrador (password = admin123)
INSERT OR IGNORE INTO roles (nombre, descripcion)
VALUES ('Administrador', 'Rol con todos los privilegios del sistema');

-- Insertar usuario administrador (password: admin123)
INSERT OR IGNORE INTO usuarios (nombre, email, password, rol_id)
VALUES (
    'admin',
    'admin@example.com',
    'pbkdf2:sha256:260000$N0aRjZ3W$3e4b1a0b5a5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e',
    (SELECT id_rol FROM roles WHERE nombre = 'Administrador')
);

-- Opcional: Insertar más roles y usuarios para testing
INSERT OR IGNORE INTO roles (nombre, descripcion)
VALUES ('Usuario', 'Usuario normal del sistema'),
       ('Editor', 'Puede editar contenido pero no administrar');

INSERT OR IGNORE INTO usuarios (nombre, email, password, rol_id)
VALUES (
    'usuario1',
    'usuario1@example.com',
    'pbkdf2:sha256:260000$N0aRjZ3W$3e4b1a0b5a5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e',
    (SELECT id_rol FROM roles WHERE nombre = 'Usuario')
);

INSERT OR IGNORE INTO usuarios (nombre, email, password, rol_id)
VALUES (
    'editor1',
    'editor1@example.com',
    'pbkdf2:sha256:260000$N0aRjZ3W$3e4b1a0b5a5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e',
    (SELECT id_rol FROM roles WHERE nombre = 'Editor')
);

-- Habilitar claves foráneas en SQLite
PRAGMA foreign_keys = ON;
"""
database.py
Capa de acceso a datos (SQLite) para el Sistema de Venta de Ropas.
"""

import sqlite3
from datetime import datetime

DB_NAME = "tienda.db"


class Database:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.crear_tablas()

    # ------------------------------------------------------------------
    # Creación de tablas
    # ------------------------------------------------------------------
    def crear_tablas(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                talla TEXT,
                color TEXT,
                categoria TEXT,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT,
                email TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                cliente_id INTEGER,
                total REAL NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS detalle_venta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)

        self.conn.commit()

    # ------------------------------------------------------------------
    # PRODUCTOS
    # ------------------------------------------------------------------
    def agregar_producto(self, codigo, nombre, talla, color, categoria, precio, stock):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO productos (codigo, nombre, talla, color, categoria, precio, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (codigo, nombre, talla, color, categoria, precio, stock))
        self.conn.commit()
        return cur.lastrowid

    def actualizar_producto(self, id_producto, codigo, nombre, talla, color, categoria, precio, stock):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE productos
            SET codigo=?, nombre=?, talla=?, color=?, categoria=?, precio=?, stock=?
            WHERE id=?
        """, (codigo, nombre, talla, color, categoria, precio, stock, id_producto))
        self.conn.commit()

    def eliminar_producto(self, id_producto):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM productos WHERE id=?", (id_producto,))
        self.conn.commit()

    def obtener_productos(self, filtro=None):
        cur = self.conn.cursor()
        if filtro:
            like = f"%{filtro}%"
            cur.execute("""
                SELECT * FROM productos
                WHERE nombre LIKE ? OR codigo LIKE ? OR categoria LIKE ?
                ORDER BY nombre
            """, (like, like, like))
        else:
            cur.execute("SELECT * FROM productos ORDER BY nombre")
        return cur.fetchall()

    def obtener_producto_por_id(self, id_producto):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM productos WHERE id=?", (id_producto,))
        return cur.fetchone()

    def actualizar_stock(self, id_producto, cantidad_vendida):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE productos SET stock = stock - ? WHERE id = ?
        """, (cantidad_vendida, id_producto))
        self.conn.commit()

    # ------------------------------------------------------------------
    # CLIENTES
    # ------------------------------------------------------------------
    def agregar_cliente(self, nombre, telefono, email):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO clientes (nombre, telefono, email) VALUES (?, ?, ?)
        """, (nombre, telefono, email))
        self.conn.commit()
        return cur.lastrowid

    def obtener_clientes(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM clientes ORDER BY nombre")
        return cur.fetchall()

    # ------------------------------------------------------------------
    # VENTAS
    # ------------------------------------------------------------------
    def registrar_venta(self, cliente_id, items):
        """
        items: lista de tuplas (producto_id, cantidad, precio_unitario)
        Retorna el id de la venta creada.
        """
        cur = self.conn.cursor()
        total = sum(cantidad * precio for _, cantidad, precio in items)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute("""
            INSERT INTO ventas (fecha, cliente_id, total) VALUES (?, ?, ?)
        """, (fecha, cliente_id, total))
        venta_id = cur.lastrowid

        for producto_id, cantidad, precio in items:
            subtotal = cantidad * precio
            cur.execute("""
                INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (venta_id, producto_id, cantidad, precio, subtotal))
            cur.execute("""
                UPDATE productos SET stock = stock - ? WHERE id = ?
            """, (cantidad, producto_id))

        self.conn.commit()
        return venta_id

    def obtener_ventas(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT v.id, v.fecha, COALESCE(c.nombre, 'Sin cliente'), v.total
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            ORDER BY v.id DESC
        """)
        return cur.fetchall()

    def obtener_detalle_venta(self, venta_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT p.nombre, d.cantidad, d.precio_unitario, d.subtotal
            FROM detalle_venta d
            JOIN productos p ON d.producto_id = p.id
            WHERE d.venta_id = ?
        """, (venta_id,))
        return cur.fetchall()

    # ------------------------------------------------------------------
    # REPORTES
    # ------------------------------------------------------------------
    def total_ventas_hoy(self):
        cur = self.conn.cursor()
        hoy = datetime.now().strftime("%Y-%m-%d")
        cur.execute("""
            SELECT COALESCE(SUM(total), 0) FROM ventas WHERE fecha LIKE ?
        """, (f"{hoy}%",))
        return cur.fetchone()[0]

    def productos_mas_vendidos(self, limite=5):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT p.nombre, SUM(d.cantidad) as total_vendido
            FROM detalle_venta d
            JOIN productos p ON d.producto_id = p.id
            GROUP BY p.id
            ORDER BY total_vendido DESC
            LIMIT ?
        """, (limite,))
        return cur.fetchall()

    def cerrar(self):
        self.conn.close()

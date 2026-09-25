"""
main.py
Sistema de Venta de Ropas - Interfaz gráfica (Tkinter)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from database import Database


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Venta de Ropas")
        self.geometry("850x550")
        self.db = Database()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_productos = FrameProductos(notebook, self.db)
        self.tab_ventas = FrameVentas(notebook, self.db, self.tab_productos)
        self.tab_reportes = FrameReportes(notebook, self.db)

        notebook.add(self.tab_productos, text="Productos")
        notebook.add(self.tab_ventas, text="Ventas")
        notebook.add(self.tab_reportes, text="Reportes")

        self.protocol("WM_DELETE_WINDOW", self.cerrar)

    def cerrar(self):
        self.db.cerrar()
        self.destroy()


# ==========================================================================
# PESTAÑA: PRODUCTOS
# ==========================================================================
class FrameProductos(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.id_seleccionado = None
        self._construir_formulario()
        self._construir_tabla()
        self.cargar_productos()

    def _construir_formulario(self):
        frame = ttk.LabelFrame(self, text="Datos del producto")
        frame.pack(fill="x", padx=10, pady=10)

        etiquetas = ["Código", "Nombre", "Talla", "Color", "Categoría", "Precio", "Stock"]
        self.entradas = {}

        for i, texto in enumerate(etiquetas):
            fila, col = divmod(i, 4)
            ttk.Label(frame, text=texto + ":").grid(row=fila * 2, column=col, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(frame, width=15)
            entry.grid(row=fila * 2 + 1, column=col, padx=5, pady=2)
            self.entradas[texto] = entry

        botones = ttk.Frame(frame)
        botones.grid(row=4, column=0, columnspan=4, pady=10)

        ttk.Button(botones, text="Agregar", command=self.agregar).pack(side="left", padx=5)
        ttk.Button(botones, text="Actualizar", command=self.actualizar).pack(side="left", padx=5)
        ttk.Button(botones, text="Eliminar", command=self.eliminar).pack(side="left", padx=5)
        ttk.Button(botones, text="Limpiar", command=self.limpiar).pack(side="left", padx=5)

        ttk.Label(self, text="Buscar:").pack(anchor="w", padx=10)
        self.entry_buscar = ttk.Entry(self)
        self.entry_buscar.pack(fill="x", padx=10)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.cargar_productos())

    def _construir_tabla(self):
        columnas = ("id", "codigo", "nombre", "talla", "color", "categoria", "precio", "stock")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", height=10)
        for col in columnas:
            self.tabla.heading(col, text=col.capitalize())
            self.tabla.column(col, width=90)
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_fila)

    def cargar_productos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        filtro = self.entry_buscar.get().strip() or None
        for p in self.db.obtener_productos(filtro):
            self.tabla.insert("", "end", values=p)

    def seleccionar_fila(self, event):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        valores = self.tabla.item(seleccion[0])["values"]
        self.id_seleccionado = valores[0]
        campos = ["Código", "Nombre", "Talla", "Color", "Categoría", "Precio", "Stock"]
        for campo, valor in zip(campos, valores[1:]):
            self.entradas[campo].delete(0, tk.END)
            self.entradas[campo].insert(0, valor)

    def _leer_formulario(self):
        try:
            codigo = self.entradas["Código"].get().strip()
            nombre = self.entradas["Nombre"].get().strip()
            talla = self.entradas["Talla"].get().strip()
            color = self.entradas["Color"].get().strip()
            categoria = self.entradas["Categoría"].get().strip()
            precio = float(self.entradas["Precio"].get())
            stock = int(self.entradas["Stock"].get())
            if not codigo or not nombre:
                raise ValueError("Código y nombre son obligatorios")
            return codigo, nombre, talla, color, categoria, precio, stock
        except ValueError as e:
            messagebox.showerror("Datos inválidos", str(e) or "Verifica precio y stock")
            return None

    def agregar(self):
        datos = self._leer_formulario()
        if not datos:
            return
        try:
            self.db.agregar_producto(*datos)
            messagebox.showinfo("Éxito", "Producto agregado")
            self.limpiar()
            self.cargar_productos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar: {e}")

    def actualizar(self):
        if not self.id_seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un producto de la tabla")
            return
        datos = self._leer_formulario()
        if not datos:
            return
        self.db.actualizar_producto(self.id_seleccionado, *datos)
        messagebox.showinfo("Éxito", "Producto actualizado")
        self.limpiar()
        self.cargar_productos()

    def eliminar(self):
        if not self.id_seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un producto de la tabla")
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar este producto?"):
            self.db.eliminar_producto(self.id_seleccionado)
            self.limpiar()
            self.cargar_productos()

    def limpiar(self):
        for entry in self.entradas.values():
            entry.delete(0, tk.END)
        self.id_seleccionado = None


# ==========================================================================
# PESTAÑA: VENTAS
# ==========================================================================
class FrameVentas(ttk.Frame):
    def __init__(self, parent, db, frame_productos):
        super().__init__(parent)
        self.db = db
        self.frame_productos = frame_productos
        self.carrito = []  # lista de (producto_id, nombre, cantidad, precio_unitario)
        self._construir_ui()

    def _construir_ui(self):
        top = ttk.LabelFrame(self, text="Agregar producto a la venta")
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Código producto:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_codigo = ttk.Entry(top, width=15)
        self.entry_codigo.grid(row=0, column=1, padx=5)

        ttk.Label(top, text="Cantidad:").grid(row=0, column=2, padx=5)
        self.entry_cantidad = ttk.Entry(top, width=8)
        self.entry_cantidad.grid(row=0, column=3, padx=5)
        self.entry_cantidad.insert(0, "1")

        ttk.Button(top, text="Agregar al carrito", command=self.agregar_al_carrito).grid(row=0, column=4, padx=10)

        columnas = ("producto", "cantidad", "precio", "subtotal")
        self.tabla_carrito = ttk.Treeview(self, columns=columnas, show="headings", height=8)
        for col in columnas:
            self.tabla_carrito.heading(col, text=col.capitalize())
        self.tabla_carrito.pack(fill="both", expand=True, padx=10, pady=10)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=5)

        self.label_total = ttk.Label(bottom, text="Total: $0.00", font=("Arial", 12, "bold"))
        self.label_total.pack(side="left")

        ttk.Button(bottom, text="Quitar seleccionado", command=self.quitar_seleccionado).pack(side="right", padx=5)
        ttk.Button(bottom, text="Confirmar venta", command=self.confirmar_venta).pack(side="right", padx=5)

    def agregar_al_carrito(self):
        codigo = self.entry_codigo.get().strip()
        if not codigo:
            return
        try:
            cantidad = int(self.entry_cantidad.get())
        except ValueError:
            messagebox.showerror("Error", "Cantidad inválida")
            return

        productos = self.db.obtener_productos(codigo)
        producto = next((p for p in productos if p[1] == codigo), None)
        if not producto:
            messagebox.showerror("Error", "Producto no encontrado")
            return

        id_prod, _, nombre, _, _, _, precio, stock = producto
        if cantidad > stock:
            messagebox.showerror("Error", f"Stock insuficiente (disponible: {stock})")
            return

        self.carrito.append((id_prod, nombre, cantidad, precio))
        self.tabla_carrito.insert("", "end", values=(nombre, cantidad, f"{precio:.2f}", f"{cantidad * precio:.2f}"))
        self.entry_codigo.delete(0, tk.END)
        self.entry_cantidad.delete(0, tk.END)
        self.entry_cantidad.insert(0, "1")
        self._actualizar_total()

    def quitar_seleccionado(self):
        seleccion = self.tabla_carrito.selection()
        if not seleccion:
            return
        idx = self.tabla_carrito.index(seleccion[0])
        self.tabla_carrito.delete(seleccion[0])
        del self.carrito[idx]
        self._actualizar_total()

    def _actualizar_total(self):
        total = sum(c * p for _, _, c, p in self.carrito)
        self.label_total.config(text=f"Total: ${total:.2f}")

    def confirmar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Aviso", "El carrito está vacío")
            return
        items = [(id_prod, cantidad, precio) for id_prod, _, cantidad, precio in self.carrito]
        venta_id = self.db.registrar_venta(cliente_id=None, items=items)
        messagebox.showinfo("Venta registrada", f"Venta #{venta_id} registrada correctamente")

        self.carrito.clear()
        for fila in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(fila)
        self._actualizar_total()
        self.frame_productos.cargar_productos()  # refresca stock


# ==========================================================================
# PESTAÑA: REPORTES
# ==========================================================================
class FrameReportes(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self._construir_ui()

    def _construir_ui(self):
        ttk.Button(self, text="Actualizar reportes", command=self.actualizar).pack(pady=10)

        self.label_total_hoy = ttk.Label(self, text="Ventas de hoy: $0.00", font=("Arial", 12, "bold"))
        self.label_total_hoy.pack(pady=5)

        ttk.Label(self, text="Historial de ventas:").pack(anchor="w", padx=10)
        columnas = ("id", "fecha", "cliente", "total")
        self.tabla_ventas = ttk.Treeview(self, columns=columnas, show="headings", height=8)
        for col in columnas:
            self.tabla_ventas.heading(col, text=col.capitalize())
        self.tabla_ventas.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Label(self, text="Productos más vendidos:").pack(anchor="w", padx=10)
        columnas2 = ("producto", "cantidad_vendida")
        self.tabla_top = ttk.Treeview(self, columns=columnas2, show="headings", height=5)
        for col in columnas2:
            self.tabla_top.heading(col, text=col.replace("_", " ").capitalize())
        self.tabla_top.pack(fill="both", expand=True, padx=10, pady=5)

        self.actualizar()

    def actualizar(self):
        total_hoy = self.db.total_ventas_hoy()
        self.label_total_hoy.config(text=f"Ventas de hoy: ${total_hoy:.2f}")

        for fila in self.tabla_ventas.get_children():
            self.tabla_ventas.delete(fila)
        for v in self.db.obtener_ventas():
            self.tabla_ventas.insert("", "end", values=v)

        for fila in self.tabla_top.get_children():
            self.tabla_top.delete(fila)
        for nombre, cantidad in self.db.productos_mas_vendidos():
            self.tabla_top.insert("", "end", values=(nombre, cantidad))


if __name__ == "__main__":
    app = App()
    app.mainloop()

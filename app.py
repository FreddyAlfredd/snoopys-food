from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-secreta-cambiar-en-produccion")

BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "tienda.db"

PRODUCTOS = [
    ("Frappé de Café", "Café frio licuado con hielo y crema batida.", 59.00, "img/frappe_cafe.jpg"),
    ("Malteada de Fresa", "Malteada cremosa de fresa con helado.", 65.00, "img/malteada_fresa.jpg"),
    ("Té Helado de Durazno", "Té negro frio con sabor a durazno.", 35.00, "img/te_durazno.jpg"),
    ("Café Americano", "Taza de café americano caliente.", 35.00, "img/cafe.jpg"),
    ("Capuchino", "Espresso con leche vaporizada y espuma.", 49.00, "img/capuchino.jpg"),
    ("Chocolate Caliente", "Chocolate de mesa preparado con leche.", 45.00, "img/chocolate_caliente.jpg"),
    ("Té de Manzanilla", "Infusión caliente de manzanilla.", 30.00, "img/te_manzanilla.jpg"),
    ("Refresco de Cola", "Refresco de cola de 600 ml.", 25.00, "img/refresco_cola.jpg"),
    ("Refresco de Naranja", "Refresco sabor naranja de 600 ml.", 25.00, "img/refresco_naranja.jpg"),
    ("Refresco de Limón", "Refresco sabor limón de 600 ml.", 25.00, "img/refresco_limon.jpg"),
    ("Agua de Horchata", "Vaso grande de agua fresca de horchata.", 30.00, "img/horchata.jpg"),
    ("Limonada Natural", "Vaso grande de limonada natural.", 30.00, "img/limonada.jpg"),
    ("Jugo de Naranja", "Jugo de naranja recién exprimido.", 40.00, "img/jugo_naranja.jpg"),
    ("Agua de Jamaica", "Vaso grande de agua fresca de jamaica.", 30.00, "img/jamaica.jpg"),
    ("Tacos al Pastor", "Orden de 5 tacos al pastor con piña.", 89.00, "img/tacos_pastor.jpg"),
    ("Enchiladas Verdes", "Enchiladas bañadas en salsa verde con pollo.", 99.00, "img/enchiladas_verdes.jpg"),
    ("Pozole Rojo", "Pozole de cerdo con lechuga, rábano y tostadas.", 119.00, "img/pozole.jpg"),
    ("Chilaquiles", "Chilaquiles con pollo, crema y queso fresco.", 85.00, "img/chilaquiles.jpg"),
    ("Spaghetti Boloñesa", "Pasta con salsa de carne molida y queso.", 109.00, "img/spaghetii_boloñesa.jpg"),
    ("Hamburguesa", "Carne de res, lechuga, jitomate y queso.", 80.00, "img/hamburguesa.jpg"),
    ("Hamburguesa Doble", "Doble carne con queso cheddar y tocino.", 120.00, "img/hamburguesadoble.jpg"),
    ("Torta Cubana", "Torta con milanesa, jamón, salchicha y queso.", 99.00, "img/torta_cubana.jpg"),
    ("Torta de Jamón", "Torta con jamón, aguacate, jitomate y frijoles.", 65.00, "img/torta_jamon.jpg"),
    ("Nachos con Queso", "Totopos con queso fundido y jalapeños.", 79.00, "img/nachos.jpg"),
    ("Papas a la Francesa", "Porción grande de papas fritas.", 49.00, "img/papas_fritas.jpg"),
    ("Alitas BBQ", "10 alitas de pollo en salsa BBQ.", 139.00, "img/alitas_bbq.jpg"),
    ("Hot Dog", "Salchicha con tocino, cebolla y aderezos.", 45.00, "img/hotdog.jpg"),
    ("Pastel de Chocolate", "Rebanada de pastel de chocolate con betún.", 55.00, "img/pastel_chocolate.jpg"),
    ("Flan Napolitano", "Porción de flan con caramelo.", 40.00, "img/flan.jpg"),
    ("Helado de Vainilla", "Copa de helado de vainilla con galleta.", 45.00, "img/helado.jpg"),
]

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_bd():
    conn = get_db()
    
    columnas = [c["name"] for c in conn.execute("PRAGMA table_info(productos)")]
    if columnas and "categoria" in columnas:
        conn.execute("DROP TABLE productos")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    precio REAL NOT NULL,
    imagen TEXT NOT NULL
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    email TEXT NOT NULL,
    direccion TEXT NOT NULL,
    total REAL NOT NULL
    )
    """)
    # --- NUEVO: Tabla pedido_producto exacta de tu pizarrón ---
    conn.execute("""
    CREATE TABLE IF NOT EXISTS pedido_producto (
    id_pedido INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    Nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    Precio REAL NOT NULL,
    Cantidad INTEGER NOT NULL,
    importe REAL NOT NULL,
    PRIMARY KEY (id_pedido, id_producto),
    FOREIGN KEY (id_pedido) REFERENCES pedidos(id),
    FOREIGN KEY (id_producto) REFERENCES productos(id)
    )
    """)
    cantidad = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    if cantidad == 0:
        conn.executemany("""
        INSERT INTO productos (nombre, descripcion, precio, imagen)
        VALUES (?, ?, ?, ?)""", PRODUCTOS)
    conn.commit()
    conn.close()

def obtener_carrito():
    carrito = session.get("carrito", {})
    if not carrito:
        return [], 0
    conn = get_db()
    items = []
    total = 0
    for producto_id, cantidad in carrito.items():
        producto = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
        if producto:
            subtotal = producto["precio"] * cantidad
            items.append({
                "id": producto["id"],
                "nombre": producto["nombre"],
                "precio": producto["precio"],
                "imagen": producto["imagen"],
                "cantidad": cantidad,
                "subtotal": subtotal
            })
            total += subtotal
    conn.close()
    return items, total

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    conn = get_db()
    if q:
        productos = conn.execute(
            "SELECT * FROM productos WHERE nombre LIKE ? OR descripcion LIKE ? ORDER BY id",
            (f"%{q}%", f"%{q}%")
        ).fetchall()
    else:
        productos = conn.execute("SELECT * FROM productos ORDER BY id").fetchall()
    conn.close()
    return render_template("index.html", productos=productos, q=q)

@app.route("/agregar/<int:producto_id>", methods=["POST"])
def agregar(producto_id):
    carrito = session.get("carrito", {})
    clave = str(producto_id)
    carrito[clave] = carrito.get(clave, 0) + 1
    session["carrito"] = carrito
    flash("Producto agregado al carrito.", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/carrito")
def carrito():
    items, total = obtener_carrito()
    return render_template("carrito.html", items=items, total=total)

@app.route("/actualizar/<int:producto_id>", methods=["POST"])
def actualizar(producto_id):
    try:
        cantidad = int(request.form.get("cantidad", 1))
    except ValueError:
        cantidad = 1
    carrito = session.get("carrito", {})
    clave = str(producto_id)
    if cantidad <= 0:
        carrito.pop(clave, None)
    else:
        carrito[clave] = cantidad
    session["carrito"] = carrito
    return redirect(url_for("carrito"))

@app.route("/eliminar/<int:producto_id>", methods=["POST"])
def eliminar(producto_id):
    carrito = session.get("carrito", {})
    carrito.pop(str(producto_id), None)
    session["carrito"] = carrito
    flash("Producto eliminado.", "info")
    return redirect(url_for("carrito"))

@app.route("/vaciar", methods=["POST"])
def vaciar():
    session["carrito"] = {}
    flash("El carrito fue vaciado.", "info")
    return redirect(url_for("carrito"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = obtener_carrito()
    if not items:
        flash("El carrito está vacío.", "warning")
        return redirect(url_for("index"))
    if request.method == "POST":
        cliente = request.form.get("cliente", "").strip()
        email = request.form.get("email", "").strip()
        direccion = request.form.get("direccion", "").strip()
        if not cliente or not email or not direccion:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("checkout.html", items=items, total=total)
        conn = get_db()
        cursor = conn.execute("INSERT INTO pedidos (cliente, email, direccion, total) VALUES (?, ?, ?, ?)",
                              (cliente, email, direccion, total))
        pedido_id = cursor.lastrowid

        
        for item in items:
         
            prod = conn.execute("SELECT descripcion FROM productos WHERE id = ?", (item["id"],)).fetchone()
            descripcion = prod["descripcion"] if prod else ""
            importe = item["precio"] * item["cantidad"]
            conn.execute("""
                INSERT INTO pedido_producto (id_pedido, id_producto, Nombre, descripcion, Precio, Cantidad, importe)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (pedido_id, item["id"], item["nombre"], descripcion, item["precio"], item["cantidad"], importe))

        conn.commit()
        conn.close()
        session["carrito"] = {}
        return render_template("confirmacion.html", pedido_id=pedido_id, cliente=cliente, total=total)
    return render_template("checkout.html", items=items, total=total)

@app.route("/pedidos")
def pedidos():
    conn = get_db()
    pedidos = conn.execute("SELECT * FROM pedidos ORDER BY id").fetchall()
    conn.close()
    return render_template("pedidos.html", pedidos=pedidos)

@app.route("/pedido_producto/<int:id_pedido>")
def pedido_producto(id_pedido):
    conn = get_db()
   
    pedido = conn.execute("SELECT * FROM pedidos WHERE id = ?", (id_pedido,)).fetchone()

    productos_pedido = conn.execute("SELECT * FROM pedido_producto WHERE id_pedido = ? ORDER BY id_producto", (id_pedido,)).fetchall()
    conn.close()
    return render_template("pedido_producto.html", pedido=pedido, pedido_productos=productos_pedido, id_pedido=id_pedido)

@app.route("/eliminar_del_pedido/<int:id_pedido>/<int:id_producto>")
def eliminar_del_pedido(id_pedido, id_producto):
    conn = get_db()
    conn.execute("DELETE FROM pedido_producto WHERE id_pedido = ? AND id_producto = ?", (id_pedido, id_producto))
   
    nuevo_total = conn.execute("SELECT COALESCE(SUM(importe),0) FROM pedido_producto WHERE id_pedido = ?", (id_pedido,)).fetchone()[0]
    conn.execute("UPDATE pedidos SET total = ? WHERE id = ?", (nuevo_total, id_pedido))
    conn.commit()
    conn.close()
    flash("Producto eliminado del pedido.", "info")
    return redirect(url_for("pedido_producto", id_pedido=id_pedido))

@app.route('/sobre_nosotros')
def sobre_nosotros():
    return render_template('sobre_nosotros.html')

# --- CAMBIO PARA SUBIR A INTERNET (RENDER) ---
# Antes tenias: app.run(debug=True) -> eso no funciona en Render
# Ahora: usa el puerto que Render te da y crea la BD si no existe
inicializar_bd()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
import flet as ft
import sqlite3
import os
from datetime import date

# -------------------------------
# CONFIGURACIÓN DE BASE DE DATOS
# -------------------------------
os.makedirs("data", exist_ok=True)
DB_NAME = os.path.join("data", "control_gastos_personales.db")


def inicializar_bd():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id_gasto INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha_gasto TEXT NOT NULL,
            categoria TEXT,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
        )
    """)
    cursor.execute("SELECT * FROM usuarios WHERE email='demo@demo.com'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO usuarios (nombre,email,password) VALUES (?,?,?)",
            ("Demo", "demo@demo.com", "1234")
        )
        conn.commit()
    conn.close()


# -------------------------------
# FUNCIONES DE BD
# -------------------------------
def verificar_usuario(email, password):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email=? AND password=?", (email, password))
    usuario = cursor.fetchone()
    conn.close()
    return dict(usuario) if usuario else None


def registrar_gasto(usuario_id, descripcion, monto, fecha, categoria):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO gastos (id_usuario, descripcion, monto, fecha_gasto, categoria) VALUES (?,?,?,?,?)",
            (usuario_id, descripcion, monto, fecha, categoria)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error al registrar gasto:", e)
        return False


def actualizar_gasto(id_gasto, usuario_id, descripcion, monto, fecha, categoria):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE gastos
            SET descripcion=?, monto=?, fecha_gasto=?, categoria=?
            WHERE id_gasto=? AND id_usuario=?
        """, (descripcion, monto, fecha, categoria, id_gasto, usuario_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error al actualizar gasto:", e)
        return False


def eliminar_gasto(id_gasto, usuario_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gastos WHERE id_gasto=? AND id_usuario=?", (id_gasto, usuario_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error al eliminar gasto:", e)
        return False


def obtener_gastos(usuario_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gastos WHERE id_usuario=? ORDER BY fecha_gasto DESC", (usuario_id,))
    gastos = cursor.fetchall()
    conn.close()
    return [dict(g) for g in gastos]


# -------------------------------
# INTERFAZ FLET
# -------------------------------
def main(page: ft.Page):
    page.title = "Control de Gastos Personales"
    page.bgcolor = "#f5f7fb"
    page.scroll = "adaptive"

    inicializar_bd()

    # --- LOGIN ---
    correo_input = ft.TextField(label="Correo electrónico", width=300)
    pass_input = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=300)
    mensaje = ft.Text("", color="red")

    def on_login(e=None):
        email = correo_input.value.strip()
        password = pass_input.value.strip()
        if not email or not password:
            mensaje.value = "Complete todos los campos."
            page.update()
            return
        usuario = verificar_usuario(email, password)
        if usuario:
            abrir_panel(usuario)
        else:
            mensaje.value = "Correo o contraseña incorrectos."
        page.update()

    login_card = ft.Container(
        content=ft.Column([
            ft.Text("Iniciar sesión", size=28, weight="bold", color="#3b82f6"),
            correo_input,
            pass_input,
            ft.ElevatedButton("Ingresar", on_click=on_login, bgcolor="#3b82f6", color="white"),
            mensaje
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
        width=400, height=400, bgcolor="white", border_radius=12, padding=30, alignment=ft.alignment.center,
        shadow=ft.BoxShadow(blur_radius=12, color="#888", offset=ft.Offset(2, 2))
    )

    # --- PANEL PRINCIPAL ---
    def abrir_panel(usuario):
        page.clean()

        gastos_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", color="white")),
                ft.DataColumn(ft.Text("Descripción", color="white")),
                ft.DataColumn(ft.Text("Monto", color="white")),
                ft.DataColumn(ft.Text("Fecha", color="white")),
                ft.DataColumn(ft.Text("Categoría", color="white")),
                ft.DataColumn(ft.Text("Acciones", color="white")),
            ],
            heading_row_color="#3b82f6",
        )

        descripcion_input = ft.TextField(label="Descripción", width=250)
        monto_input = ft.TextField(label="Monto", width=250)
        categoria_input = ft.TextField(label="Categoría", width=250)
        fecha_input = ft.TextField(label="Fecha (YYYY-MM-DD)", value=str(date.today()), width=250)
        mensaje_form = ft.Text("", color="green")

        # Variable para saber si estamos editando
        gasto_editando = {"id": None}

        # Guardar o actualizar gasto
        def guardar_o_actualizar(e):
            if not descripcion_input.value or not monto_input.value or not categoria_input.value or not fecha_input.value:
                mensaje_form.value = "Complete todos los campos."
                mensaje_form.color = "red"
                page.update()
                return

            if gasto_editando["id"] is None:
                # Guardar nuevo gasto
                exito = registrar_gasto(
                    usuario["id_usuario"],
                    descripcion_input.value,
                    float(monto_input.value),
                    fecha_input.value,
                    categoria_input.value
                )
                if exito:
                    mensaje_form.value = "✅ Registro agregado"
                    mensaje_form.color = "green"
            else:
                # Actualizar gasto existente
                exito = actualizar_gasto(
                    gasto_editando["id"], usuario["id_usuario"],
                    descripcion_input.value,
                    float(monto_input.value),
                    fecha_input.value,
                    categoria_input.value
                )
                if exito:
                    mensaje_form.value = "✅ Registro actualizado"
                    mensaje_form.color = "green"
                gasto_editando["id"] = None
                boton_guardar.text = "Guardar"

            # Limpiar formulario
            descripcion_input.value = ""
            monto_input.value = ""
            categoria_input.value = ""
            fecha_input.value = str(date.today())
            page.update()
            cargar_gastos()

        boton_guardar = ft.ElevatedButton("Guardar", on_click=guardar_o_actualizar, bgcolor="#3b82f6", color="white")

        # Cargar tabla
        def cargar_gastos():
            gastos_table.rows.clear()
            gastos = obtener_gastos(usuario["id_usuario"])
            if not gastos:
                gastos_table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("No hay registros"))] * 6))
            else:
                for g in gastos:
                    editar_btn = ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color="blue",
                        tooltip="Editar",
                        on_click=lambda e, g=g: editar_gasto(g)
                    )
                    eliminar_btn = ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color="red",
                        tooltip="Eliminar",
                        on_click=lambda e, g=g: eliminar_registro(g["id_gasto"])
                    )
                    gastos_table.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(g["id_gasto"]))),
                        ft.DataCell(ft.Text(g["descripcion"])),
                        ft.DataCell(ft.Text(f"{g['monto']:.2f}")),
                        ft.DataCell(ft.Text(g["fecha_gasto"])),
                        ft.DataCell(ft.Text(g["categoria"])),
                        ft.DataCell(ft.Row([editar_btn, eliminar_btn]))
                    ]))
            page.update()

        # Cargar datos al formulario para editar
        def editar_gasto(g):
            gasto_editando["id"] = g["id_gasto"]
            descripcion_input.value = g["descripcion"]
            monto_input.value = str(g["monto"])
            fecha_input.value = g["fecha_gasto"]
            categoria_input.value = g["categoria"]
            boton_guardar.text = "Actualizar"
            page.update()

        # Eliminar gasto
        def eliminar_registro(id_gasto):
            exito = eliminar_gasto(id_gasto, usuario["id_usuario"])
            if exito:
                mensaje_form.value = "🗑️ Gasto eliminado correctamente."
                mensaje_form.color = "green"
                cargar_gastos()
            else:
                mensaje_form.value = "❌ Error al eliminar."
                mensaje_form.color = "red"
            page.update()

        # Cerrar sesión
        def cerrar_sesion(e):
            page.clean()
            page.add(ft.Row([login_card], alignment=ft.MainAxisAlignment.CENTER))

        # Formulario principal
        formulario = ft.Column([
            ft.Text("Agregar / Editar gasto", size=20, weight="bold"),
            descripcion_input,
            monto_input,
            fecha_input,
            categoria_input,
            boton_guardar,
            mensaje_form
        ], spacing=10)

        # AppBar con cerrar sesión arriba a la derecha
        app_bar = ft.AppBar(
            title=ft.Text(f"Bienvenido, {usuario['nombre']}"),
            bgcolor="#3b82f6",
            color="white",
            actions=[ft.ElevatedButton("🔌 Cerrar sesión", on_click=cerrar_sesion, bgcolor="#ef4444", color="white")]
        )

        page.add(
            app_bar,
            ft.Row([
                ft.Column([gastos_table], expand=True),
                ft.Column([formulario], width=300)
            ], spacing=50)
        )

        cargar_gastos()

    # Mostrar login
    page.add(ft.Row([login_card], alignment=ft.MainAxisAlignment.CENTER))


# Ejecutar app
ft.app(target=main)

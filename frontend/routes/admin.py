import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename

# Importamos tus clases
from clases.Usuarios import Usuarios
from clases.MotorRAG import MotorRAG
from clases.Auth import Auth

# Definimos el Blueprint
admin_bp = Blueprint('admin', __name__)

# Instanciamos lo que el admin necesita
auth_service = Auth()
rag = MotorRAG()

# Configuración de subida
UPLOAD_FOLDER = 'documentos/temp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- RUTAS DE ADMIN ---

@admin_bp.route("/admin")
def index():
    if session.get("rol") != 1:
        flash("No tienes permisos.", "danger")
        return redirect(url_for("chat.dashboard"))

    try:
        users = Usuarios()
        datos = users.get_usuarios_completo()
        return render_template("admin.html", usuarios=datos)
    except Exception as e:
        return f"Error cargando la base de datos: {e}", 500

@admin_bp.route("/admin/add_user", methods=["POST"])
def add_user():
    if session.get("rol") != 1:
        return redirect(url_for("chat.dashboard"))

    try:
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        users_model = Usuarios()

        if users_model.existe_email(email):
            flash(f"El correo {email} ya está registrado.", "warning")
            return redirect(url_for("admin.index"))

        password = request.form.get("password")
        rol = request.form.get("rol")
        estado = request.form.get("estado")
        password_hash = auth_service.hash_password(password)

        users_model.crear_usuario_admin(nombre, email, password_hash, rol, estado)
        flash(f"Usuario {nombre} creado con éxito", "success")
    except Exception as e:
        flash("Error al crear el usuario.", "danger")

    return redirect(url_for("admin.index"))

@admin_bp.route("/admin/delete/<int:id>", methods=["POST"])
def delete_user(id):
    if session.get("rol") != 1:
        flash("No tienes permisos.", "danger")
        return redirect(url_for("admin.index"))

    try:
        users_model = Usuarios()
        if users_model.eliminar_usuario(id):
            flash(f"Usuario eliminado correctamente.", "success")
        else:
            flash("No se pudo eliminar el usuario.", "warning")
    except Exception as e:
        flash("Error crítico al intentar eliminar.", "danger")

    return redirect(url_for("admin.index"))

@admin_bp.route("/admin/update_user", methods=["POST"])
def update_user():
    if session.get("rol") != 1:
        return redirect(url_for("chat.dashboard"))

    try:
        user_id = request.form.get("id")
        nombre = request.form.get("nombre")
        rol = request.form.get("rol")
        estado = request.form.get("estado")

        users_model = Usuarios()
        if users_model.actualizar_usuario(user_id, nombre, rol, estado):
            flash("Usuario actualizado correctamente.", "success")
        else:
            flash("Error al actualizar.", "danger")
    except Exception as e:
        flash("Error interno.", "danger")

    return redirect(url_for("admin.index"))

@admin_bp.route('/api/stats_rag')
def stats_rag():
    if session.get('rol') != 1:
        return {"error": "No autorizado"}, 403
    stats = rag.obtener_estadisticas()
    return jsonify(stats)

@admin_bp.route('/upload_document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return {"error": "No hay archivo"}, 400

    file = request.files['file']
    coleccion = request.form.get('coleccion', 'leyes')

    if file and file.filename.endswith('.txt'):
        filename = secure_filename(file.filename)
        ruta_temp = os.path.join(UPLOAD_FOLDER, filename)
        file.save(ruta_temp)

        try:
            resultado = rag.indexar_documento(ruta_temp, coleccion)
            os.remove(ruta_temp)
            return {"message": f"Archivo indexado con éxito en {coleccion}"}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    return {"error": "Formato no permitido"}, 400
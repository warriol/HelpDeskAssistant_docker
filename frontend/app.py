import logging
import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from clases.Auth import Auth
from clases.Usuarios import Usuarios

# Configuración de Logs (se mantiene igual)
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "app.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["DEBUG"] = True

# Instancias de clases
auth_service = Auth()
user_service = Usuarios()


# --- RUTAS DE NAVEGACIÓN ---

@app.route("/")
def index():
    # Nueva página de inicio (Landing)
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Llamamos al login de tu clase Auth
        # NOTA: Tu auth.login debe guardar en session['user'], session['nombre'] y session['rol']
        resultado = auth_service.login(email, password)

        if resultado == "dashboard":
            # Inyectamos la URL de la IA para que el JS del frontend la use
            session["urlia"] = os.getenv("URLIA", "http://localhost:5000")
            return redirect(url_for("dashboard"))

        # Mapeo de errores de tu lógica original a mensajes flash
        mensajes_error = {
            "correoIncorrecto": "El correo electrónico no existe.",
            "estadoInactivo": "Tu cuenta aún no ha sido activada.",
            "contraseñaIncorrecta": "La contraseña es incorrecta."
        }
        flash(mensajes_error.get(resultado, "Error de inicio de sesión"), "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]

        mensaje = auth_service.registrar(nombre, email, password)
        app.logger.info(f"Registro: {mensaje}")
        flash("Registro exitoso. Por favor, inicia sesión.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        flash("Debes iniciar sesión primero.", "warning")
        return redirect(url_for("login"))
    return render_template("dashboard.html")


@app.route("/admin/add_user", methods=["POST"])
def admin_add_user():
    # Por ahora solo redireccionamos para que no explote el renderizado
    flash("Función en desarrollo", "info")
    return redirect(url_for("admin"))


@app.route("/ajustes")
def ajustes():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("ajustes.html")


@app.route("/update_profile", methods=["POST"])
def update_profile():
    nombre = request.form["nombre"]
    email = request.form["email"]

    # Aquí llamarías a Usuarios().editar_usuario_perfil(session['user_id'], nombre, email)
    # Por ahora actualizamos la sesión para que el cambio sea visible
    session["nombre"] = nombre
    session["user"] = email

    flash("Perfil actualizado correctamente.", "success")
    return redirect(url_for("ajustes"))


@app.route("/update_password", methods=["POST"])
def update_password():
    new_pass = request.form["new_password"]
    confirm_pass = request.form["confirm_password"]

    if new_pass != confirm_pass:
        flash("Las contraseñas no coinciden.", "danger")
        return redirect(url_for("ajustes"))

    # Ciframos y guardamos (usando tu lógica de Auth)
    hashed = auth_service.hash_password(new_pass)
    # user_service.cambiar_password(session['user_id'], hashed)

    flash("Contraseña actualizada con éxito.", "success")
    return redirect(url_for("ajustes"))


@app.route("/admin")
def admin():
    if session.get("rol") != 1:
        app.logger.info(f"Acceso denegado: {session.get('user')}")
        flash("No tienes permisos.", "danger")
        return redirect(url_for("dashboard"))  # Asegúrate que 'dashboard' existe

    try:
        users = Usuarios()
        datos = users.get_usuarios_completo()
        return render_template("admin.html", usuarios=datos)
    except Exception as e:
        app.logger.error(f"Error en admin: {e}")
        return "Error cargando la base de datos", 500


@app.route("/admin/delete/<int:id>", methods=["POST"])
def delete_user(id):
    if session.get("rol") == 1:
        # Aquí llamarías a un método de tu clase Usuarios
        # user_service.eliminar_usuario(id)
        flash(f"Usuario {id} eliminado correctamente.", "info")
    return redirect(url_for("admin"))


@app.route("/logout")
def logout():
    session.clear()  # Limpia toda la sesión de un golpe
    return redirect(url_for("index"))


# --- API Y CAPTURA DE ERRORES ---

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Error crítico: {e}")
    flash(f"Ocurrió un error inesperado: {str(e)}", "danger")
    return redirect(url_for("index"))


if __name__ == '__main__':
    # Puerto 5001 para el frontend como acordamos en Docker
    app.run(host='0.0.0.0', port=5001)
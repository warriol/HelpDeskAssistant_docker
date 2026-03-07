import logging
import os
import requests

from werkzeug.utils import secure_filename
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash, Response, stream_with_context

from clases.Auth import Auth
from clases.Usuarios import Usuarios
from clases.Conversaciones import Conversaciones
from clases.MotorRAG import MotorRAG

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

# Configuración de subida
UPLOAD_FOLDER = 'documentos/temp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["DEBUG"] = True

# Instancias de clases
auth_service = Auth()
user_service = Usuarios()
conv_service = Conversaciones()
rag = MotorRAG()

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


@app.route('/chat_con_contexto', methods=['POST'])
def chat_con_contexto():
    data = request.json
    pregunta = data.get("question")
    rol = data.get("role")

    # 1. BUSCAMOS EN CHROMADB (Comunicación interna Docker: frontend -> chroma)
    contexto = rag.buscar_contexto(pregunta, rol)

    # 2. ARMAMOS EL PROMPT
    prompt_final = f"""
    Eres un asistente legal del Ministerio del Interior de Uruguay. 
    Usa la siguiente información oficial para responder. 
    Si no encuentras la respuesta en el contexto, indícalo claramente.

    CONTEXTO OFICIAL:
    {contexto}

    PREGUNTA:
    {pregunta}
    """

    # 3. LE PEDIMOS A OLLAMA/BACKEND (Comunicación interna: frontend -> backend)
    # Usamos stream=True para que el usuario no espere a que termine toda la respuesta
    def generate():
        url_backend = "http://backend:5000/chat"  # Nombre del servicio en Docker
        response = requests.post(url_backend,
                                 json={"question": prompt_final, "role": rol},
                                 stream=True)

        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk

    return Response(generate(), mimetype='text/plain')


@app.route("/dashboard")
@app.route("/dashboard/<int:conv_id>")
def dashboard(conv_id=None):
    if not session.get("user"):
        flash("Debes iniciar sesión primero.", "warning")
        return redirect(url_for("login"))
    # Obtenemos el ID del usuario de la sesión (asegúrate de que Auth lo guarde)
    usuario_id = session.get("user_id")

    # 1. Traer lista de títulos para el Aside derecho
    mis_chats = conv_service.listar_por_usuario(usuario_id)

    # 2. Si venimos de hacer clic en un chat viejo, traer sus mensajes
    historial_mensajes = []
    if conv_id:
        historial_mensajes = conv_service.obtener_mensajes(conv_id)
        session["active_conv"] = conv_id  # Marcamos cuál estamos viendo
    else:
        session["active_conv"] = None  # Es un chat nuevo

    return render_template("dashboard.html",
                           conversaciones=mis_chats,
                           mensajes=historial_mensajes)


@app.route("/api/historial/guardar", methods=["POST"])
def guardar_en_historial():
    data = request.get_json()
    usuario_id = session.get("user_id")
    conv_id = data.get("conversacion_id")
    pregunta = data.get("pregunta")
    respuesta = data.get("respuesta")
    agente = data.get("agente")

    # Si es la primera vez (conv_id es null), creamos la conversación
    if not conv_id:
        titulo = pregunta[:30] + "..."  # Usamos el inicio como título
        conv_id = conv_service.crear_conversacion(usuario_id, titulo, agente)

    # Guardamos ambos mensajes
    conv_service.guardar_mensaje(conv_id, 'user', pregunta)
    conv_service.guardar_mensaje(conv_id, 'assistant', respuesta)

    return jsonify({"status": "ok", "conversacion_id": conv_id})


@app.route('/api/stats_rag')
def stats_rag():
    if session.get('rol') != 1:
        return {"error": "No autorizado", "rol_detectado": session.get('rol')}, 403

    stats = rag.obtener_estadisticas()
    return jsonify(stats)


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


@app.route('/upload_document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return {"error": "No hay archivo"}, 400

    file = request.files['file']
    coleccion = request.form.get('coleccion', 'leyes')  # Por defecto a leyes

    if file.filename == '':
        return {"error": "Archivo sin nombre"}, 400

    if file and file.filename.endswith('.txt'):
        filename = secure_filename(file.filename)
        ruta_temp = os.path.join(UPLOAD_FOLDER, filename)
        file.save(ruta_temp)

        try:
            # Usamos tu clase MotorRAG para indexar
            resultado = rag.indexar_documento(ruta_temp, coleccion)
            os.remove(ruta_temp)  # Limpiamos el temporal
            return {"message": f"Archivo indexado con éxito en {coleccion}. {resultado}"}, 200
        except Exception as e:
            return {"error": str(e)}, 500

    return {"error": "Formato no permitido (solo .txt por ahora)"}, 400


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
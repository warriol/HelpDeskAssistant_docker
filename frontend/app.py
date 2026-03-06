import logging
import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from clases.Auth import Auth
from clases.Usuarios import Usuarios

# Create the log directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure logging
log_file = os.path.join(log_dir, "app.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
auth = Auth()

app.secret_key = os.urandom(24)

# Enable Flask logging
app.config["DEBUG"] = True

# Routes for POST
@app.route("/login", methods=["POST"])
def login():
    session["user"] = None
    session["mensaje"] = None
    # Get form data
    email = request.form["email"]
    password = request.form["password"]
    # Attempt to log in the user
    mensaje = auth.login(email, password)
    # Log the message
    app.logger.info(mensaje)
    # Show the message in the Flask response
    return redirect(url_for(mensaje))

# Routes for GET
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]

        auth = Auth()
        mensaje = auth.registrar(nombre, email, password)
        session["mensaje"] = "Usuario registrado correctamente."

        app.logger.info("Registro: " + mensaje)
        return render_template("login.html")

    return render_template("register.html")

# Application routes
@app.route("/correoIncorrecto")
def correoIncorrecto():
    session["mensaje"] = "El correo es incorrecto."
    return render_template("login.html")

@app.route("/estadoInactivo")
def estadoInactivo():
    session["mensaje"] = "El usuario no está activo."
    return render_template("login.html")

@app.route("/contraseñaIncorrecta")
def contraseñaIncorrecta():
    session["mensaje"] = "La contraseña es incorrecta."
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    # Show the dashboard
    if session["user"] is None:
        user = session["user"]
        app.logger.info(f"Email recibido: {user}")
        return render_template("login.html")
    else:
        return render_template("dashboard.html")

@app.route("/admin")
def admin():
    # Show the admin
    if session["rol"] != "Administrador":
        app.logger.info(f"Rol incorrecto: {session['rol']}")
        return redirect(url_for("home"))
    else:
        return render_template("admin.html")

@app.route("/logout")
def logout():
    # Log out
    session["user"] = None
    session["rol"] = None
    return render_template("login.html")

@app.route("/")
def home():
    # Show login
    return render_template("login.html")

@app.route("/usuarios")
def usuarios():
    # Create an instance of the Usuarios class
    users = Usuarios()
    # Create an empty list to store the results
    datos = []
    # Get the results and add them to a list
    datos = users.get_usuarios()
    # Log the number of results
    app.logger.info("Página de inicio accedida")
    app.logger.info(f"Consulta ejecutada. Registros encontrados: {len(datos)}")
    # Show the data in the Flask response
    return f"¡Flask está funcionando correctamente!<br>Usuarios:<br>{'<br>'.join(map(str, datos))}"

@app.route("/api/usuarios", methods=["GET"])
def obtener_usuarios():
    users = Usuarios()
    datos = users.get_usuarios_completo()
    app.logger.info(f"Consulta ejecutada. Registros encontrados: {datos}")
    return jsonify(datos)

@app.route("/api/usuarios", methods=["POST"])
def agregar_usuario():
    data = request.get_json()
    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")

    auth = Auth()
    mensaje = auth.registrar(nombre, email, password)
    return jsonify({"mensaje": mensaje}), 201

@app.route("/api/usuarios/<int:id>", methods=["PUT"])
def editar_usuario(id):
    data = request.get_json()
    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")

    users = Usuarios()
    mensaje = users.editar_usuario(id, nombre, email, password)
    return jsonify({"mensaje": mensaje}), 200

# Capture unhandled errors
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Error: {e}")
    session["error"] = f"Ocurrió un error: {str(e)}"
    return render_template("login.html"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
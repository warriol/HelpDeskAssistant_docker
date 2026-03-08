import os
import logging
from flask import Flask, render_template, flash, redirect, url_for

from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.perfil import perfil_bp

# Configuración de Logs
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

# REGISTRO DEL BLUEPRINT
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(perfil_bp)

# --- INICIO ---
@app.route("/")
def index():
    return render_template("index.html")


# --- CAPTURA DE ERRORES ---
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Error crítico: {e}")
    flash(f"Ocurrió un error inesperado: {str(e)}", "danger")
    return redirect(url_for("index"))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from clases.Auth import Auth

auth_bp = Blueprint('auth', __name__)
auth_service = Auth()

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        resultado = auth_service.login(email, password)

        if resultado == "dashboard":
            session["urlia"] = os.getenv("URLIA", "http://localhost:5000")
            return redirect(url_for("chat.dashboard"))

        mensajes_error = {
            "correoIncorrecto": "El correo electrónico no existe.",
            "estadoInactivo": "Tu cuenta aún no ha sido activada.",
            "contraseñaIncorrecta": "La contraseña es incorrecta."
        }
        flash(mensajes_error.get(resultado, "Error de inicio de sesión"), "danger")
        return redirect(url_for("auth.login"))

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]

        mensaje = auth_service.registrar(nombre, email, password)
        flash("Registro exitoso. Por favor, inicia sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
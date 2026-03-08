from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from clases.Auth import Auth
from clases.Usuarios import Usuarios

perfil_bp = Blueprint('perfil', __name__)
auth_service = Auth()
user_service = Usuarios()


@perfil_bp.route("/ajustes")
def ajustes():
    if not session.get("user"):
        return redirect(url_for("auth.login"))
    return render_template("ajustes.html")


@perfil_bp.route("/update_profile", methods=["POST"])
def update_profile():
    try:
        nombre = request.form["nombre"]

        user_service.editar_usuario_perfil(session['user_id'], nombre)
        session["nombre"] = nombre
        flash("Perfil actualizado correctamente.", "success")
    except Exception as e:
        flash("Error al actualizar el perfil.", "danger")
        print(f"Error en update_profile: {e}")

    return redirect(url_for("perfil.ajustes"))


@perfil_bp.route("/update_password", methods=["POST"])
def update_password():
    try:
        new_pass = request.form["new_password"]
        confirm_pass = request.form["confirm_password"]

        if new_pass != confirm_pass:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for("perfil.ajustes"))

        hashed = auth_service.hash_password(new_pass)

        user_service.cambiar_password(session['user_id'], hashed)
        flash("Contraseña actualizada con éxito.", "success")
    except Exception as e:
        flash("Error al actualizar la contraseña.", "danger")
        print(f"Error en update_password: {e}")

    return redirect(url_for("perfil.ajustes"))
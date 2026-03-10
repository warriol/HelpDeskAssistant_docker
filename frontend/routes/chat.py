import requests
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, Response, jsonify, \
    stream_with_context

# Importamos tus servicios
from clases.Conversaciones import Conversaciones
from clases.MotorRAG import MotorRAG

chat_bp = Blueprint('chat', __name__)
conv_service = Conversaciones()
rag = MotorRAG()


@chat_bp.route("/dashboard")
@chat_bp.route("/dashboard/<int:conv_id>")
def dashboard(conv_id=None):
    if not session.get("user"):
        flash("Debes iniciar sesión primero.", "warning")
        return redirect(url_for("auth.login"))  # Apunta al blueprint auth

    usuario_id = session.get("user_id")
    mis_chats = conv_service.listar_por_usuario(usuario_id)

    historial_mensajes = []
    if conv_id:
        historial_mensajes = conv_service.obtener_mensajes(conv_id)
        session["active_conv"] = conv_id
    else:
        session["active_conv"] = None

    return render_template("dashboard.html",
                           conversaciones=mis_chats,
                           mensajes=historial_mensajes)


@chat_bp.route('/chat_con_contexto', methods=['POST'])
def chat_con_contexto():
    data = request.json
    pregunta = data.get("question")
    rol = data.get("role")

    contexto = rag.buscar_contexto(pregunta, rol)

    def generate():
        url_backend = "http://backend:5000/chat"
        response = requests.post(url_backend,
                                 json={"question": pregunta, "contexto": contexto, "role": rol},
                                 stream=True)

        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk

    return Response(generate(), mimetype='text/plain')



@chat_bp.route("/api/historial/guardar", methods=["POST"])
def guardar_en_historial():
    data = request.get_json()
    usuario_id = session.get("user_id")
    conv_id = data.get("conversacion_id")
    pregunta = data.get("pregunta")
    respuesta = data.get("respuesta")
    agente = data.get("agente")

    if not conv_id or conv_id == "null":
        titulo = pregunta[:30] + "..."
        conv_id = conv_service.crear_conversacion(usuario_id, titulo, agente)

    if conv_id:
        try:
            conv_service.guardar_mensaje(conv_id, 'user', pregunta)
            conv_service.guardar_mensaje(conv_id, 'assistant', respuesta)

            # Devolvemos el conv_id para que el JS sepa en qué chat estamos
            return jsonify({"status": "ok", "conversacion_id": conv_id})
        except Exception as e:
            flash(f"Error guardando mensajes: {e}", "warning")
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "error", "message": "No se pudo crear/obtener conv_id"}), 500


@chat_bp.route("/dashboard/delete/<int:conv_id>", methods=["POST"])
def delete_conversation(conv_id):
    if not session.get("user"): return jsonify({"error": "No autorizado"}), 401

    if conv_service.eliminar_conversacion(conv_id):
        return jsonify({"success": True})
    return jsonify({"error": "No se pudo eliminar"}), 500


@chat_bp.route("/dashboard/rename/<int:conv_id>", methods=["POST"])
def rename_conversation(conv_id):
    if not session.get("user"): return jsonify({"error": "No autorizado"}), 401

    nuevo_titulo = request.json.get("titulo")
    if conv_service.actualizar_titulo(conv_id, nuevo_titulo):
        return jsonify({"success": True})
    return jsonify({"error": "No se pudo renombrar"}), 500


@chat_bp.route("/api/sidebar_chats")
def sidebar_chats():
    if not session.get("user"):
        return "", 401

    usuario_id = session.get("user_id")
    mis_chats = conv_service.listar_por_usuario(usuario_id)

    return render_template("partials/_sidebar_items.html", conversaciones=mis_chats)
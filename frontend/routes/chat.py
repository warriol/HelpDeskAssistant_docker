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

    prompt_final = f"Eres un asistente legal... [resto de tu prompt] ... {contexto} ... {pregunta}"

    def generate():
        url_backend = "http://backend:5000/chat"
        response = requests.post(url_backend,
                                 json={"question": prompt_final, "role": rol},
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
    return jsonify({"status": "ok", "conversacion_id": conv_id})


@chat_bp.route("/dashboard/delete/<int:conv_id>", methods=["POST"])
def delete_conversation(conv_id):
    if conv_service.eliminar_conversacion(conv_id):
        return jsonify({"success": True})
    return jsonify({"error": "Error"}), 500


@chat_bp.route("/dashboard/rename/<int:conv_id>", methods=["POST"])
def rename_conversation(conv_id):
    nuevo_titulo = request.json.get("titulo")
    if conv_service.actualizar_titulo(conv_id, nuevo_titulo):
        return jsonify({"success": True})
    return jsonify({"error": "Error"}), 500
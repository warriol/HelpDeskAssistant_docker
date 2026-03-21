import os
import requests
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, Response, jsonify, \
    stream_with_context
from dotenv import load_dotenv
import redis
import json
import html

# Importamos tus servicios
from clases.Conversaciones import Conversaciones
from clases.MotorRAG import MotorRAG

chat_bp = Blueprint('chat', __name__)
conv_service = Conversaciones()
rag = MotorRAG()

load_dotenv()

# Conexión a Redis
try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True,
        socket_connect_timeout=2
    )
    # Probar conexión
    r.ping()
except Exception as e:
    print(f"⚠️ Redis no disponible: {e}")
    r = None

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

        # --- ENRIQUECIMIENTO CON REDIS ---
        for msg in historial_mensajes:
            # Solo buscamos votos para las respuestas del asistente
            if msg.get('rol') != 'user':
                # Normalizamos la pregunta para buscar la llave exacta
                pregunta_key = msg.get('pregunta', '').strip().lower()
                agente = msg.get('agente', '')
                redis_key = f"{agente}:{pregunta_key}"

                cache_data = r.get(redis_key)
                if cache_data:
                    data = json.loads(cache_data)
                    # Agregamos el valor al diccionario del mensaje para Jinja2
                    msg['votos_cache'] = data.get('votos', 0)
                else:
                    msg['votos_cache'] = 0

        session["active_conv"] = conv_id
    else:
        session["active_conv"] = None

    return render_template("dashboard.html",
                           conversaciones=mis_chats,
                           mensajes=historial_mensajes)


@chat_bp.route('/chat_con_contexto', methods=['POST'])
def chat_con_contexto():
    data = request.json
    pregunta = html.escape(data.get("question").strip().lower())  # Normalizamos la pregunta
    rol = data.get("role")

    redis_key = f"{rol}:{pregunta}"
    cache_data = r.get(redis_key)

    if cache_data:
        info = json.loads(cache_data)
        if info.get('votos', 0) >= 0:
            return Response(info.get('respuesta'), mimetype='text/plain')

    contexto = rag.buscar_contexto(pregunta, rol)

    def generate():
        url_backend = "http://backend:5000/chat"
        response = requests.post(url_backend,
                                 json={"question": pregunta, "contexto": contexto, "role": rol},
                                 stream=True)

        full_response = ""
        for chunk in response.iter_content(chunk_size=1024): # Leemos la respuesta en chunks para ir enviándola al frontend en tiempo real
            if chunk:
                decoded_chunk = chunk.decode('utf-8')
                full_response += decoded_chunk
                yield chunk

        # Guardamos la respuesta completa en Redis para futuras consultas
        if r:
            try:
                r.set(redis_key, json.dumps({
                    "pregunta": pregunta,
                    "respuesta": full_response,
                    "rol": rol,
                    "votos": 0
                }))
            except Exception as e:
                print(f"Error al guardar en caché: {e}")

    return Response(generate(), mimetype='text/plain')


@chat_bp.route('/votar_pregunta', methods=['POST'])
def votar_pregunta():
    data = request.json
    pregunta = data.get("question").strip().lower()
    rol = data.get("role")
    puntos = int(data.get("voto"))

    redis_key = f"{rol}:{pregunta}"
    cache_data = r.get(redis_key)

    if cache_data:
        info = json.loads(cache_data)
        info['votos'] = info.get('votos', 0) + puntos
        r.set(redis_key, json.dumps(info))
        return {"status": "ok", "nuevos_votos": info['votos']}

    return {"status": "error", "message": "Pregunta no encontrada"}, 404

@chat_bp.route('/faqs')
def faqs():
    # Renderizamos una nueva página, similar al dashboard pero enfocada en la búsqueda global
    return render_template('faqs.html')


@chat_bp.route('/get_faqs')
def get_faqs():
    rol_filtro = request.args.get('role')

    # Buscamos llaves que sigan el patrón "rol:pregunta"
    pattern = f"{rol_filtro}:*" if rol_filtro and rol_filtro != 'todos' else "*"
    keys = r.keys(pattern)

    lista_faqs = []
    for k in keys:
        try:
            raw_data = r.get(k)
            if raw_data:
                data = json.loads(raw_data)
                # Si tiene mas de 5 votos negativos, lo consideramos no relevante para mostrar en FAQs
                if data.get('votos', 0) > -5:
                    lista_faqs.append(data)
        except Exception as e:
            print(f"Error procesando llave {k}: {e}")
            continue

    lista_faqs = sorted(lista_faqs, key=lambda x: x.get('votos', 0), reverse=True)

    return jsonify(lista_faqs)

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
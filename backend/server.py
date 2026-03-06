import requests
import pandas as pd
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import os

app = Flask(__name__)
# Permitimos explícitamente el origen del frontend
CORS(app, resources={r"/*": {"origins": ["http://localhost:8501", "http://127.0.0.1:8501"]}})

# En Docker, usamos el nombre del servicio definido en docker-compose
OLLAMA_API_URL = "http://ollama:11434/api/generate"

# Verificación de datos de entrenamiento (SGSP)
CSV_PATH = "train.csv"
if os.path.exists(CSV_PATH):
    train_data = pd.read_csv(CSV_PATH, sep=",", encoding="utf-8")
else:
    print(f"⚠️ Alerta: No se encontró {CSV_PATH}. El rol SGSP no funcionará correctamente.")
    train_data = pd.DataFrame(columns=['Contexto', 'Response'])

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get("question", "").strip()
    role = data.get("role", "leyes").strip()

    if not question:
        return jsonify({"response": "Por favor, ingresa una pregunta."}), 400

    # Lógica de Prompts (Derecho Penal Uruguayo / Ortografía / SGSP)
    if role == "leyes":
        prompt = (
            "Eres un abogado experto en derecho penal uruguayo. "
            "Responde siempre en español, utilizando un lenguaje técnico pero claro. "
            "Debes fundamentar tus respuestas con base en el Código Penal y Código de Faltas de Uruguay. "
            f"Pregunta del usuario: {question}"
        )
    elif role == "ortografia":
        prompt = f"Eres un profesor de lengua española. Revisa este texto, aplica sangrías de 5 espacios al inicio de párrafos e indica correcciones al final: {question}"
    elif role == "sgsp":
        context = "\n".join(f"{row['Contexto']}: {row['Response']}" for _, row in train_data.iterrows())
        prompt = f"Experto en SGSP. Usa este contexto:\n{context}\nPregunta: {question}"
    else:
        return jsonify({"response": "Rol no reconocido."}), 400

    def generate():
        payload = {
            "model": "gemma3:4b", # Asegúrate de que este modelo esté descargado en Ollama
            "prompt": prompt,
            "stream": True
        }
        try:
            with requests.post(OLLAMA_API_URL, json=payload, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        response_text = chunk.get("response", "")
                        yield response_text
                        if chunk.get("done"):
                            break
        except Exception as e:
            yield f" Error de conexión con Ollama: {str(e)}"

    return Response(generate(), content_type='text/plain')

@app.route('/')
def saludo():
    return 'Servidor de Wilson Arriola (Calidad de Información - MI) Online!'

if __name__ == '__main__':
    # Importante: host 0.0.0.0 para que sea accesible desde fuera del contenedor
    app.run(host="0.0.0.0", port=5000)
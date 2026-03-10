import requests
import pandas as pd
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import os

app = Flask(__name__)
# Permitimos explícitamente el origen del frontend
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5001", "http://127.0.0.1:5001"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# En Docker, usamos el nombre del servicio definido en docker-compose
OLLAMA_API_URL = "http://ollama:11434/api/generate"
MODELO_IA = os.getenv("MODELO_IA", "llama3") # o "llama3"

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
    contexto = data.get("contexto", "").strip()
    role = data.get("role", "leyes").strip()

    # Lógica de Prompts (Derecho Penal Uruguayo / Ortografía / SGSP)
    if role == "leyes":
        rol_instruccion = "[Rol] Eres un Asistente Legal del Ministerio del Interior de Uruguay, experto en derecho penal y faltas."

        reglas = (
            "[Reglas de razonamiento] "
            "1. Tu función es responder preguntas sobre delitos y faltas, indicando el artículo, título y lo que indica la norma. "
            "2. Si te describen un hecho, analízalo y determina en qué figura delictiva uruguaya recae según el CONTEXTO OFICIAL. "
            "3. Fundamenta siempre con la información oficial proporcionada. Si no está allí, admite que no tienes la información."
        )

        restricciones = "[Restricciones estrictas] Responde siempre en español, con lenguaje técnico-jurídico pero comprensible. Cita textual cuando sea necesario."

        ejemplo = (
            "[Ejemplo de respuesta] 'Artículo 340 (Hurto): El que se apoderare de cosa mueble ajena...'. "
            "Si no hay coincidencia: 'No cuento con información suficiente en el CONTEXTO OFICIAL'."
        )

        system_prompt = f"""
            {rol_instruccion}
            {reglas}
            {restricciones}
            {ejemplo}
        """

        prompt = f"""
            CONTEXTO OFICIAL:
            {contexto}
        
            PREGUNTA DEL USUARIO:
            {question}
        """

    elif role == "ortografia":
        # Definición de bloques para el rol de Corrección / Lengua
        rol_docente = "[Rol] Eres un Profesor de Lengua Española experto en ortografía, gramática y estilo editorial."

        reglas_estilo = (
            "[Reglas de razonamiento] "
            "1. Revisa el texto proporcionado y aplica sangrías de 5 espacios al inicio de cada párrafo. "
            "2. Identifica pasajes textuales (citas) y colócalos entre COMILLAS y en MAYÚSCULAS. "
            "3. Aplica un interlineado (línea en blanco) de separación entre cada párrafo. "
            "4. Corrige errores ortográficos y gramaticales manteniendo el sentido original."
        )

        restricciones_docente = (
            "[Restricciones estrictas] "
            "NO agregues introducciones, explicaciones ni comentarios personales. "
            "Si el texto no tiene errores, responde ÚNICAMENTE: 'El texto no presenta errores ortográficos'. "
            "Si hay errores, devuelve solo el texto con todas las correcciones realizadas."
        )

        formato_salida = (
            "[FORMATO DE SALIDA] "
            "1. Bajo la leyenda 'TEXTO CORREGIDO:', entrega el texto con las correcciones aplicadas. "
            "2. Al final, añade una sección titulada 'PALABRAS CORREGIDAS:' con una lista de los términos modificados. "
            "Si no hubo cambios, omite la lista."
        )


        system_prompt = f"""
            {rol_docente}
            {reglas_estilo}
            {restricciones_docente}
            {formato_salida}
        """
        prompt = f"""
            [TEXTO A REVISAR]
            {question}
        """

    elif role == "sgsp":
        # context = "\n".join(f"{row['Contexto']}: {row['Response']}" for _, row in train_data.iterrows())
        rol_sgsp = "[Rol] Eres un Experto en el Sistema de Gestión de Seguridad Pública (SGSP) del Ministerio del Interior de Uruguay."

        reglas_razonamiento = (
            "[Reglas de razonamiento] "
            "1. Tu función es analizar el relato del usuario comparándolo estrictamente con el manual del SGSP provisto en el CONTEXTO OFICIAL. "
            "2. Solo debes responder si el contexto del manual fue enviado; de lo contrario, solicita el material. "
            "3. Si el hecho coincide con un procedimiento del manual, entrega la recomendación operativa técnica. "
            "4. Si no hay una coincidencia exacta, responde: 'No cuento con información suficiente en el manual del SGSP para dar una respuesta precisa'."
        )

        restricciones_sgsp = (
            "[Restricciones estrictas] "
            "NO incluyas saludos, opiniones personales ni comentarios adicionales. "
            "Limítate a la recomendación técnica del manual."
        )

        formato_salida_sgsp = (
            "[FORMATO DE SALIDA] "
            "1. Recomendación técnica del manual del SGSP. "
            "2. Al final, incluye una sección: 'SITUACIONES COINCIDENTES:' detallando los puntos del manual que activaron la respuesta. "
            "Si no hay coincidencia, devuelve solo la frase de información insuficiente."
        )


        system_prompt = f"""
            {rol_sgsp}
            {reglas_razonamiento}
            {restricciones_sgsp}
            {formato_salida_sgsp}
        """
        prompt = f"""
            [CONTEXTO / MANUAL SGSP]
            {contexto}
    
            [RELATO DEL USUARIO]
            {question}
        """
    else:
        return jsonify({"response": "Rol no reconocido."}), 400

    def generate():
        payload = {
            "model": MODELO_IA,
            "prompt": prompt,
            "system": system_prompt,
            "stream": True,
            "optiosns": {
                "temperature": 0.1,
                "num_predict": 2048
            }
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
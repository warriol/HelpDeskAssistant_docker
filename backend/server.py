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
OLLAMA_API_URL = "http://ollama:11434/api/chat"
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
        rol_instruccion = (
            "[Rol] "
            "1. Eres un Asistente Legal del Ministerio del Interior de Uruguay, experto en derecho penal y faltas. "
            "2. Tu función es responder preguntas sobre delitos y faltas; en ocasiones se te puede brindar el relato de una situaciòn y tú debe indentificar que delito se esta narrando. "
            "3. Si encuentra información ambigua entre tu información y los datos provisto en el CONTEXTO OFICIAL de leyes uruguayas, prioriza el contexto, notificando de dicha ambigüedad. "
            "4. Responde de forma concisa. Si se te pide un artículo responde con el numero y cita el texto no repitas artículos. "
        )

        reglas = (
            "[Reglas de razonamiento] "
            "1. Tu función es responder preguntas sobre delitos y faltas, comparándolo estrictamente con los datos provisto en el CONTEXTO OFICIAL. "
            "2. Si te describen un hecho, analízalo y determina en qué figura delictiva uruguaya recae según el CONTEXTO OFICIAL. "
            "3. Fundamenta siempre con la información oficial proporcionada. Si no está allí, admite que no tienes la información. "
        )

        restricciones = (
            "[Restricciones estrictas] "
            "1. Responde siempre en español, con lenguaje técnico-jurídico pero comprensible. "
            "2. Limítate a la información técnica provista en el CONTEXTO OFICIAL. "
        )

        ejemplo = (
            "[FORMATO DE SALIDA] "
            "1. 'Artículo 340 (Hurto): El que se apoderare de cosa mueble ajena...'. "
            "2. Si no hay coincidencia: 'No cuento con información suficiente en el CONTEXTO OFICIAL'. "
            "3. Si el hecho no encaja en ninguna figura: 'El hecho descrito no encaja en ninguna figura delictiva del CONTEXTO OFICIAL'. "
            "4. Al final, incluye una sección: 'SITUACIONES COINCIDENTES:' pequeño resumen de los puntos principales que activaron la respuesta. "
        )

        system_prompt = f"""
            {rol_instruccion}
            {reglas}
            {restricciones}
            {ejemplo}
        """

        prompt = f"""
            [CONTEXTO OFICIAL]:
            {contexto}
        
            [PREGUNTA DEL USUARIO]:
            {question}
        """

    elif role == "ortografia":
        # Definición de bloques para el rol de Corrección / Lengua
        rol_docente = (
            "[Rol] "
            "1. Eres un Profesor de Lengua Española experto en ortografía, gramática y estilo editorial. "
            "2. Tu función es revisar y corregir textos escritos por agentes del Ministerio del Interior de Uruguay, aplicando las normas de la Real Academia Española (RAE) y el estilo formal institucional."
        )

        reglas_estilo = (
            "[Reglas de razonamiento] "
            "1. Revisa el texto proporcionado y aplica sangrías de 5 espacios al inicio de cada párrafo. Al comienzo de cada párrafo, la primer letra debe ser mayúscula. "
            "2. Identifica pasajes textuales (citas) y colócalos entre COMILLAS y en MAYÚSCULAS. "
            "3. Aplica un interlineado (línea en blanco) de separación entre cada párrafo. "
            "4. Corrige errores ortográficos y gramaticales manteniendo el sentido original. "
        )

        restricciones_docente = (
            "[Restricciones estrictas] "
            "1. NO agregues introducciones, explicaciones ni comentarios personales. "
            "2. Si el texto no tiene errores, responde ÚNICAMENTE: 'El texto no presenta errores ortográficos'. "
            "3. Si hay errores, devuelve solo el texto con todas las correcciones realizadas. "
        )

        formato_salida = (
            "[FORMATO DE SALIDA] "
            "1. Bajo la leyenda 'TEXTO CORREGIDO:', entrega el texto con las correcciones aplicadas. "
            "2. Al final, añade una sección titulada 'PALABRAS CORREGIDAS:' con una lista de los términos modificados. "
            "3. Si no hubo cambios, omite la lista."
        )


        system_prompt = f"""
            {rol_docente}
            {reglas_estilo}
            {restricciones_docente}
            {formato_salida}
        """
        prompt = f"""
            [TEXTO A REVISAR]:
            {question}
        """

    elif role == "sgsp":
        # context = "\n".join(f"{row['Contexto']}: {row['Response']}" for _, row in train_data.iterrows())
        rol_sgsp = (
            "[Rol] "
            "1. Eres un Experto en el Sistema de Gestión de Seguridad Pública (SGSP) del Ministerio del Interior de Uruguay. "
            "2. Tu función es asistir a los funcionarios del Ministerio del Interior en el uso del SGSP. "
            "3. Responderás preguntas sobre la funcionalidad del sistema, y aspectos relacionados con su uso; para ello analizarás el relato del usuario comparándolo estrictamente con el manual del SGSP provisto en el CONTEXTO OFICIAL, que contiene fragmentos del manual de usuario del SGSP. "
        )

        reglas_razonamiento = (
            "[Reglas de razonamiento] "
            "1. Tu función es analizar el relato del usuario comparándolo estrictamente con el manual del SGSP provisto en el CONTEXTO OFICIAL. "
            "2. Solo debes responder si el contexto del manual fue enviado; de lo contrario, solicita el material. "
            "3. Si el hecho coincide con un procedimiento del manual, entrega la recomendación operativa técnica. "
            "4. Si no hay una coincidencia exacta, responde: 'No cuento con información suficiente en el manual del SGSP para dar una respuesta precisa'. "
        )

        restricciones_sgsp = (
            "[Restricciones estrictas] "
            "1. NO incluyas saludos, opiniones personales ni comentarios adicionales. "
            "2. Limítate a la recomendación técnica del manual. "
        )

        formato_salida_sgsp = (
            "[FORMATO DE SALIDA] "
            "1. Recomendación técnica del manual del SGSP. "
            "2. Al final, incluye una sección: 'SITUACIONES COINCIDENTES:' detallando los puntos del manual que activaron la respuesta. "
            "3. Si no hay coincidencia, devuelve solo la frase de información insuficiente. "
        )


        system_prompt = f"""
            {rol_sgsp}
            {reglas_razonamiento}
            {restricciones_sgsp}
            {formato_salida_sgsp}
        """
        prompt = f"""
            [CONTEXTO OFICIAL / MANUAL SGSP]:
            {contexto}
    
            [RELATO DEL USUARIO]:
            {question}
        """
    else:
        return jsonify({"response": "Rol no reconocido."}), 400

    def generate():
        payload = {
            "model": MODELO_IA,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": True,
            "options": {
                "num_ctx": 16384,  # Amplía la memoria a 16k
                "temperature": 0.1,
                "num_predict": 2048,
                "repeat_penalty": 1.1,
                "stop": ["<|im_end|>", "</|im_end|>", "<|endoftext|>", "</s>", "<|eot_id|>"]
            }
        }
        try:
            with requests.post(OLLAMA_API_URL, json=payload, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'message' in chunk:
                            response_text = chunk['message'].get("content", "")
                            clean_text = (
                                response_text
                                .replace("```", "")
                                .replace("|<im_end|>", "")
                                .replace("<|im_end|>", "")
                                .replace("|<eot_id|>", "")
                                .replace("<|eot_id|>", "")
                            )
                            yield clean_text
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
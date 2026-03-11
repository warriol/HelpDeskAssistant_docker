import os
import chromadb
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.config import Settings

class MotorRAG:
    def __init__(self):
        self.host = os.environ.get("CHROMA_HOST", "http://chroma:8000")
        self.client = chromadb.HttpClient(
            host="chroma",
            port=8000,
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )

    def indexar_documento(self, ruta_archivo, coleccion_nombre):
        contenido = None
        # 1. Intentamos detectar el encoding sin romper el texto
        encodings_a_probar = ['utf-8', 'latin-1', 'cp1252']

        for enc in encodings_a_probar:
            try:
                with open(ruta_archivo, 'r', encoding=enc) as f:
                    contenido = f.read()
                print(f"Leído exitosamente con: {enc}")
                break
            except UnicodeDecodeError:
                continue

        if contenido is None:
            return "Error: No se pudo determinar la codificación del archivo."

        # 2. Guardamos una versión limpia en UTF-8 para que TextLoader no falle
        # Esto asegura que el manual del SGSP se guarde perfecto
        try:
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
        except Exception as e:
            return f"Error al normalizar archivo: {e}"

        # 3. Procesamos con LangChain
        try:
            loader = TextLoader(ruta_archivo, encoding='utf-8')
            documento = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
            chunks = text_splitter.split_documents(documento)

            coleccion = self.client.get_or_create_collection(name=coleccion_nombre)

            documentos_texto = [c.page_content for c in chunks]
            metadatos = [{"fuente": os.path.basename(ruta_archivo)} for _ in chunks]
            ids = [f"{coleccion_nombre}_{os.path.basename(ruta_archivo)}_{i}" for i in range(len(chunks))]

            coleccion.add(
                documents=documentos_texto,
                metadatas=metadatos,
                ids=ids
            )
            return f"Éxito: {len(chunks)} fragmentos indexados correctamente."
        except Exception as e:
            return f"Error durante la indexación en Chroma: {e}"

    def buscar_contexto(self, pregunta, coleccion_nombre):
        coleccion = self.client.get_or_create_collection(name=coleccion_nombre)
        resultados = coleccion.query(
            query_texts=[pregunta],
            n_results=5
        )
        return "\n\n".join(resultados['documents'][0])

    def obtener_estadisticas(self):
        stats = {}
        colecciones = ["leyes", "sgsp", "ortografia"]

        for nombre in colecciones:
            try:
                col = self.client.get_collection(name=nombre)
                count = col.count()
                stats[nombre] = count
            except Exception:
                stats[nombre] = 0
        return stats
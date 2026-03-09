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
        try:
            with open(ruta_archivo, 'r', encoding='utf-8', errors='replace') as f:
                contenido = f.read()

            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)

            loader = TextLoader(ruta_archivo, encoding='utf-8')
            documento = loader.load()

        except Exception as e:
            return f"Error crítico de lectura: {e}"

        try:
            loader = TextLoader(ruta_archivo, encoding='utf-8')
            documento = loader.load()
        except RuntimeError:
            loader = TextLoader(ruta_archivo, encoding='latin-1')
            documento = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_documents(documento)

        coleccion = self.client.get_or_create_collection(name=coleccion_nombre)

        documentos_texto = [c.page_content for c in chunks]
        metadatos = [{"fuente": ruta_archivo} for _ in chunks]
        ids = [f"{coleccion_nombre}_{i}" for i in range(len(chunks))]

        coleccion.add(
            documents=documentos_texto,
            metadatas=metadatos,
            ids=ids
        )
        return f"Éxito: {len(chunks)} fragmentos indexados."

    def buscar_contexto(self, pregunta, coleccion_nombre):
        coleccion = self.client.get_or_create_collection(name=coleccion_nombre)
        resultados = coleccion.query(
            query_texts=[pregunta],
            n_results=3  # Traemos los 3 párrafos más parecidos, tarda un poco mas, lo bajamos a 2 para que sea más rápido en esta demo. En producción podríamos subirlo a 3 o 4.
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
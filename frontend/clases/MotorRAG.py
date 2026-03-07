import os
import chromadb
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class MotorRAG:
    def __init__(self):
        # Nos conectamos al contenedor 'chroma' que definimos en el compose
        self.host = os.environ.get("CHROMA_HOST", "http://chroma:8000")
        self.client = chromadb.HttpClient(host="chroma", port=8000)

    def indexar_documento(self, ruta_archivo, coleccion_nombre):
        """Lee un archivo y lo guarda en ChromaDB dividido en trozos"""
        # 1. Cargar el texto
        try:
            loader = TextLoader(ruta_archivo, encoding='utf-8')
            documento = loader.load()
        except RuntimeError:
            loader = TextLoader(ruta_archivo, encoding='latin-1')
            documento = loader.load()

        # 2. Dividir en trozos (Chunks) de 1000 caracteres
        # Usamos un overlap (solapamiento) para no cortar frases a la mitad
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_documents(documento)

        # 3. Obtener o crear la colección (ej: 'leyes')
        coleccion = self.client.get_or_create_collection(name=coleccion_nombre)

        # 4. Preparar datos para Chroma
        documentos_texto = [c.page_content for c in chunks]
        metadatos = [{"fuente": ruta_archivo} for _ in chunks]
        ids = [f"{coleccion_nombre}_{i}" for i in range(len(chunks))]

        # 5. Guardar
        coleccion.add(
            documents=documentos_texto,
            metadatas=metadatos,
            ids=ids
        )
        return f"Éxito: {len(chunks)} fragmentos indexados."

    def buscar_contexto(self, pregunta, coleccion_nombre):
        """Busca los fragmentos más relevantes para una pregunta"""
        coleccion = self.client.get_or_create_collection(name=coleccion_nombre)
        resultados = coleccion.query(
            query_texts=[pregunta],
            n_results=2  # Traemos los 3 párrafos más parecidos, tarda un poco mas, lo bajamos a 2 para que sea más rápido en esta demo. En producción podríamos subirlo a 3 o 4.
        )
        return "\n\n".join(resultados['documents'][0])

    def obtener_estadisticas(self):
        stats = {}
        colecciones = ["leyes", "sgsp", "ortografia"]

        for nombre in colecciones:
            try:
                # Intentamos obtener la colección
                col = self.client.get_collection(name=nombre)
                count = col.count()
                stats[nombre] = count
            except Exception:
                # Si la colección aún no existe, el conteo es 0
                stats[nombre] = 0
        return stats
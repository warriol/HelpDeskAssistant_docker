import os
import chromadb
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import logging

# Configuración de logging para depuración
log_file = "motor_rag_debug.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MotorRAG")

class MotorRAG:
    def __init__(self):
        # Configuración de la función de embeddings usando el modelo Nomic en Ollama
        # Esta URL asume que el contenedor se llama 'ollama_server' dentro de tu red de Docker
        self.embedding_fn = embedding_functions.OllamaEmbeddingFunction(
            url="http://ollama_server:11434/api/embeddings",
            model_name="nomic-embed-text"
        )

        self.client = chromadb.HttpClient(
            host="chroma",
            port=8000,
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )

    def _get_coleccion(self, nombre):
        """Método privado para asegurar que siempre se use la misma función de embeddings"""
        return self.client.get_or_create_collection(
            name=nombre,
            embedding_function=self.embedding_fn
        )

    def indexar_documento(self, ruta_archivo, coleccion_nombre):
        contenido = None
        encodings_a_probar = ['utf-8', 'latin-1', 'cp1252']

        for enc in encodings_a_probar:
            try:
                with open(ruta_archivo, 'r', encoding=enc) as f:
                    contenido = f.read()
                break
            except UnicodeDecodeError:
                continue

        if contenido is None:
            return "Error: No se pudo determinar la codificación del archivo."

        try:
            # Normalizar a utf-8 para evitar problemas con LangChain
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)

            loader = TextLoader(ruta_archivo, encoding='utf-8')
            documento = loader.load()

            # Splitter optimizado para leyes (Artículos)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1100,
                chunk_overlap=280,
                separators=["\nArt.", "\nArticulo", "\n\n", "\n", " ", ""]
            )
            chunks = text_splitter.split_documents(documento)

            coleccion = self._get_coleccion(coleccion_nombre)

            documentos_texto = [c.page_content for c in chunks]
            metadatos = [{"fuente": os.path.basename(ruta_archivo)} for _ in chunks]
            ids = [f"{coleccion_nombre}_{os.path.basename(ruta_archivo)}_{i}" for i in range(len(chunks))]

            coleccion.add(
                documents=documentos_texto,
                metadatas=metadatos,
                ids=ids
            )
            return f"Éxito: {len(chunks)} fragmentos indexados con Nomic Embeddings."
        except Exception as e:
            return f"Error durante la indexación en Chroma: {e}"

    def buscar_contexto(self, pregunta, coleccion_nombre):
        try:
            coleccion = self._get_coleccion(coleccion_nombre)

            # TODO: debug de algunas prgeuntas sin respuesta, luego quitar
            logger.info(f"--- INICIO BÚSQUEDA RAG ---")
            logger.debug(f"Colección: {coleccion_nombre}")
            logger.debug(f"Pregunta del usuario: {pregunta}")

            resultados = coleccion.query(
                query_texts=[pregunta],
                n_results=5
            )

            # TODO: debug para luego quitar
            logger.debug(f"Pregunta: {pregunta}")
            logger.debug(f"IDs encontrados en Chroma: {resultados['ids']}")
            logger.debug(f"Contenido encontrado: {resultados['documents']}")
            logger.info(f"--- FIN BÚSQUEDA RAG ---")

            if not resultados['documents'] or not resultados['documents'][0]:
                print("DEBUG: No se encontraron resultados.")
                logger.warning("No se encontró NADA en ChromaDB para esta consulta.")
                return "No se encontró contexto relevante en la base de datos."

            # TODO: debug para luego quitar
            fragmento_test = resultados['documents'][0][0][:100].replace('\n', ' ')
            logger.info(f"Fragmento recuperado (primeros 100 caracteres): {fragmento_test}...")
            logger.info(f"--- FIN BÚSQUEDA RAG (ÉXITO) ---")

            return "\n\n".join(resultados['documents'][0])
        except Exception as e:
            return f"Error en la búsqueda de contexto: {e}"

    def obtener_estadisticas(self):
        stats = {}
        colecciones = ["leyes", "sgsp", "ortografia"]

        for nombre in colecciones:
            try:
                col = self.client.get_collection(name=nombre, embedding_function=self.embedding_fn)
                count = col.count()
                stats[nombre] = count
            except Exception:
                stats[nombre] = 0
        return stats
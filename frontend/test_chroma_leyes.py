# copiar el archivo al contenedor
# docker cp .\test_chroma_leyes.py HDA_frontend:/app/
# ejecutarlo dentro del docker
# docker exec -it HDA_frontend python /app/test_chroma_leyes.py
import chromadb


def probar_coleccion_leyes():
    # Conexión al cliente (ajusta la ruta si usas persistencia local)
    # Si lo corres desde fuera de Docker usa la IP o 'localhost'
    # Si lo corres dentro usa 'chroma'
    try:
        # cliente = chromadb.HttpClient(host='localhost', port=8000)
        cliente = chromadb.HttpClient(host='chroma', port=8000)

        nombre_coleccion = "leyes"  # ASEGÚRATE QUE SEA ESTE EL NOMBRE

        print(f"--- REVISANDO COLECCIÓN: {nombre_coleccion} ---")

        # 1. Intentar obtener la colección
        coleccion = cliente.get_collection(name=nombre_coleccion)

        # 2. Contar elementos
        conteo = coleccion.count()
        print(f"Total de fragmentos indexados: {conteo}")

        if conteo == 0:
            print("ERROR: La colección está vacía. El proceso de carga falló.")
            return

        # 3. Traer una muestra de datos (los primeros 2)
        muestra = coleccion.peek(limit=2)

        print("\n--- MUESTRA DE CONTENIDO ---")
        for i in range(len(muestra['ids'])):
            print(f"ID: {muestra['ids'][i]}")
            # Limpiamos el texto para que no rompa la consola si hay basura
            texto_limpio = muestra['documents'][i][:200].replace('\n', ' ')
            print(f"Texto: {texto_limpio}...")
            print("-" * 30)

        # 4. Prueba de búsqueda manual
        print("\n--- PRUEBA DE BÚSQUEDA ---")
        pregunta_test = "pena máxima de penitenciaría artículo 79"
        res = coleccion.query(query_texts=[pregunta_test], n_results=1)

        if res['documents'][0]:
            print("Resultado de búsqueda: EXITOSO")
            print(f"Fragmento hallado: {res['documents'][0][0][:150]}...")
        else:
            print("Resultado de búsqueda: NO ENCONTRÓ NADA")

    except Exception as e:
        print(f"ERROR CRÍTICO: No se pudo conectar o la colección no existe: {e}")


if __name__ == "__main__":
    probar_coleccion_leyes()
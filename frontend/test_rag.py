# docker exec -it HDA_frontend python test_rag.py
from clases.MotorRAG import MotorRAG

rag = MotorRAG()
# Indexamos el primer documento
print(rag.indexar_documento("documentos/codigo_penal-072020.txt", "leyes"))

# Probamos una búsqueda
contexto = rag.buscar_contexto("¿Qué dice sobre el hurto?", "leyes")
print("Contexto encontrado:")
print(contexto)
from .DataBase import DataBase

class Conversaciones(DataBase):
    def __init__(self):
        super().__init__()
        self.connect()

    def crear_conversacion(self, usuario_id, titulo, agente):
        self.connect()
        cursor = self.get_cursor()
        if cursor:
            query = "INSERT INTO conversaciones (usuario_id, titulo, agente_usado) VALUES (%s, %s, %s)"
            cursor.execute(query, (usuario_id, titulo, agente))
            self.connection.commit()
            last_id = cursor.lastrowid # Obtenemos el ID de la conversación recién creada
            cursor.close()
            return last_id
        return None

    def guardar_mensaje(self, conversacion_id, rol, contenido):
        self.connect()
        cursor = self.get_cursor()
        if cursor:
            query = "INSERT INTO mensajes (conversacion_id, rol, contenido) VALUES (%s, %s, %s)"
            cursor.execute(query, (conversacion_id, rol, contenido))
            self.connection.commit()
            cursor.close()
            return True
        return False

    def listar_por_usuario(self, usuario_id):
        self.connect()
        cursor = self.get_cursor()
        if cursor:
            # Traemos las más recientes primero
            query = "SELECT id, titulo, fecha_creacion FROM conversaciones WHERE usuario_id = %s ORDER BY ultima_interaccion DESC"
            cursor.execute(query, (usuario_id,))
            res = cursor.fetchall()
            cursor.close()
            return res
        return []

    def eliminar_conversacion(self, conv_id):
        self.connect()
        cursor = self.get_cursor()
        if cursor:
            try:
                cursor.execute("DELETE FROM mensajes WHERE conversacion_id = %s", (conv_id,))
                cursor.execute("DELETE FROM conversaciones WHERE id = %s", (conv_id,))
                self.connection.commit()
                return True
            except Exception as e:
                print(f"Error al eliminar conversación: {e}")
                if hasattr(self, 'db'): self.db.rollback()
                return False
            finally:
                cursor.close()
        return False

    def actualizar_titulo(self, conv_id, nuevo_titulo):
        self.connect()
        cursor = self.get_cursor()
        if cursor:
            try:
                query = "UPDATE conversaciones SET titulo = %s WHERE id = %s"
                cursor.execute(query, (nuevo_titulo, conv_id))
                self.connection.commit()
                return True
            except Exception as e:
                print(f"Error al actualizar título: {e}")
                return False
            finally:
                cursor.close()
        return False

    def obtener_mensajes(self, conversacion_id):
        self.connect()
        cursor = self.get_cursor()
        if cursor:
            query = "SELECT rol, contenido, fecha_envio FROM mensajes WHERE conversacion_id = %s ORDER BY fecha_envio ASC"
            cursor.execute(query, (conversacion_id,))
            res = cursor.fetchall()
            cursor.close()
            return res
        return []
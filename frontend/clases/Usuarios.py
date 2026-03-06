from .DataBase import DataBase

class Usuarios(DataBase):
    def __init__(self):
        super().__init__()
        self.connect()

    def get_usuarios(self):
        self.connect() # Asegura conexión fresca
        cursor = self.get_cursor()
        if cursor:
            query = "SELECT email, nombre FROM usuarios"
            cursor.execute(query)
            usuarios = cursor.fetchall()
            cursor.close()
            return usuarios
        return []

    def get_usuarios_completo(self):
        self.connect()
        cursor = self.get_cursor()
        if cursor:
            # Agregamos estado y rol para que la tabla de Admin se vea completa
            query = "SELECT id, email, nombre, estado, rol FROM usuarios"
            cursor.execute(query)
            usuarios = cursor.fetchall()
            cursor.close()
            return usuarios
        return []

    def get_usuario(self, id):
        self.connect()
        cursor = self.get_cursor()
        if cursor:
            query = "SELECT * FROM usuarios WHERE id = %s"
            cursor.execute(query, (id,))
            usuario = cursor.fetchone()
            cursor.close()
            return usuario
        return None

    def eliminar_usuario(self, id):
        """Método necesario para la acción de borrar en admin.html"""
        self.connect()
        cursor = self.get_cursor()
        if cursor:
            try:
                query = "DELETE FROM usuarios WHERE id = %s"
                cursor.execute(query, (id,))
                self.connection.commit()
                return True
            except Exception as e:
                print(f"Error al eliminar: {e}")
                return False
            finally:
                cursor.close()
        return False
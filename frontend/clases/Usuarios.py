from .DataBase import DataBase

class Usuarios(DataBase):
    def __init__(self):
        super().__init__()
        self.connect()

    def get_usuarios(self):
        cursor = self.get_cursor()
        if cursor:
            query = "SELECT email, nombre FROM usuarios"
            cursor.execute(query)
            usuarios = cursor.fetchall()
            cursor.close()
            self.close()
            return usuarios
        return "Error en la conexión"

    def get_usuarios_completo(self):
        cursor = self.get_cursor()
        if cursor:
            query = "SELECT id, email, nombre FROM usuarios"
            cursor.execute(query)
            usuarios = cursor.fetchall()
            cursor.close()
            self.close()
            return usuarios
        return "Error en la conexión"

    def get_usuario(self, id):
        cursor = self.get_cursor()
        if cursor:
            query = "SELECT * FROM usuarios WHERE id = %s"
            cursor.execute(query, (id,))
            usuario = cursor.fetchone()
            cursor.close()
            self.close()
            return usuario
        return "Error en la conexión"

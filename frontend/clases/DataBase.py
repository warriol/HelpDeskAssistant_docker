# DataBase.py
import mysql.connector
import os
#from dotenv import load_dotenv

class DataBase:
    def __init__(self):
        #load_dotenv()
        self.host = os.environ.get("HOST")
        self.user = os.environ.get("USER")
        self.password = os.environ.get("PASSWORD")
        self.database = os.environ.get("DATABASE")
        self.connection = None

    def connect(self):
        if self.connection is None:
            # Intento de reconexión simple
            import time
            for i in range(5):  # Reintenta 5 veces
                try:
                    self.connection = mysql.connector.connect(
                        host=self.host,
                        user=self.user,
                        passwd=self.password,
                        database=self.database,
                    )
                    print("✅ Conectado a MySQL con éxito")
                    break
                except mysql.connector.Error as err:
                    print(f"⚠️ Intento {i + 1}: Esperando a MySQL...")
                    time.sleep(3)  # Espera 3 segundos antes de reintentar

            if self.connection is None:
                raise Exception("No se pudo conectar a MySQL tras varios intentos.")

    def get_cursor(self):
        if self.connection is None:
            raise Exception("No hay conexión con MySQL")
        return self.connection.cursor(dictionary=True)

    def close(self):
        if self.connection:
            self.connection.close()
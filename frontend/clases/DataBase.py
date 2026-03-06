# DataBase.py
import mysql.connector
import os
import time

class DataBase:
    def __init__(self):
        self.host = os.environ.get("HOST")
        self.user = os.environ.get("USER")
        self.password = os.environ.get("PASSWORD")
        self.database = os.environ.get("DATABASE")
        self.connection = None

    def connect(self):
        # Si ya existe conexión, verificamos si sigue activa
        if self.connection and self.connection.is_connected():
            return

        # Lógica de reintento para el arranque de Docker
        for i in range(5):
            try:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    passwd=self.password,
                    database=self.database,
                    # Agregar estas opciones ayuda con la estabilidad en Docker
                    consume_results=True,
                    autocommit=True
                )
                print(f"✅ Conectado a MySQL con éxito ({self.database})")
                return
            except mysql.connector.Error as err:
                print(f"⚠️ Intento {i + 1}: Esperando a MySQL en {self.host}...")
                time.sleep(3)

        raise Exception("No se pudo conectar a MySQL tras varios intentos.")

    def get_cursor(self):
        # Aseguramos que la conexión esté viva antes de pedir un cursor
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            return self.connection.cursor(dictionary=True)
        except Exception as e:
            print(f"❌ Error al obtener cursor: {e}")
            return None

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
import hashlib
import os
import logging
import mysql.connector
from flask import session
from .DataBase import DataBase


class Auth(DataBase):
    def __init__(self):
        super().__init__()
        self.connect()
        # Configuración de logs simplificada para evitar duplicados
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/auth.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

    def hash_password(self, password):
        return hashlib.sha512(password.encode()).hexdigest()

    def login(self, email, password):
        self.logger.info(f"Intentando login para: {email}")
        passCifrada = self.hash_password(password)

        # Forzar reconexión para evitar el error de "datos viejos" que tuviste antes
        self.connect()
        cursor = self.get_cursor()

        # Inyectar la URL de la IA en la sesión
        session["urlia"] = os.environ.get("URLIA", "http://localhost:5000")

        if cursor:
            try:
                query = "SELECT * FROM usuarios WHERE email = %s"
                cursor.execute(query, (email,))
                user = cursor.fetchone()

                if not user:
                    return "correoIncorrecto"

                if user["estado"] != 1:
                    return "estadoInactivo"

                if user["password"] != passCifrada:
                    return "contraseñaIncorrecta"

                # --- AJUSTE DE SESIÓN PARA COMPATIBILIDAD ---
                session["user"] = user["email"]  # Usamos el email como ID único
                session["nombre"] = user["nombre"]  # Nombre para mostrar en la UI
                session["rol"] = int(user["rol"])  # Guardamos 0 o 1 (entero)

                self.logger.info(f"Login exitoso: {email} (Rol: {session['rol']})")
                return "dashboard"

            except mysql.connector.Error as err:
                self.logger.error(f"SQL error: {err}")
                return f"Error sql {err}"
            finally:
                cursor.close()

        return "Error en la conexión"

    def registrar(self, nombre, email, password):
        self.logger.info(f"Registrando usuario: {email}")
        self.connect()
        cursor = self.get_cursor()
        if cursor:
            try:
                hashed_password = self.hash_password(password)
                # El estado y rol se manejan por defecto en la DB (0 y 0)
                query = "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)"
                cursor.execute(query, (nombre, email, hashed_password))
                self.connection.commit()
                return "Usuario registrado exitosamente!"
            except mysql.connector.Error as err:
                self.logger.error(f"Error al registrar: {err}")
                return f"Error: {err}"
            finally:
                cursor.close()
        return "Error en la conexión"
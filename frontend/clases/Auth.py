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
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('logs/auth.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def hash_password(self, password):
        return hashlib.sha512(password.encode()).hexdigest()

    def login(self, email, password):
        self.logger.info(f"Attempting login for email: {email}")
        passCifrada = self.hash_password(password)
        cursor = self.get_cursor()
        session["urlia"] = os.environ.get("URLIA")
        if cursor:
            try:
                # Verificar si el correo existe
                query = "SELECT * FROM usuarios WHERE email = %s"
                cursor.execute(query, (email,))
                user = cursor.fetchone()

                if not user:
                    self.logger.warning(f"Login failed for email: {email} - Email not found")
                    return "correoIncorrecto"

                # Verificar si el estado es 1
                if user["estado"] != 1:
                    self.logger.warning(f"Login failed for email: {email} - Inactive account: {user['estado']}")
                    return "estadoInactivo"

                # Verificar la contraseña
                if user["password"] != passCifrada:
                    self.logger.warning(f"Login failed for email: {email} - Incorrect password")
                    return "contraseñaIncorrecta"

                # Asignar rol
                session["user"] = user["nombre"]
                if user["rol"] == 1:
                    session["rol"] = "Administrador"
                else:
                    session["rol"] = "Usuario"
                self.logger.info(f"Login successful for email: {email}")
                return "dashboard"

            except mysql.connector.Error as err:
                self.logger.error(f"SQL error: {err}")
                return f"Error sql {err}"

        self.logger.error("Connection error")
        return "Error en la conexión"

    def registrar(self, nombre, email, password):
        self.logger.info(f"Attempting to register user: {email}")
        cursor = self.get_cursor()
        if cursor:
            hashed_password = self.hash_password(password)
            query = "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (nombre, email, hashed_password))
            self.connection.commit()
            cursor.close()
            self.close()
            self.logger.info(f"User registered successfully: {email}")
            return "Usuario registrado exitosamente!"
        self.logger.error("Connection error")
        return "Error en la conexión"
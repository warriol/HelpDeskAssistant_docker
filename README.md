# Help Desk Assistant
# 📄 Guía de Configuración: HDA (Docker + GPU)

# Autor: Wilson Arriola

## Instalación y Configuración de HDA (Help Desk Assistant) con Docker y GPU
### Prerequisitos
- Docker Desktop (con soporte para WSL2 en Windows)
- NVIDIA Container Toolkit (para soporte GPU)
- Drivers de NVIDIA actualizados
### Descripción del proceso
1. Clona el repositorio de HDA.
2. Configura tu entorno para permitir que Docker acceda a la GPU.
3. Crea el archivo .env con tus variables de entorno (si es necesario).
```bash
MYSQL_ROOT_PASSWORD=la_contraseña_que_desees_para_el_usuario_root
MYSQL_ROOT_USER=el_usuario_de_tu_base_de_datos
DB_NAME=el_nombre_de_tu_base_de_datos
MODEL_IA=modelo_que_descargaste_en_ollama
```
4. Ejecuta `docker-compose up -d`
5. Descarga el modelo Ollama `docker exec -it ollama_server ollama pull llama3`
6. Crea la base de datos ejecutando el script SQL dentro del contenedor MySQL:
```bash
# CMD
docker exec -i HDA_mysql mysql -u root -ptu_password_root nombre_base_datos < init.sql
# PowerShell
Get-Content init.sql | docker exec -i HDA_mysql mysql -u root -ptu_password_root nombre_base_datos
```
7. Entra en la apliación y registrate como usuario
8. Debe activiar tu usuario por primera vez y marcarlo como admin
```bash
docker exec -it HDA_backend mysql -u root -ptu_password_root -e "USE nombre_base_datos; UPDATE users SET estado = 1, rol = 1 WHERE email = 'tu_email_de_registro';"
```
9. Accede a la aplicación en http://localhost:8501 y comienza a interactuar con tu asistente de help desk impulsado por IA.
### Posibles problemas y soluciones
- **Error de GPU no detectada**: Asegúrate de que tu sistema tiene
- drivers NVIDIA actualizados y que el NVIDIA Container Toolkit está correctamente instalado.
- **Problemas de conexión a la base de datos**: Verifica que el contenedor
- MySQL esté corriendo y que las credenciales en tu archivo .env coincidan con las configuradas en el contenedor.
- **Errores al construir los contenedores**: Revisa los logs de Docker para
- identificar el paso específico que falla y asegúrate de que todas las dependencias estén correctamente definidas en los Dockerfiles.
- **Problemas de CORS**: Si el frontend no puede comunicarse con el backend, asegúrate de que el backend esté configurado para permitir CORS desde el origen del frontend.
- **Problema de comnicación con el backend: error 404**: Verifica que el backend esté corriendo y que el endpoint de chat esté correctamente definido y accesible.
- Verifica en server.py que el MODEL_IA sea el modelo que descargaste en Ollama (ejemplo: llama3)

## Casos de uso
- BACKEND:
    - Admitir CORS <img src="https://img.shields.io/badge/Hecho-success">
    - EndPoint CHAT <img src="https://img.shields.io/badge/Hecho-success">

## Este proyecto unifica el Frontend (Python), el Backend (Python) y el motor de IA (Ollama) en un entorno de contenedores con aceleración por hardware.
# 1. Requisitos Previos (En tu PC/Host)

Antes de ejecutar Docker, tu sistema debe estar preparado para "prestarle" la GPU a los contenedores:

- Drivers de NVIDIA: Asegúrate de tener instalados los controladores más recientes de tu tarjeta gráfica.
- Docker Desktop: Instalado y funcionando (con soporte para WSL2 si estás en Windows).
- NVIDIA Container Toolkit:
  - En Linux: Sigue los pasos de la documentación oficial.
  - En Windows (WSL2): Generalmente se instala automáticamente con Docker Desktop, pero asegúrate de que la opción "Use the WSL 2 based engine" esté activa en la configuración de Docker.

# 2. Estructura del Proyecto

```
HDA/
├── backend/
│   ├── server.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── init.sql
```

# 3. Configuración de Docker Compose

```bash
# construye y levanta los contenedores
docker-compose up --build
```

## 3.1. En caso de error
```bash
# limipar las capas corruptas
docker system prune -f
# volver al paso 3.
```

## 3.2. En caso de éxito
```bash
 ✔ Image helpdeskassistant_docker-backend      Built                                                                                                                                                                             87.0s
 ✔ Image helpdeskassistant_docker-frontend     Built                                                                                                                                                                             87.0s
 ✔ Network helpdeskassistant_docker_default    Created                                                                                                                                                                           0.0s 
 ✔ Volume helpdeskassistant_docker_ollama_data Created                                                                                                                                                                           0.0s 
 ✔ Volume helpdeskassistant_docker_mysql_data  Created                                                                                                                                                                           0.0s 
 ✔ Container HDA_mysql                         Created                                                                                                                                                                           0.9s 
 ✔ Container ollama_server                     Created                                                                                                                                                                           0.5s 
 ✔ Container HDA_backend                       Created                                                                                                                                                                           0.6s
 ✔ Container HDA_frontend                      Created   
 ```

### 3.2.1 Check-list de Verificación (Logs)
#### Mientras los contenedores suben, busca estos mensajes clave en la pantalla:

- HDA_mysql: Debería decir ready for connections.
- ollama_server: Busca NVIDIA GPU detected para confirmar que tu GPU está activa.
- HDA_backend: Debería mostrar Running on http://0.0.0.0:5000.
- HDA_frontend: Debería mostrar la URL de acceso (generalmente http://localhost:8501).

### 3.2.2 Verificar que los contenedores estén corriendo
#### Prueba,Comando,Qué debe pasar
- ¿Ollama responde?
  - curl http://localhost:11434
  - Debe decir Ollama is running.
- ¿Backend responde?
  - curl http://localhost:5000/
  - Debe decir Servidor de Wilson Arriola... Online!.
- ¿MySQL responde?
  - docker exec -it HDA_mysql mysqladmin -u root -p[tu_pass] ping
  - Debe decir mysqld is alive.
 
## 3.3. En caso de error al iniciar algun servicio
```bash
# Detener lo que quedó colgado:
docker-compose down

# Construir y levantar:
docker-compose up --build -d

# Verificar el frontend:
docker logs HDA_frontend
```


# 4. Configura la base de datos

```
docker exec -i HDA_mysql mysql -u root -ptu_password_root hdassistant < init.sql
```
# 5. Accede a la aplicación
```bash
# inicia la aplicación sin mostrar logs en la terminal
docker-compose up -d

# inicia la aplicación mostrando logs en la terminal
docker-compose up

# ver los logs de un contenedor específico (ejemplo: frontend)
docker logs -f HDA_frontend


```
Abre tu navegador y ve a http://localhost:8501 para interactuar con el Frontend de HDA.
Aquí podrás hacer preguntas, ver respuestas.

# 6. Detener los contenedores
```bash
docker-compose down
```

# 7. Limpieza de recursos (opcional)
```bash
# Elimina imágenes, contenedores y volúmenes no utilizados
docker system prune -a --volumes
```

# 8. Mantenimiento
- Para actualizar el código, haz cambios en los archivos locales y luego reconstruye
los contenedores
```bash
docker-compose up --build
```
- Si solo tocamos uno de los servidores
```bash
docker-compose up --build -d [nombre_servicio]
# docker-compose up --build -d frontend
```
- Si realizo cambios en la base de datos
- No basta con cambiar el init.sql
```bash
# Detener los contenedores
docker-compose down
# Volver a crear la base de datos
docker volume rm helpdeskassistant_docker_mysql_data
# Volver a levantar los contenedores
docker-compose up --build
```
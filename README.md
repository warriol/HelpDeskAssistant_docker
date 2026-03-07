# Help Desk Assistant
# 📄 Guía de Configuración: HDA (Docker + GPU)

# Autor: Wilson Arriola

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
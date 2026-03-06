# 🛠️ Proyecto Frontend - Configuración y Uso
- Autor: Wilson Denis Arriola
- Fecha: 2021-09-29
- Versión: 1.0.0
- Estado: En Proceso
- Descripción: Configuración y uso de un proyecto backend para chat con inteligencia artifical.

## 🚀 Instalación y Configuración

### 1️⃣ Clonar el repositorio y configurar el entorno
```sh
# Clonar el repositorio
git clone https://github.com/warriol/apiIABackend.git
cd apiIABackend

# Crear y activar entorno virtual
python -m venv .venv

# En Linux/Mac
source .venv/bin/activate
# En Windows
.\.venv\Scripts\activate

# Instala Flask y GPT4All
pip install flask gpt4all
pip install sentence-transformers
pip install faiss-cpu
pip install pandas numpy
```

### 2️⃣ conectar back con front - exponer back
- instalar ngrok en la pc y configurar el puerto 5000
```sh
# Instalar ngrok
https://ngrok.com/download

pip install ngrok
pip install pyngrok

# Autenticar tu cuenta (si es la primera vez)
ngrok authtoken <tu-token>

# habilitar CORS en Flak
pip install flask-cors

# para mayor control de CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configurar puerto 5000 (inicia la aplicacion)
ngrok http --url=deciding-rested-badger.ngrok-free.app 127.0.0.1:5000
```
### 3️⃣ Freezing Your Requirements
```sh
# Instalar dependencias
pip install -r requirements.txt

# Guardar dependencias en caso de nuevas instalaciones
pip freeze > requirements.txt
```
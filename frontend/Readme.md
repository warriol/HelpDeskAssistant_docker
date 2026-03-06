# 🛠️ Proyecto Frontend - Configuración y Uso
- Autor: Wilson Denis Arriola
- Fecha: 2021-09-29
- Versión: 1.0.0
- Estado: En Proceso
- Descripción: Configuración y uso de proyecto frontend con Flask y GPT4All, para consultas de derecho uruguayo asitido con inteligencia artificial.
- Tecnologías: Python, Flask, GPT4All, MySQL, PHP

## 🚀 Instalación y Configuración

### 1️⃣ Clonar el repositorio y configurar el entorno
```sh
# Clonar el repositorio
git clone https://github.com/warriol/apiIAFrontend.git
cd apiIAFrontend

# Crear y activar entorno virtual
python -m venv .venv

# En Linux/Mac
source .venv/bin/activate

# En Windows
.\.venv\Scripts\activate


# Instalar dependencias
pip install -r requirements.txt

# Guardar dependencias en caso de nuevas instalaciones
pip freeze > requirements.txt
```

### 2️⃣ Instalación de dependencias adicionales
```sh
# Instalación de dependencias
pip install flask transformers torch gpt4all
pip install python-dotenv
pip install mysql-connector-python
npm install react-markdown remark-gfm
npm install marked

```

### 🌍 Configuración en Hosting
```sh
# Crear y activar entorno virtual en hosting
python3 -m venv .venv
source /home/warriols/virtualenv/flask.cpia/3.11/bin/activate

# Verificar instalación de paquetes
python3 -m pip show flask transformers torch gpt4all
```

### 📌 Base de Datos - MySQL
```sql
CREATE DATABASE warriols_py;
USE warriols_py;

CREATE TABLE usuarios (
  id INT(11) NOT NULL AUTO_INCREMENT,
  email VARCHAR(200) NOT NULL COMMENT 'Nombre de usuario para iniciar sesión.',
  password VARCHAR(200) NOT NULL,
  nombre VARCHAR(200) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO usuarios (email, password, nombre) VALUES
('warriol@gmail.com', 'HASH_PASSWORD', 'Wilson Denis'),
('sandbox@factus.com.co', 'HASH_PASSWORD', 'Test');

ALTER TABLE `usuarios` ADD `estado` TINYINT NOT NULL DEFAULT '0' AFTER `nombre`; 
ALTER TABLE `usuarios` ADD `rol` TINYINT NOT NULL DEFAULT '0' AFTER `estado`; 
```

### 📌 Ventajas del proyecto:

✅ No dependes de APIs externas.
✅ Más económico a largo plazo.
❌ Requiere configuración de servidor Python.
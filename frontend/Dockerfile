FROM python:3.13

WORKDIR /app

# Instalamos dependencias del sistema necesarias para MySQL y compilación
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos e instalamos las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el contenido (incluyendo la carpeta 'clases')
COPY . .

# Exponemos el puerto (usaremos el 5001 para que no choque con el backend)
EXPOSE 5001

# Comando para arrancar tu app de Flask
CMD ["python", "app.py"]
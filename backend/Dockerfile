FROM python:3.13

WORKDIR /app

# Instalamos dependencias mínimas para que Pandas funcione en Linux
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos e instalamos dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código del servidor y el archivo train.csv
COPY . .

# Exponemos el puerto del Backend
EXPOSE 5000

# Comando para arrancar el servidor de Wilson
CMD ["python", "server.py"]
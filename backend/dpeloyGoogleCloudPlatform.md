## Despliegue en Google App Engine
1. Instalar Google Cloud SDK:  
   - Descarga e instala el Google Cloud SDK.


2. Inicializar el SDK:
```sh
   gcloud init
```

3. Crear un archivo app.yaml: Este archivo define la configuración de tu aplicación para App Engine.  
```sh
    runtime: python39
    entrypoint: gunicorn -b :$PORT serverOllama:app
    
    handlers:
    - url: /static
      static_dir: static
    
    - url: /.*
      script: auto
    
    env_variables:
      OLLAMA_API_URL: 'http://localhost:11434/api/generate'
      MODEL_NAME: 'gemma3:4b'
```

4. Instalar Gunicorn:
```sh
    pip install gunicorn
```

5. Desplegar la aplicación:  
```sh
    gcloud app deploy
```

## Cambios en cuanto a seguridad
1. Configurar HTTPS:  
GCP proporciona certificados SSL automáticamente para tus aplicaciones en App Engine.

2. Configurar variables de entorno:  
No almacenes credenciales o información sensible en el código fuente. Usa variables de entorno para configuraciones sensibles.

- env_variables:
  SECRET_KEY: 'mysecretkey'

- En tu aplicación Flask:
```python
import os

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
```

3. Deshabilitar el modo de depuración:  
Asegúrate de que el modo de depuración esté deshabilitado en producción.

```python
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
```

4. Revisar dependencias:  
Asegúrate de que todas las dependencias estén actualizadas y no tengan vulnerabilidades conocidas.

```sh
pip install --upgrade pip
pip list --outdated
```
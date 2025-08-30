# Imagen base con Python
FROM python:3.11-slim

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos los archivos de la aplicación
COPY requirements.txt requirements.txt
COPY . .

# Instalamos dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponemos el puerto Flask
EXPOSE 5000

# Comando por defecto
CMD ["python", "app.py"]

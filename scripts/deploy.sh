#!/bin/bash

# Script de Despliegue Automático - TODAVÍA
# Este script se ejecuta en el servidor (VM)

PROJECT_DIR="/root/proyecto_todavia"
VENV_DIR="$PROJECT_DIR/venv"

echo "=== Iniciando Despliegue de Cambios ==="

cd $PROJECT_DIR

# 1. Obtener cambios de GitHub
echo ">>> Trayendo cambios de GitHub..."
git pull origin main

# 2. Activar entorno virtual e instalar dependencias si cambiaron
echo ">>> Actualizando dependencias..."
source $VENV_DIR/bin/activate
pip install -r requirements.txt

# 3. Aplicar migraciones
echo ">>> Aplicando migraciones de Base de Datos..."
python manage.py migrate

# 4. Recolectar archivos estáticos
echo ">>> Recolectando archivos estáticos (CSS/JS)..."
python manage.py collectstatic --noinput

# 5. Reiniciar el servicio backend
echo ">>> Reiniciando Gunicorn..."
sudo systemctl restart gunicorn

echo "=== Despliegue completado con éxito! ==="

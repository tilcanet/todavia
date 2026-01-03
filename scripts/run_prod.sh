#!/bin/bash

# run_prod.sh
# Script de inicio rápido para producción (Ubuntu/Debian)

echo "🚀 Iniciando despliegue de Todavía..."

# 1. Verificar entorno virtual
if [ ! -d "venv" ]; then
    echo "⚠️  No se encontró directorio venv. Creando entorno virtual..."
    python3 -m venv venv
fi

echo "🔌 Activando entorno virtual..."
source venv/bin/activate

# 2. Instalar dependencias
echo "📦 Instalando dependencias desde requirements.txt..."
pip install -r requirements.txt

# 3. Migraciones de Base de Datos
echo "🗄️  Aplicando migraciones a la Base de Datos..."
python manage.py migrate

# 4. Archivos Estáticos
echo "🎨 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# 5. Crear usuario admin si no existe (Opcional, manual es mejor en prod)
# echo "👤 (Opcional) Creando superusuario..."
# python manage.py createsuperuser --noinput --username admin --email admin@example.com || true

# 6. Lanzar Gunicorn
echo "🔥 Arrancando servidor Gunicorn..."
# Ejecuta en segundo plano o bloqueante según prefieras. Aquí bloqueante para ver logs.
gunicorn -c gunicorn_config.py backend_todavia.wsgi

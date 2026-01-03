#!/bin/bash

# run_prod.sh
# Script de inicio rápido para producción (Ubuntu/Debian)

# Asegurarnos de estar en la raíz del proyecto (un nivel arriba de scripts/)
cd "$(dirname "$0")/.."
echo "📍 Directorio de trabajo: $(pwd)"

echo "🚀 Iniciando despliegue de Todavía..."

# 1. Verificar entorno virtual
if [ ! -d "venv" ]; then
    echo "⚠️  No se encontró directorio venv. Creando entorno virtual..."
    python3 -m venv venv
fi

echo "🔌 Activando entorno virtual..."
source venv/bin/activate

# 2. Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt
# Fallback por si requirements.txt no se actualizó bien en el server
pip install gunicorn psycopg2-binary dj-database-url whitenoise

# 3. Migraciones de Base de Datos
echo "🗄️  Aplicando migraciones a la Base de Datos..."
python manage.py migrate

# 4. Archivos Estáticos
echo "🎨 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# 5. Liberar puerto 8000 (Si quedó colgado)
echo "🧹 Verificando puerto 8000..."
fuser -k 8000/tcp || true

# 6. Lanzar Gunicorn
echo "🔥 Arrancando servidor Gunicorn..."
# Ejecuta en segundo plano o bloqueante según prefieras. Aquí bloqueante para ver logs.
gunicorn -c gunicorn_config.py backend_todavia.wsgi

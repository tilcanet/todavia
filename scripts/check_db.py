
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_todavia.settings')
django.setup()

from django.conf import settings
from django.db import connection

print("-" * 40)
print("VERIFICACIÓN DE BASE DE DATOS")
print("-" * 40)

db_settings = settings.DATABASES['default']
engine = db_settings['ENGINE']
name = db_settings['NAME']

print(f"MOTOR (ENGINE): {engine}")
print(f"NOMBRE (NAME):  {name}")

if 'sqlite' in engine:
    print("\n[!] ESTÁS USANDO SQLITE (Archivo local).")
    print("    Si deberías estar en PostgreSQL, revisa que la variable DATABASE_URL esté definida en tu .env")
elif 'postgresql' in engine or 'psycopg' in engine:
    print("\n[OK] ESTÁS USANDO POSTGRESQL.")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            row = cursor.fetchone()
            print(f"    Versión del servidor: {row[0]}")
            print("    Conexión exitosa.")
    except Exception as e:
        print(f"\n[ERROR] Parece que es Postgres, pero falló la conexión: {e}")
else:
    print(f"\n[?] Motor desconocido o diferente: {engine}")

print("-" * 40)

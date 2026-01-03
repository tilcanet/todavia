import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(BASE_DIR)) # Add project root to path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_todavia.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import Aliado

def ensure_aliado():
    try:
        user = User.objects.get(username="tilcanet")
        if not hasattr(user, 'perfil_aliado'):
            print("Creando perfil de Aliado para 'tilcanet'...")
            Aliado.objects.create(
                usuario_real=user,
                nombre_visible="Admin Tilca",
                especialidad="TRABAJOR_SOCIAL",
                esta_disponible=True
            )
            print("Perfil Aliado creado.")
        else:
            print("El usuario 'tilcanet' ya es Aliado.")
            
    except User.DoesNotExist:
        print("Error: El usuario 'tilcanet' no existe. Ejecuta create_superuser.py primero.")

if __name__ == "__main__":
    ensure_aliado()

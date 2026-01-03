import os
import sys
import django

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_todavia.settings")
django.setup()

from django.contrib.auth import get_user_model

def create_superuser():
    User = get_user_model()
    username = "tilcanet"
    email = "admin@tilcanet.com"
    password = "admin"  # Simple password for initial access

    if not User.objects.filter(username=username).exists():
        print(f"Creando superusuario '{username}'...")
        User.objects.create_superuser(username, email, password)
        print(f"Superusuario creado con éxito.")
        print(f"Usuario: {username}")
        print(f"Contraseña: {password}")
    else:
        print(f"El usuario '{username}' ya existe. Reseteando contraseña...")
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        print(f"Contraseña actualizada a: {password}")

if __name__ == "__main__":
    create_superuser()

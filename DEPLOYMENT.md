# Guía de Despliegue en VM - Proyecto TODAVÍA

Esta guía detalla los pasos para subir el proyecto a una Máquina Virtual (VM) utilizando Ubuntu 22.04+, Nginx y Gunicorn.

## 1. Requisitos Previos en la VM

Actualizar el sistema e instalar dependencias básicas:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx git -y
```

## 2. Preparación del Proyecto

1. **Clonar el repositorio** (si usas Git) o subir los archivos vía SCP/SFTP.
2. **Crear entorno virtual**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   pip install gunicorn
   ```

## 3. Configuración de Django

Asegúrate de configurar los siguientes valores en `settings.py` (o mediante variables de entorno):
- `DEBUG = False`
- `ALLOWED_HOSTS = ['tu-dominio.com', 'tu-ip-publica']`

Ejecutar migraciones y recolectar estáticos:
```bash
python manage.py migrate
python manage.py collectstatic
```

## 4. Configuración de Gunicorn

Crea un archivo de servicio para systemd:
`sudo nano /etc/systemd/system/gunicorn.service`

```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/root/proyecto_todavia
ExecStart=/root/proyecto_todavia/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          backend_todavia.wsgi:application

[Install]
WantedBy=multi-user.target
```

## 5. Configuración de Nginx

Crea un archivo de configuración para tu sitio:
`sudo nano /etc/nginx/sites-available/todavia`

```nginx
server {
    listen 80;
    server_name todavia.tilcanet.com.ar 200.45.208.61;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /root/proyecto_todavia;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Activa el sitio y reinicia Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/todavia /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## 6. Consideraciones de Seguridad
- Instalar SSL con Certbot: `sudo apt install python3-certbot-nginx && sudo certbot --nginx`
- Configurar el Firewall: `sudo ufw allow 'Nginx Full'`

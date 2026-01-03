# gunicorn_config.py

import multiprocessing

# bind = "0.0.0.0:8000"  # Lo gestiona el proveedor de la nube o Docker usualmente
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
timeout = 120 # 2 minutos para dar tiempo a la IA si está lenta
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

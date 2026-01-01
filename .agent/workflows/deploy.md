---
description: Cómo sincronizar cambios desde tu PC hacia el servidor web
---

# Sincronización de Cambios (PC a Web)

Este flujo te permite trabajar cómodamente en tu computadora y subir los cambios al servidor con pocos comandos.

## 1. Preparación Única (Solo la primera vez)

### En tu PC:
1. Crea un repositorio en GitHub (privado).
2. Abre la terminal en el proyecto y ejecuta:
```powershell
git init
git add .
git commit -m "Primer commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

### En el Servidor (VM):
1. Borra la carpeta vieja (o cámbiale el nombre).
2. Clona el repo de GitHub:
```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git /root/proyecto_todavia
```

## 2. Flujo Diario de Trabajo

### Paso 1: Cambios en tu PC
Cuando termines un cambio (ej: en Django o Flutter), ejecutas esto en tu PC:
```powershell
git add .
git commit -m "Descripción de lo que cambiaste"
git push origin main
```

### Paso 2: Actualizar la Web
En el servidor, simplemente ejecutas el script de despliegue:
```bash
bash /root/proyecto_todavia/scripts/deploy.sh
```

### Paso 3: Probar en el Móvil
En tu PC, como ya tienes el SDK de Android, solo haces:
```powershell
cd app_todavia
flutter run
```
*La app se conectará automáticamente al servidor web actualizado por internet.*

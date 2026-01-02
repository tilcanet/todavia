Write-Host ">>> COMPILANDO Y ACTUALIZANDO APKS <<<" -ForegroundColor Cyan

# 0. Crear carpeta media si no existe
if (-not (Test-Path "media")) {
    New-Item -ItemType Directory -Force -Path "media"
}

# 1. Compilar App Comunidad (Todavia)
Write-Host "1. Compilando App Comunidad (app_todavia)..." -ForegroundColor Yellow
Set-Location "app_todavia"
cmd /c "flutter clean"
cmd /c "flutter pub get"
cmd /c "flutter build apk --release"
Set-Location ..

if (Test-Path "app_todavia/build/app/outputs/flutter-apk/app-release.apk") {
    Copy-Item "app_todavia/build/app/outputs/flutter-apk/app-release.apk" -Destination "media/todavia_comunidad.apk" -Force
    Write-Host "   > APK Comunidad copiado con éxito." -ForegroundColor Green
} else {
    Write-Host "   > ERROR: No se generó el APK de Comunidad." -ForegroundColor Red
}

# 2. Compilar App Aliados
Write-Host "2. Compilando App Aliados (app_aliado)..." -ForegroundColor Yellow
Set-Location "app_aliado"
cmd /c "flutter clean"
cmd /c "flutter pub get"
cmd /c "flutter build apk --release"
Set-Location ..

if (Test-Path "app_aliado/build/app/outputs/flutter-apk/app-release.apk") {
    Copy-Item "app_aliado/build/app/outputs/flutter-apk/app-release.apk" -Destination "media/todavia_aliados.apk" -Force
    Write-Host "   > APK Aliados copiado con éxito." -ForegroundColor Green
} else {
    Write-Host "   > ERROR: No se generó el APK de Aliados." -ForegroundColor Red
}

# 3. Subir al Repo
Write-Host "3. Subiendo APKs al repositorio..." -ForegroundColor Yellow
git add media/*.apk
git commit -m "Updated Release APKs"
git push origin main

Write-Host ">>> PROCESO FINALIZADO. Ejecuta 'bash scripts/deploy.sh' en el servidor. <<<" -ForegroundColor Cyan

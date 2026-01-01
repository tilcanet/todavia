# core/models.py
from django.db import models
import uuid  # Librería para generar IDs únicos y aleatorios
from django.contrib.auth.models import User # <--- IMPORTANTE: Agrega esto arriba

class UsuarioAnonimo(models.Model):
    """
    Representa a la persona que usa la app.
    Usamos UUID (un código largo y raro) en lugar de números (1, 2, 3)
    para que nadie pueda adivinar el ID de otro usuario.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alias = models.CharField(max_length=50, default="Viajero", help_text="Un nombre ficticio que el usuario elija")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    # Datos para estadísticas (Opcionales y generales)
    edad = models.IntegerField(null=True, blank=True)
    zona = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        help_text="Barrio o Localidad aproximada (Ej: Tilcara Centro, Sumay Pacha)"
    )
    
    # Geolocalización
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    
    # Metadatos técnicos para informes
    dispositivo_modelo = models.CharField(max_length=100, null=True, blank=True)
    dispositivo_os = models.CharField(max_length=50, null=True, blank=True)

    # Estado de Crisis / Zona Roja
    en_zona_roja = models.BooleanField(default=False, help_text="Indica si el usuario está en crisis activa")
    fecha_zona_roja = models.DateTimeField(null=True, blank=True, help_text="Cuándo entró en crisis")
    
    def __str__(self):
        return f"{self.alias} ({str(self.id)[:8]}...)"

class Mensaje(models.Model):
    """
    Cada mensaje que se envía en el chat.
    """
    usuario = models.ForeignKey(UsuarioAnonimo, on_delete=models.CASCADE, related_name='mensajes')
    texto = models.TextField()
    es_de_la_ia = models.BooleanField(default=False) # Si es True, lo escribió el bot. Si es False, el usuario.
    fecha = models.DateTimeField(auto_now_add=True)

    # Metadatos para el Ministerio (Invisibles para el usuario)
    sentimiento_detectado = models.CharField(max_length=50, null=True, blank=True) # Ej: "Angustia", "Esperanza"
    aliado_emisor = models.ForeignKey('Aliado', null=True, blank=True, on_delete=models.SET_NULL, help_text="Si el mensaje lo escribió un humano aliado")

    def __str__(self):
        origen = "IA" if self.es_de_la_ia else "Usuario"
        return f"[{origen}] {self.texto[:30]}..."

# ... (Aquí están tus clases UsuarioAnonimo y Mensaje, déjalas igual) ...

# --- NUEVO: TABLA DE VOLUNTARIOS (LOS HOMBROS) ---
class Aliado(models.Model):
    # Vinculamos al Aliado con el sistema de usuarios real de Django (para que tenga usuario y contraseña)
    usuario_real = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_aliado')
    
    nombre_visible = models.CharField(max_length=50, help_text="Ej: 'Vecino Juan', 'Padre Roberto'")
    telefono = models.CharField(max_length=20, help_text="Para contacto interno, no se muestra al usuario")
    
    # Seguridad
    es_verificado = models.BooleanField(default=False, help_text="Si está marcado, tú lo aprobaste manualmente")
    esta_disponible = models.BooleanField(default=False, help_text="Switch ON/OFF para recibir alertas")
    
    # Tecnología (Para notificaciones Push)
    fcm_token = models.CharField(max_length=255, null=True, blank=True) 

    def __str__(self):
        estado = "🟢" if self.esta_disponible else "🔴"
        return f"{estado} {self.nombre_visible} ({self.usuario_real.username})"

# core/models.py (Al final)

class SesionHumana(models.Model):
    usuario = models.ForeignKey(UsuarioAnonimo, on_delete=models.CASCADE)
    aliado = models.ForeignKey(Aliado, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"Link: {self.usuario.alias} <--> {self.aliado.nombre_visible}"

class Sugerencia(models.Model):
    """
    Guarda lo que el usuario considera que 'hace falta' en su comunidad o en el sistema.
    """
    usuario = models.ForeignKey(UsuarioAnonimo, on_delete=models.CASCADE, related_name='sugerencias')
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sugerencia de {self.usuario.alias}: {self.texto[:30]}..."

class RegistroUbicacion(models.Model):
    """
    Registro histórico de la ubicación del usuario, guardado por día.
    """
    usuario = models.ForeignKey(UsuarioAnonimo, on_delete=models.CASCADE, related_name='ubicaciones')
    latitud = models.FloatField()
    longitud = models.FloatField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Registros de Ubicación"

    def __str__(self):
        return f"Ubicación de {self.usuario.alias} el {self.fecha}"

class Localidad(models.Model):
    """
    Datos geográficos de localidades de Jujuy para georeferenciación.
    """
    nombre = models.CharField(max_length=200)
    latitud = models.FloatField()
    longitud = models.FloatField()
    municipio = models.CharField(max_length=200, blank=True, null=True)
    departamento = models.CharField(max_length=200, blank=True, null=True)
    provincia = models.CharField(max_length=100, default='JUJUY')

    def __str__(self):
        return f"{self.nombre} ({self.departamento})"

class TicketAyuda(models.Model):
    """
    Registro de solicitudes de ayuda externa (Botones de emergencia).
    """
    usuario = models.ForeignKey(UsuarioAnonimo, on_delete=models.CASCADE, related_name='tickets_ayuda')
    tipo = models.CharField(max_length=100) # Ej: "POLICIA", "SAME", "CENTRO"
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.tipo} - {self.usuario.alias} ({self.fecha})"

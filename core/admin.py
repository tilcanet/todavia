from django.contrib import admin
from django.db.models import Count
# Importamos todos tus modelos aquí
from .models import UsuarioAnonimo, Mensaje, Aliado, SesionHumana

# --- 1. ADMINISTRACIÓN DE USUARIOS (Con Mapa de Calor) ---
@admin.register(UsuarioAnonimo)
class UsuarioAnonimoAdmin(admin.ModelAdmin):
    # Qué columnas ver en la lista general
    list_display = ('alias', 'zona', 'latitud', 'longitud', 'dispositivo_modelo', 'fecha_registro', 'id')
    
    # Filtros laterales (¡Aquí está la magia para ver de qué barrio escriben!)
    list_filter = ('zona', 'fecha_registro')
    
    # Buscador por ID, Alias o Zona
    search_fields = ('alias', 'id', 'zona')
    
    # Ordenar para que el más nuevo salga primero
    ordering = ('-fecha_registro',)


# --- 2. ADMINISTRACIÓN DE MENSAJES (Con Estadísticas) ---
@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'es_de_la_ia', 'sentimiento_detectado', 'texto_corto')
    list_filter = ('sentimiento_detectado', 'fecha', 'es_de_la_ia')
    search_fields = ('texto', 'sentimiento_detectado')

    def texto_corto(self, obj):
        # Muestra solo los primeros 50 caracteres para no ensuciar la tabla
        return obj.texto[:50] + "..." if obj.texto else "-"

    # Tu lógica personalizada para ver estadísticas arriba de la tabla
    def changelist_view(self, request, extra_context=None):
        stats = Mensaje.objects.filter(es_de_la_ia=True).values('sentimiento_detectado').annotate(total=Count('id')).order_by('-total')
        extra_context = extra_context or {}
        extra_context['stats'] = stats
        return super().changelist_view(request, extra_context=extra_context)


# --- 3. ADMINISTRACIÓN DE ALIADOS (Los Voluntarios) ---
@admin.register(Aliado)
class AliadoAdmin(admin.ModelAdmin):
    list_display = ('nombre_visible', 'telefono', 'es_verificado', 'esta_disponible')
    list_filter = ('es_verificado', 'esta_disponible')
    search_fields = ('nombre_visible', 'telefono')
    
    # Acción rápida para aprobar voluntarios masivamente
    actions = ['aprobar_aliados']

    def aprobar_aliados(self, request, queryset):
        queryset.update(es_verificado=True)
    aprobar_aliados.short_description = "✅ Verificar/Aprobar aliados seleccionados"


# --- 4. ADMINISTRACIÓN DE SESIONES (Conexiones Humanas) ---
@admin.register(SesionHumana)
class SesionHumanaAdmin(admin.ModelAdmin):
    # Para ver quién está hablando con quién
    list_display = ('usuario', 'aliado', 'fecha_inicio', 'activa')
    list_filter = ('activa', 'fecha_inicio')
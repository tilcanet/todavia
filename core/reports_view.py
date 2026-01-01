# core/reports_view.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count
from .models import Mensaje, UsuarioAnonimo
from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
def reporte_politicas_publicas(request):
    """
    Genera un reporte resumido para el Concejo, Hospital y Ministerio.
    Datos totalmente anónimos y estadísticos.
    """
    periodo_dias = int(request.query_params.get('dias', 30))
    fecha_inicio = timezone.now() - timedelta(days=periodo_dias)

    # 1. Temas más frecuentes (Por qué están mal)
    temas = Mensaje.objects.filter(
        fecha__gte=fecha_inicio, 
        es_de_la_ia=True
    ).exclude(
        sentimiento_detectado="General"
    ).values('sentimiento_detectado').annotate(
        total=Count('sentimiento_detectado')
    ).order_by('-total')

    # 2. Distribución por Zonas (Donde hay más actividad)
    zonas = UsuarioAnonimo.objects.filter(
        fecha_registro__gte=fecha_inicio,
        zona__isnull=False
    ).values('zona').annotate(
        total=Count('zona')
    ).order_by('-total')

    # 3. Alertas de Crisis (Parámetro crítico para Seguridad/Salud)
    alertas_crisis = Mensaje.objects.filter(
        fecha__gte=fecha_inicio,
        sentimiento_detectado="RIESGO_ALTO"
    ).count()

    # 4. Tendencia por Edad (Si los datos existen)
    edades = UsuarioAnonimo.objects.filter(
        fecha_registro__gte=fecha_inicio,
        edad__isnull=False
    ).values('edad').annotate(
        total=Count('edad')
    ).order_by('edad')

    # 5. Métricas de Dispositivos (Alcance técnico)
    dispositivos = UsuarioAnonimo.objects.filter(
        fecha_registro__gte=fecha_inicio,
        dispositivo_modelo__isnull=False
    ).values('dispositivo_modelo', 'dispositivo_os').annotate(
        total=Count('id')
    ).order_by('-total')

    # 6. Mapa de Calor (Coordenadas para riesgo)
    from .models import RegistroUbicacion
    mapa_calor = RegistroUbicacion.objects.filter(
        fecha__gte=fecha_inicio.date()
    ).values('latitud', 'longitud', 'usuario__zona')

    # 7. Lo que la gente dice que falta (Sugerencias/Propuestas)
    from .models import Sugerencia
    sugerencias = Sugerencia.objects.filter(
        fecha__gte=fecha_inicio
    ).values('texto', 'usuario__alias', 'fecha').order_by('-fecha')[:20]

    reporte = {
        "periodo_analizado_dias": periodo_dias,
        "total_charlas_nuevas": UsuarioAnonimo.objects.filter(fecha_registro__gte=fecha_inicio).count(),
        "temas_preocupacion_ranking": list(temas),
        "focos_geograficos": list(zonas),
        "alertas_riesgo_extremo": alertas_crisis,
        "segmentacion_edad": list(edades),
        "metricas_dispositivos": list(dispositivos),
        "mapa_riesgo_coordenadas": list(mapa_calor),
        "sugerencias_comunidad": list(sugerencias),
        "fecha_generacion": timezone.now().isoformat()
    }

    return Response(reporte)

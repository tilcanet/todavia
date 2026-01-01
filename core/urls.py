# core/urls.py
from django.urls import path
from . import views, reports_view

urlpatterns = [
    path('', views.home_view, name='home'),
    path('registrar/', views.registrar_usuario, name='registrar'),
    path('chat/<uuid:usuario_id>/', views.enviar_mensaje, name='chat'),
    path('usuario/<uuid:usuario_id>/zona/', views.actualizar_zona, name='actualizar_zona'),
    path('usuario/<uuid:usuario_id>/alias/', views.actualizar_alias, name='actualizar_alias'),
    path('chat/<uuid:usuario_id>/rompehielo/', views.generar_rompehielo, name='rompehielo'),
    path('chat/<uuid:usuario_id>/actualizar-ubicacion/', views.actualizar_ubicacion, name='actualizar_ubicacion'),
    path('usuario/<uuid:usuario_id>/ticket-ayuda/', views.registrar_ticket_ayuda, name='ticket_ayuda'),
    path('reporte-publico/', reports_view.reporte_politicas_publicas, name='reporte_publico'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
# core/urls.py
from django.urls import path
from . import views, reports_view

urlpatterns = [
    path('', views.home_view, name='home'),
    path('registrar/', views.registrar_usuario, name='registrar'),
    path('usuario/<uuid:usuario_id>/zona/', views.actualizar_zona, name='actualizar_zona'),
    path('chat/<uuid:usuario_id>/', views.enviar_mensaje, name='enviar_mensaje'),
    path('chat/<uuid:usuario_id>/historial/', views.historico_usuario, name='historico_usuario'),
    path('usuario/<uuid:usuario_id>/alias/', views.actualizar_alias, name='actualizar_alias'),
    path('chat/<uuid:usuario_id>/rompehielo/', views.generar_rompehielo, name='rompehielo'),
    path('chat/<uuid:usuario_id>/actualizar-ubicacion/', views.actualizar_ubicacion, name='actualizar_ubicacion'),
    path('usuario/<uuid:usuario_id>/ticket-ayuda/', views.registrar_ticket_ayuda, name='ticket_ayuda'),
    path('usuario/<uuid:usuario_id>/solicitar-aliado/', views.solicitar_aliado, name='solicitar_aliado'),
    path('reporte-publico/', reports_view.reporte_politicas_publicas, name='reporte_publico'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # --- APP ALIADOS ---
    path('aliado/registro/', views.registrar_aliado, name='registrar_aliado'),
    path('aliado/login/', views.login_aliado, name='login_aliado'),
    path('aliado/<int:aliado_id>/estado/', views.estado_aliado, name='estado_aliado'),
    path('aliado/<int:aliado_id>/chats/', views.aliado_mis_chats, name='aliado_chats'),
    path('aliado/chat/<int:sesion_id>/mensajes/', views.aliado_chat_mensajes, name='aliado_chat_mensajes'),
    
    # --- WEB ALIADOS ---
    path('aliado/web/login/', views.aliado_login_web, name='aliado_login_web'),
    path('aliado/web/dashboard/', views.aliado_dashboard_web, name='aliado_dashboard_web'),
    path('aliado/web/registro/', views.aliado_registro_web, name='aliado_registro_web'),
    path('aliado/web/chat/<int:sesion_id>/', views.aliado_chat_web, name='aliado_chat_web'),
    path('aliado/web/status/', views.aliado_toggle_status_web, name='aliado_toggle_status_web'),
]
# core/views.py
import os
import re
import json # <--- AGREGADO
from django.utils import timezone # <--- AGREGADO
from django.shortcuts import render # <--- AGREGADO
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import UsuarioAnonimo, Mensaje, Sugerencia
from .serializers import UsuarioSerializer
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key)
else:
    client = None

# --- 1. PROTOCOLO DE EMERGENCIA (Keywords) ---
KEYWORDS_CRISIS = [
    r'matar', r'morir', r'suicid', r'no quiero vivir', 
    r'terminar con todo', r'quitarme la vida', r'pastillas', 
    r'ahorcar', r'disparo', r'cortarme', r'desaparecer', 
    r'no aguanto mas', r'todo se acabe',
    r'ahogar.*alcohol', r'borracho', r'ebrio', r'mamado', r'machado',
    r'droga', r'coca', r'merca', r'pasta base', r'sobredosis', r'mezclar.*pastillas'
]

# --- 2. EL CEREBRO TERAPÉUTICO (Prompt Técnico) ---
# --- 2. EL CEREBRO TERAPÉUTICO (Prompt Técnico) ---
SYSTEM_PROMPT = """
Eres 'Todavía', una IA de contención emocional para la comunidad. 
Tu propósito es ofrecer un espacio seguro y técnico. 

REGLAS CRÍTICAS:
1. IDIOMA: Responde SIEMPRE en ESPAÑOL.
2. CONOCIMIENTO TERRITORIAL: 
   - SI EL USUARIO ES DE TILCARA: Hospital Tilcara (Lavalle 552, 0388 495-5001).
   - SI ES DE OTRA LOCALIDAD: Pregunta dónde está para buscar ayuda local o sugiere llamar al 911/107.
   - Centro de Atención Provincial: 0800-888-4767.
   - Emergencias Generales: 911.
3. RECOLECCIÓN DE DATOS: 
   - IMPORTANTE: Si no sabes de dónde es el usuario, PREGUNTA SU LOCALIDAD sutilmente.
   - Indaga sutilmente sobre edad si no la tienes.
   - Tu objetivo es profundizar. Si menciona un problema, PREGUNTA POR QUÉ o QUÉ SIENTE QUE FALTA.
4. ESTILO: Máximo 3 oraciones. Empático, cálido y universal.
5. BOTONES DE AYUDA: Explica e invita al usuario a presionar el botón de la campana/alarma (Emergencias) o el de las manos (Aliado) en la parte superior si necesita ayuda inmediata o hablar con una persona.
"""

def home_view(request):
    """
    Página de inicio pública con información de la app y descarga de APK.
    """
    return render(request, 'home.html')

@api_view(['POST'])
def registrar_usuario(request):
    serializer = UsuarioSerializer(data=request.data)
    if serializer.is_valid():
        usuario = serializer.save()
        
        # Guardar metadatos técnicos si vienen
        dispositivo_modelo = request.data.get('dispositivo_modelo')
        dispositivo_os = request.data.get('dispositivo_os')
        if dispositivo_modelo: usuario.dispositivo_modelo = dispositivo_modelo
        if dispositivo_os: usuario.dispositivo_os = dispositivo_os
        usuario.save()
        
        return Response({"mensaje": "Usuario creado", "usuario": serializer.data})
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def enviar_mensaje(request, usuario_id):
    # 1. Validar Usuario
    try:
        usuario = UsuarioAnonimo.objects.get(id=usuario_id)
    except UsuarioAnonimo.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)

    # 2. Validar Texto
    data = request.data
    texto_usuario = data.get('texto') if isinstance(data, dict) else None
    if not texto_usuario:
        return Response({"error": "Falta texto"}, status=400)

    # 3. Guardar mensaje del usuario (SIEMPRE se guarda primero)
    Mensaje.objects.create(usuario=usuario, texto=texto_usuario, es_de_la_ia=False)

    # --- NUEVO: DETECCIÓN DE SUGERENCIAS/LO QUE FALTA ---
    # Si el usuario dice que "falta" algo o similares, lo guardamos como sugerencia.
    palabras_clave_sugerencia = ['falta', 'necesitamos', 'debería', 'estaría bueno', 'necesito que', 'podrían', 'mejorar']
    try:
        if any(p in texto_usuario.lower() for p in palabras_clave_sugerencia):
            # Verificamos que no sea un duplicado exacto reciente para no spamear
            if not Sugerencia.objects.filter(usuario=usuario, texto=texto_usuario).exists():
                Sugerencia.objects.create(usuario=usuario, texto=texto_usuario)
    except Exception as e:
        print(f"Error guardando sugerencia: {e}")

    # 4. DETECTOR DE CRISIS (Seguridad)
    modo_crisis = False
    texto_lower = texto_usuario.lower()
    for pattern in KEYWORDS_CRISIS:
        if re.search(pattern, texto_lower):
            modo_crisis = True
            break
    
    # --- CAMINO A: ES CRISIS ---
    if modo_crisis:
        texto_respuesta = "Estoy detectando mucho dolor en tus palabras. Por favor, no estás solo en esto. Necesito que hablemos con alguien real ahora mismo. Toca el botón rojo de ayuda."
        
        # Guardamos alerta
        msg = Mensaje.objects.create(usuario=usuario, texto=texto_respuesta, es_de_la_ia=True)
        msg.sentimiento_detectado = "RIESGO_ALTO" 
        msg.save()

        # Marcar usuario en ZONA ROJA
        usuario.en_zona_roja = True
        usuario.fecha_zona_roja = timezone.now()
        usuario.save()

        return Response({
            "respuesta": texto_respuesta,
            "alerta_crisis": True 
        })

    # --- CAMINO B: NO ES CRISIS (IA Responde) ---
    
    # Preparamos historial (System Prompt dinámico + Últimos 4 mensajes)
    ultimos_mensajes = usuario.mensajes.order_by('-fecha')[:4]
    info_faltante = []
    if not usuario.zona: info_faltante.append("ZONA DE RESIDENCIA EN TILCARA")
    if not usuario.alias or usuario.alias == "Viajero": info_faltante.append("NOMBRE/ALIAS")
    # También chequear si ya dio una sugerencia
    if not Sugerencia.objects.filter(usuario=usuario).exists():
        info_faltante.append("OPINIÓN SOBRE QUÉ HACE FALTA")
    
    prompt_con_contexto = SYSTEM_PROMPT
    if info_faltante:
        prompt_con_contexto += f"\n\nIMPORTANTE: Te falta conocer: {', '.join(info_faltante)}. Intenta preguntarlo de forma natural pero prioritaria en esta respuesta."

    historial_para_gpt = [{"role": "system", "content": prompt_con_contexto}]
    
    for msg in reversed(ultimos_mensajes):
        role = "assistant" if msg.es_de_la_ia else "user"
        historial_para_gpt.append({"role": role, "content": msg.texto})

    # Llamamos a OpenAI
    if not client:
        texto_ia = "Error: Falta configuración de API Key."
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", # O gpt-4o-mini si tienes acceso
                messages=historial_para_gpt,
                temperature=0.5, # Un poco más creativo para empatía
                max_tokens=200
            )
            texto_ia = response.choices[0].message.content
        except Exception as e:
            texto_ia = "Lo siento, tuve un problema de conexión momentáneo. ¿Podrías repetirlo?"
            print(f"Error OpenAI: {e}")

    # AUTO-ETIQUETADO (Clasificación de tema)
    tema_detectado = "General"
    texto_analisis = texto_usuario.lower() + " " + texto_ia.lower()

    if any(x in texto_analisis for x in ['novia', 'novio', 'pareja', 'amor', 'ruptura', 'dejo']):
        tema_detectado = "Ruptura Amorosa"
    elif any(x in texto_analisis for x in ['alcohol', 'cerveza', 'vino', 'chupar', 'tomar', 'drogas']):
        tema_detectado = "Consumo Sustancias"
    elif any(x in texto_analisis for x in ['trabajo', 'plata', 'dinero', 'deuda', 'económico']):
        tema_detectado = "Problemas Económicos"
    elif any(x in texto_analisis for x in ['solo', 'soledad', 'nadie', 'aislado', 'vacío']):
        tema_detectado = "Soledad"
    elif any(x in texto_analisis for x in ['ansiedad', 'miedo', 'panico', 'nervios']):
        tema_detectado = "Ansiedad"

    # AUTO-DETECCIÓN DE ZONA (Si no la tiene)
    if not usuario.zona:
        zonas_posibles = [
            "Centro", "Matadero", "Villa Florida", "Pueblo Nuevo", 
            "Sumay Pacha", "Maimará", "Juella", "Huacalera"
        ]
        for z in zonas_posibles:
            if z.lower() in texto_usuario.lower():
                usuario.zona = f"Tilcara - {z}" if z not in ["Maimará", "Juella", "Huacalera", "Sumay Pacha"] else z
                usuario.save()
                break

    # Guardamos respuesta de la IA
    msg_ia = Mensaje.objects.create(usuario=usuario, texto=texto_ia, es_de_la_ia=True)
    msg_ia.sentimiento_detectado = tema_detectado
    msg_ia.save()

    return Response({
        "respuesta": texto_ia,
        "alerta_crisis": False
    })

@api_view(['POST'])
def actualizar_zona(request, usuario_id):
    try:
        usuario = UsuarioAnonimo.objects.get(id=usuario_id)
        nueva_zona = request.data.get('zona')
        if nueva_zona:
            usuario.zona = nueva_zona
            usuario.save()
            return Response({"mensaje": "Zona guardada", "zona": nueva_zona})
        else:
            return Response({"error": "Falta zona"}, status=400)
    except UsuarioAnonimo.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)

@api_view(['POST'])
def actualizar_alias(request, usuario_id):
    """
    Permite al usuario ponerse un nombre/apodo. 
    Si el usuario no existe (ej: DB reiniciada), lo creamos con ese ID.
    """
    alias = request.data.get('alias')
    modelo = request.data.get('dispositivo_modelo')
    os_info = request.data.get('dispositivo_os')

    usuario, created = UsuarioAnonimo.objects.get_or_create(
        id=usuario_id,
        defaults={
            'alias': alias if alias else "Viajero",
            'dispositivo_modelo': modelo,
            'dispositivo_os': os_info
        }
    )

    if not created:
        if alias: usuario.alias = alias
        if modelo: usuario.dispositivo_modelo = modelo
        if os_info: usuario.dispositivo_os = os_info
        usuario.save()

    return Response({
        "mensaje": "Usuario sincronizado" if created else "Alias guardado",
        "alias": usuario.alias,
        "created": created
    })

@api_view(['GET'])
def generar_rompehielo(request, usuario_id):
    try:
        usuario = UsuarioAnonimo.objects.get(id=usuario_id)
    except UsuarioAnonimo.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)

    # Prompt para que GPT genere una pregunta de seguimiento inteligente
    missing_info = []
    if not usuario.zona: missing_info.append("su barrio o zona aquí en Tilcara (esto es prioridad para focalizar ayuda)")
    if not usuario.alias or usuario.alias == "Viajero": missing_info.append("su nombre o cómo prefiere que lo llamen")
    
    # También chequear si ya dio una sugerencia
    from .models import Sugerencia
    if not Sugerencia.objects.filter(usuario=usuario).exists():
        missing_info.append("su opinión sobre qué hace falta en la comunidad para ayudar mejor")

    instruccion = f"El usuario está en silencio. Genera una frase corta, empática y en ESPAÑOL."
    if missing_info:
        instruccion += f" Tu objetivo PRIORITARIO es intentar saber: {', '.join(missing_info)}. Hazlo de forma sutil pero clara."
    else:
        instruccion += " Simplemente recuérdale que estás aquí para acompañarlo y escucharlo."
    
    prompt_rompehielo = f"{instruccion} Mantén el tono de 'Todavía'. Responde SOLO con la frase."

    if not client:
        return Response({"respuesta": "Sigo aquí, por si quieres compartir algo más. 🌿"})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt_rompehielo}],
            temperature=0.7,
            max_tokens=100
        )
        texto_rompehielo = response.choices[0].message.content
        return Response({"respuesta": texto_rompehielo})
    except Exception as e:
        print(f"Error Rompehielo: {e}")
        return Response({"respuesta": "A veces el silencio también ayuda a pensar. Tómate tu tiempo. 🌿"})

@api_view(['POST'])
def actualizar_ubicacion(request, usuario_id):
    """
    Guarda las coordenadas GPS del usuario en el registro diario.
    """
    from .models import RegistroUbicacion
    from django.utils import timezone
    try:
        usuario = UsuarioAnonimo.objects.get(id=usuario_id)
        lat = request.data.get('latitud')
        lon = request.data.get('longitud')
        
        if lat is not None and lon is not None:
            # Creamos un nuevo registro histórico para generar puntos calientes
            RegistroUbicacion.objects.create(
                usuario=usuario, 
                latitud=lat,
                longitud=lon
            )
            
            # También mantenemos la última ubicación en el perfil del usuario para acceso rápido
            usuario.latitud = lat
            usuario.longitud = lon
            
            # --- GEO-DETERMINACIÓN DE ZONA (Mejora con Localidades) ---
            # Si el usuario no tiene zona o la zona fue auto-detectada previamente, intentamos mejorarla
            if not usuario.zona or usuario.zona.startswith("Detectado:"):
                from .models import Localidad
                from math import radians, cos, sin, asin, sqrt

                def haversine(lon1, lat1, lon2, lat2):
                    # Distancia en KM
                    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                    dlon = lon2 - lon1 
                    dlat = lat2 - lat1 
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a)) 
                    return c * 6371 

                localidad_cercana = None
                distancia_minima = float('inf')
                
                # Buscamos la más cercana (Optimización simple: traer solo campos necesarios)
                # NOTA: Con 361 registros es rápido iterar en Python. Para miles, usar GeoDjango.
                for loc in Localidad.objects.all():
                    dist = haversine(lon, lat, loc.longitud, loc.latitud)
                    if dist < distancia_minima:
                        distancia_minima = dist
                        localidad_cercana = loc
                
                # Si está a menos de 5 KM, asignamos
                if localidad_cercana and distancia_minima < 5:
                    nueva_zona = f"Detectado: {localidad_cercana.nombre}"
                    # Agregamos municipio si es distinto
                    if localidad_cercana.municipio and localidad_cercana.municipio.lower() not in localidad_cercana.nombre.lower():
                         nueva_zona += f" ({localidad_cercana.municipio})"
                    usuario.zona = nueva_zona

            usuario.save()
            
            return Response({
                "mensaje": "Ubicación diaria actualizada correctamente", 
                "es_nuevo_dia": created
            })
        else:
            return Response({"error": "Faltan coordenadas"}, status=400)
    except UsuarioAnonimo.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)


@api_view(['POST'])
def registrar_ticket_ayuda(request, usuario_id):
    """
    Registra un click en un botón de emergencia (SAME, Policía, etc.)
    """
    from .models import TicketAyuda
    try:
        usuario = UsuarioAnonimo.objects.get(id=usuario_id)
        tipo = request.data.get('tipo', 'DESCONOCIDO')
        
        # Usamos la ubicación actual del usuario si no se envía nueva
        lat = request.data.get('latitud', usuario.latitud)
        lon = request.data.get('longitud', usuario.longitud)

        TicketAyuda.objects.create(
            usuario=usuario,
            tipo=tipo,
            latitud=lat,
            longitud=lon
        )
        return Response({"mensaje": f"Ticket {tipo} registrado"}, status=201)
    except UsuarioAnonimo.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    """
    Vista que renderiza el tablero visual (Dashboard).
    Recopila todos los datos estadísticos y los envía al template.
    Permite filtrar por periodo: hoy, semana, mes, siempre.
    """
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    import json

    # 1. Definir Periodo de Filtrado
    periodo = request.GET.get('periodo', 'semana') 
    fecha_param = request.GET.get('fecha')
    ahora = timezone.now()
    
    filtro_kwargs = {}
    filtro_registro_kwargs = {}

    if fecha_param:
        # MODO HISTÓRICO (Día específico)
        try:
            fecha_obj = timezone.datetime.strptime(fecha_param, '%Y-%m-%d').date()
            # Filtramos todo lo que ocurra en ese día
            filtro_kwargs = {
                "fecha__year": fecha_obj.year, 
                "fecha__month": fecha_obj.month, 
                "fecha__day": fecha_obj.day
            }
            # Para modelos con field 'fecha_registro' (UsuarioAnonimo)
            filtro_registro_kwargs = {
                "fecha_registro__year": fecha_obj.year,
                "fecha_registro__month": fecha_obj.month,
                "fecha_registro__day": fecha_obj.day
            }
            periodo = fecha_param # Para que la UI sepa que estamos en modo fecha
        except ValueError:
            # Si falla la fecha, volvemos a hoy
            fecha_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
            filtro_kwargs = {"fecha__gte": fecha_inicio}
            filtro_registro_kwargs = {"fecha_registro__gte": fecha_inicio}
            periodo = 'hoy'
            fecha_param = None

    else:
        # MODO PERIODO RELATIVO
        hoy_local = timezone.localtime(ahora).date()
        if periodo == 'hoy':
            fecha_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
            filtro_kwargs = {"fecha__date": hoy_local}
            filtro_registro_kwargs = {"fecha_registro__date": hoy_local}
            filtro_ubicacion_kwargs = {"fecha__date": hoy_local}
        elif periodo == 'semana':
            fecha_inicio = ahora - timedelta(days=7)
            filtro_kwargs = {"fecha__gte": fecha_inicio}
            filtro_registro_kwargs = {"fecha_registro__gte": fecha_inicio}
            filtro_ubicacion_kwargs = {"fecha__gte": fecha_inicio.date()}
        elif periodo == 'mes':
            fecha_inicio = ahora - timedelta(days=30)
            filtro_kwargs = {"fecha__gte": fecha_inicio}
            filtro_registro_kwargs = {"fecha_registro__gte": fecha_inicio}
            filtro_ubicacion_kwargs = {"fecha__gte": fecha_inicio.date()}
        else: # 'siempre'
            periodo = 'siempre'
            fecha_inicio = ahora - timedelta(days=365*20)
            filtro_kwargs = {}
            filtro_registro_kwargs = {}
            filtro_ubicacion_kwargs = {}

    # 2. KPIs Filtrados
    total_usuarios = UsuarioAnonimo.objects.filter(**filtro_registro_kwargs).count()
    total_mensajes = Mensaje.objects.filter(**filtro_kwargs).count()
    
    # Alertas
    alertas_dict = filtro_kwargs.copy()
    alertas_dict['sentimiento_detectado'] = "RIESGO_ALTO"
    alertas_riesgo = Mensaje.objects.filter(**alertas_dict).count()
    
    # Usuarios en Zona Roja ACTIVOS
    usuarios_zona_roja = UsuarioAnonimo.objects.filter(en_zona_roja=True).order_by('-fecha_zona_roja')

    # 3. Datos para el mapa (Usando RegistroUbicacion para historial)
    from .models import RegistroUbicacion
    if fecha_param:
        puntos_gps = list(RegistroUbicacion.objects.filter(fecha__date=fecha_obj)
                          .values('usuario__alias', 'latitud', 'longitud', 'fecha', 'usuario__en_zona_roja'))
    else:
        puntos_gps = list(RegistroUbicacion.objects.filter(**filtro_ubicacion_kwargs)
                          .values('usuario__alias', 'latitud', 'longitud', 'fecha', 'usuario__en_zona_roja'))
    
    # Adaptar nombres para el JS del mapa y agregar intensidad para heatmap
    datos_mapa = []
    for p in puntos_gps:
        intensidad = 1.0
        if p['usuario__en_zona_roja']:
            intensidad = 5.0 
        
        datos_mapa.append({
            'lat': p['latitud'],
            'lng': p['longitud'],
            'alias': p['usuario__alias'],
            'fecha': p['fecha'].strftime('%d/%m'),
            'en_zona_roja': p['usuario__en_zona_roja'],
            'intensity': intensidad
        })

    # 4. Datos para Gráficos
    sent_dict = filtro_kwargs.copy()
    sent_dict['es_de_la_ia'] = True
    sentimientos = list(Mensaje.objects.filter(**sent_dict)
                        .exclude(sentimiento_detectado__in=["General", None])
                        .values('sentimiento_detectado')
                        .annotate(total=Count('id'))
                        .order_by('-total')[:5])
    
    dispositivos = list(UsuarioAnonimo.objects.filter(**filtro_registro_kwargs)
                        .values('dispositivo_modelo')
                        .annotate(total=Count('id'))
                        .order_by('-total')[:5])

    # 5. Sugerencias Recientes
    sugerencias = Sugerencia.objects.filter(**filtro_kwargs).order_by('-fecha')[:10]

    # 6. Tickets de Emergencia
    from .models import TicketAyuda
    tickets_emergencia = TicketAyuda.objects.filter(**filtro_kwargs).select_related('usuario').order_by('-fecha')[:20]

    context = {
        "periodo": periodo,
        "kpis": {
            "usuarios": total_usuarios,
            "mensajes": total_mensajes,
            "alertas": alertas_riesgo,
            "zona_roja_activos": usuarios_zona_roja.count()
        },
        "puntos_gps": json.dumps(datos_mapa),
        "usuarios_zona_roja": usuarios_zona_roja[:5], # Pasamos los primeros 5 para mostrar lista si se quiere
        "sentimientos_json": json.dumps(sentimientos),
        "dispositivos_json": json.dumps(dispositivos),
        "sugerencias": sugerencias,
        "tickets_emergencia": tickets_emergencia,
    }
    
    return render(request, 'dashboard.html', context)
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
    from .models import Aliado, SesionHumana # Importación local

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

    # 0. CHEQUEO DE SESIÓN HUMANA ACTIVA
    # Si ya está hablando con un humano, la IA se calla.
    sesion_activa = SesionHumana.objects.filter(usuario=usuario, activa=True).first()
    if sesion_activa:
        # Aquí la app del Aliado debería hacer polling para recibir este mensaje
        return Response({"respuesta": "", "modo_humano": True})

    # --- NUEVO: DETECCIÓN DE SUGERENCIAS/LO QUE FALTA ---
    palabras_clave_sugerencia = ['falta', 'necesitamos', 'debería', 'estaría bueno', 'necesito que', 'podrían', 'mejorar']
    try:
        if any(p in texto_usuario.lower() for p in palabras_clave_sugerencia):
            if not Sugerencia.objects.filter(usuario=usuario, texto=texto_usuario).exists():
                Sugerencia.objects.create(usuario=usuario, texto=texto_usuario)
    except Exception as e:
        print(f"Error guardando sugerencia: {e}")

    texto_lower = texto_usuario.lower()

    # --- LÓGICA DE CONEXIÓN CON HUMANO ---
    # Si está en crisis y dice que SÍ (o pide hablar con alguien explícitamente)
    intencion_humana = 'hablar con alguien' in texto_lower or 'persona real' in texto_lower
    respuesta_afirmativa_crisis = usuario.en_zona_roja and any(x == texto_lower for x in ['si', 'sí', 'bueno', 'dale', 'por favor'])
    
    if intencion_humana or respuesta_afirmativa_crisis:
         aliado_disp = Aliado.objects.filter(esta_disponible=True).first()
         if aliado_disp:
             SesionHumana.objects.create(usuario=usuario, aliado=aliado_disp, activa=True)
             # aliado_disp.esta_disponible = False # Opcional: Si queremos que atienda a uno solo a la vez
             # aliado_disp.save()
             
             msg_sys = f"Te he conectado con {aliado_disp.nombre_visible} ({aliado_disp.get_especialidad_display()}). Te leerá en breve."
             Mensaje.objects.create(usuario=usuario, texto=msg_sys, es_de_la_ia=True)
             
             return Response({"respuesta": msg_sys, "modo_humano": True})
         else:
             if intencion_humana: # Solo si lo pidió explícitamente avisamos que no hay nadie
                 msg_sys = "Lo siento, no hay aliados conectados ahora mismo. Pero yo sigo aquí."
                 Mensaje.objects.create(usuario=usuario, texto=msg_sys, es_de_la_ia=True)
                 return Response({"respuesta": msg_sys, "alerta_crisis": False})

    # 4. DETECTOR DE CRISIS (Seguridad)
    modo_crisis = False
    for pattern in KEYWORDS_CRISIS:
        if re.search(pattern, texto_lower):
            modo_crisis = True
            break
    
    # --- CAMINO A: ES CRISIS ---
    if modo_crisis:
        texto_respuesta = "Estoy detectando mucho dolor en tus palabras. Por favor, no estás solo en esto. Necesito que hablemos con alguien real ahora mismo. Toca el botón rojo de ayuda."
        
        # Ofrecer Aliado si hay
        if Aliado.objects.filter(esta_disponible=True).exists():
            texto_respuesta += "\n\n(Hay vecinos escuchando ahora mismo. ¿Quieres que te conecte con uno? Responde SÍ)."

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

@api_view(['GET'])
def historico_usuario(request, usuario_id):
    """
    Devuelve todo el historial de chat para este usuario.
    Útil para polling en la app móvil y ver respuestas del Aliado.
    """
    try:
        usuario = UsuarioAnonimo.objects.get(id=usuario_id)
        # Traemos los ultimos 50 mensajes cronológicos
        mensajes = usuario.mensajes.all().order_by('fecha')[:50]
        
        data = []
        for m in mensajes:
            data.append({
                "texto": m.texto,
                "es_de_la_ia": m.es_de_la_ia,
                "fecha": m.fecha.isoformat(),
                # "id": m.id # Opcional si queremos dedup en el cliente
            })
        return Response({"mensajes": data})
    except UsuarioAnonimo.DoesNotExist:
         return Response({"error": "Usuario no encontrado"}, status=404)

@api_view(['POST'])
def solicitar_aliado(request, usuario_id):
    """
    Endpoint específico para el botón de 'Manitos'.
    Busca un aliado disponible y crea la sesión.
    """
    from .models import Aliado, SesionHumana
    try:
        usuario = UsuarioAnonimo.objects.get(id=usuario_id)
        
        # 1. Si ya tiene sesión activa, devolvemos OK
        if SesionHumana.objects.filter(usuario=usuario, activa=True).exists():
             return Response({"mensaje": "Ya tienes una sesión activa", "estado": "YA_EXISTE"})

        # 2. Buscar aliado
        aliado_disp = Aliado.objects.filter(esta_disponible=True).first()
        
        if aliado_disp:
             SesionHumana.objects.create(usuario=usuario, aliado=aliado_disp, activa=True)
             
             # Mensaje de sistema confirmando
             msg_sys = f"Conectando con {aliado_disp.nombre_visible}... Te leerá en breve."
             Mensaje.objects.create(usuario=usuario, texto=msg_sys, es_de_la_ia=True)
             
             return Response({
                 "mensaje": "Aliado asignado", 
                 "estado": "ASIGNADO",
                 "aliado_nombre": aliado_disp.nombre_visible
             })
        else:
             # No hay nadie
             msg_sys = "No hemos encontrado aliados disponibles en este momento. Pero yo (Todavía) sigo aquí para escucharte."
             Mensaje.objects.create(usuario=usuario, texto=msg_sys, es_de_la_ia=True)
             return Response({"mensaje": "Sin aliados disponibles", "estado": "SIN_ALIADOS"})

    except UsuarioAnonimo.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)

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
                "es_nuevo_dia": True  # Simplificado ya que se crea el registro
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
    periodo = request.GET.get('periodo', 'siempre') 
    fecha_param = request.GET.get('fecha')
    
    # Determinar la Fecha de Referencia (Fin del intervalo)
    ahora = timezone.now()
    hoy_local = timezone.localtime(ahora).date()
    
    if fecha_param:
        try:
            fecha_ref = timezone.datetime.strptime(fecha_param, '%Y-%m-%d').date()
        except ValueError:
            fecha_ref = hoy_local
    else:
        fecha_ref = hoy_local

    # Determinar Fecha de Inicio según el periodo
    fecha_inicio = None
    
    if periodo == 'hoy':
        fecha_inicio = fecha_ref
    elif periodo == 'semana':
        fecha_inicio = fecha_ref - timedelta(days=7)
    elif periodo == 'mes':
        fecha_inicio = fecha_ref - timedelta(days=30)
    else: # 'siempre'
        fecha_inicio = None # Sin limite inferior

    # Construir kwargs de filtro
    filtro_kwargs = {}
    filtro_registro_kwargs = {}
    filtro_ubicacion_kwargs = {}

    if fecha_inicio:
        # Rango inclusivo [Inicio, Fin]
        filtro_kwargs = {"fecha__date__range": [fecha_inicio, fecha_ref]}
        filtro_registro_kwargs = {"fecha_registro__date__range": [fecha_inicio, fecha_ref]}
        filtro_ubicacion_kwargs = {"fecha__date__range": [fecha_inicio, fecha_ref]}
    else:
        # Solo limite superior (hasta fecha_ref incluidos)
        filtro_kwargs = {"fecha__date__lte": fecha_ref}
        filtro_registro_kwargs = {"fecha_registro__date__lte": fecha_ref}
        filtro_ubicacion_kwargs = {"fecha__date__lte": fecha_ref}

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
    print(f"DEBUG: filtro_ubicacion_kwargs = {filtro_ubicacion_kwargs}")
    puntos_gps = list(RegistroUbicacion.objects.filter(**filtro_ubicacion_kwargs)
                        .values('usuario__alias', 'latitud', 'longitud', 'fecha', 'usuario__en_zona_roja'))
    
    print(f"DEBUG: Encontrados {len(puntos_gps)} puntos GPS")
    
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
        "sugerencias": sugerencias,
        "puntos_gps": json.dumps(datos_mapa),
        "usuarios_zona_roja": usuarios_zona_roja[:5], # Pasamos los primeros 5 para mostrar lista si se quiere
        "sentimientos_json": json.dumps(sentimientos),
        "dispositivos_json": json.dumps(dispositivos),
        "sugerencias": sugerencias,
        "tickets_emergencia": tickets_emergencia,
    }
    
    return render(request, 'dashboard.html', context)

# ---------------------------------------------------------
#                 APP ALIADOS (Profesionales/Amigos)
# ---------------------------------------------------------

@api_view(['POST'])
def registrar_aliado(request):
    """
    Registro desde la App de Acompañante.
    Crea un Djando User + Perfil Aliado.
    """
    from django.contrib.auth.models import User
    from .models import Aliado
    
    data = request.data
    username = data.get('username') # Email o telefono
    password = data.get('password')
    nombre = data.get('nombre_visible')
    telefono = data.get('telefono')
    especialidad = data.get('especialidad', 'VECINO')
    especialidad_otro = data.get('especialidad_otro', '')
    
    if not username or not password or not nombre:
        return Response({"error": "Faltan datos obligatorios"}, status=400)
        
    if User.objects.filter(username=username).exists():
        return Response({"error": "Este usuario ya existe"}, status=400)
    
    try:
        # Crear User
        user = User.objects.create_user(username=username, password=password)
        
        # Crear Aliado
        aliado = Aliado.objects.create(
            usuario_real=user,
            nombre_visible=nombre,
            telefono=telefono,
            especialidad=especialidad,
            especialidad_otro=especialidad_otro,
            esta_disponible=True # Al registrarse ya queda disponible
        )
        
        return Response({
            "mensaje": "Cuenta creada con éxito",
            "aliado_id": aliado.id,
            "nombre": aliado.nombre_visible,
            "especialidad": aliado.get_especialidad_display()
        }, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def login_aliado(request):
    """
    Login simple para la App de Acompañante.
    """
    from django.contrib.auth import authenticate
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    # Intenta autenticar
    user = authenticate(username=username, password=password)
    
    if user:
        try:
            aliado = user.perfil_aliado
            # Auto-activar al loguearse
            aliado.esta_disponible = True
            aliado.save()
            
            return Response({
                "mensaje": "Login exitoso",
                "aliado_id": aliado.id,
                "nombre": aliado.nombre_visible,
                "especialidad": aliado.get_especialidad_display(),
                "esta_disponible": aliado.esta_disponible
            })
        except:
             return Response({"error": "Este usuario no tiene perfil de Aliado"}, status=403)
    else:
        return Response({"error": "Credenciales inválidas"}, status=401)

@api_view(['POST'])
def estado_aliado(request, aliado_id):
    """
    Switch ON/OFF (Estoy en línea / Me voy)
    """
    from .models import Aliado
    try:
        aliado = Aliado.objects.get(id=aliado_id)
        nuevo_estado = request.data.get('disponible') # Boolean
        
        if nuevo_estado is not None:
            aliado.esta_disponible = nuevo_estado
            aliado.save()
        
        return Response({
            "mensaje": "Estado actualizado", 
            "esta_disponible": aliado.esta_disponible
        })
    except Aliado.DoesNotExist:
        return Response({"error": "Aliado no encontrado"}, status=404)

@api_view(['GET'])
def aliado_mis_chats(request, aliado_id):
    """
    Devuelve las sesiones activas asignadas a este aliado.
    """
    from .models import Aliado, SesionHumana
    try:
        aliado = Aliado.objects.get(id=aliado_id)
        sesiones = SesionHumana.objects.filter(aliado=aliado, activa=True).order_by('-fecha_inicio')
        
        data = []
        for s in sesiones:
            data.append({
                "sesion_id": s.id,
                "usuario_alias": s.usuario.alias,
                "usuario_zona": s.usuario.zona or "Desconocida",
                "fecha_inicio": s.fecha_inicio,
                "mensajes_no_leidos": 0 # TODO: Implementar contador real
            })
            
        return Response({"sesiones": data})
            
    except Aliado.DoesNotExist:
        return Response({"error": "Aliado no encontrado"}, status=404)

@api_view(['GET', 'POST'])
def aliado_chat_mensajes(request, sesion_id):
    """
    Gestiona los mensajes dentro de una sesión humana.
    GET: Trae el historial.
    POST: El Aliado envía un mensaje al Usuario.
    """
    from .models import SesionHumana, Mensaje
    try:
        sesion = SesionHumana.objects.get(id=sesion_id)
        
        # GET: Historial
        if request.method == 'GET':
            # Traemos los ultimos 50 mensajes
            mensajes = Mensaje.objects.filter(usuario=sesion.usuario).order_by('fecha')
            data = []
            for m in mensajes:
                 # En la APP Aliado:
                 # es_de_la_ia = False -> Es del USUARIO (Izquierda)
                 # es_de_la_ia = True -> Es MIO o IA (Derecha)
                data.append({
                    "texto": m.texto,
                    "es_de_la_ia": m.es_de_la_ia, 
                    "fecha": m.fecha
                })
            return Response({"mensajes": data})

        # POST: Enviar respuesta
        elif request.method == 'POST':
            texto = request.data.get('texto')
            if not texto: return Response({"error": "Falta texto"}, status=400)
            
            Mensaje.objects.create(
                usuario=sesion.usuario,
                texto=texto,
                es_de_la_ia=True 
            )
            return Response({"mensaje": "Enviado"})

    except SesionHumana.DoesNotExist:
        return Response({"error": "Sesión no encontrada"}, status=404)

# ---------------------------------------------------------
#                 WEB ALIADOS (INTERFACE PC)
# ---------------------------------------------------------

def aliado_login_web(request):
    from django.contrib.auth import authenticate, login
    from django.shortcuts import redirect
    
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
             if hasattr(user, 'perfil_aliado'):
                 login(request, user)
                 # Auto activar
                 user.perfil_aliado.esta_disponible = True
                 user.perfil_aliado.save()
                 return redirect('aliado_dashboard_web')
             else:
                 return render(request, 'aliado_login.html', {"error": "Tu usuario no es Aliado"})
        else:
            return render(request, 'aliado_login.html', {"error": "Credenciales inválidas"})
            
    return render(request, 'aliado_login.html')

@login_required
def aliado_dashboard_web(request):
    try:
        aliado = request.user.perfil_aliado
    except:
        return render(request, 'aliado_login.html', {"error": "No tienes perfil de Aliado"})

    from .models import SesionHumana
    sesiones = SesionHumana.objects.filter(aliado=aliado, activa=True).order_by('-fecha_inicio')
    
    return render(request, 'aliado_dashboard.html', {
        "aliado": aliado, 
        "sesiones": sesiones
    })

@login_required
def aliado_chat_web(request, sesion_id):
    from .models import SesionHumana
    # Validar que sea SU sesión
    try:
        aliado = request.user.perfil_aliado
        sesion = SesionHumana.objects.get(id=sesion_id, aliado=aliado)
    except:
        return redirect('aliado_dashboard_web')
    
    return render(request, 'aliado_chat.html', {"sesion": sesion})

@login_required
def aliado_toggle_status_web(request):
    import json
    from django.http import JsonResponse
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            aliado = request.user.perfil_aliado
            aliado.esta_disponible = body.get('disponible', False)
            aliado.save()
            return JsonResponse({"estado": aliado.esta_disponible})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
@login_required
def aliado_registro_web(request):
    """
    Permite a un Aliado existente (o admin) registrar uno nuevo.
    """
    if not request.user.is_staff and not hasattr(request.user, 'perfil_aliado'):
        return  render(request, 'aliado_login.html', {"error": "No tienes permisos"})

    if request.method == 'POST':
        from django.contrib.auth.models import User
        from .models import Aliado
        
        u = request.POST.get('username')
        p = request.POST.get('password')
        n = request.POST.get('nombre')
        t = request.POST.get('telefono')
        e = request.POST.get('especialidad')
        
        if User.objects.filter(username=u).exists():
             return render(request, 'aliado_registro.html', {"error": "El usuario ya existe"})
             
        user = User.objects.create_user(username=u, password=p)
        Aliado.objects.create(
            usuario_real=user,
            nombre_visible=n,
            telefono=t,
            especialidad=e,
            esta_disponible=True
        )
        return redirect('aliado_dashboard_web')

    return render(request, 'aliado_registro.html')
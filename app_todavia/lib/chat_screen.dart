import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:geolocator/geolocator.dart';
import 'package:url_launcher/url_launcher.dart';

class PantallaChat extends StatefulWidget {
  final String usuarioId;
  final String baseUrl;
  final String aliasUsuario;

  const PantallaChat({
    super.key,
    required this.usuarioId,
    required this.baseUrl,
    required this.aliasUsuario,
  });

  @override
  State<PantallaChat> createState() => _PantallaChatState();
}

class _PantallaChatState extends State<PantallaChat> {
  final TextEditingController _mensajeController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<Map<String, dynamic>> _mensajes = [];
  bool _enviando = false;

  @override
  void initState() {
    super.initState();
    // Mensaje de bienvenida inicial
    _mensajes.add({
      "texto": "Hola ${widget.aliasUsuario}, soy Todavía. Estoy aquí para escucharte. ¿Cómo te sientes hoy?",
      "es_de_la_ia": true,
      "fecha": DateTime.now(),
    });
    
    // Solicitar ubicación al iniciar
    _enviarUbicacionActual();
  }

  Future<void> _enviarUbicacionActual() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) return;

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) return;
      }
      
      if (permission == LocationPermission.deniedForever) return;

      Position position = await Geolocator.getCurrentPosition();
      
      final url = Uri.parse('${widget.baseUrl}/chat/${widget.usuarioId}/actualizar-ubicacion/');
      await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "latitud": position.latitude,
          "longitud": position.longitude,
        }),
      );
      print("Ubicación enviada: ${position.latitude}, ${position.longitude}");
    } catch (e) {
      print("Error enviando ubicación: $e");
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _enviarMensaje() async {
    final texto = _mensajeController.text.trim();
    if (texto.isEmpty || _enviando) return;

    setState(() {
      _mensajes.add({
        "texto": texto,
        "es_de_la_ia": false,
        "fecha": DateTime.now(),
      });
      _enviando = true;
    });
    _mensajeController.clear();
    _scrollToBottom();

    try {
      final url = Uri.parse('${widget.baseUrl}/chat/${widget.usuarioId}/');
      final respuesta = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"texto": texto}),
      );

      if (respuesta.statusCode == 200) {
        final data = jsonDecode(respuesta.body);
        setState(() {
          _mensajes.add({
            "texto": data['respuesta'],
            "es_de_la_ia": true,
            "fecha": DateTime.now(),
          });
        });
        _scrollToBottom();
      } else {
        _mostrarError("Error del servidor: ${respuesta.statusCode}");
      }
    } catch (e) {
      _mostrarError("Error de conexión. Verifica tu internet.");
    } finally {
      setState(() => _enviando = false);
    }
  }

  void _mostrarError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.redAccent),
    );
  }

  void _mostrarOpcionesEmergencia() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => Container(
        padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 50, height: 5,
              margin: const EdgeInsets.only(bottom: 20),
              decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(10)),
            ),
            Text("AYUDA INMEDIATA", style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.redAccent)),
            const SizedBox(height: 8),
            Text("Se registrará tu ubicación para asistencia.", style: GoogleFonts.outfit(color: Colors.grey, fontSize: 13)),
            const SizedBox(height: 25),
            _botonEmergencia(Icons.medical_services, "SAME (107)", Colors.red, "SAME", "107"),
            _botonEmergencia(Icons.local_police, "POLICÍA (911)", Colors.blue, "POLICIA", "911"),
            _botonEmergencia(Icons.local_fire_department, "BOMBEROS (100)", Colors.orange, "BOMBEROS", "100"),
            _botonEmergencia(Icons.woman, "V. GÉNERO (144)", Colors.purple, "GENERO", "144"),
            const SizedBox(height: 10),
          ],
        ),
      ),
    );
  }

  Widget _botonEmergencia(IconData icono, String label, Color color, String tipo, String numero) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(backgroundColor: color.withOpacity(0.1), child: Icon(icono, color: color)),
        title: Text(label, style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
        trailing: const Icon(Icons.phone_in_talk, size: 20, color: Colors.green),
        onTap: () async {
          Navigator.pop(context);
          // 1. Registrar el ticket en el servidor
          _registrarTicketAyuda(tipo);
          
          // 2. Realizar la llamada real
          final url = Uri.parse("tel:$numero");
          if (await canLaunchUrl(url)) {
            await launchUrl(url);
          }
        },
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15), side: BorderSide(color: Colors.grey[200]!)),
      ),
    );
  }

  Future<void> _registrarTicketAyuda(String tipo) async {
    try {
      Position? position;
      try {
        position = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.high,
          timeLimit: const Duration(seconds: 5),
        );
      } catch (_) {}

      final url = Uri.parse('${widget.baseUrl}/usuario/${widget.usuarioId}/ticket-ayuda/');
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "tipo": tipo,
          "latitud": position?.latitude,
          "longitud": position?.longitude,
        }),
      );
      
      if (response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Pedido de ayuda ($tipo) enviado correctamente."), backgroundColor: Colors.green),
        );
      } else {
        print("Error en ticket: ${response.body}");
        _mostrarError("Error al registrar alerta en el servidor.");
      }
    } catch (e) {
      _mostrarError("Error enviando alerta. Llama directamente al número de emergencia.");
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorPrimario = const Color(0xFF009688);
    final colorFondo = const Color(0xFFF1F8E9);

    return Scaffold(
      backgroundColor: colorFondo,
      appBar: AppBar(
        title: Text("Todavía", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: colorPrimario,
        elevation: 0,
        centerTitle: true,
        actions: [
          IconButton(
            icon: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.redAccent.withOpacity(0.1),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.redAccent, width: 2),
              ),
              child: const Icon(Icons.emergency_share_outlined, color: Colors.redAccent, size: 24),
            ),
            onPressed: _mostrarOpcionesEmergencia,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(20),
              itemCount: _mensajes.length,
              itemBuilder: (context, index) {
                final msg = _mensajes[index];
                final esIA = msg['es_de_la_ia'];

                return Align(
                  alignment: esIA ? Alignment.centerLeft : Alignment.centerRight,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                    decoration: BoxDecoration(
                      color: esIA ? Colors.white : colorPrimario,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(20),
                        topRight: const Radius.circular(20),
                        bottomLeft: Radius.circular(esIA ? 0 : 20),
                        bottomRight: Radius.circular(esIA ? 20 : 0),
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.05),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        )
                      ],
                    ),
                    child: Text(
                      msg['texto'],
                      style: GoogleFonts.outfit(
                        color: esIA ? Colors.black87 : Colors.white,
                        fontSize: 16,
                      ),
                    ),
                  ).animate().fadeIn(duration: 400.ms).slideX(begin: esIA ? -0.1 : 0.1, end: 0),
                );
              },
            ),
          ),
          if (_enviando)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: const Text("Todavía está pensando...", 
                style: TextStyle(fontSize: 12, color: Colors.grey, fontStyle: FontStyle.italic)
              ).animate(onPlay: (c) => c.repeat(reverse: true)).fadeIn(duration: 800.ms),
            ),
          _construirInput(colorPrimario),
        ],
      ),
    );
  }

  Widget _construirInput(Color colorPrimario) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, -2))],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(25),
                ),
                child: TextField(
                  controller: _mensajeController,
                  style: GoogleFonts.outfit(),
                  decoration: InputDecoration(
                    hintText: "Escribe un mensaje...",
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 10),
            CircleAvatar(
              backgroundColor: colorPrimario,
              child: IconButton(
                icon: const Icon(Icons.send, color: Colors.white),
                onPressed: _enviarMensaje,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

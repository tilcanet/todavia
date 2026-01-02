import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io'; 
import 'package:device_info_plus/device_info_plus.dart'; 
import 'package:shared_preferences/shared_preferences.dart'; // <--- AGREGADO
import 'package:uuid/uuid.dart'; // <--- AGREGADO
import 'main.dart'; 
import 'chat_screen.dart'; 

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _aliasController = TextEditingController();
  
  String? _usuarioId; // Ahora es dinámico
  final String _baseUrl = "https://todavia.tilcanet.com.ar/api"; 

  bool _cargando = false;
  bool _mostrarInput = false; 

  @override
  void initState() {
    super.initState();
    _cargarUsuario(); // Cargar o generar ID al inicio
    Future.delayed(const Duration(milliseconds: 2500), () {
      if (mounted) {
        setState(() => _mostrarInput = true);
      }
    });
  }

  // Lógica para obtener o crear ID único
  Future<void> _cargarUsuario() async {
    final prefs = await SharedPreferences.getInstance();
    String? idGuardado = prefs.getString('usuario_id');
    String? aliasGuardado = prefs.getString('usuario_alias');

    if (idGuardado == null) {
      // Es la primera vez que entra, generamos un ID único
      idGuardado = const Uuid().v4();
      await prefs.setString('usuario_id', idGuardado);
      debugPrint("Generado NUEVO ID de usuario: $idGuardado");
    } else {
      debugPrint("Recuperado ID de usuario existente: $idGuardado");
    }

    if (aliasGuardado != null) {
      _aliasController.text = aliasGuardado;
    }

    setState(() {
      _usuarioId = idGuardado;
    });
  }

  Future<void> _entrar() async {
    if (_aliasController.text.trim().isEmpty || _usuarioId == null) return;

    setState(() => _cargando = true);

    // Guardar el alias localmente también
    final prefs = await SharedPreferences.getInstance();
    String? aliasGuardado = prefs.getString('usuario_alias');
    String aliasActual = _aliasController.text.trim();

    // SI EL NICK ES DIFERENTE, BORRON Y CUENTA NUEVA
    if (aliasGuardado != null && aliasGuardado != aliasActual) {
      String nuevoId = const Uuid().v4();
      await prefs.setString('usuario_id', nuevoId);
      setState(() {
        _usuarioId = nuevoId;
      });
      debugPrint("Cambio de Nick detectado. Nuevo ID generado: $_usuarioId");
    }

    await prefs.setString('usuario_alias', aliasActual);

    String modelo = "Desconocido";
    String os = Platform.operatingSystem;

    try {
      final deviceInfo = DeviceInfoPlugin();
      if (Platform.isAndroid) {
        final androidInfo = await deviceInfo.androidInfo;
        modelo = "${androidInfo.manufacturer} ${androidInfo.model}";
      } else if (Platform.isIOS) {
        final iosInfo = await deviceInfo.iosInfo;
        modelo = iosInfo.utsname.machine;
      }
    } catch (e) {
      debugPrint("Error obteniendo info dispositivo: $e");
    }

    final url = Uri.parse('$_baseUrl/usuario/$_usuarioId/alias/');
    try {
      final respuesta = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "alias": _aliasController.text,
          "dispositivo_modelo": modelo,
          "dispositivo_os": os,
        }),
      );

      if (respuesta.statusCode == 200 && mounted) {
        Navigator.pushReplacement(
          context,
          PageRouteBuilder(
            pageBuilder: (_, __, ___) => PantallaChat(
              usuarioId: _usuarioId!, 
              baseUrl: _baseUrl,
              aliasUsuario: _aliasController.text
            ),
            transitionsBuilder: (_, animation, __, child) {
              return FadeTransition(opacity: animation, child: child);
            },
            transitionDuration: const Duration(milliseconds: 800),
          ),
        );
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("Error del servidor: ${respuesta.statusCode}"))
          );
        }
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Error de conexión")));
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    debugPrint("[TODAVIA] Dibujando LoginScreen...");
    final colorFondo = const Color(0xFFE0F2F1); 
    final colorPrimario = const Color(0xFF009688);

    return Scaffold(
      backgroundColor: colorFondo,
      body: Stack(
        children: [
          // FONDO DECORATIVO
          Positioned(
            top: -50, right: -50,
            child: CircleAvatar(radius: 100, backgroundColor: Colors.white.withOpacity(0.3)),
          ).animate().scale(duration: 3.seconds, curve: Curves.easeInOut).fadeIn(),
          
          Positioned(
            bottom: -30, left: -30,
            child: CircleAvatar(radius: 80, backgroundColor: Colors.white.withOpacity(0.3)),
          ).animate(delay: 500.ms).scale(duration: 3.seconds, curve: Curves.easeInOut).fadeIn(),

          // CONTENIDO CENTRAL
          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 30),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.spa_rounded, size: 100, color: Color(0xFF009688))
                    .animate(target: _mostrarInput ? 0 : 1)
                    .shimmer(duration: 1500.ms, color: const Color(0xFF80CBC4))
                    .animate(onPlay: (controller) => controller.repeat(reverse: true))
                    .scaleXY(begin: 1.0, end: 1.1, duration: 2000.ms, curve: Curves.easeInOut)
                    .then()
                    .animate(target: _mostrarInput ? 1 : 0)
                    .moveY(end: -30, duration: 800.ms, curve: Curves.easeOutQuart),

                  const SizedBox(height: 20),

                  Text("Todavía", 
                    style: GoogleFonts.outfit(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.black87)
                  ).animate().fadeIn(duration: 1000.ms).slideY(begin: 0.2, end: 0, duration: 800.ms),

                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 600),
                    child: !_mostrarInput
                        ? Text("Respira...", 
                            key: const ValueKey(1),
                            style: GoogleFonts.outfit(fontSize: 18, color: Colors.grey[600]))
                        : Text("¿Cómo quieres llamarte hoy?", 
                            key: const ValueKey(2),
                            style: GoogleFonts.outfit(fontSize: 18, color: colorPrimario, fontWeight: FontWeight.w500)),
                  ),

                  const SizedBox(height: 40),

                  if (_mostrarInput) 
                    Column(
                      children: [
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(20),
                            boxShadow: [BoxShadow(color: colorPrimario.withOpacity(0.1), blurRadius: 20, offset: const Offset(0, 5))],
                          ),
                          child: TextField(
                            controller: _aliasController,
                            textAlign: TextAlign.center,
                            style: GoogleFonts.outfit(fontSize: 18),
                            decoration: InputDecoration(
                              hintText: "Escribe tu alias aquí",
                              hintStyle: TextStyle(color: Colors.grey[300]),
                              border: InputBorder.none,
                              contentPadding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
                            ),
                          ),
                        ).animate().fadeIn(duration: 600.ms).moveY(begin: 20, end: 0),

                        const SizedBox(height: 30),

                        SizedBox(
                          width: double.infinity,
                          height: 55,
                          child: ElevatedButton(
                            onPressed: _cargando ? null : _entrar,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: colorPrimario,
                              foregroundColor: Colors.white,
                              elevation: 0,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                            ),
                            child: _cargando
                              ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                              : const Text("Comenzar", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          ),
                        ).animate().fadeIn(delay: 200.ms).scale(),
                      ],
                    ),
                ],
              ),
            ),
          ),

          // --- AQUÍ ESTÁ TU MARCA "TILCANET" ---
          Positioned(
            bottom: 20,
            left: 0,
            right: 0,
            child: Column(
              children: [
                Text("Hecho en Tilcara", style: GoogleFonts.outfit(fontSize: 12, color: Colors.grey[600], fontWeight: FontWeight.bold)),
                Text("© TILCANET", style: GoogleFonts.outfit(fontSize: 10, color: Colors.grey[400])),
                const SizedBox(height: 5),
                Text("v1.0.3 Debug", style: GoogleFonts.outfit(fontSize: 10, color: Colors.redAccent)),
                IconButton(
                  icon: const Icon(Icons.refresh, size: 15, color: Colors.grey),
                  tooltip: "Reset ID",
                  onPressed: () async {
                    final prefs = await SharedPreferences.getInstance();
                    await prefs.remove('usuario_id');
                    await prefs.remove('usuario_alias');
                   // Recargar app
                   if (context.mounted) {
                     Navigator.of(context).pushAndRemoveUntil(
                       MaterialPageRoute(builder: (c) => const LoginScreen()),
                       (route) => false
                     );
                   }
                  },
                )
              ],
            ).animate().fadeIn(delay: 2000.ms),
          ),
        ],
      ),
    );
  }
}
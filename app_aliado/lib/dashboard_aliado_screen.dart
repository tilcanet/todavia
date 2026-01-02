import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async'; // Para Timer
import 'package:shared_preferences/shared_preferences.dart';
import 'login_aliado_screen.dart';
import 'chat_humano_screen.dart';

const String _baseUrl = 'https://todavia.tilcanet.com.ar/api';

class DashboardAliadoScreen extends StatefulWidget {
  const DashboardAliadoScreen({super.key});

  @override
  State<DashboardAliadoScreen> createState() => _DashboardAliadoScreenState();
}

class _DashboardAliadoScreenState extends State<DashboardAliadoScreen> {
  int? _aliadoId;
  String _nombre = "Aliado";
  bool _estaDisponible = false;
  List<dynamic> _sesiones = [];
  Timer? _pollingTimer;

  @override
  void initState() {
    super.initState();
    _cargarDatos();
    // Polling cada 10s para ver nuevos chats
    _pollingTimer = Timer.periodic(const Duration(seconds: 10), (timer) {
      if (_aliadoId != null) _fetchChats();
    });
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }

  Future<void> _cargarDatos() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _aliadoId = prefs.getInt('aliado_id');
      _nombre = prefs.getString('aliado_nombre') ?? "Aliado";
      // Asumimos que si entra está activo, o podríamos guardar estado local
      // Idealmente, preguntar al backend el estado real, pero por ahora lo forzamos a true al login
      _estaDisponible = true; 
    });
    _fetchChats();
  }

  Future<void> _toggleDisponibilidad(bool valor) async {
    if (_aliadoId == null) return;
    
    // Optimista
    setState(() => _estaDisponible = valor);

    try {
      await http.post(
        Uri.parse('$_baseUrl/aliado/$_aliadoId/estado/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'disponible': valor}),
      );
    } catch (e) {
      // Revertir si falla
      setState(() => _estaDisponible = !valor);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Error de conexión")));
    }
  }

  Future<void> _fetchChats() async {
    if (_aliadoId == null) return;
    try {
      final response = await http.get(Uri.parse('$_baseUrl/aliado/$_aliadoId/chats/'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _sesiones = data['sesiones'];
        });
      }
    } catch (e) {
      print("Error fetching chats: $e");
    }
  }

  void _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    if (mounted) {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginAliadoScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Hola, $_nombre"),
        actions: [
          IconButton(onPressed: _logout, icon: const Icon(Icons.logout))
        ],
      ),
      body: Column(
        children: [
          // ZONA DE ESTADO
          Container(
            padding: const EdgeInsets.all(20),
            color: _estaDisponible ? const Color(0xFFE0F2F1) : const Color(0xFFFFEBEE),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _estaDisponible ? "ESTÁS EN LÍNEA" : "DESCONECTADO",
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: _estaDisponible ? Colors.teal : Colors.red
                      ),
                    ),
                    const Text("Recibirás notificaciones si alguien te necesita.", style: TextStyle(fontSize: 12)),
                  ],
                ),
                Switch(
                  value: _estaDisponible, 
                  activeColor: Colors.teal,
                  onChanged: _toggleDisponibilidad
                )
              ],
            ),
          ),
          
          const Padding(
            padding: EdgeInsets.all(16.0),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text("Chats Activos", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold))
            ),
          ),

          Expanded(
            child: _sesiones.isEmpty 
              ? const Center(child: Text("No hay solicitudes activas por ahora.", style: TextStyle(color: Colors.grey)))
              : RefreshIndicator(
                  onRefresh: _fetchChats,
                  child: ListView.builder(
                    itemCount: _sesiones.length,
                    itemBuilder: (context, index) {
                      final sesion = _sesiones[index];
                      return Card(
                        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        child: ListTile(
                          leading: const CircleAvatar(
                            backgroundColor: Colors.teal, 
                            child: Icon(Icons.person, color: Colors.white)
                          ),
                          title: Text(sesion['usuario_alias'] ?? "Usuario"),
                          subtitle: Text("Zona: ${sesion['usuario_zona']}"),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () {
                             Navigator.push(
                               context, 
                               MaterialPageRoute(builder: (_) => ChatHumanoScreen(
                                 sesionId: sesion['sesion_id'],
                                 aliasUsuario: sesion['usuario_alias'],
                               ))
                             );
                          },
                        ),
                      );
                    },
                  ),
                ),
          ),
        ],
      ),
    );
  }
}

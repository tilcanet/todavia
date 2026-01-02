import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'dashboard_aliado_screen.dart';

const String _baseUrl = 'https://todavia.tilcanet.com.ar/api';

class RegistroAliadoScreen extends StatefulWidget {
  const RegistroAliadoScreen({super.key});

  @override
  State<RegistroAliadoScreen> createState() => _RegistroAliadoScreenState();
}

class _RegistroAliadoScreenState extends State<RegistroAliadoScreen> {
  final _nombreController = TextEditingController();
  final _telefonoController = TextEditingController();
  final _userController = TextEditingController(); // Email/User
  final _passController = TextEditingController();
  
  String _especialidad = 'VECINO';
  final Map<String, String> _especialidades = {
    'TRABAJOR_SOCIAL': 'Trabajador/a Social',
    'PSICOLOGO': 'Psicólogo/a',
    'TERAPEUTA': 'Terapeuta',
    'PSIQUIATRA': 'Psiquiatra',
    'ENFERMERO': 'Enfermero/a',
    'RELIGIOSO': 'Religioso/a',
    'VECINO': 'Vecino/a Voluntario',
    'OTRO': 'Otro',
  };

  bool _isLoading = false;

  Future<void> _registrar() async {
    if (_nombreController.text.isEmpty || _userController.text.isEmpty || _passController.text.isEmpty) {
      _mostrarError("Nombre, Usuario y Contraseña son obligatorios.");
      return;
    }

    setState(() => _isLoading = true);
    
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/aliado/registro/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': _userController.text.trim(),
          'password': _passController.text.trim(),
          'nombre_visible': _nombreController.text.trim(),
          'telefono': _telefonoController.text.trim(),
          'especialidad': _especialidad,
        }),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        
        // Auto-login (guardar sesión)
        final prefs = await SharedPreferences.getInstance();
        await prefs.setInt('aliado_id', data['aliado_id']);
        await prefs.setString('aliado_nombre', data['nombre']);
        await prefs.setString('aliado_especialidad', data['especialidad']);
        
        if (mounted) {
           Navigator.pushAndRemoveUntil(
              context, 
              MaterialPageRoute(builder: (_) => const DashboardAliadoScreen()),
              (r) => false
           );
        }
      } else {
        final err = jsonDecode(response.body)['error'] ?? "Error desconocido";
        _mostrarError("Error al registrar: $err");
      }
    } catch (e) {
      _mostrarError("Error de conexión: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _mostrarError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Registro de Aliado")),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text("Únete a la red de contención.", style: TextStyle(fontSize: 18, color: Colors.grey)),
              const SizedBox(height: 24),

              TextField(
                controller: _nombreController,
                decoration: const InputDecoration(labelText: "Nombre Visible (Ej: Vecino Juan)", border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),
              
              TextField(
                controller: _telefonoController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(labelText: "Teléfono (Privado)", border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),

              DropdownButtonFormField<String>(
                value: _especialidad,
                decoration: const InputDecoration(labelText: "Tu Rol / Especialidad", border: OutlineInputBorder()),
                items: _especialidades.entries.map((e) => DropdownMenuItem(value: e.key, child: Text(e.value))).toList(),
                onChanged: (val) => setState(() => _especialidad = val!),
              ),
              const SizedBox(height: 16),

              const Divider(),
              const SizedBox(height: 16),
              
              TextField(
                controller: _userController,
                decoration: const InputDecoration(labelText: "Usuario / Email", border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),
              
              TextField(
                controller: _passController,
                obscureText: true,
                decoration: const InputDecoration(labelText: "Contraseña", border: OutlineInputBorder()),
              ),
              const SizedBox(height: 32),

              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00BFA5),
                    foregroundColor: Colors.white,
                  ),
                  onPressed: _isLoading ? null : _registrar,
                  child: _isLoading 
                    ? const CircularProgressIndicator(color: Colors.white) 
                    : const Text("CREAR CUENTA"),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

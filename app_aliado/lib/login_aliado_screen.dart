import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'dashboard_aliado_screen.dart';
import 'registro_aliado_screen.dart';

// RECUERDA: Cambiar esto a la IP real si pruebas en dispositivo físico
const String _baseUrl = 'https://todavia.tilcanet.com.ar/api';

class LoginAliadoScreen extends StatefulWidget {
  const LoginAliadoScreen({super.key});

  @override
  State<LoginAliadoScreen> createState() => _LoginAliadoScreenState();
}

class _LoginAliadoScreenState extends State<LoginAliadoScreen> {
  final _userController = TextEditingController();
  final _passController = TextEditingController();
  bool _isLoading = false;

  Future<void> _login() async {
    setState(() => _isLoading = true);
    
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/aliado/login/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': _userController.text.trim(),
          'password': _passController.text.trim(),
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Guardar sesión
        final prefs = await SharedPreferences.getInstance();
        await prefs.setInt('aliado_id', data['aliado_id']);
        await prefs.setString('aliado_nombre', data['nombre']);
        await prefs.setString('aliado_especialidad', data['especialidad']);
        
        if (mounted) {
           Navigator.pushReplacement(
              context, 
              MaterialPageRoute(builder: (_) => const DashboardAliadoScreen())
           );
        }
      } else {
        _mostrarError("Credenciales incorrectas o usuario no registrado como aliado.");
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
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Center(
            child: SingleChildScrollView(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.handshake_rounded, size: 80, color: Color(0xFF00BFA5)),
                  const SizedBox(height: 16),
                  Text("Todavía | Aliados", style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  const Text("Comunidad de Contención", style: TextStyle(color: Colors.grey)),
                  const SizedBox(height: 48),
                  
                  TextField(
                    controller: _userController,
                    decoration: const InputDecoration(labelText: "Usuario / Email", border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _passController,
                    decoration: const InputDecoration(labelText: "Contraseña", border: OutlineInputBorder()),
                    obscureText: true,
                  ),
                  const SizedBox(height: 24),
                  
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00BFA5),
                        foregroundColor: Colors.white,
                      ),
                      onPressed: _isLoading ? null : _login,
                      child: _isLoading 
                        ? const CircularProgressIndicator(color: Colors.white) 
                        : const Text("INGRESAR"),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextButton(
                    onPressed: () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const RegistroAliadoScreen()));
                    }, 
                    child: const Text("¿Eres nuevo? Regístrate aquí")
                  )
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

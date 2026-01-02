import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';

const String _baseUrl = 'https://todavia.tilcanet.com.ar/api';

class ChatHumanoScreen extends StatefulWidget {
  final int sesionId;
  final String aliasUsuario;
  
  const ChatHumanoScreen({super.key, required this.sesionId, required this.aliasUsuario});

  @override
  State<ChatHumanoScreen> createState() => _ChatHumanoScreenState();
}

class _ChatHumanoScreenState extends State<ChatHumanoScreen> {
  final TextEditingController _msgController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  List<dynamic> _mensajes = [];
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _fetchMensajes();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchMensajes());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _fetchMensajes() async {
    try {
      final response = await http.get(Uri.parse('$_baseUrl/aliado/chat/${widget.sesionId}/mensajes/'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final nuevosMensajes = data['mensajes'] as List;
        
        // Solo actualizar si hay cambios
        if (nuevosMensajes.length != _mensajes.length) {
            setState(() {
              _mensajes = nuevosMensajes;
            });
            _scrollToBottom();
        }
      }
    } catch (e) {
      print("Error chat: $e");
    }
  }

  Future<void> _enviar() async {
    final texto = _msgController.text.trim();
    if (texto.isEmpty) return;
    
    _msgController.clear();
    
    // Add optimism
    setState(() {
      _mensajes.add({
        "texto": texto,
        "es_de_la_ia": true, // Es mio
        "fecha": DateTime.now().toIso8601String()
      });
    });
    _scrollToBottom();

    try {
      await http.post(
        Uri.parse('$_baseUrl/aliado/chat/${widget.sesionId}/mensajes/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'texto': texto}),
      );
      _fetchMensajes(); // Sync real
    } catch (e) {
      print("Error sending: $e");
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Chat con ${widget.aliasUsuario}")),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _mensajes.length,
              itemBuilder: (context, index) {
                final msg = _mensajes[index];
                final bool soyYo = msg['es_de_la_ia'] == true;
                
                return Align(
                  alignment: soyYo ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    decoration: BoxDecoration(
                      color: soyYo ? const Color(0xFF00BFA5) : const Color(0xFFEEEEEE),
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(16),
                        topRight: const Radius.circular(16),
                        bottomLeft: soyYo ? const Radius.circular(16) : const Radius.circular(2),
                        bottomRight: soyYo ? const Radius.circular(2) : const Radius.circular(16),
                      ),
                    ),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                    child: Text(
                      msg['texto'],
                      style: TextStyle(color: soyYo ? Colors.white : Colors.black87),
                    ),
                  ),
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(8),
            color: Colors.white,
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _msgController,
                    decoration: const InputDecoration(
                      hintText: "Escribe un mensaje...",
                      border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(30))),
                      contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                CircleAvatar(
                  backgroundColor: const Color(0xFF00BFA5),
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white),
                    onPressed: _enviar,
                  ),
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class CounselorDashboard extends StatefulWidget {
  final String baseUrl;
  const CounselorDashboard({super.key, required this.baseUrl});

  @override
  State<CounselorDashboard> createState() => _CounselorDashboardState();
}

class _CounselorDashboardState extends State<CounselorDashboard> {
  List<dynamic> _activeRequests = [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _fetchRequests();
  }

  Future<void> _fetchRequests() async {
    setState(() => _loading = true);
    // Simulating fetching active sessions from backend
    try {
      // In a real scenario, we'd have a specific endpoint for counselors
      // final response = await http.get(Uri.parse('${widget.baseUrl}/counselor/requests/'));
      await Future.delayed(const Duration(seconds: 1)); // Mock delay
      setState(() {
        _activeRequests = [
          {"id": 1, "user_alias": "Viajero Tilcara", "last_message": "Me siento muy solo...", "time": "Hace 2 min", "risk": "Medio"},
          {"id": 2, "user_alias": "Anónimo Juárez", "last_message": "No sé qué hacer con mi vida", "time": "Hace 5 min", "risk": "ALTO"},
        ];
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Error al cargar pedidos")));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        title: Text("Panel de Escucha", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _fetchRequests),
        ],
      ),
      body: _loading 
        ? const Center(child: CircularProgressIndicator(color: Color(0xFF009688)))
        : Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.all(20),
                child: Text(
                  "Solicitudes Pendientes",
                  style: GoogleFonts.outfit(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.black87),
                ).animate().fadeIn().slideX(),
              ),
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  itemCount: _activeRequests.length,
                  itemBuilder: (context, index) {
                    final req = _activeRequests[index];
                    final bool isHighRisk = req['risk'] == "ALTO";

                    return Container(
                      margin: const EdgeInsets.only(bottom: 16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.05),
                            blurRadius: 10,
                            offset: const Offset(0, 4),
                          )
                        ],
                        border: isHighRisk ? Border.all(color: Colors.redAccent, width: 2) : null,
                      ),
                      child: ListTile(
                        contentPadding: const EdgeInsets.all(16),
                        leading: CircleAvatar(
                          backgroundColor: isHighRisk ? Colors.red[50] : Colors.teal[50],
                          child: Icon(
                            isHighRisk ? Icons.warning_rounded : Icons.person,
                            color: isHighRisk ? Colors.redAccent : Colors.teal,
                          ),
                        ),
                        title: Text(
                          req['user_alias'],
                          style: GoogleFonts.outfit(fontWeight: FontWeight.bold, fontSize: 18),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 4),
                            Text(req['last_message'], maxLines: 1, overflow: TextOverflow.ellipsis),
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Icon(Icons.access_time, size: 14, color: Colors.grey[400]),
                                const SizedBox(width: 4),
                                Text(req['time'], style: TextStyle(fontSize: 12, color: Colors.grey[500])),
                                const Spacer(),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: isHighRisk ? Colors.redAccent : Colors.orangeAccent,
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Text(
                                    "Riesgo ${req['risk']}",
                                    style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                        onTap: () {
                          // TODO: Implement navigation to real-time chat with user
                        },
                      ),
                    ).animate(delay: (index * 100).ms).fadeIn().slideY(begin: 0.2, end: 0);
                  },
                ),
              ),
            ],
          ),
    );
  }
}

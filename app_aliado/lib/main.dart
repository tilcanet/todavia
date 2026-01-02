import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // <--- AGREGADO PARA MODO INMERSIVO
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async'; // <--- IMPORTANTE PARA EL TEMPORIZADOR
import 'dart:math'; // Para elegir frase aleatoria
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter_linkify/flutter_linkify.dart'; // <--- AGREGADO
import 'package:geolocator/geolocator.dart'; // <--- AGREGADO
import 'login_screen.dart';
import 'notifications_service.dart';
import 'splash_screen.dart';

void main() {
  debugPrint("[TODAVIA] 1. main()");
  WidgetsFlutterBinding.ensureInitialized();
  debugPrint("[TODAVIA] 2. Binding Inicializado");
  
  // MODO INMERSIVO (Pantalla Completa)
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
  ));

  runApp(const TodaviaApp());
  debugPrint("[TODAVIA] 3. runApp llamado");
}

class TodaviaApp extends StatelessWidget {
  const TodaviaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Todavía',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF009688),
          brightness: Brightness.light,
          primary: const Color(0xFF009688),
          secondary: const Color(0xFF26A69A),
          surface: const Color(0xFFF5F7FA),
        ),
        scaffoldBackgroundColor: const Color(0xFFF5F7FA),
        // textTheme: GoogleFonts.outfitTextTheme(Theme.of(context).textTheme),
        appBarTheme: AppBarTheme(
          backgroundColor: const Color(0xFFF5F7FA),
          elevation: 0,
          centerTitle: true,
          // titleTextStyle: GoogleFonts.outfit(color: Colors.black87, fontSize: 22, fontWeight: FontWeight.bold),
          iconTheme: const IconThemeData(color: Colors.black87),
        ),
      ),
      home: const SplashScreen(),
    );
  }
}


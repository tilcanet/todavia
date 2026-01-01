import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import 'dart:math';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();

  // --- FRASES ---
  final List<String> _frasesDia = [
    "Quien tiene un porqué para vivir, puede soportar casi cualquier cómo. - Viktor Frankl",
    "Hoy es un buen día para ser amable contigo mismo. - Carl Rogers",
    "Respira el aire de los cerros... hoy es una nueva oportunidad. - Todavía",
    "Tu historia importa. Haz que hoy cuente un poquito.",
    "La perseverancia es caerse 19 veces y levantarse 20.",
  ];

  final List<String> _frasesNoche = [
    "Has sido valiente hoy. Ahora toca descansar. - Brené Brown",
    "Suelta lo que no puedes controlar. Mañana será otro día.",
    "La paz viene de aceptar este momento tal cual es. - Marsha Linehan",
    "Que el silencio de la noche te traiga calma. Descansa.",
    "Lo hiciste bien hoy. Buenas noches.",
  ];

  Future<void> init() async {
    tz.initializeTimeZones();

    // Configuración Android (Icono por defecto)
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const InitializationSettings initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid,
    );

    await flutterLocalNotificationsPlugin.initialize(initializationSettings);
  }

  // Pedir permiso en Android 13+
  Future<void> requestPermissions() async {
    await flutterLocalNotificationsPlugin
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.requestNotificationsPermission();
  }

  // Programar mensaje de la MAÑANA (Ej: 9:00 AM)
  Future<void> scheduleDailyMorning() async {
    await _scheduleDaily(
      id: 1, 
      title: "¡Buen día! ☀️", 
      frases: _frasesDia, 
      hour: 9, 
      minute: 00
    );
  }

  // Programar mensaje de la NOCHE (Ej: 22:00 PM)
  Future<void> scheduleDailyNight() async {
    await _scheduleDaily(
      id: 2, 
      title: "Buenas noches 🌙", 
      frases: _frasesNoche, 
      hour: 22, 
      minute: 00
    );
  }

  Future<void> _scheduleDaily({
    required int id, 
    required String title, 
    required List<String> frases, 
    required int hour, 
    required int minute
  }) async {
    final String fraseAleatoria = frases[Random().nextInt(frases.length)];

    await flutterLocalNotificationsPlugin.zonedSchedule(
      id,
      title,
      fraseAleatoria,
      _nextInstanceOfTime(hour, minute),
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'canal_diario', 
          'Mensajes Diarios',
          channelDescription: 'Frases de aliento diarias',
          importance: Importance.max,
          priority: Priority.high,
        ),
      ),
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      uiLocalNotificationDateInterpretation: UILocalNotificationDateInterpretation.absoluteTime,
      matchDateTimeComponents: DateTimeComponents.time, // Repetir cada día a la misma hora
    );
  }

  tz.TZDateTime _nextInstanceOfTime(int hour, int minute) {
    final tz.TZDateTime now = tz.TZDateTime.now(tz.local);
    tz.TZDateTime scheduledDate = tz.TZDateTime(tz.local, now.year, now.month, now.day, hour, minute);
    if (scheduledDate.isBefore(now)) {
      scheduledDate = scheduledDate.add(const Duration(days: 1));
    }
    return scheduledDate;
  }
}
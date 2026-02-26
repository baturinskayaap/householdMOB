import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/login_screen.dart';
import 'screens/main_menu_screen.dart'; // новый импорт

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final hasChatId = prefs.containsKey('chat_id');
  runApp(MyApp(initialRoute: hasChatId ? '/home' : '/'));
}

class MyApp extends StatelessWidget {
  final String initialRoute;
  const MyApp({super.key, required this.initialRoute});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Домашние дела',
      initialRoute: initialRoute,
      routes: {
        '/': (context) => LoginScreen(),
        '/home': (context) => MainMenuScreen(), // заменён HomeScreen
      },
    );
  }
}
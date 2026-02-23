import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _controller = TextEditingController();

  Future<void> _saveChatId() async {
    final chatId = int.tryParse(_controller.text);
    if (chatId != null) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt('chat_id', chatId);
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Введите корректный Chat ID')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Вход')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _controller,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'Ваш Chat ID',
                hintText: 'Введите цифровой ID',
              ),
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _saveChatId,
              child: Text('Войти'),
            ),
          ],
        ),
      ),
    );
  }
}
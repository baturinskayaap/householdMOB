import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:dio/dio.dart';
import '../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _controller = TextEditingController();
  bool _isLoading = false;

  Future<void> _login() async {
    final name = _controller.text.trim();
    if (name.isEmpty) return;
    setState(() => _isLoading = true);
    try {
      final response = await Dio().post(
        '${ApiService.baseUrl}/login',
        data: {'name': name},
      );
      if (response.statusCode == 200) {
        final chatId = response.data['chat_id'] as int;
        final prefs = await SharedPreferences.getInstance();
        await prefs.setInt('chat_id', chatId);
        if (!mounted) return;
        Navigator.pushReplacementNamed(context, '/home');
      }
    } on DioException catch (e) {
      String errorMsg = 'Ошибка входа';
      if (e.response?.statusCode == 404) {
        errorMsg = 'Пользователь не найден';
      } else if (e.response?.data != null) {
        errorMsg = e.response?.data['message'] ?? errorMsg;
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(errorMsg)),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Вход')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _controller,
              decoration: const InputDecoration(
                labelText: 'Ваше имя',
                hintText: 'Введите имя пользователя',
              ),
              autofocus: true,
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _isLoading ? null : _login,
              child: _isLoading
                  ? const CircularProgressIndicator()
                  : const Text('Войти'),
            ),
          ],
        ),
      ),
    );
  }
}
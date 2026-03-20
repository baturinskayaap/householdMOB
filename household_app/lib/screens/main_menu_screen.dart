import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/services.dart'; // для SystemNavigator
import '../services/api_service.dart';
import '../app_config.dart'; // импортируем конфиг
import 'tasks_screen.dart';
import 'shopping_screen.dart';

class MainMenuScreen extends StatefulWidget {
  const MainMenuScreen({super.key});

  @override
  State<MainMenuScreen> createState() => _MainMenuScreenState();
}

class _MainMenuScreenState extends State<MainMenuScreen> {
  int _tasksCount = 0;
  int _shoppingCount = 0;
  bool _isLoading = true;
  String _userName = '';

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final prefs = await SharedPreferences.getInstance();
    final chatId = prefs.getInt('chat_id');
    final userName = prefs.getString('username');
    setState(() {
      _userName = userName?.toString() ?? 'пользователь';
    });

    try {
      final apiService = ApiService();
      final tasks = await apiService.getTasks(chatId: chatId?.toString() ?? '');
      final shopping = await apiService.getShoppingItems(chatId: chatId?.toString() ?? '');
      setState(() {
        _tasksCount = tasks.length;
        _shoppingCount = shopping.length;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка загрузки: $e')),
      );
    }
  }

  // Функция показа диалога смены IP
  Future<void> _showChangeIpDialog() async {
    final prefs = await SharedPreferences.getInstance();
    final currentIp = prefs.getString('server_ip') ?? AppConfig.baseUrl;
    final controller = TextEditingController(text: currentIp);

    return showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Изменить IP сервера'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'IP адрес (с портом)',
            hintText: 'http://192.168.1.100:8000',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Отмена'),
          ),
          ElevatedButton(
            onPressed: () async {
              final newIp = controller.text.trim();
              if (newIp.isNotEmpty) {
                await AppConfig.save(newIp);
                if (!mounted) return;
                // Показываем сообщение и закрываем приложение
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('IP изменён. Приложение будет перезапущено.')),
                );
                // Небольшая задержка, чтобы пользователь увидел сообщение
                await Future.delayed(const Duration(seconds: 2));
                // Закрываем приложение (только для Android)
                SystemNavigator.pop();
              }
            },
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Главное меню'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: _showChangeIpDialog,
            tooltip: 'Настройки сервера',
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Привет, $_userName',
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 20),
                  // Плитка статистики
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.blue[100],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      'Всего задач: $_tasksCount, Покупок: $_shoppingCount',
                      style: const TextStyle(fontSize: 18),
                    ),
                  ),
                  const SizedBox(height: 20),
                  // Две плитки меню
                  Row(
                    children: [
                      Expanded(child: _buildMenuCard(
                        title: 'Задачи',
                        icon: Icons.task,
                        onTap: () async {
                          await Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => TasksScreen()),
                          );
                          if (mounted) _loadData();
                        },
                      )),
                      const SizedBox(width: 16),
                      Expanded(child: _buildMenuCard(
                        title: 'Список покупок',
                        icon: Icons.shopping_cart,
                        onTap: () async {
                          await Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => ShoppingScreen()),
                          );
                          if (mounted) _loadData();
                        },
                      )),
                    ],
                  ),
                ],
              ),
      ),
    );
  }

  Widget _buildMenuCard({required String title, required IconData icon, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 120,
        decoration: BoxDecoration(
          color: Colors.grey[200],
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 40),
            const SizedBox(height: 8),
            Text(title, style: const TextStyle(fontSize: 18)),
          ],
        ),
      ),
    );
  }
}
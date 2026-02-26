import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import 'tasks_screen.dart';
import 'shopping_screen.dart';

class MainMenuScreen extends StatefulWidget {
  const MainMenuScreen({super.key}); // добавили ключ

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
    final chatId = prefs.getInt('chat_id'); // читаем как int
    setState(() {
      _userName = chatId?.toString() ?? 'пользователь';
    });

    try {
      // Параллельная загрузка задач и покупок
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Главное меню')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: _isLoading
            ? Center(child: CircularProgressIndicator())
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Привет, $_userName',
                    style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 20),
                  // Плитка статистики
                  Container(
                    width: double.infinity,
                    padding: EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.blue[100],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      'Всего задач: $_tasksCount, Покупок: $_shoppingCount',
                      style: TextStyle(fontSize: 18),
                    ),
                  ),
                  SizedBox(height: 20),
                  // Две плитки меню
                  Row(
                    children: [
                      Expanded(child: _buildMenuCard(
                        title: 'Задачи',
                        icon: Icons.task,
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => TasksScreen()),
                        ),
                      )),
                      SizedBox(width: 16),
                      Expanded(child: _buildMenuCard(
                        title: 'Список покупок',
                        icon: Icons.shopping_cart,
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => ShoppingScreen()),
                        ),
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
            SizedBox(height: 8),
            Text(title, style: TextStyle(fontSize: 18)),
          ],
        ),
      ),
    );
  }
}
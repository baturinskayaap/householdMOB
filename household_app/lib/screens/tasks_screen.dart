import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/task.dart';
import '../services/api_service.dart';
import 'task_settings_screen.dart';

class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  final _apiService = ApiService();
  List<Task> _tasks = [];
  bool _isLoading = true;
  String? _error;
  String _chatId = '';

  @override
  void initState() {
    super.initState();
    _loadChatIdAndTasks();
  }

  Future<void> _loadChatIdAndTasks() async {
    final prefs = await SharedPreferences.getInstance();
    final chatId = prefs.getInt('chat_id'); // читаем как int
    if (!mounted) return;
    setState(() {
      _chatId = chatId?.toString() ?? ''; // преобразуем в строку для API
    });
    await _fetchTasks();
  }

  Future<void> _fetchTasks() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final tasks = await _apiService.getTasks(chatId: _chatId);
      if (!mounted) return;
      setState(() {
        _tasks = tasks;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  // Группировка задач по дате следующего выполнения
  Map<String, List<Task>> _groupTasksByDate() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final tomorrow = today.add(Duration(days: 1));

    final grouped = <String, List<Task>>{};

    for (var task in _tasks) {
      final nextDue = task.nextDueDate();
      if (nextDue == null) {
        // никогда не выполнялась — считаем просроченной?
        grouped.putIfAbsent('Просрочено', () => []).add(task);
        continue;
      }
      final dueDate = DateTime(nextDue.year, nextDue.month, nextDue.day);

      if (dueDate.isBefore(today)) {
        grouped.putIfAbsent('Просрочено', () => []).add(task);
      } else if (dueDate.isAtSameMomentAs(today)) {
        grouped.putIfAbsent('Сегодня', () => []).add(task);
      } else if (dueDate.isAtSameMomentAs(tomorrow)) {
        grouped.putIfAbsent('Завтра', () => []).add(task);
      } else {
        final key = '${dueDate.day.toString().padLeft(2, '0')}.${dueDate.month.toString().padLeft(2, '0')}.${dueDate.year}';
        grouped.putIfAbsent(key, () => []).add(task);
      }
    }

    // Сортировка секций: сначала просрочено, потом сегодня, потом завтра, потом остальные по дате.
    // Для этого нужно упорядочить ключи.
    // Создадим список всех ключей в правильном порядке.
    final order = <String>[];
    if (grouped.containsKey('Просрочено')) order.add('Просрочено');
    if (grouped.containsKey('Сегодня')) order.add('Сегодня');
    if (grouped.containsKey('Завтра')) order.add('Завтра');

    // Остальные ключи (даты) отсортируем по возрастанию даты.
    final dateKeys = grouped.keys.where((key) => !['Просрочено', 'Сегодня', 'Завтра'].contains(key)).toList();
    dateKeys.sort((a, b) {
      // парсим дату из строки d.m.y
      List<int> parseDate(String s) {
        var parts = s.split('.');
        return [int.parse(parts[2]), int.parse(parts[1]), int.parse(parts[0])]; // year, month, day
      }
      final dateA = parseDate(a);
      final dateB = parseDate(b);
      // сравниваем год, месяц, день
      if (dateA[0] != dateB[0]) return dateA[0].compareTo(dateB[0]);
      if (dateA[1] != dateB[1]) return dateA[1].compareTo(dateB[1]);
      return dateA[2].compareTo(dateB[2]);
    });
    order.addAll(dateKeys);

    // Возвращаем упорядоченную мапу
    return Map.fromEntries(order.map((key) => MapEntry(key, grouped[key]!)));
  }

  Future<void> _markTaskDone(Task task) async {
    try {
      await _apiService.markTaskDone(task.id);
      await _fetchTasks(); // перезагружаем список после отметки
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Задачи'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const TaskSettingsScreen()),
              );
            },
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Ошибка: $_error'),
            ElevatedButton(
              onPressed: _fetchTasks,
              child: const Text('Повторить'),
            ),
          ],
        ),
      );
    }

    final grouped = _groupTasksByDate();
    final sections = grouped.entries.where((e) => e.value.isNotEmpty).toList();

    if (sections.isEmpty) {
      return const Center(child: Text('Нет задач'));
    }

    return ListView.builder(
      itemCount: sections.length,
      itemBuilder: (ctx, index) {
        final section = sections[index];
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Text(
                section.key,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
            ...section.value.map((task) => _buildTaskTile(task)),
          ],
        );
      },
    );
  }

  Widget _buildTaskTile(Task task) {
    final subtitle = StringBuffer();
    if (task.lastDone != null) {
      subtitle.write('Последний раз: ${_formatDate(task.lastDone!)}');
    }
    subtitle.write('  Интервал: ${task.intervalDays} дн.');
    
    return CheckboxListTile(
      title: Text(task.name),
      subtitle: Text(subtitle.toString()),
      value: false,
      onChanged: (_) => _markTaskDone(task),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}.${date.month}.${date.year}';
  }
}
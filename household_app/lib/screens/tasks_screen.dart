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
    final overdue = <Task>[];
    final todayTasks = <Task>[];
    final upcoming = <Task>[];

    for (var task in _tasks) {
      final nextDue = task.nextDueDate();
      if (nextDue == null) {
        overdue.add(task); // никогда не выполнялась
        continue;
      }
      final dueDate = DateTime(nextDue.year, nextDue.month, nextDue.day);
      if (dueDate.isBefore(today)) {
        overdue.add(task);
      } else if (dueDate.isAtSameMomentAs(today)) {
        todayTasks.add(task);
      } else {
        upcoming.add(task);
      }
    }
    return {'Просрочено': overdue, 'Сегодня': todayTasks, 'Предстоящие': upcoming};
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
    final nextDue = task.nextDueDate();
    final subtitle = StringBuffer();
    if (task.lastDone != null) {
      subtitle.write('Последний раз: ${_formatDate(task.lastDone!)}');
    }
    subtitle.write('  Интервал: ${task.intervalDays} дн.');
    
    return CheckboxListTile(
      title: Text(task.name),
      subtitle: Text(subtitle.toString()),
      value: false, // чекбокс всегда неотмечен – нажатие выполняет задачу
      onChanged: (_) => _markTaskDone(task),
      secondary: nextDue != null
          ? Text(
              '${nextDue.day}.${nextDue.month}',
              style: const TextStyle(fontSize: 12),
            )
          : null,
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}.${date.month}.${date.year}';
  }
}
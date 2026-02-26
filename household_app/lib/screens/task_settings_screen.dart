import 'package:flutter/material.dart';
import '../models/task.dart';
import '../services/api_service.dart';

class TaskSettingsScreen extends StatefulWidget {
  const TaskSettingsScreen({super.key});

  @override
  State<TaskSettingsScreen> createState() => _TaskSettingsScreenState();
}

class _TaskSettingsScreenState extends State<TaskSettingsScreen> {
  final _apiService = ApiService();
  List<Task> _tasks = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadTasks();
  }

  Future<void> _loadTasks() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      // Для загрузки задач нужен chatId, но getTasks в ApiService уже использует _setChatIdHeader,
      // который берёт chatId из SharedPreferences. Поэтому можно вызвать без параметров,
      // если метод getTasks объявлен как Future<List<Task>> getTasks().
      // В текущей реализации getTasks требует параметр chatId, но он не используется,
      // потому что заголовок устанавливается через _setChatIdHeader.
      // Чтобы не ломать существующий код, передаём пустую строку или любой chatId.
      final tasks = await _apiService.getTasks(chatId: '123456789'); 
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

  Future<void> _createTask(String name, int intervalDays) async {
    try {
      await _apiService.createTask(name, intervalDays);
      await _loadTasks(); // перезагружаем список
    } catch (e) {
      if (!mounted) return;
      _showErrorSnackBar('Ошибка создания: $e');
    }
  }

  Future<void> _updateTask(Task task, String newName, int newInterval) async {
    try {
      final updatedTask = task.copyWith(
        name: newName,
        intervalDays: newInterval,
      );
      await _apiService.updateTask(task: updatedTask);
      await _loadTasks();
    } catch (e) {
      if (!mounted) return;
      _showErrorSnackBar('Ошибка обновления: $e');
    }
  }

  Future<void> _deleteTask(int taskId) async {
    try {
      await _apiService.deleteTask(taskId);
      await _loadTasks();
    } catch (e) {
      if (!mounted) return;
      _showErrorSnackBar('Ошибка удаления: $e');
    }
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  void _showTaskDialog({Task? task}) {
    final isEditing = task != null;
    final nameController = TextEditingController(text: task?.name ?? '');
    final intervalController = TextEditingController(
      text: task?.intervalDays.toString() ?? '',
    );

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(isEditing ? 'Редактировать задачу' : 'Новая задача'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: const InputDecoration(labelText: 'Название'),
              autofocus: true,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: intervalController,
              decoration: const InputDecoration(labelText: 'Интервал (дней)'),
              keyboardType: TextInputType.number,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Отмена'),
          ),
          ElevatedButton(
            onPressed: () async {
              final name = nameController.text.trim();
              final interval = int.tryParse(intervalController.text.trim());
              if (name.isEmpty || interval == null || interval <= 0) {
                ScaffoldMessenger.of(ctx).showSnackBar(
                  const SnackBar(content: Text('Заполните корректно поля')),
                );
                return;
              }
              Navigator.pop(ctx); // закрываем диалог
              if (isEditing) {
                await _updateTask(task, name, interval);
              } else {
                await _createTask(name, interval);
              }
            },
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  void _confirmDelete(int taskId) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Удалить задачу?'),
        content: const Text('Вы уверены?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Отмена'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _deleteTask(taskId);
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Удалить'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Настройки задач'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('Ошибка: $_error'),
                      ElevatedButton(
                        onPressed: _loadTasks,
                        child: const Text('Повторить'),
                      ),
                    ],
                  ),
                )
              : _tasks.isEmpty
                  ? const Center(child: Text('Нет задач'))
                  : ListView.builder(
                      itemCount: _tasks.length + 1, // +1 для плитки создания
                      itemBuilder: (ctx, index) {
                        if (index == _tasks.length) {
                          // Плитка создания новой задачи
                          return _buildAddTile();
                        }
                        final task = _tasks[index];
                        return _buildTaskTile(task);
                      },
                    ),
    );
  }

  Widget _buildTaskTile(Task task) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        title: Text(task.name),
        subtitle: Text('Каждые ${task.intervalDays} дн.'),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: const Icon(Icons.edit),
              onPressed: () => _showTaskDialog(task: task),
            ),
            IconButton(
              icon: const Icon(Icons.delete),
              onPressed: () => _confirmDelete(task.id),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAddTile() {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      color: Colors.grey[200],
      child: ListTile(
        leading: const Icon(Icons.add),
        title: const Text('Создать новую задачу'),
        onTap: () => _showTaskDialog(),
      ),
    );
  }
}
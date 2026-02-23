import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/task.dart';

class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  _TasksScreenState createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  final ApiService _api = ApiService();
  late Future<List<Task>> _tasksFuture;

  @override
  void initState() {
    super.initState();
    _refreshTasks();
  }

  void _refreshTasks() {
    setState(() {
      _tasksFuture = _api.getTasks();
    });
  }

  Future<void> _markDone(Task task) async {
    await _api.markTaskDone(task.id);
    _refreshTasks();
  }

  Future<void> _deleteTask(Task task) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Удалить задачу?'),
        content: Text('Вы уверены, что хотите удалить "${task.name}"?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text('Нет')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: Text('Да')),
        ],
      ),
    );
    if (confirm == true) {
      await _api.deleteTask(task.id);
      _refreshTasks();
    }
  }

  Future<void> _editTask(Task task) async {
    final nameController = TextEditingController(text: task.name);
    final intervalController = TextEditingController(text: task.intervalDays.toString());
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Редактировать задачу'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: InputDecoration(labelText: 'Название'),
            ),
            TextField(
              controller: intervalController,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(labelText: 'Интервал (дни)'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text('Отмена')),
          ElevatedButton(
            onPressed: () async {
              final newName = nameController.text.trim();
              final newInterval = int.tryParse(intervalController.text);
              if (newName.isNotEmpty && newInterval != null) {
                await _api.updateTask(task.id, name: newName, intervalDays: newInterval);
                _refreshTasks();
                Navigator.pop(context);
              }
            },
            child: Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: FutureBuilder<List<Task>>(
        future: _tasksFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Ошибка: ${snapshot.error}'));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return Center(child: Text('Нет задач'));
          } else {
            final tasks = snapshot.data!;
            return ListView.builder(
              itemCount: tasks.length,
              itemBuilder: (context, index) {
                final task = tasks[index];
                return Dismissible(
                  key: Key(task.id.toString()),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    color: Colors.red,
                    alignment: Alignment.centerRight,
                    padding: EdgeInsets.only(right: 20),
                    child: Icon(Icons.delete, color: Colors.white),
                  ),
                  onDismissed: (_) => _deleteTask(task),
                  child: ListTile(
                    leading: Text(task.statusEmoji, style: TextStyle(fontSize: 24)),
                    title: Text(task.name),
                    subtitle: Text(
                      task.lastDone == null
                          ? 'Никогда не выполнялась'
                          : 'Последний раз: ${task.lastDone!.day}.${task.lastDone!.month}.${task.lastDone!.year}',
                    ),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (task.isOverdue)
                          Icon(Icons.warning, color: Colors.red)
                        else
                          Text('${task.daysUntilDue} дн.'),
                        Checkbox(
                          value: task.lastDone != null && !task.isOverdue,
                          onChanged: (_) => _markDone(task),
                        ),
                      ],
                    ),
                    onTap: () => _editTask(task),
                  ),
                );
              },
            );
          }
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddTaskDialog,
        child: Icon(Icons.add),
      ),
    );
  }

  void _showAddTaskDialog() {
    final nameController = TextEditingController();
    final intervalController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Новая задача'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: InputDecoration(labelText: 'Название'),
            ),
            TextField(
              controller: intervalController,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(labelText: 'Интервал (дни)'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text('Отмена')),
          ElevatedButton(
            onPressed: () async {
              final name = nameController.text.trim();
              final interval = int.tryParse(intervalController.text);
              if (name.isNotEmpty && interval != null) {
                await _api.createTask(name, interval);
                _refreshTasks();
                Navigator.pop(context);
              }
            },
            child: Text('Добавить'),
          ),
        ],
      ),
    );
  }
}
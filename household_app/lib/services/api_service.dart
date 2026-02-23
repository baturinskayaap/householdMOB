import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/task.dart';
import '../models/shopping_item.dart';

class ApiService {
  static const String baseUrl = 'http://100.109.226.246:8000'; // ваш IP
  final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    headers: {'Content-Type': 'application/json'},
  ));

  // Метод для установки chat_id в заголовки
  Future<void> _setChatIdHeader() async {
    final prefs = await SharedPreferences.getInstance();
    final chatId = prefs.getInt('chat_id');
    if (chatId != null) {
      _dio.options.headers['X-Chat-ID'] = chatId;
    } else {
      throw Exception('Chat ID not set');
    }
  }

  // Задачи
  Future<List<Task>> getTasks() async {
    await _setChatIdHeader();
    final response = await _dio.get('/tasks');
    if (response.statusCode == 200) {
      return (response.data as List).map((e) => Task.fromJson(e)).toList();
    } else {
      throw Exception('Failed to load tasks');
    }
  }

  Future<Task> createTask(String name, int intervalDays) async {
    await _setChatIdHeader();
    final response = await _dio.post('/tasks', data: {
      'name': name,
      'interval_days': intervalDays,
    });
    if (response.statusCode == 201) {
      return Task.fromJson(response.data);
    } else {
      throw Exception('Failed to create task');
    }
  }

  Future<Task> updateTask(int taskId, {String? name, int? intervalDays}) async {
    await _setChatIdHeader();
    final Map<String, dynamic> data = {};
    if (name != null) data['name'] = name;
    if (intervalDays != null) data['interval_days'] = intervalDays;
    final response = await _dio.patch('/tasks/$taskId', data: data);
    if (response.statusCode == 200) {
      return Task.fromJson(response.data);
    } else {
      throw Exception('Failed to update task');
    }
  }

  Future<void> deleteTask(int taskId) async {
    await _setChatIdHeader();
    final response = await _dio.delete('/tasks/$taskId');
    if (response.statusCode != 204) {
      throw Exception('Failed to delete task');
    }
  }

  Future<Task> markTaskDone(int taskId) async {
    await _setChatIdHeader();
    final response = await _dio.post('/tasks/$taskId/done');
    if (response.statusCode == 200) {
      return Task.fromJson(response.data);
    } else {
      throw Exception('Failed to mark task done');
    }
  }

  // Покупки
  Future<List<ShoppingItem>> getShoppingItems({bool showChecked = true}) async {
    await _setChatIdHeader();
    final response = await _dio.get('/shopping', queryParameters: {'show_checked': showChecked});
    if (response.statusCode == 200) {
      return (response.data as List).map((e) => ShoppingItem.fromJson(e)).toList();
    } else {
      throw Exception('Failed to load shopping items');
    }
  }

  Future<ShoppingItem> createShoppingItem(String itemText) async {
    await _setChatIdHeader();
    final response = await _dio.post('/shopping', data: {'item_text': itemText});
    if (response.statusCode == 201) {
      return ShoppingItem.fromJson(response.data);
    } else {
      throw Exception('Failed to create shopping item');
    }
  }

  Future<ShoppingItem> toggleShoppingItem(int itemId) async {
    await _setChatIdHeader();
    final response = await _dio.patch('/shopping/$itemId/toggle');
    if (response.statusCode == 200) {
      return ShoppingItem.fromJson(response.data);
    } else {
      throw Exception('Failed to toggle shopping item');
    }
  }

  Future<int> deleteCheckedItems() async {
    await _setChatIdHeader();
    final response = await _dio.delete('/shopping/checked');
    if (response.statusCode == 200) {
      return response.data['deleted'];
    } else {
      throw Exception('Failed to delete checked items');
    }
  }

  Future<int> deleteAllItems() async {
    await _setChatIdHeader();
    final response = await _dio.delete('/shopping/all');
    if (response.statusCode == 200) {
      return response.data['deleted'];
    } else {
      throw Exception('Failed to delete all items');
    }
  }

  Future<Map<String, int>> getShoppingStats() async {
    await _setChatIdHeader();
    final response = await _dio.get('/shopping/stats');
    if (response.statusCode == 200) {
      return Map<String, int>.from(response.data);
    } else {
      throw Exception('Failed to get shopping stats');
    }
  }
}
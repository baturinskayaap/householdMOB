import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/shopping_item.dart';

class ShoppingScreen extends StatefulWidget {
  const ShoppingScreen({super.key});

  @override
  _ShoppingScreenState createState() => _ShoppingScreenState();
}

class _ShoppingScreenState extends State<ShoppingScreen> {
  final ApiService _api = ApiService();
  late Future<List<ShoppingItem>> _itemsFuture;
  bool _showChecked = true; // текущий режим отображения

  @override
  void initState() {
    super.initState();
    _refreshItems();
  }

  void _refreshItems() {
    setState(() {
      _itemsFuture = _api.getShoppingItems(showChecked: _showChecked);
    });
  }

  // Переключение режима отображения
  void _toggleViewMode() {
    setState(() {
      _showChecked = !_showChecked;
      _itemsFuture = _api.getShoppingItems(showChecked: _showChecked);
    });
  }

  // Добавление нового пункта
  Future<void> _addItem() async {
    final controller = TextEditingController();
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Новый пункт'),
        content: TextField(
          controller: controller,
          decoration: InputDecoration(labelText: 'Название'),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Отмена'),
          ),
          ElevatedButton(
            onPressed: () {
              if (controller.text.trim().isNotEmpty) {
                Navigator.pop(context, true);
              }
            },
            child: Text('Добавить'),
          ),
        ],
      ),
    );

    if (result == true) {
      final name = controller.text.trim();
      await _api.createShoppingItem(name);
      _refreshItems();
    }
  }

  // Переключение отметки пункта
  Future<void> _toggleItem(int itemId) async {
    await _api.toggleShoppingItem(itemId);
    _refreshItems();
  }

  // Удаление отмеченных пунктов
  Future<void> _deleteChecked() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Удалить отмеченные?'),
        content: Text('Вы уверены? Отмеченные пункты будут удалены.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text('Нет')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: Text('Да')),
        ],
      ),
    );

    if (confirm == true) {
      await _api.deleteCheckedItems();
      _refreshItems();
    }
  }

  // Удаление всех пунктов
  Future<void> _deleteAll() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Очистить весь список?'),
        content: Text('Все пункты будут удалены безвозвратно.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text('Нет')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: Text('Да')),
        ],
      ),
    );

    if (confirm == true) {
      await _api.deleteAllItems();
      _refreshItems();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Список покупок'),
        actions: [
          // Кнопка переключения режима отображения
          IconButton(
            icon: Icon(_showChecked ? Icons.visibility : Icons.visibility_off),
            tooltip: _showChecked ? 'Скрыть отмеченные' : 'Показать все',
            onPressed: _toggleViewMode,
          ),
          // Кнопка удалить отмеченные
          IconButton(
            icon: Icon(Icons.clean_hands),
            tooltip: 'Удалить отмеченные',
            onPressed: _deleteChecked,
          ),
          // Кнопка удалить все
          IconButton(
            icon: Icon(Icons.delete_sweep),
            tooltip: 'Удалить все',
            onPressed: _deleteAll,
          ),
        ],
      ),
      body: FutureBuilder<List<ShoppingItem>>(
        future: _itemsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Ошибка: ${snapshot.error}'));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.shopping_cart_outlined, size: 80, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('Список покупок пуст'),
                ],
              ),
            );
          } else {
            final items = snapshot.data!;
            return ListView.builder(
              itemCount: items.length,
              itemBuilder: (context, index) {
                final item = items[index];
                return ListTile(
                  leading: Checkbox(
                    value: item.isChecked,
                    onChanged: (_) => _toggleItem(item.id),
                  ),
                  title: Text(
                    item.itemText,
                    style: item.isChecked
                        ? TextStyle(decoration: TextDecoration.lineThrough, color: Colors.grey)
                        : null,
                  ),
                  trailing: IconButton(
                    icon: Icon(Icons.delete_outline),
                    onPressed: () async {
                      // Для простоты – сразу переключаем в отмеченные и потом удалим через _deleteChecked,
                      // но можно реализовать отдельное удаление элемента.
                      // Пока оставим так: отметим и предложим удалить через общую кнопку.
                      // Альтернативно: можно добавить Dismissible для удаления свайпом.
                      await _toggleItem(item.id);
                    },
                  ),
                );
              },
            );
          }
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addItem,
        child: Icon(Icons.add),
      ),
    );
  }
}
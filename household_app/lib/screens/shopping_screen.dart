import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/shopping_item.dart';
import '../services/api_service.dart';
import 'add_items_screen.dart';

class ShoppingScreen extends StatefulWidget {
  const ShoppingScreen({super.key});

  @override
  State<ShoppingScreen> createState() => _ShoppingScreenState();
}

class _ShoppingScreenState extends State<ShoppingScreen> {
  final _apiService = ApiService();
  List<ShoppingItem> _items = [];
  bool _isLoading = true;
  String? _error;
  String _chatId = '';
  String _selectedFilter = 'all'; // 'all', 'supermarket', 'household'

  @override
  void initState() {
    super.initState();
    _loadChatIdAndItems();
  }

  Future<void> _loadChatIdAndItems() async {
    final prefs = await SharedPreferences.getInstance();
    final chatId = prefs.getInt('chat_id');
    if (!mounted) return;
    setState(() {
      _chatId = chatId?.toString() ?? '';
    });
    await _fetchItems();
  }

  Future<void> _fetchItems() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      // Параметр showChecked=true – показываем все, но разделим на две секции сами
      final items = await _apiService.getShoppingItems(
        showChecked: true,
        category: _selectedFilter == 'all' ? null : _selectedFilter,
        chatId: _chatId,
      );
      if (!mounted) return;
      setState(() {
        _items = items;
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

  Future<void> _toggleItem(ShoppingItem item) async {
    try {
      await _apiService.toggleShoppingItem(item.id);
      // Обновляем локально, чтобы избежать перезагрузки всего списка
      setState(() {
        final index = _items.indexWhere((i) => i.id == item.id);
        if (index != -1) {
          _items[index] = item.copyWith(isChecked: !item.isChecked);
        }
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e')),
      );
    }
  }

  Future<void> _deleteChecked() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Удалить отмеченные?'),
        content: const Text('Все отмеченные пункты будут удалены.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Отмена'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Удалить'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      await _apiService.deleteCheckedItems();
      await _fetchItems(); // перезагружаем список
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e')),
      );
    }
  }

  Future<void> _deleteAll() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Удалить всё?'),
        content: const Text('Все пункты списка покупок будут удалены.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Отмена'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Удалить всё'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      await _apiService.deleteAllItems();
      await _fetchItems();
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
        title: const Text('Список покупок'),
        actions: [
          IconButton(
            icon: const Icon(Icons.cleaning_services),
            onPressed: _deleteChecked,
            tooltip: 'Очистить отмеченные',
          ),
          IconButton(
            icon: const Icon(Icons.delete_sweep),
            onPressed: _deleteAll,
            tooltip: 'Удалить все',
          ),
        ],
      ),
      body: Column(
        children: [
          // Фильтры по категориям
          Container(
            padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                FilterChip(
                  label: const Text('Все'),
                  selected: _selectedFilter == 'all',
                  onSelected: (sel) {
                    setState(() => _selectedFilter = 'all');
                    _fetchItems();
                  },
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: const Text('Супермаркет'),
                  selected: _selectedFilter == 'supermarket',
                  onSelected: (sel) {
                    setState(() => _selectedFilter = 'supermarket');
                    _fetchItems();
                  },
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: const Text('Бытовой'),
                  selected: _selectedFilter == 'household',
                  onSelected: (sel) {
                    setState(() => _selectedFilter = 'household');
                    _fetchItems();
                  },
                ),
              ],
            ),
          ),
          // Основной список
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text('Ошибка: $_error'),
                            ElevatedButton(
                              onPressed: _fetchItems,
                              child: const Text('Повторить'),
                            ),
                          ],
                        ),
                      )
                    : _buildList(),
          ),
        ],
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      floatingActionButton: SizedBox(
        width: double.infinity,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: ElevatedButton(
            onPressed: () async {
              final result = await Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const AddItemsScreen()),
              );
              // Если добавлен новый элемент – обновить список
              if (result == true) {
                _fetchItems();
              }
            },
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
            child: const Text('+ Добавить пункты'),
          ),
        ),
      ),
    );
  }

  Widget _buildList() {
    final unchecked = _items.where((i) => !i.isChecked).toList();
    final checked = _items.where((i) => i.isChecked).toList();

    return ListView(
      children: [
        if (unchecked.isNotEmpty) ...[
          const Padding(
            padding: EdgeInsets.all(16.0),
            child: Text(
              'Невыполненные',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ),
          ...unchecked.map((item) => _buildItemTile(item)),
        ],
        if (checked.isNotEmpty) ...[
          const Padding(
            padding: EdgeInsets.all(16.0),
            child: Text(
              'Выполненные',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ),
          ...checked.map((item) => _buildItemTile(item, isChecked: true)),
        ],
        if (_items.isEmpty)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(32.0),
              child: Text('Список покупок пуст'),
            ),
          ),
      ],
    );
  }

  Widget _buildItemTile(ShoppingItem item, {bool isChecked = false}) {
    return CheckboxListTile(
      title: Text(
        item.itemText,
        style: isChecked
            ? const TextStyle(decoration: TextDecoration.lineThrough)
            : null,
      ),
      subtitle: Text(_categoryName(item.category)),
      value: item.isChecked,
      onChanged: (_) => _toggleItem(item),
    );
  }

  String _categoryName(String cat) {
    switch (cat) {
      case 'supermarket':
        return 'Супермаркет';
      case 'household':
        return 'Бытовой';
      default:
        return cat;
    }
  }
}
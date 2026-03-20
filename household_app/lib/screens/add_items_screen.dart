import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  ChatMessage({required this.text, required this.isUser, DateTime? timestamp})
      : timestamp = timestamp ?? DateTime.now();
}

class AddItemsScreen extends StatefulWidget {
  const AddItemsScreen({super.key});

  @override
  State<AddItemsScreen> createState() => _AddItemsScreenState();
}

class _AddItemsScreenState extends State<AddItemsScreen> {
  final _controller = TextEditingController();
  final List<ChatMessage> _messages = [];
  String _selectedCategory = '';
  late ApiService _apiService;
  bool _itemsAdded = false;
  List<String> _categories = [];

  @override
  void initState() {
    super.initState();
    _apiService = ApiService();
    _loadCategories();
    _messages.add(ChatMessage(
      text: 'Введите пункты списка покупок. Выберите категорию.',
      isUser: false,
    ));
  }

  Future<void> _loadCategories() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final chatId = prefs.getInt('chat_id')?.toString() ?? '';
      final cats = await _apiService.getCategories(chatId: chatId);
      if (!mounted) return;
      setState(() {
        _categories = cats;
        if (_categories.isNotEmpty) _selectedCategory = _categories.first;
      });
    } catch (e) {
      if (!mounted) return;
      // В случае ошибки (например, нет эндпоинта) используем категории по умолчанию
      setState(() {
        _categories = ['supermarket', 'household'];
        _selectedCategory = 'supermarket';
      });
    }
  }

  Future<void> _createNewCategory() async {
    final TextEditingController dialogController = TextEditingController();
    final newCat = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Новая категория'),
        content: TextField(
          controller: dialogController,
          autofocus: true,
          decoration: const InputDecoration(
            hintText: 'Введите название категории',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Отмена'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, dialogController.text.trim()),
            child: const Text('Добавить'),
          ),
        ],
      ),
    );
    if (newCat != null && newCat.isNotEmpty && !_categories.contains(newCat)) {
      setState(() {
        _categories.add(newCat);
        _selectedCategory = newCat;
      });
    }
  }

  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _selectedCategory.isEmpty) return;

    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true));
      _controller.clear();
    });

    try {
      await _apiService.createShoppingItem(text, _selectedCategory);
      if (!mounted) return;
      setState(() {
        _messages.add(ChatMessage(
          text: '✅ Добавлено в категорию "$_selectedCategory"',
          isUser: false,
        ));
        _itemsAdded = true;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _messages.add(ChatMessage(
          text: '❌ Ошибка: $e',
          isUser: false,
        ));
      });
    }
  }

  // Метод для отображения категории (можно доработать под свои нужды)
  String _displayCategory(String cat) {
    // Здесь можно добавить маппинг английских названий на русские, если нужно
    // Например: if (cat == 'supermarket') return 'Супермаркет';
    return cat; // пока возвращаем как есть
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async {
        Navigator.pop(context, _itemsAdded);
        return false;
      },
      child: Scaffold(
        appBar: AppBar(
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => Navigator.pop(context, _itemsAdded),
          ),
          title: const Text('Добавить пункты'),
        ),
        body: Column(
          children: [
            // Панель выбора категории
            Container(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
              color: Colors.grey[200],
              child: Row(
                children: [
                  const Text('Категория: '),
                  Expanded(
                    child: DropdownButton<String>(
                      value: _selectedCategory.isNotEmpty ? _selectedCategory : null,
                      isExpanded: true,
                      hint: const Text('Выберите категорию'),
                      items: _categories.map((cat) {
                        return DropdownMenuItem(
                          value: cat,
                          child: Text(_displayCategory(cat)),
                        );
                      }).toList(),
                      onChanged: (value) {
                        setState(() => _selectedCategory = value!);
                      },
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.add),
                    onPressed: _createNewCategory,
                    tooltip: 'Создать категорию',
                  ),
                ],
              ),
            ),
            // Список сообщений
            Expanded(
              child: ListView.builder(
                reverse: true,
                itemCount: _messages.length,
                itemBuilder: (ctx, index) {
                  final msg = _messages[_messages.length - 1 - index];
                  return _buildMessageBubble(msg);
                },
              ),
            ),
            // Нижняя панель ввода
            Container(
              padding: const EdgeInsets.all(8.0),
              color: Colors.grey[100],
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: const InputDecoration(
                        hintText: 'Введите пункт...',
                        border: OutlineInputBorder(),
                      ),
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.send),
                    onPressed: _sendMessage,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage msg) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
        decoration: BoxDecoration(
          color: msg.isUser ? Colors.blue[100] : Colors.grey[300],
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(msg.text),
      ),
    );
  }
}
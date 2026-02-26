import 'package:flutter/material.dart';
import '../services/api_service.dart';

// Простая модель сообщения для чата
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
  String _selectedCategory = 'supermarket'; // 'supermarket' или 'household'
  late ApiService _apiService;

  @override
  void initState() {
    super.initState();
    _apiService = ApiService();
    // Можно добавить приветственное сообщение
    _messages.add(ChatMessage(
      text: 'Введите пункты списка покупок. Они будут добавлены в категорию.',
      isUser: false,
    ));
  }

  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true));
      _controller.clear();
    });

    try {
      await _apiService.createShoppingItem(text, _selectedCategory);
      setState(() {
        _messages.add(ChatMessage(
          text: '✅ Добавлено в категорию "${_categoryName(_selectedCategory)}"',
          isUser: false,
        ));
      });
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(
          text: '❌ Ошибка: $e',
          isUser: false,
        ));
      });
    }
  }

  String _categoryName(String cat) {
    return cat == 'supermarket' ? 'Супермаркет' : 'Бытовой';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
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
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('Категория: '),
                ChoiceChip(
                  label: const Text('Супермаркет'),
                  selected: _selectedCategory == 'supermarket',
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedCategory = 'supermarket');
                  },
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Бытовой'),
                  selected: _selectedCategory == 'household',
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedCategory = 'household');
                  },
                ),
              ],
            ),
          ),
          // Список сообщений
          Expanded(
            child: ListView.builder(
              reverse: true, // чтобы новые сообщения были снизу
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
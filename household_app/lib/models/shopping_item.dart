class ShoppingItem {
  final int id;
  final String itemText;
  final bool isChecked;
  final String category;          // если ещё не добавили
  final DateTime createdAt;

  ShoppingItem({
    required this.id,
    required this.itemText,
    required this.isChecked,
    required this.category,
    required this.createdAt,
  });

  factory ShoppingItem.fromJson(Map<String, dynamic> json) {
    return ShoppingItem(
      id: json['id'],
      itemText: json['item_text'],
      isChecked: json['is_checked'] == 1,
      category: json['category'] ?? 'supermarket', // значение по умолчанию
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'item_text': itemText,
    'is_checked': isChecked,
    'category': category,
    'created_at': createdAt.toIso8601String(),
  };

  // ✅ Добавляем метод copyWith
  ShoppingItem copyWith({
    int? id,
    String? itemText,
    bool? isChecked,
    String? category,
    DateTime? createdAt,
  }) {
    return ShoppingItem(
      id: id ?? this.id,
      itemText: itemText ?? this.itemText,
      isChecked: isChecked ?? this.isChecked,
      category: category ?? this.category,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
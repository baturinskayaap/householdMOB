class ShoppingItem {
  final int id;
  final String itemText;
  final bool isChecked;
  final DateTime createdAt;

  ShoppingItem({
    required this.id,
    required this.itemText,
    required this.isChecked,
    required this.createdAt,
  });

  factory ShoppingItem.fromJson(Map<String, dynamic> json) {
    return ShoppingItem(
      id: json['id'],
      itemText: json['item_text'],
      isChecked: json['is_checked'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'item_text': itemText,
    'is_checked': isChecked,
    'created_at': createdAt.toIso8601String(),
  };

  String get displayText => isChecked ? '<s>$itemText</s>' : itemText;
}
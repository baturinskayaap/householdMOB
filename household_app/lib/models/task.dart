class Task {
  final int id;
  final String name;
  final int intervalDays;
  final DateTime? lastDone;
  final int? lastDoneBy;
  // final DateTime? createdAt;

  Task({
    required this.id,
    required this.name,
    required this.intervalDays,
    this.lastDone,
    this.lastDoneBy,
    // this.createdAt,
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: json['id'] as int,
      name: json['name'] as String,
      intervalDays: json['interval_days'] as int,
      lastDone: json['last_done'] != null ? DateTime.parse(json['last_done']) : null,
      lastDoneBy: json['last_done_by'] as int?,
      // createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
    );
  }
// 'created_at': createdAt?.toIso8601String(),
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'interval_days': intervalDays,
      'last_done': lastDone?.toIso8601String(),
      'last_done_by': lastDoneBy
    };      
  }

  // Вычисляемое свойство: просрочена ли задача
  bool isOverdue() {
    if (lastDone == null) return true;
    final nextDue = lastDone!.add(Duration(days: intervalDays));
    return DateTime.now().isAfter(nextDue);
  }

  // Сколько дней осталось до следующего выполнения (0, если просрочено)
  int daysUntilDue() {
    if (lastDone == null) return 0;
    final nextDue = lastDone!.add(Duration(days: intervalDays));
    final diff = nextDue.difference(DateTime.now()).inDays;
    return diff < 0 ? 0 : diff;
  }

  // Дата следующего выполнения
  DateTime? nextDueDate() {
    if (lastDone == null) return null;
    return lastDone!.add(Duration(days: intervalDays));
  }

  // Статус в виде эмодзи (как в бэкенде)
  String getStatusEmoji() {
    if (lastDone == null) return "🔔";
    if (isOverdue()) return "🔔";
    return "⏳";
  }

  Task copyWith({
    int? id,
    String? name,
    int? intervalDays,
    DateTime? lastDone,
    int? lastDoneBy,
    DateTime? createdAt,
  }) {
    return Task(
      id: id ?? this.id,
      name: name ?? this.name,
      intervalDays: intervalDays ?? this.intervalDays,
      lastDone: lastDone ?? this.lastDone,
      lastDoneBy: lastDoneBy ?? this.lastDoneBy,
      // createdAt: createdAt ?? this.createdAt,
    );
  }
}
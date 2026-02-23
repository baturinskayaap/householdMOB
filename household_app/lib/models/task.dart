class Task {
  final int id;
  final String name;
  final int intervalDays;
  final DateTime? lastDone;
  final int? lastDoneBy;
  final DateTime? createdAt;

  Task({
    required this.id,
    required this.name,
    required this.intervalDays,
    this.lastDone,
    this.lastDoneBy,
    this.createdAt,
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: json['id'],
      name: json['name'],
      intervalDays: json['interval_days'],
      lastDone: json['last_done'] != null ? DateTime.parse(json['last_done']) : null,
      lastDoneBy: json['last_done_by'],
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'interval_days': intervalDays,
    'last_done': lastDone?.toIso8601String(),
    'last_done_by': lastDoneBy,
    'created_at': createdAt?.toIso8601String(),
  };

  // Логика статусов (как в models.py)
  int? get daysSinceDone {
    if (lastDone == null) return null;
    return DateTime.now().difference(lastDone!).inDays;
  }

  bool get isOverdue {
    if (lastDone == null) return true;
    return (daysSinceDone ?? 0) >= intervalDays;
  }

  int get daysUntilDue {
    if (lastDone == null) return intervalDays;
    return (intervalDays - (daysSinceDone ?? 0)).clamp(0, intervalDays);
  }

  String get statusEmoji {
    if (lastDone == null) return '🔔';
    if (isOverdue) return '🔔';
    return '⏳';
  }
}
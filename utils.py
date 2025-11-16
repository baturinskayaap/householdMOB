# utils.py
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from models import Task

logger = logging.getLogger(__name__)

def format_reminder_message(overdue_tasks: List[Task], due_soon_tasks: List[Task]) -> str:
    """Форматирование сообщения для напоминаний"""
    message_lines = ["🔔 Ежедневное напоминание о задачах:\n"]
    
    if overdue_tasks:
        message_lines.append("📛 ПРОСРОЧЕННЫЕ ЗАДАЧИ:")
        for task in overdue_tasks:
            overdue_days = (task.days_since_done() or 0) - task.interval_days
            message_lines.append(f"🔴 {task.name} - просрочено на {overdue_days} дней")
        message_lines.append("")
    
    if due_soon_tasks:
        message_lines.append("⏰ СКОРО НУЖНО ВЫПОЛНИТЬ:")
        for task in due_soon_tasks:
            days_left = task.days_until_due()
            message_lines.append(f"🟡 {task.name} - осталось {days_left} дней")
        message_lines.append("")
    
    message_lines.append("Используйте /done [задача] чтобы отметить выполнение")
    
    return "\n".join(message_lines)

def validate_time_string(time_str: str) -> bool:
    """Проверка корректности строки времени"""
    try:
        hours, minutes = map(int, time_str.split(':'))
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    except (ValueError, AttributeError):
        return False

def get_weekday_name(weekday_num: int) -> str:
    """Получить название дня недели"""
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    return days[weekday_num] if 0 <= weekday_num < 7 else "Неизвестно"

def safe_datetime_parse(date_string: Optional[str]) -> Optional[datetime]:
    """Безопасное преобразование строки в datetime"""
    if not date_string:
        return None
    try:
        return datetime.fromisoformat(date_string)
    except (ValueError, TypeError):
        return None

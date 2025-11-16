import sys
import os
import asyncio
import logging

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reminder_system import ReminderSystem
from database import Database

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/botuser/household-bot/cron.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def send_daily_reminders():
    """Отправка ежедневных напоминаний"""
    try:
        db = Database()
        reminder_system = ReminderSystem(db)
        await reminder_system.send_daily_reminders()
        logger.info("✅ Ежедневные напоминания отправлены")
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке ежедневных напоминаний: {e}")

async def send_weekly_summary():
    """Отправка недельной статистики"""
    try:
        db = Database()
        reminder_system = ReminderSystem(db)
        await reminder_system.send_weekly_summary()
        logger.info("✅ Недельная статистика отправлена")
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке недельной статистики: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python cron_reminder.py [daily|weekly]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "daily":
            asyncio.run(send_daily_reminders())
        elif command == "weekly":
            asyncio.run(send_weekly_summary())
        else:
            print("Неизвестная команда. Используйте: daily или weekly")
            sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)

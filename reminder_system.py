import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
from database import Database
from utils import format_reminder_message, get_weekday_name
import config

logger = logging.getLogger(__name__)

class ReminderSystem:
    def __init__(self, database: Database):
        self.db = database
        self.bot = None
    
    async def initialize_bot(self):
        """Асинхронная инициализация бота"""
        if self.bot is None:
            self.bot = Bot(config.BOT_TOKEN)
    
    async def send_daily_reminders(self):
        """Отправка ежедневных напоминаний"""
        try:
            await self.initialize_bot()
            logger.info("🕒 Starting daily reminders check...")
            
            overdue_tasks = self.db.get_overdue_tasks()
            due_soon_tasks = self.db.get_tasks_due_soon(days_threshold=1)
            
            if not overdue_tasks and not due_soon_tasks:
                logger.info("✅ No reminders to send today - all tasks are up to date!")
                return
            
            message = format_reminder_message(overdue_tasks, due_soon_tasks)
            
            logger.info(f"📤 Sending reminders: {len(overdue_tasks)} overdue, {len(due_soon_tasks)} due soon")
            
            success_count = 0
            for chat_id in config.ADMIN_IDS:
                try:
                    await self.bot.send_message(chat_id=chat_id, text=message)
                    success_count += 1
                    logger.info(f"✅ Reminder sent to chat {chat_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to send reminder to {chat_id}: {e}")
            
            logger.info(f"📊 Reminders delivered: {success_count}/{len(config.ADMIN_IDS)}")
        
        except Exception as e:
            logger.error(f"💥 Critical error in daily reminders: {e}")
    
    async def send_weekly_summary(self):
        """Отправка еженедельной статистики"""
        try:
            await self.initialize_bot()
            logger.info("📈 Starting weekly summary...")
            
            stats = self.db.get_user_statistics(days=7)
            
            message_lines = ["📊 Недельная статистика:\n"]
            
            if stats['user_stats']:
                message_lines.append("👥 Выполнено задач за неделю:")
                for user_name, user_data in stats['user_stats'].items():
                    percentage = (user_data['task_count'] / stats['total_tasks'] * 100) if stats['total_tasks'] > 0 else 0
                    message_lines.append(f"   {user_name}: {user_data['task_count']} задач ({percentage:.1f}%)")
                message_lines.append("")
            else:
                message_lines.append("😴 На этой неделе задачи не выполнялись")
                message_lines.append("")
            
            if stats['popular_tasks']:
                message_lines.append("🏆 Самые частые задачи:")
                for task_name, count in stats['popular_tasks']:
                    message_lines.append(f"   {task_name}: {count} раз")
                message_lines.append("")
            
            message = "\n".join(message_lines)
            
            success_count = 0
            for chat_id in config.ADMIN_IDS:
                try:
                    await self.bot.send_message(chat_id=chat_id, text=message)
                    success_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to send weekly summary to {chat_id}: {e}")
            
            logger.info(f"📊 Weekly summaries delivered: {success_count}/{len(config.ADMIN_IDS)}")
        
        except Exception as e:
            logger.error(f"💥 Error in weekly summary: {e}")
    
    async def send_achievement_message(self, chat_id: int, achievement: str):
        """Отправка сообщения о достижении"""
        try:
            await self.initialize_bot()
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"🎉 Достижение: {achievement}"
            )
        except Exception as e:
            logger.error(f"Error sending achievement: {e}")

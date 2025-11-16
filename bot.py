import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext, CallbackQueryHandler, MessageHandler, filters
from datetime import time
import config
from database import Database
from reminder_system import ReminderSystem
from utils import format_reminder_message
from keyboards import \
    get_main_keyboard, \
    get_tasks_keyboard, get_management_keyboard, \
    get_reminders_keyboard, get_task_selection_keyboard, \
    get_confirmation_keyboard, get_cancel_keyboard, get_back_keyboard \

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class HouseholdBot:
    def __init__(self):
        self.db = Database()
        self.reminder_system = ReminderSystem(self.db)
        self.application = None
        self.user_states = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start с основной клавиатурой"""
        try:
            welcome_text = """
👋 Привет! Я бот для управления домашними делами для пары.

📱 Используйте кнопки ниже для быстрого доступа к функциям:

📋 Список задач - все задачи со статусами
⏰ Ближайшие - срочные задачи
📊 Статистика - ваша активность
✅ Выполнить - быстрая отметка выполнения
🛠️ Управление - добавление и редактирование задач
🔔 Напоминания - управление уведомлениями

Или используйте команды:
/tasks - список задач
/stats - статистика
/manage - управление задачами
            """
            keyboard = get_main_keyboard()
            await update.message.reply_text(welcome_text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error in /start: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений от кнопок"""
        try:
            text = update.message.text
            user_id = update.effective_user.id
            
            if text == "📋 Список задач":
                await self.tasks_with_keyboard(update, context)
            elif text == "⏰ Ближайшие":
                await self.show_next_tasks(update, context)
            elif text == "📊 Статистика":
                await self.show_stats(update, context)
            elif text == "✅ Выполнить":
                await self.quick_done(update, context)
            elif text == "🛠️ Управление":
                await self.manage_tasks(update, context)
            elif text == "🔔 Напоминания":
                await self.reminder_settings(update, context)
            else:
                # Обработка состояний пользователя
                await self.handle_user_state(update, context)
                
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            await update.message.reply_text("❌ Ошибка при обработке сообщения")
    
    async def quick_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрая отметка выполнения через кнопки"""
        try:
            tasks = self.db.get_all_tasks()
            urgent_tasks = [t for t in tasks if t.is_overdue() or t.days_until_due() <= 2]
            
            if not urgent_tasks:
                await update.message.reply_text("🎉 Нет срочных задач для выполнения!")
                return
            
            keyboard = get_tasks_keyboard(show_all=False)
            await update.message.reply_text(
                "✅ Выберите задачу для отметки выполнения:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in quick_done: {e}")
            await update.message.reply_text("❌ Ошибка при получении списка задач")
    async def show_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обработчик команды /tasks (старая версия без кнопок)"""
            try:
                tasks = self.db.get_all_tasks()
                
                if not tasks:
                    await update.message.reply_text("📝 Задачи еще не настроены.")
                    return
                
                # Формируем красивый список задач
                message_lines = ["📋 Список домашних задач:\n"]
                
                for task in tasks:
                    status_line = task.format_status(self.db.get_user_name)
                    message_lines.append(status_line)
                
                # Добавляем информацию о просроченных задачах
                overdue_count = sum(1 for task in tasks if task.is_overdue())
                if overdue_count > 0:
                    message_lines.append(f"\n⚠️  Всего просрочено задач: {overdue_count}")
                
                message_lines.append("\n🔔 - просрочено, ⏳ - ожидает")
                
                await update.message.reply_text("\n".join(message_lines))
            
            except Exception as e:
                logger.error(f"Error in /tasks: {e}")
                await update.message.reply_text("❌ Ошибка при получении списка задач.")    

    async def reminder_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Настройки напоминаний"""
        try:
            keyboard = get_reminders_keyboard()
            message = """
🔔 Управление напоминаниями:

• Ежедневные напоминания приходят в 17:00
• Недельная статистика - по воскресеньям в 18:00

Для настройки времени измените config.py
            """
            await update.message.reply_text(message, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in reminder_settings: {e}")
            await update.message.reply_text("❌ Ошибка при открытии настроек напоминаний")
    
    async def rename_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Переименование задачи"""
        try:
            if not context.args or len(context.args) < 2:
                await update.message.reply_text(
                    "✏️ Переименование задачи:\n\n"
                    "Формат: /rename_task ID_задачи Новое_название\n"
                    "Пример: /rename_task 1 Мыть полы\n\n"
                    "ID задачи можно посмотреть в /tasks"
                )
                return
            
            task_id_str, new_name = context.args[0], " ".join(context.args[1:])
            
            if not task_id_str.isdigit():
                await update.message.reply_text("❌ ID задачи должен быть числом")
                return
            
            task_id = int(task_id_str)
            task = self.db.get_task_by_id(task_id)
            
            if not task:
                await update.message.reply_text("❌ Задача с таким ID не найдена")
                return
            
            # Здесь нужно добавить метод rename_task в Database
            # Показываем сообщение, что функция в разработке
            await update.message.reply_text(
                "🔄 Функция переименования в разработке\n"
                f"Вы хотите переименовать: {task.name} → {new_name}"
            )
            
        except Exception as e:
            logger.error(f"Error in /rename_task: {e}")
            await update.message.reply_text("❌ Ошибка при переименовании задачи")
    
    async def backup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создание бэкапа базы данных"""
        try:
            import shutil
            import os
            from datetime import datetime
            
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"household_backup_{timestamp}.db")
            
            shutil.copy2("household.db", backup_file)
            
            await update.message.reply_text(
                f"✅ Бэкап создан: {backup_file}\n"
                f"📁 Папка: {backup_dir}"
            )
            
        except Exception as e:
            logger.error(f"Error in /backup: {e}")
            await update.message.reply_text("❌ Ошибка при создании бэкапа")
    
    async def achievements_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать достижения"""
        try:
            stats = self.db.get_user_statistics(days=30)
            total_tasks = stats['total_tasks']
            
            achievements = []
            
            if total_tasks >= 50:
                achievements.append("🏆 Трудолюбивая пчела (50+ задач за месяц)")
            elif total_tasks >= 25:
                achievements.append("⭐ Активный помощник (25+ задач за месяц)")
            elif total_tasks >= 10:
                achievements.append("👍 Начинающий (10+ задач за месяц)")
            
            if stats['user_stats']:
                for user_name, user_data in stats['user_stats'].items():
                    if user_data['task_count'] >= 30:
                        achievements.append(f"👑 {user_name} - Супермен (30+ задач)")
                    elif user_data['task_count'] >= 15:
                        achievements.append(f"💪 {user_name} - Старатель (15+ задач)")
            
            if not achievements:
                achievements.append("🎯 Выполняйте задачи, чтобы получать достижения!")
            
            message = "🏅 Ваши достижения:\n\n" + "\n".join(f"• {ach}" for ach in achievements)
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error in /achievements: {e}")
            await update.message.reply_text("❌ Ошибка при получении достижений")
    
    # ОБНОВЛЯЕМ СУЩЕСТВУЮЩИЕ МЕТОДЫ ДЛЯ РАБОТЫ С НОВЫМИ КЛАВИАТУРАМИ
    
    async def tasks_with_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE, show_all=True):
        """Команда /tasks с инлайн-кнопками"""
        try:
            tasks = self.db.get_all_tasks()
            
            if not tasks:
                await update.message.reply_text("📝 Задачи еще не настроены.")
                return
            
            message_lines = ["📋 Список домашних задач:\n"]
            
            for task in tasks:
                status_line = task.format_status(self.db.get_user_name)
                message_lines.append(status_line)
            
            overdue_count = sum(1 for task in tasks if task.is_overdue())
            if overdue_count > 0:
                message_lines.append(f"\n⚠️  Всего просрочено задач: {overdue_count}")
            
            message_lines.append("\n💡 Нажмите на кнопку с задачей, чтобы отметить её выполненной")
            
            keyboard = get_tasks_keyboard(show_all=show_all)
            
            if isinstance(update, Update):
                await update.message.reply_text("\n".join(message_lines), reply_markup=keyboard)
            else:
                # Если это callback query
                await update.edit_message_text("\n".join(message_lines), reply_markup=keyboard)
        
        except Exception as e:
            logger.error(f"Error in tasks_with_keyboard: {e}")
            if isinstance(update, Update):
                await update.message.reply_text("❌ Ошибка при получении списка задач")
            else:
                await update.edit_message_text("❌ Ошибка при получении списка задач")
    
    async def manage_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для управления задачами"""
        try:
            keyboard = get_management_keyboard()
            message = """
🛠️ Управление задачами:

• Добавить новую задачу
• Изменить интервал выполнения
• Переименовать задачу
• Удалить задачу
            """
            if isinstance(update, Update):
                await update.message.reply_text(message, reply_markup=keyboard)
            else:
                await update.edit_message_text(message, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error in manage_tasks: {e}")
            if isinstance(update, Update):
                await update.message.reply_text("❌ Ошибка при открытии управления задачами")
            else:
                await update.edit_message_text("❌ Ошибка при открытии управления задачами")
    
    # ОБНОВЛЯЕМ ОБРАБОТЧИК КНОПОК ДЛЯ НОВЫХ ФУНКЦИЙ
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на инлайн-кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if user_id not in config.ADMIN_IDS:
            await query.edit_message_text("❌ У вас нет прав для выполнения этого действия")
            return
        
        data = query.data
        
        try:
            if data.startswith("done_"):
                # Отметка задачи выполненной через кнопку
                task_id = int(data.split("_")[1])
                await self.mark_task_done_from_button(query, task_id)
            
            elif data == "refresh_tasks":
                await self.tasks_with_keyboard(query, context, show_all=True)
            
            elif data == "show_all_tasks":
                await self.tasks_with_keyboard(query, context, show_all=True)
            
            elif data == "show_urgent_tasks":
                await self.tasks_with_keyboard(query, context, show_all=False)
            
            elif data == "add_task":
                await self.handle_add_task(query)
            
            elif data == "edit_interval":
                keyboard = get_task_selection_keyboard("edit_interval")
                await query.edit_message_text("📅 Выберите задачу для изменения интервала:", reply_markup=keyboard)
            
            elif data == "rename_task":
                keyboard = get_task_selection_keyboard("rename")
                await query.edit_message_text("✏️ Выберите задачу для переименования:", reply_markup=keyboard)
            
            elif data == "delete_task":
                keyboard = get_task_selection_keyboard("delete")
                await query.edit_message_text("🗑️ Выберите задачу для удаления:", reply_markup=keyboard)
            
            elif data == "show_tasks":
                await self.tasks_with_keyboard(query, context, show_all=True)
            
            elif data == "back_to_main":
                await self.show_main_menu(query)
            
            elif data == "back_to_manage":
                await self.manage_tasks(query, context)
            
            elif data == "test_reminders":
                await self.test_reminders_from_button(query)
            
            elif data == "test_weekly":
                await self.test_weekly_from_button(query)
            
            elif data == "reminder_settings":
                await self.reminder_settings_from_button(query)
            
            elif data == "show_stats":
                await self.show_stats_from_button(query)
            
            elif data == "cancel_action":
                await self.show_main_menu(query)
            
            elif data.startswith("edit_interval_"):
                task_id = int(data.split("_")[2])
                self.user_states[user_id] = f"waiting_interval_{task_id}"
                await query.edit_message_text(
                    f"📅 Введите новый интервал в днях для этой задачи:",
                    reply_markup=get_cancel_keyboard()
                )
            
            elif data.startswith("confirm_delete_"):
                task_id = int(data.split("_")[2])
                await self.confirm_delete_task(query, task_id)
            
            else:
                await query.edit_message_text("❌ Неизвестное действие")
                
        except Exception as e:
            logger.error(f"Error in button handler: {e}")
            await query.edit_message_text("❌ Произошла ошибка при обработке действия")
    
    async def mark_task_done_from_button(self, query, task_id):
        """Отметка задачи выполненной из кнопки"""
        task = self.db.get_task_by_id(task_id)
        
        if task:
            self.db.mark_task_done(
                task_id=task.id,
                user_chat_id=query.from_user.id,
                username=query.from_user.username or "нет",
                first_name=query.from_user.first_name or "Аноним"
            )
            
            tasks = self.db.get_all_tasks()
            message_lines = ["📋 Список домашних задач:\n"]
            
            for t in tasks:
                status_line = t.format_status(self.db.get_user_name)
                message_lines.append(status_line)
            
            overdue_count = sum(1 for t in tasks if t.is_overdue())
            if overdue_count > 0:
                message_lines.append(f"\n⚠️  Всего просрочено задач: {overdue_count}")
            
            message_lines.append(f"\n✅ {query.from_user.first_name} выполнил(а): {task.name}")
            
            keyboard = get_tasks_keyboard(show_all=True)
            await query.edit_message_text("\n".join(message_lines), reply_markup=keyboard)
        else:
            await query.edit_message_text("❌ Задача не найдена")
    
    async def handle_add_task(self, query):
        """Обработка добавления задачи"""
        self.user_states[query.from_user.id] = "waiting_for_new_task"
        await query.edit_message_text(
            "📝 Добавление новой задачи:\n\n"
            "Отправьте сообщение в формате:\n"
            "Название задачи | интервал_в_днях\n\n"
            "Пример: Полить цветы | 3",
            reply_markup=get_cancel_keyboard()
        )
    
    async def test_reminders_from_button(self, query):
        """Тест напоминаний из кнопки"""
        await query.edit_message_text("🔄 Тестирование напоминаний...")
        overdue_tasks = self.db.get_overdue_tasks()
        due_soon_tasks = self.db.get_tasks_due_soon(days_threshold=2)
        
        test_message = format_reminder_message(overdue_tasks, due_soon_tasks)
        await query.edit_message_text(test_message, reply_markup=get_back_keyboard())
    
    async def test_weekly_from_button(self, query):
        """Тест недельной статистики из кнопки"""
        await query.edit_message_text("📊 Тестирование недельной статистики...")
        stats = self.db.get_user_statistics(days=7)
        
        message_lines = ["📊 Недельная статистика (тест):\n"]
        message_lines.append(f"Всего выполнено задач: {stats['total_tasks']}")
        
        if stats['user_stats']:
            message_lines.append("\n👥 По пользователям:")
            for user_name, user_data in stats['user_stats'].items():
                message_lines.append(f"   {user_name}: {user_data['task_count']} задач")
        
        await query.edit_message_text("\n".join(message_lines), reply_markup=get_back_keyboard())
    
    async def reminder_settings_from_button(self, query):
        """Настройки напоминаний из кнопки"""
        message = """
⚙️ Настройки напоминаний:

Текущее время напоминаний:
• Ежедневные: 17:00
• Недельные: воскресенье 18:00

Для изменения отредактируйте config.py
        """
        await query.edit_message_text(message, reply_markup=get_back_keyboard())
    
    async def show_stats_from_button(self, query):
        """Статистика из кнопки"""
        stats = self.db.get_user_statistics(days=30)
        
        message_lines = [f"📊 Статистика за 30 дней:\n"]
        message_lines.append(f"📈 Всего выполнено задач: {stats['total_tasks']}")
        
        if stats['user_stats']:
            message_lines.append("\n👥 Распределение:")
            for user_name, user_data in stats['user_stats'].items():
                percentage = (user_data['task_count'] / stats['total_tasks'] * 100) if stats['total_tasks'] > 0 else 0
                message_lines.append(f"   {user_name}: {user_data['task_count']} ({percentage:.1f}%)")
        
        await query.edit_message_text("\n".join(message_lines), reply_markup=get_back_keyboard())
    
    async def confirm_delete_task(self, query, task_id):
        """Подтверждение удаления задачи"""
        task = self.db.get_task_by_id(task_id)
        
        if task:
            success = self.db.delete_task(task_id)
            if success:
                await query.edit_message_text(f"✅ Задача '{task.name}' удалена", reply_markup=get_back_keyboard())
            else:
                await query.edit_message_text("❌ Ошибка при удалении задачи", reply_markup=get_back_keyboard())
        else:
            await query.edit_message_text("❌ Задача не найдена", reply_markup=get_back_keyboard())
    
    async def show_main_menu(self, query):
        """Показать главное меню"""
        welcome_text = """
👋 Главное меню

📱 Используйте кнопки ниже для быстрого доступа:
        """
        keyboard = get_main_keyboard()
        await query.edit_message_text(welcome_text, reply_markup=keyboard)
    
    async def handle_user_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка состояний пользователя"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        user_message = update.message.text
        
        try:
            if state == "waiting_for_new_task":
                if "|" not in user_message:
                    await update.message.reply_text(
                        "❌ Неверный формат. Используйте: Название | интервал_в_днях\n"
                        "Пример: Полить цветы | 3",
                        reply_markup=get_cancel_keyboard()
                    )
                    return
                
                task_name, interval_str = user_message.split("|", 1)
                task_name = task_name.strip()
                interval_str = interval_str.strip()
                
                if not task_name or not interval_str.isdigit():
                    await update.message.reply_text(
                        "❌ Неверный формат. Интервал должен быть числом.",
                        reply_markup=get_cancel_keyboard()
                    )
                    return
                
                interval = int(interval_str)
                success = self.db.add_new_task(task_name, interval)
                
                if success:
                    await update.message.reply_text(
                        f"✅ Задача добавлена:\n"
                        f"Название: {task_name}\n"
                        f"Интервал: {interval} дней"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Задача с названием '{task_name}' уже существует."
                    )
                
                del self.user_states[user_id]
            
            elif state.startswith("waiting_interval_"):
                task_id = int(state.split("_")[2])
                
                if not user_message.isdigit():
                    await update.message.reply_text(
                        "❌ Интервал должен быть числом.",
                        reply_markup=get_cancel_keyboard()
                    )
                    return
                
                new_interval = int(user_message)
                task = self.db.get_task_by_id(task_id)
                
                if task:
                    success = self.db.update_task_interval(task_id, new_interval)
                    if success:
                        await update.message.reply_text(
                            f"✅ Интервал обновлен:\n"
                            f"Задача: {task.name}\n"
                            f"Новый интервал: {new_interval} дней"
                        )
                    else:
                        await update.message.reply_text("❌ Ошибка при обновлении интервала")
                else:
                    await update.message.reply_text("❌ Задача не найдена")
                
                del self.user_states[user_id]
        
        except Exception as e:
            logger.error(f"Error handling user state: {e}")
            await update.message.reply_text("❌ Ошибка при обработке запроса")
            if user_id in self.user_states:
                del self.user_states[user_id]
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        try:
            welcome_text = """
👋 Привет! Я бот для управления домашними делами для пары.

📋 Доступные команды:
/tasks - список всех задач и их статус
/done [задача] - отметить задачу выполненной  
/stats - статистика выполнения
/next - когда следующие задачи
/test_reminders - тест системы напоминаний
/add_task - добавить новую задачу
/delete_task - удалить задачу
/edit_task - изменить интервал задачи

⏰ Я буду присылать ежедневные напоминания в 17:00!
            """
            await update.message.reply_text(welcome_text)
        except Exception as e:
            logger.error(f"Error in /start: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
    
    async def show_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /tasks"""
        try:
            tasks = self.db.get_all_tasks()
            
            if not tasks:
                await update.message.reply_text("📝 Задачи еще не настроены.")
                return
            
            # Формируем красивый список задач
            message_lines = ["📋 Список домашних задач:\n"]
            
            for task in tasks:
                status_line = task.format_status(self.db.get_user_name)
                message_lines.append(status_line)
            
            # Добавляем информацию о просроченных задачах
            overdue_count = sum(1 for task in tasks if task.is_overdue())
            if overdue_count > 0:
                message_lines.append(f"\n⚠️  Всего просрочено задач: {overdue_count}")
            
            message_lines.append("\n🔔 - просрочено, ⏳ - ожидает")
            
            await update.message.reply_text("\n".join(message_lines))
        
        except Exception as e:
            logger.error(f"Error in /tasks: {e}")
            await update.message.reply_text("❌ Ошибка при получении списка задач.")
    
    async def mark_task_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /done"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ Укажите задачу. Например: /done полы\n"
                    "Посмотреть все задачи: /tasks"
                )
                return
            
            task_query = " ".join(context.args)
            task = self.db.find_task_by_name(task_query)
            
            if not task:
                await update.message.reply_text(
                    f"❌ Задача '{task_query}' не найдена.\n"
                    "Посмотреть все задачи: /tasks"
                )
                return
            
            # Получаем информацию о пользователе
            user = update.effective_user
            self.db.mark_task_done(
                task_id=task.id,
                user_chat_id=user.id,
                username=user.username or "нет",
                first_name=user.first_name or "Аноним"
            )
            
            await update.message.reply_text(
                f"✅ Отлично! {user.first_name} выполнил(а) задачу: {task.name}\n"
                f"Следующее выполнение через {task.interval_days} дней."
            )
        
        except Exception as e:
            logger.error(f"Error in /done: {e}")
            await update.message.reply_text("❌ Ошибка при отметке задачи.")
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats"""
        try:
            tasks = self.db.get_all_tasks()
            
            completed_count = sum(1 for task in tasks if task.last_done and not task.is_overdue())
            overdue_count = sum(1 for task in tasks if task.is_overdue())
            total_count = len(tasks)
            
            stats_text = (
                f"📊 Статистика выполнения:\n"
                f"✅ Выполнено вовремя: {completed_count}/{total_count}\n"
                f"🔔 Просрочено: {overdue_count}/{total_count}\n"
                f"📈 Прогресс: {completed_count/total_count*100:.1f}%" if total_count > 0 else "0%"
            )
            
            await update.message.reply_text(stats_text)
        
        except Exception as e:
            logger.error(f"Error in /stats: {e}")
            await update.message.reply_text("❌ Ошибка при получении статистики.")
    
    async def show_next_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /next - ближайшие задачи"""
        try:
            tasks = self.db.get_all_tasks()
            
            # Сортируем по срочности (просроченные сначала, затем по оставшимся дням)
            tasks_sorted = sorted(tasks, key=lambda t: (
                0 if t.is_overdue() else 1,  # просроченные сначала
                t.days_until_due() if not t.is_overdue() else float('inf')
            ))
            
            message_lines = ["⏰ Ближайшие задачи:\n"]
            
            for task in tasks_sorted[:5]:  # Показываем 5 самых срочных
                if task.is_overdue():
                    overdue_days = (task.days_since_done() or 0) - task.interval_days
                    message_lines.append(f"🔔 {task.name} - просрочено на {overdue_days} дн.")
                else:
                    days_left = task.days_until_due()
                    message_lines.append(f"⏳ {task.name} - через {days_left} дн.")
            
            await update.message.reply_text("\n".join(message_lines))
        
        except Exception as e:
            logger.error(f"Error in /next: {e}")
            await update.message.reply_text("❌ Ошибка при получении списка задач.")
    
    async def test_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /test_reminders"""
        try:
            # Проверяем права пользователя
            user_id = update.effective_user.id
            if user_id not in config.ADMIN_IDS:
                await update.message.reply_text("❌ Эта команда только для администраторов")
                return
            
            await update.message.reply_text("🔄 Тестирование системы напоминаний...")
            
            # Тестируем напоминания
            overdue_tasks = self.db.get_overdue_tasks()
            due_soon_tasks = self.db.get_tasks_due_soon(days_threshold=2)
            
            test_message = format_reminder_message(overdue_tasks, due_soon_tasks)
            
            await update.message.reply_text(test_message)
            
            logger.info(f"🧪 Test reminders executed by user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in /test_reminders: {e}")
            await update.message.reply_text("❌ Ошибка при тестировании напоминаний")
    
    async def add_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /add_task"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "📝 Добавление новой задачи:\n\n"
                    "Формат: /add_task Название | интервал_в_днях\n"
                    "Пример: /add_task Полить цветы | 3"
                )
                return
            
            # Обработка команды с аргументами
            user_input = " ".join(context.args)
            if "|" not in user_input:
                await update.message.reply_text(
                    "❌ Неверный формат. Используйте: Название | интервал_в_днях\n"
                    "Пример: Полить цветы | 3"
                )
                return
            
            task_name, interval_str = user_input.split("|", 1)
            task_name = task_name.strip()
            interval_str = interval_str.strip()
            
            if not task_name or not interval_str.isdigit():
                await update.message.reply_text("❌ Неверный формат. Интервал должен быть числом.")
                return
            
            interval = int(interval_str)
            
            # Добавляем задачу
            success = self.db.add_new_task(task_name, interval)
            
            if success:
                await update.message.reply_text(
                    f"✅ Задача добавлена:\n"
                    f"Название: {task_name}\n"
                    f"Интервал: {interval} дней"
                )
            else:
                await update.message.reply_text(
                    f"❌ Задача с названием '{task_name}' уже существует."
                )
                
        except Exception as e:
            logger.error(f"Error in /add_task: {e}")
            await update.message.reply_text("❌ Ошибка при добавлении задачи")
    
    async def delete_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /delete_task"""
        try:
            if not context.args:
                # Показываем список задач для удаления
                tasks = self.db.get_all_tasks()
                
                if not tasks:
                    await update.message.reply_text("📝 Нет задач для удаления.")
                    return
                
                message_lines = ["🗑️ Выберите задачу для удаления:\n"]
                for task in tasks:
                    message_lines.append(f"{task.id}. {task.name} (интервал: {task.interval_days} дн.)")
                
                message_lines.append("\nФормат: /delete_task номер_задачи")
                message_lines.append("Пример: /delete_task 3")
                
                await update.message.reply_text("\n".join(message_lines))
                return
            
            # Обработка удаления по ID
            task_id_str = context.args[0]
            if not task_id_str.isdigit():
                await update.message.reply_text("❌ Неверный формат. Укажите номер задачи.")
                return
            
            task_id = int(task_id_str)
            task = self.db.get_task_by_id(task_id)
            
            if not task:
                await update.message.reply_text("❌ Задача с таким номером не найдена.")
                return
            
            # Удаляем задачу
            success = self.db.delete_task(task_id)
            
            if success:
                await update.message.reply_text(f"✅ Задача '{task.name}' удалена")
            else:
                await update.message.reply_text("❌ Ошибка при удалении задачи")
                
        except Exception as e:
            logger.error(f"Error in /delete_task: {e}")
            await update.message.reply_text("❌ Ошибка при удалении задачи")
    
    async def edit_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /edit_task"""
        try:
            if not context.args or len(context.args) < 2:
                # Показываем список задач для редактирования
                tasks = self.db.get_all_tasks()
                
                if not tasks:
                    await update.message.reply_text("📝 Нет задач для редактирования.")
                    return
                
                message_lines = ["⚙️ Редактирование задачи:\n"]
                for task in tasks:
                    message_lines.append(f"{task.id}. {task.name} (текущий интервал: {task.interval_days} дн.)")
                
                message_lines.append("\nФормат: /edit_task номер_задачи новый_интервал")
                message_lines.append("Пример: /edit_task 3 7")
                
                await update.message.reply_text("\n".join(message_lines))
                return
            
            # Обработка редактирования
            task_id_str, new_interval_str = context.args[0], context.args[1]
            
            if not task_id_str.isdigit() or not new_interval_str.isdigit():
                await update.message.reply_text("❌ Неверный формат. Номер задачи и интервал должны быть числами.")
                return
            
            task_id = int(task_id_str)
            new_interval = int(new_interval_str)
            
            if new_interval <= 0:
                await update.message.reply_text("❌ Интервал должен быть положительным числом.")
                return
            
            task = self.db.get_task_by_id(task_id)
            if not task:
                await update.message.reply_text("❌ Задача с таким номером не найдена.")
                return
            
            # Обновляем интервал
            success = self.db.update_task_interval(task_id, new_interval)
            
            if success:
                await update.message.reply_text(
                    f"✅ Задача обновлена:\n"
                    f"Название: {task.name}\n"
                    f"Новый интервал: {new_interval} дней"
                )
            else:
                await update.message.reply_text("❌ Ошибка при обновлении задачи")
                
        except Exception as e:
            logger.error(f"Error in /edit_task: {e}")
            await update.message.reply_text("❌ Ошибка при редактировании задачи")
    
    def run(self):
        """Запуск бота"""
        try:
            self.application = Application.builder().token(config.BOT_TOKEN).build()
            
            # Регистрируем обработчики команд
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("tasks", self.show_tasks))
            self.application.add_handler(CommandHandler("done", self.mark_task_done))
            self.application.add_handler(CommandHandler("stats", self.show_stats))
            self.application.add_handler(CommandHandler("next", self.show_next_tasks))
            self.application.add_handler(CommandHandler("test_reminders", self.test_reminders))
            self.application.add_handler(CommandHandler("add_task", self.add_task_command))
            self.application.add_handler(CommandHandler("delete_task", self.delete_task_command))
            self.application.add_handler(CommandHandler("edit_task", self.edit_task_command))
            
            # Запускаем бота
            logger.info("🤖 Бот запускается...")
            self.application.run_polling()
            
        except Exception as e:
            logger.error(f"💥 Критическая ошибка при запуске бота: {e}")
    
    def run(self):
        """Запуск бота с новыми обработчиками"""
        try:
            self.application = Application.builder().token(config.BOT_TOKEN).build()
            
            # Регистрируем обработчики команд
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("tasks", self.show_tasks))
            self.application.add_handler(CommandHandler("tasks_kbd", self.tasks_with_keyboard))
            self.application.add_handler(CommandHandler("done", self.mark_task_done))
            self.application.add_handler(CommandHandler("stats", self.show_stats))
            self.application.add_handler(CommandHandler("next", self.show_next_tasks))
            self.application.add_handler(CommandHandler("test_reminders", self.test_reminders))
            
            # Новые команды управления
            self.application.add_handler(CommandHandler("manage", self.manage_tasks))
            self.application.add_handler(CommandHandler("add_task", self.add_task_command))
            self.application.add_handler(CommandHandler("delete_task", self.delete_task_command))
            self.application.add_handler(CommandHandler("edit_task", self.edit_task_command))
            self.application.add_handler(CommandHandler("rename_task", self.rename_task_command))
            self.application.add_handler(CommandHandler("backup", self.backup_command))
            self.application.add_handler(CommandHandler("achievements", self.achievements_command))
            
            # Обработчики кнопок и сообщений
            self.application.add_handler(CallbackQueryHandler(self.button_handler))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
            
            # Запускаем бота
            logger.info("🤖 Бот запускается с улучшенным интерфейсом...")
            logger.info("✅ Новые функции: Reply-клавиатура, достижения, бэкапы")
            self.application.run_polling()
            
        except Exception as e:
            logger.error(f"💥 Критическая ошибка при запуске бота: {e}")

if __name__ == "__main__":
    bot = HouseholdBot()
    bot.run()

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from models import Task, ShoppingItem

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="household_dev.db"):
        self.db_path = db_path
        self.init_db()
        self.create_shopping_table()

    def init_db(self):
        """Инициализация таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица задач
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                interval_days INTEGER NOT NULL,
                last_done TIMESTAMP,
                last_done_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (last_done_by) REFERENCES users (chat_id)
            )
        ''')

        # Таблица для хранения истории выполнений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                done_by INTEGER,
                done_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                FOREIGN KEY (done_by) REFERENCES users (chat_id)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_history_date 
            ON task_history(done_at)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_history_task 
            ON task_history(task_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tasks_interval 
            ON tasks(interval_days)
        ''')
        conn.commit()
        conn.close()

        # Добавляем стандартные задачи при первом запуске
        self.add_default_tasks()

    def create_shopping_table(self):
        """Создание таблицы для списка покупок с категориями"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Создаём таблицу, если её нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shopping_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_text TEXT NOT NULL,
                is_checked BOOLEAN DEFAULT 0,
                category TEXT DEFAULT 'supermarket',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Проверяем наличие колонки category (для старых баз)
        cursor.execute("PRAGMA table_info(shopping_items)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'category' not in columns:
            cursor.execute("ALTER TABLE shopping_items ADD COLUMN category TEXT DEFAULT 'supermarket'")

        conn.commit()
        conn.close()

    def add_default_tasks(self):
        """Добавление стандартных задач при первом запуске"""
        default_tasks = [
            ("Помыть полы", 7),
            ("Пропылесосить", 7),
            ("Помыть ванну", 21),
            ("Приготовить еду", 3),
            ("Поменять постельное", 7)
        ]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks")
        count = cursor.fetchone()[0]

        if count == 0:
            for task_name, interval in default_tasks:
                cursor.execute(
                    "INSERT INTO tasks (name, interval_days) VALUES (?, ?)",
                    (task_name, interval)
                )

        conn.commit()
        conn.close()

    def get_all_tasks(self) -> List[Task]:
        """Получить все задачи"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, interval_days, last_done, last_done_by, created_at 
            FROM tasks 
            ORDER BY name
        ''')

        tasks = []
        for row in cursor.fetchall():
            task = Task(
                id=row[0],
                name=row[1],
                interval_days=row[2],
                last_done=datetime.fromisoformat(row[3]) if row[3] else None,
                last_done_by=row[4],
                created_at=datetime.fromisoformat(row[5]) if row[5] else None
            )
            tasks.append(task)

        conn.close()
        return tasks

    # ================== МЕТОДЫ ДЛЯ СПИСКА ПОКУПОК ==================

    def add_shopping_item(self, item_text: str, category: str = 'supermarket') -> bool:
        """Добавить пункт в список покупок с указанием категории"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id FROM shopping_items 
                WHERE LOWER(item_text) = LOWER(?) AND is_checked = 0
            ''', (item_text,))
            existing_item = cursor.fetchone()
            if existing_item:
                conn.close()
                return False

            cursor.execute('''
                INSERT INTO shopping_items (item_text, is_checked, category) 
                VALUES (?, 0, ?)
            ''', (item_text, category))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding shopping item: {e}")
            return False

    def get_shopping_items(self, show_checked: bool = True, category: Optional[str] = None) -> List[ShoppingItem]:
        """Получить пункты списка покупок с возможностью фильтрации по категории"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = '''
                SELECT id, item_text, is_checked, category, created_at 
                FROM shopping_items 
                WHERE 1=1
            '''
            params = []

            if not show_checked:
                query += " AND is_checked = 0"

            if category and category != 'all':
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY is_checked, created_at DESC"

            cursor.execute(query, params)

            items = []
            for row in cursor.fetchall():
                item = ShoppingItem(
                    id=row[0],
                    item_text=row[1],
                    is_checked=bool(row[2]),
                    category=row[3],
                    created_at=datetime.fromisoformat(row[4]) if row[4] else datetime.now()
                )
                items.append(item)

            conn.close()
            return items
        except Exception as e:
            logger.error(f"Error getting shopping items: {e}")
            return []

    def toggle_shopping_item(self, item_id: int) -> Optional[ShoppingItem]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, item_text, is_checked, category, created_at 
                FROM shopping_items 
                WHERE id = ?
            ''', (item_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None

            current_status = bool(row[2])
            new_status = 0 if current_status else 1

            cursor.execute('''
                UPDATE shopping_items 
                SET is_checked = ? 
                WHERE id = ?
            ''', (new_status, item_id))

            conn.commit()
            conn.close()

            return ShoppingItem(
                id=row[0],
                item_text=row[1],
                is_checked=new_status,
                category=row[3],
                created_at=datetime.fromisoformat(row[4]) if row[4] else datetime.now()
            )
        except Exception as e:
            logger.error(f"Error toggling shopping item: {e}")
            return None

    def delete_checked_items(self) -> int:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM shopping_items WHERE is_checked = 1')
            count = cursor.fetchone()[0]
            cursor.execute('DELETE FROM shopping_items WHERE is_checked = 1')
            conn.commit()
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error deleting checked items: {e}")
            return 0

    def delete_all_shopping_items(self) -> int:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM shopping_items')
            count = cursor.fetchone()[0]
            cursor.execute('DELETE FROM shopping_items')
            conn.commit()
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error deleting all shopping items: {e}")
            return 0

    def get_shopping_item_count(self) -> Dict[str, int]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM shopping_items WHERE is_checked = 0')
            unchecked = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM shopping_items WHERE is_checked = 1')
            checked = cursor.fetchone()[0]
            conn.close()
            return {'total': unchecked + checked, 'unchecked': unchecked, 'checked': checked}
        except Exception as e:
            logger.error(f"Error getting shopping item count: {e}")
            return {'total': 0, 'unchecked': 0, 'checked': 0}

    # ================== МЕТОДЫ ДЛЯ ЗАДАЧ ==================

    def get_user_by_name(self, name: str) -> Optional[int]:
        """Возвращает chat_id пользователя по first_name (регистронезависимо) или None"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT chat_id FROM users WHERE LOWER(first_name) = LOWER(?)",
            (name,)
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def user_exists(self, chat_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE chat_id = ?", (chat_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def get_user_name(self, chat_id: int) -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT first_name FROM users WHERE chat_id = ?', (chat_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "Неизвестный пользователь"

    def mark_task_done(self, task_id: int, user_chat_id: int):
        """Отметить задачу выполненной пользователем с данным chat_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username, first_name FROM users WHERE chat_id = ?",
            (user_chat_id,)
        )
        user_row = cursor.fetchone()
        if user_row:
            username, first_name = user_row
        else:
            username = f"user_{user_chat_id}"
            first_name = f"User {user_chat_id}"

        cursor.execute('''
            INSERT OR REPLACE INTO users (chat_id, username, first_name, joined_at)
            VALUES (?, ?, ?, COALESCE((SELECT joined_at FROM users WHERE chat_id = ?), CURRENT_TIMESTAMP))
        ''', (user_chat_id, username, first_name, user_chat_id))

        current_time = datetime.now().isoformat()
        cursor.execute('''
            UPDATE tasks 
            SET last_done = ?, last_done_by = ? 
            WHERE id = ?
        ''', (current_time, user_chat_id, task_id))

        cursor.execute('''
            INSERT INTO task_history (task_id, done_by, done_at) 
            VALUES (?, ?, ?)
        ''', (task_id, user_chat_id, current_time))

        conn.commit()
        conn.close()
        self.cleanup_old_history()

    def find_task_by_name(self, task_name: str) -> Optional[Task]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, interval_days, last_done, last_done_by, created_at 
            FROM tasks 
            WHERE LOWER(name) LIKE LOWER(?)
        ''', (f'%{task_name}%',))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Task(
                id=row[0],
                name=row[1],
                interval_days=row[2],
                last_done=datetime.fromisoformat(row[3]) if row[3] else None,
                last_done_by=row[4],
                created_at=datetime.fromisoformat(row[5]) if row[5] else None
            )
        return None

    def get_overdue_tasks(self) -> List[Task]:
        tasks = self.get_all_tasks()
        return [task for task in tasks if task.is_overdue()]

    def get_tasks_due_soon(self, days_threshold: int = 2) -> List[Task]:
        tasks = self.get_all_tasks()
        due_soon = []
        for task in tasks:
            if task.last_done and not task.is_overdue():
                days_until_due = task.days_until_due()
                if 0 < days_until_due <= days_threshold:
                    due_soon.append(task)
        return due_soon

    def cleanup_old_history(self, days_to_keep: int = 90):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            cursor.execute('DELETE FROM task_history WHERE done_at < ?', (cutoff_date,))
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            if deleted_count > 0:
                logger.info(f"🧹 Автоочистка: удалено {deleted_count} старых записей истории")
        except Exception as e:
            logger.error(f"Error cleaning old history: {e}")

    def get_history_stats(self) -> Dict[str, int]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM task_history')
            total = cursor.fetchone()[0]
            since_date = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute('SELECT COUNT(*) FROM task_history WHERE done_at >= ?', (since_date,))
            last_30_days = cursor.fetchone()[0]
            since_week = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute('SELECT COUNT(*) FROM task_history WHERE done_at >= ?', (since_week,))
            last_7_days = cursor.fetchone()[0]
            conn.close()
            return {'total': total, 'last_30_days': last_30_days, 'last_7_days': last_7_days}
        except Exception as e:
            logger.error(f"Error getting history stats: {e}")
            return {'total': 0, 'last_30_days': 0, 'last_7_days': 0}

    def add_new_task(self, name: str, interval_days: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tasks WHERE LOWER(name) = LOWER(?)", (name,))
            existing_task = cursor.fetchone()
            if existing_task:
                conn.close()
                return False
            cursor.execute(
                "INSERT INTO tasks (name, interval_days) VALUES (?, ?)",
                (name, interval_days)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding new task: {e}")
            return False

    def update_task_interval(self, task_id: int, new_interval: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET interval_days = ? WHERE id = ?",
                (new_interval, task_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating task interval: {e}")
            return False

    def delete_task(self, task_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM task_history WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False

    def rename_task(self, task_id: int, new_name: str) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tasks WHERE LOWER(name) = LOWER(?) AND id != ?", (new_name, task_id))
            existing_task = cursor.fetchone()
            if existing_task:
                conn.close()
                return False
            cursor.execute("UPDATE tasks SET name = ? WHERE id = ?", (new_name, task_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error renaming task: {e}")
            return False

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, interval_days, last_done, last_done_by, created_at 
                FROM tasks WHERE id = ?
            ''', (task_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return Task(
                    id=row[0],
                    name=row[1],
                    interval_days=row[2],
                    last_done=datetime.fromisoformat(row[3]) if row[3] else None,
                    last_done_by=row[4],
                    created_at=datetime.fromisoformat(row[5]) if row[5] else None
                )
            return None
        except Exception as e:
            logger.error(f"Error getting task by ID: {e}")
            return None
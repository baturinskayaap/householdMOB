import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from models import Task, ShoppingItem

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="household_dev.db"):
        self.db_path = db_path
        self._init_db()
        self._init_shopping_table()
        self._add_default_tasks()
        self._add_default_user()

    def _init_db(self):
        """Инициализация таблиц пользователей, задач и истории"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    username TEXT
                )
            ''')
            # Таблица задач (без created_at)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    interval_days INTEGER NOT NULL,
                    last_done TIMESTAMP,
                    last_done_by INTEGER,
                    FOREIGN KEY (last_done_by) REFERENCES users(chat_id)
                )
            ''')
            # Таблица истории
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    done_by INTEGER,
                    done_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id),
                    FOREIGN KEY (done_by) REFERENCES users(chat_id)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_history_date ON task_history(done_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_history_task ON task_history(task_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_interval ON tasks(interval_days)')
            conn.commit()

    def _init_shopping_table(self):
        """Инициализация таблицы покупок (без created_at)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shopping_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_text TEXT NOT NULL,
                    is_checked BOOLEAN DEFAULT 0,
                    category TEXT DEFAULT 'supermarket'
                )
            ''')
            # Для старых баз добавляем category, если её нет
            cursor.execute("PRAGMA table_info(shopping_items)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'category' not in columns:
                cursor.execute("ALTER TABLE shopping_items ADD COLUMN category TEXT DEFAULT 'supermarket'")
            conn.commit()

    def _add_default_tasks(self):
        """Добавление стандартных задач при первом запуске"""
        default_tasks = [
            ("Помыть полы", 7),
            ("Пропылесосить", 7),
            ("Помыть ванну", 21),
            ("Полотенца", 7),
            ("Постельное", 7),
            ("Раковина + плита", 7)
        ]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks")
            if cursor.fetchone()[0] == 0:
                cursor.executemany(
                    "INSERT INTO tasks (name, interval_days) VALUES (?, ?)",
                    default_tasks
                )
                conn.commit()

    def _add_default_user(self):
        """Добавление пользователя по умолчанию при первом запуске"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO users (chat_id, username) VALUES (?, ?)",
                    (1, 'настя')
                    (2, 'костя')  # можно изменить имя
                )
                conn.commit()
                logger.info("✅ Создан пользователь по умолчанию: настя")

    # ================== ПОЛЬЗОВАТЕЛИ ==================
    def get_user_by_name(self, name: str) -> Optional[int]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT chat_id FROM users WHERE LOWER(username) = LOWER(?)",
                (name,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def user_exists(self, chat_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE chat_id = ?", (chat_id,))
            return cursor.fetchone() is not None

    # ================== ЗАДАЧИ ==================
    def get_all_tasks(self) -> List[Task]:
        """Получить все задачи (без created_at)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, interval_days, last_done, last_done_by
                FROM tasks ORDER BY name
            ''')
            return [
                Task(
                    id=row[0],
                    name=row[1],
                    interval_days=row[2],
                    last_done=datetime.fromisoformat(row[3]) if row[3] else None,
                    last_done_by=row[4]
                )
                for row in cursor.fetchall()
            ]

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, interval_days, last_done, last_done_by
                FROM tasks WHERE id = ?
            ''', (task_id,))
            row = cursor.fetchone()
            if row:
                return Task(
                    id=row[0],
                    name=row[1],
                    interval_days=row[2],
                    last_done=datetime.fromisoformat(row[3]) if row[3] else None,
                    last_done_by=row[4]
                )
            return None

    def add_new_task(self, name: str, interval_days: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM tasks WHERE LOWER(name) = LOWER(?)",
                    (name,)
                )
                if cursor.fetchone():
                    return False
                cursor.execute(
                    "INSERT INTO tasks (name, interval_days) VALUES (?, ?)",
                    (name, interval_days)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return False

    def update_task_interval(self, task_id: int, new_interval: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE tasks SET interval_days = ? WHERE id = ?",
                    (new_interval, task_id)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating task interval: {e}")
            return False

    def rename_task(self, task_id: int, new_name: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM tasks WHERE LOWER(name) = LOWER(?) AND id != ?",
                    (new_name, task_id)
                )
                if cursor.fetchone():
                    return False
                cursor.execute(
                    "UPDATE tasks SET name = ? WHERE id = ?",
                    (new_name, task_id)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error renaming task: {e}")
            return False

    def delete_task(self, task_id: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM task_history WHERE task_id = ?", (task_id,))
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False

    def mark_task_done(self, task_id: int, user_chat_id: int):
        """Отметить задачу выполненной пользователем"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Получаем имя пользователя (необязательно, можно использовать для логирования)
            cursor.execute(
                "SELECT username FROM users WHERE chat_id = ?",
                (user_chat_id,)
            )
            user_row = cursor.fetchone()
            username = user_row[0] if user_row else f"user_{user_chat_id}"

            # Если пользователя нет в БД, создаём
            if not user_row:
                cursor.execute(
                    "INSERT INTO users (chat_id, username) VALUES (?, ?)",
                    (user_chat_id, username)
                )

            current_time = datetime.now().isoformat()
            cursor.execute('''
                UPDATE tasks SET last_done = ?, last_done_by = ? WHERE id = ?
            ''', (current_time, user_chat_id, task_id))
            cursor.execute('''
                INSERT INTO task_history (task_id, done_by, done_at) VALUES (?, ?, ?)
            ''', (task_id, user_chat_id, current_time))
            conn.commit()
        self._cleanup_old_history()

    def _cleanup_old_history(self, days_to_keep: int = 90):
        try:
            cutoff = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM task_history WHERE done_at < ?", (cutoff,))
                deleted = cursor.rowcount
                conn.commit()
                if deleted:
                    logger.info(f"🧹 Очищено {deleted} старых записей истории")
        except Exception as e:
            logger.error(f"Error cleaning history: {e}")

    # ================== ПОКУПКИ ==================
    def add_shopping_item(self, item_text: str, category: str = 'supermarket') -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM shopping_items
                    WHERE LOWER(item_text) = LOWER(?) AND is_checked = 0
                ''', (item_text,))
                if cursor.fetchone():
                    return False
                cursor.execute('''
                    INSERT INTO shopping_items (item_text, is_checked, category)
                    VALUES (?, 0, ?)
                ''', (item_text, category))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding shopping item: {e}")
            return False

    def get_shopping_items(self, show_checked: bool = True, category: Optional[str] = None) -> List[ShoppingItem]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT id, item_text, is_checked, category
                    FROM shopping_items
                    WHERE 1=1
                '''
                params = []
                if not show_checked:
                    query += " AND is_checked = 0"
                if category and category != 'all':
                    query += " AND category = ?"
                    params.append(category)
                # Сортировка: сначала неотмеченные, потом отмеченные; внутри по убыванию id (новые сверху)
                query += " ORDER BY is_checked, id DESC"
                cursor.execute(query, params)
                return [
                    ShoppingItem(
                        id=row[0],
                        item_text=row[1],
                        is_checked=bool(row[2]),
                        category=row[3]
                    )
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Error getting shopping items: {e}")
            return []

    def toggle_shopping_item(self, item_id: int) -> Optional[ShoppingItem]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, item_text, is_checked, category
                    FROM shopping_items WHERE id = ?
                ''', (item_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                new_status = 0 if row[2] else 1
                cursor.execute('''
                    UPDATE shopping_items SET is_checked = ? WHERE id = ?
                ''', (new_status, item_id))
                conn.commit()
                return ShoppingItem(
                    id=row[0],
                    item_text=row[1],
                    is_checked=new_status,
                    category=row[3]
                )
        except Exception as e:
            logger.error(f"Error toggling shopping item: {e}")
            return None

    def delete_checked_items(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM shopping_items WHERE is_checked = 1")
                count = cursor.fetchone()[0]
                cursor.execute("DELETE FROM shopping_items WHERE is_checked = 1")
                conn.commit()
                return count
        except Exception as e:
            logger.error(f"Error deleting checked items: {e}")
            return 0

    def delete_all_shopping_items(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM shopping_items")
                count = cursor.fetchone()[0]
                cursor.execute("DELETE FROM shopping_items")
                conn.commit()
                return count
        except Exception as e:
            logger.error(f"Error deleting all items: {e}")
            return 0

    def get_shopping_item_count(self) -> Dict[str, int]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM shopping_items WHERE is_checked = 0")
                unchecked = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM shopping_items WHERE is_checked = 1")
                checked = cursor.fetchone()[0]
                return {
                    'total': unchecked + checked,
                    'unchecked': unchecked,
                    'checked': checked
                }
        except Exception as e:
            logger.error(f"Error getting item count: {e}")
            return {'total': 0, 'unchecked': 0, 'checked': 0}
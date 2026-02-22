# app.py
import logging
from functools import wraps
from datetime import datetime
from flask import Flask, request, jsonify, abort

from database import Database
from models import Task, ShoppingItem
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Инициализация базы данных (один экземпляр на всё приложение)
db = Database(config.DATABASE_PATH)


# Декоратор для проверки X-Chat-ID
def require_chat_id(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        chat_id = request.headers.get('X-Chat-ID')
        if not chat_id:
            abort(401, description='Missing X-Chat-ID header')
        try:
            chat_id = int(chat_id)
        except ValueError:
            abort(400, description='X-Chat-ID must be integer')
        if chat_id not in config.ALLOWED_CHAT_IDS:
            abort(403, description='Access denied')
        # Передаём chat_id в функцию как keyword argument
        kwargs['chat_id'] = chat_id
        return f(*args, **kwargs)
    return decorated


# ========== Вспомогательные функции сериализации ==========
def task_to_dict(task: Task) -> dict:
    return {
        'id': task.id,
        'name': task.name,
        'interval_days': task.interval_days,
        'last_done': task.last_done.isoformat() if task.last_done else None,
        'last_done_by': task.last_done_by,
        'created_at': task.created_at.isoformat() if task.created_at else None,
        # Добавим вычисляемые поля для удобства мобильного приложения
        'is_overdue': task.is_overdue(),
        'days_until_due': task.days_until_due(),
        'days_since_done': task.days_since_done(),
    }


def shopping_item_to_dict(item: ShoppingItem) -> dict:
    return {
        'id': item.id,
        'item_text': item.item_text,
        'is_checked': item.is_checked,
        'created_at': item.created_at.isoformat() if item.created_at else None,
    }


# ========== Эндпоинты для задач ==========

@app.route('/tasks', methods=['GET'])
@require_chat_id
def get_tasks(chat_id):
    """Получить все задачи."""
    tasks = db.get_all_tasks()
    return jsonify([task_to_dict(t) for t in tasks])


@app.route('/tasks', methods=['POST'])
@require_chat_id
def create_task(chat_id):
    """Создать новую задачу."""
    data = request.get_json()
    if not data:
        abort(400, description='Missing JSON body')
    name = data.get('name')
    interval_days = data.get('interval_days')
    if not name or not interval_days:
        abort(400, description='name and interval_days are required')
    if not isinstance(interval_days, int) or interval_days <= 0:
        abort(400, description='interval_days must be positive integer')

    success = db.add_new_task(name, interval_days)
    if not success:
        abort(409, description='Task with this name already exists')

    # Найдём созданную задачу (по имени)
    tasks = db.get_all_tasks()
    task = next((t for t in tasks if t.name.lower() == name.lower()), None)
    if not task:
        abort(500, description='Task created but not found')
    return jsonify(task_to_dict(task)), 201


@app.route('/tasks/<int:task_id>', methods=['PATCH'])
@require_chat_id
def update_task(task_id, chat_id):
    """Обновить задачу (переименовать или изменить интервал)."""
    task = db.get_task_by_id(task_id)
    if not task:
        abort(404, description='Task not found')

    data = request.get_json()
    if not data:
        abort(400, description='Missing JSON body')

    if 'name' in data:
        new_name = data['name'].strip()
        if not new_name:
            abort(400, description='name cannot be empty')
        success = db.rename_task(task_id, new_name)
        if not success:
            abort(409, description='Task with this name already exists')

    if 'interval_days' in data:
        new_interval = data['interval_days']
        if not isinstance(new_interval, int) or new_interval <= 0:
            abort(400, description='interval_days must be positive integer')
        db.update_task_interval(task_id, new_interval)

    updated_task = db.get_task_by_id(task_id)
    return jsonify(task_to_dict(updated_task))


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@require_chat_id
def delete_task(task_id, chat_id):
    """Удалить задачу."""
    task = db.get_task_by_id(task_id)
    if not task:
        abort(404, description='Task not found')
    db.delete_task(task_id)
    return '', 204


@app.route('/tasks/<int:task_id>/done', methods=['POST'])
@require_chat_id
def mark_task_done(task_id, chat_id):
    """Отметить задачу выполненной текущим пользователем."""
    task = db.get_task_by_id(task_id)
    if not task:
        abort(404, description='Task not found')

    # В методе mark_task_done мы передаём username и first_name = None,
    # тогда get_or_create_user подставит существующие данные или значения по умолчанию.
    db.mark_task_done(task_id, chat_id)

    updated_task = db.get_task_by_id(task_id)
    return jsonify(task_to_dict(updated_task))


# ========== Эндпоинты для покупок ==========

@app.route('/shopping', methods=['GET'])
@require_chat_id
def get_shopping_items(chat_id):
    """Получить список покупок."""
    show_checked = request.args.get('show_checked', 'true').lower() == 'true'
    items = db.get_shopping_items(show_checked=show_checked)
    return jsonify([shopping_item_to_dict(i) for i in items])


@app.route('/shopping', methods=['POST'])
@require_chat_id
def create_shopping_item(chat_id):
    """Добавить новый пункт в список покупок."""
    data = request.get_json()
    if not data:
        abort(400, description='Missing JSON body')
    item_text = data.get('item_text')
    if not item_text:
        abort(400, description='item_text is required')
    item_text = item_text.strip()
    if not item_text:
        abort(400, description='item_text cannot be empty')

    success = db.add_shopping_item(item_text)
    if not success:
        abort(409, description='Item already exists (unchecked)')

    # Найдём созданный элемент
    items = db.get_shopping_items(show_checked=True)
    item = next((i for i in items if i.item_text.lower() == item_text.lower()), None)
    if not item:
        abort(500, description='Item created but not found')
    return jsonify(shopping_item_to_dict(item)), 201


@app.route('/shopping/<int:item_id>/toggle', methods=['PATCH'])
@require_chat_id
def toggle_shopping_item(item_id, chat_id):
    """Переключить состояние отметки пункта."""
    updated = db.toggle_shopping_item(item_id)
    if not updated:
        abort(404, description='Item not found')
    return jsonify(shopping_item_to_dict(updated))


@app.route('/shopping/checked', methods=['DELETE'])
@require_chat_id
def delete_checked_items(chat_id):
    """Удалить все отмеченные пункты."""
    count = db.delete_checked_items()
    return jsonify({'deleted': count})


@app.route('/shopping/all', methods=['DELETE'])
@require_chat_id
def delete_all_items(chat_id):
    """Удалить все пункты списка покупок."""
    count = db.delete_all_shopping_items()
    return jsonify({'deleted': count})


@app.route('/shopping/stats', methods=['GET'])
@require_chat_id
def shopping_stats(chat_id):
    """Получить статистику по списку покупок."""
    stats = db.get_shopping_item_count()
    return jsonify(stats)


# ========== Запуск ==========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
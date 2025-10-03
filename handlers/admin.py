from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_admin_keyboard, get_main_keyboard
from config import ADMIN_ID
from datetime import datetime

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id == ADMIN_ID

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Главная команда админ-панели"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к админ-панели.")
        return
    
    await update.message.reply_text(
        "🔐 Админ-панель\n\nВыберите действие:",
        reply_markup=get_admin_keyboard()
    )

async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Показывает общую статистику"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет доступа.")
        return
    
    # Собираем статистику
    total_users = db.get_all_users_count()
    active_subs = db.get_active_subscriptions_count()
    total_revenue = db.get_total_revenue()
    
    trial_users = len(db.get_trial_users())
    paid_users = len(db.get_paid_users())
    
    revenue_by_method = db.get_revenue_by_method()
    
    # Формируем сообщение
    stats_text = f"""
📊 **Общая статистика**

👥 Всего пользователей: **{total_users}**
✅ Активных подписок: **{active_subs}**

🎁 Пробный период: **{trial_users}**
💎 Платных подписок: **{paid_users}**

💰 Общая выручка: **{total_revenue:.2f}₽**

**По методам оплаты:**
"""
    
    for method, count, total in revenue_by_method:
        method_name = {
            'yookassa': '💳 ЮКасса',
            'stars': '⭐ Stars',
            'cryptobot': '₿ Крипто'
        }.get(method, method)
        stats_text += f"{method_name}: {count} платежей, {total:.2f}₽\n"
    
    await query.edit_message_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )

async def admin_trial_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Показывает пользователей с пробным периодом"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет доступа.")
        return
    
    trial_users = db.get_trial_users()
    
    if not trial_users:
        await query.edit_message_text(
            "📋 Нет пользователей на пробном периоде",
            reply_markup=get_admin_keyboard()
        )
        return
    
    text = "🎁 **Пользователи на пробном периоде:**\n\n"
    
    for user_id, username, start_date, end_date, is_active in trial_users:
        status = "✅ Активен" if is_active and datetime.fromisoformat(end_date) > datetime.now() else "❌ Истек"
        end_date_formatted = datetime.fromisoformat(end_date).strftime("%d.%m.%Y %H:%M")
        
        text += f"👤 @{username or 'Без имени'} (ID: `{user_id}`)\n"
        text += f"   Статус: {status}\n"
        text += f"   До: {end_date_formatted}\n\n"
    
    # Telegram ограничивает длину сообщения до 4096 символов
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (список обрезан)"
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )

async def admin_paid_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Показывает пользователей с платной подпиской"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет доступа.")
        return
    
    paid_users = db.get_paid_users()
    
    if not paid_users:
        await query.edit_message_text(
            "📋 Нет пользователей с платной подпиской",
            reply_markup=get_admin_keyboard()
        )
        return
    
    text = "💎 **Пользователи с платной подпиской:**\n\n"
    
    for user_id, username, start_date, end_date, is_active in paid_users:
        status = "✅ Активна" if is_active and datetime.fromisoformat(end_date) > datetime.now() else "❌ Истекла"
        end_date_formatted = datetime.fromisoformat(end_date).strftime("%d.%m.%Y %H:%M")
        
        text += f"👤 @{username or 'Без имени'} (ID: `{user_id}`)\n"
        text += f"   Статус: {status}\n"
        text += f"   До: {end_date_formatted}\n\n"
    
    # Telegram ограничивает длину сообщения до 4096 символов
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (список обрезан)"
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )

async def admin_recent_payments_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Показывает последние платежи"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет доступа.")
        return
    
    recent_payments = db.get_recent_payments(limit=20)
    
    if not recent_payments:
        await query.edit_message_text(
            "📋 Нет платежей",
            reply_markup=get_admin_keyboard()
        )
        return
    
    text = "💳 **Последние платежи:**\n\n"
    
    for user_id, username, amount, payment_method, status, created_at in recent_payments:
        status_emoji = "✅" if status == "paid" else "⏳"
        method_name = {
            'yookassa': '💳',
            'stars': '⭐',
            'cryptobot': '₿'
        }.get(payment_method, '💰')
        
        created_at_formatted = datetime.fromisoformat(created_at).strftime("%d.%m.%Y %H:%M")
        
        text += f"{status_emoji} {method_name} **{amount:.2f}₽** - @{username or 'Без имени'}\n"
        text += f"   Дата: {created_at_formatted}\n\n"
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )

async def admin_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в админ-панель"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет доступа.")
        return
    
    await query.edit_message_text(
        "🔐 Админ-панель\n\nВыберите действие:",
        reply_markup=get_admin_keyboard()
    )
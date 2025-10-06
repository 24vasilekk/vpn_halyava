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
    
    trial_users = db.get_trial_users()
    paid_users = db.get_paid_users()
    
    # Разделяем на активные и истёкшие
    now = datetime.now()
    active_trial = [u for u in trial_users if u[4] and datetime.fromisoformat(u[3]) > now]
    expired_trial = [u for u in trial_users if not u[4] or datetime.fromisoformat(u[3]) <= now]
    
    active_paid = [u for u in paid_users if u[4] and datetime.fromisoformat(u[3]) > now]
    expired_paid = [u for u in paid_users if not u[4] or datetime.fromisoformat(u[3]) <= now]
    
    revenue_by_method = db.get_revenue_by_method()
    
    # Формируем сообщение
    stats_text = f"""
📊 **Общая статистика**

👥 Всего пользователей: **{total_users}**
✅ Активных подписок: **{active_subs}**

**🎁 Пробный период:**
├ Активных: **{len(active_trial)}**
└ Истекло: **{len(expired_trial)}**

**💎 Платные подписки:**
├ Активных: **{len(active_paid)}**
└ Истекло: **{len(expired_paid)}**

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
    
    # Разделяем на активные и истёкшие
    now = datetime.now()
    active = [u for u in trial_users if u[4] and datetime.fromisoformat(u[3]) > now]
    expired = [u for u in trial_users if not u[4] or datetime.fromisoformat(u[3]) <= now]
    
    # Сортируем по дате истечения
    active.sort(key=lambda x: x[3])
    expired.sort(key=lambda x: x[3], reverse=True)
    
    text = f"🎁 **Пробный период** (всего: {len(trial_users)})\n\n"
    
    # Активные подписки
    if active:
        text += f"✅ **АКТИВНЫЕ ({len(active)}):**\n\n"
        for user_id, username, start_date, end_date, is_active in active:
            end_dt = datetime.fromisoformat(end_date)
            days_left = (end_dt - now).days
            hours_left = (end_dt - now).seconds // 3600
            
            time_left = f"{days_left}д {hours_left}ч" if days_left > 0 else f"{hours_left}ч"
            end_formatted = end_dt.strftime("%d.%m.%Y %H:%M")
            
            text += f"👤 @{username or 'Без имени'} (ID: `{user_id}`)\n"
            text += f"   ⏰ До: {end_formatted} (осталось: {time_left})\n\n"
    
    # Истёкшие подписки
    if expired:
        text += f"\n❌ **ИСТЕКШИЕ ({len(expired)}):**\n\n"
        for user_id, username, start_date, end_date, is_active in expired[:10]:
            end_formatted = datetime.fromisoformat(end_date).strftime("%d.%m.%Y %H:%M")
            
            text += f"👤 @{username or 'Без имени'} (ID: `{user_id}`)\n"
            text += f"   📅 Истекло: {end_formatted}\n\n"
        
        if len(expired) > 10:
            text += f"... и ещё {len(expired) - 10} пользователей\n"
    
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
    
    # Разделяем на активные и истёкшие
    now = datetime.now()
    active = [u for u in paid_users if u[4] and datetime.fromisoformat(u[3]) > now]
    expired = [u for u in paid_users if not u[4] or datetime.fromisoformat(u[3]) <= now]
    
    # Сортируем по дате истечения
    active.sort(key=lambda x: x[3])
    expired.sort(key=lambda x: x[3], reverse=True)
    
    text = f"💎 **Платные подписки** (всего: {len(paid_users)})\n\n"
    
    # Активные подписки
    if active:
        text += f"✅ **АКТИВНЫЕ ({len(active)}):**\n\n"
        for user_id, username, start_date, end_date, is_active in active:
            end_dt = datetime.fromisoformat(end_date)
            days_left = (end_dt - now).days
            hours_left = (end_dt - now).seconds // 3600
            
            time_left = f"{days_left}д {hours_left}ч" if days_left > 0 else f"{hours_left}ч"
            end_formatted = end_dt.strftime("%d.%m.%Y %H:%M")
            
            text += f"👤 @{username or 'Без имени'} (ID: `{user_id}`)\n"
            text += f"   ⏰ До: {end_formatted} (осталось: {time_left})\n\n"
    
    # Истёкшие подписки
    if expired:
        text += f"\n❌ **ИСТЕКШИЕ ({len(expired)}):**\n\n"
        for user_id, username, start_date, end_date, is_active in expired[:10]:
            end_formatted = datetime.fromisoformat(end_date).strftime("%d.%m.%Y %H:%M")
            
            text += f"👤 @{username or 'Без имени'} (ID: `{user_id}`)\n"
            text += f"   📅 Истекло: {end_formatted}\n\n"
        
        if len(expired) > 10:
            text += f"... и ещё {len(expired) - 10} пользователей\n"
    
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

async def admin_expiring_soon_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """НОВАЯ ФУНКЦИЯ: Показывает подписки, которые скоро истекут (< 3 дней)"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ У вас нет доступа.")
        return
    
    expiring = db.get_expiring_subscriptions(days=3)
    
    if not expiring:
        await query.edit_message_text(
            "✅ Нет подписок, истекающих в ближайшие 3 дня",
            reply_markup=get_admin_keyboard()
        )
        return
    
    text = f"⚠️ **Истекают в ближайшие 3 дня** ({len(expiring)}):\n\n"
    
    now = datetime.now()
    for user_id, username, end_date, is_trial in expiring:
        end_dt = datetime.fromisoformat(end_date)
        hours_left = int((end_dt - now).total_seconds() / 3600)
        days_left = hours_left // 24
        
        sub_type = "🎁 Trial" if is_trial else "💎 Платная"
        time_left = f"{days_left}д {hours_left % 24}ч" if days_left > 0 else f"{hours_left}ч"
        
        text += f"👤 @{username or 'Без имени'} (ID: `{user_id}`)\n"
        text += f"   {sub_type} | Осталось: {time_left}\n\n"
    
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (список обрезан)"
    
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
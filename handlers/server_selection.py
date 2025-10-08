from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_protocol_selection_keyboard, get_device_options_keyboard

async def choose_protocol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Показывает выбор протокола"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    _, protocol = db.get_user_preferences(user_id)
    
    protocol_names = {
        'wireguard': '🔷 WireGuard',
        'v2ray': '🔶 V2Ray'
    }
    
    current = protocol_names.get(protocol, "Не выбран")
    
    await query.edit_message_text(
        f"Выберите протокол:\n\n"
        f"Текущий: {current}\n\n"
        f"WireGuard - быстрый, стабильный\n"
        f"V2Ray - обход блокировок",
        reply_markup=get_protocol_selection_keyboard()
    )

async def select_protocol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Сохраняет выбор протокола"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    protocol = query.data.split('_')[-1]  # select_protocol_wireguard -> wireguard
    
    # Всегда сервер 1
    db.set_user_preferences(user_id, 1, protocol)
    
    protocol_names = {
        'wireguard': '🔷 WireGuard',
        'v2ray': '🔶 V2Ray'
    }
    
    await query.edit_message_text(
        f"Выбран протокол: {protocol_names[protocol]}",
        reply_markup=get_device_options_keyboard()
    )
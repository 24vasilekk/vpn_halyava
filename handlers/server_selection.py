from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_server_selection_keyboard, get_protocol_selection_keyboard, get_device_options_keyboard

async def choose_server_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Показывает выбор сервера"""
    query = update.callback_query
    await query.answer()
    
    # Получаем текущие настройки
    user_id = query.from_user.id
    server, protocol = db.get_user_preferences(user_id)
    
    server_names = {
        1: "🎯 Сервер 1 - TikTok (RU)",
        2: "⚡ Сервер 2 - Скорость (NL)"
    }
    
    current = server_names.get(server, "Не выбран")
    
    await query.edit_message_text(
        f"Выберите сервер:\n\n"
        f"Текущий: {current}\n\n"
        f"🎯 **Сервер 1 (Россия)** - работает TikTok\n"
        f"⚡ **Сервер 2 (Нидерланды)** - максимальная скорость",
        parse_mode='Markdown',
        reply_markup=get_server_selection_keyboard()
    )

async def select_server_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Сохраняет выбор сервера"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    server = int(query.data.split('_')[-1])  # select_server_1 -> 1
    
    # Получаем текущий протокол
    _, current_protocol = db.get_user_preferences(user_id)
    
    # V2Ray доступен только на сервере 1
    if server == 2 and current_protocol == 'v2ray':
        current_protocol = 'wireguard'
    
    # Сохраняем выбор
    db.set_user_preferences(user_id, server, current_protocol)
    
    server_names = {
        1: "🎯 Сервер 1 - TikTok (RU)",
        2: "⚡ Сервер 2 - Скорость (NL)"
    }
    
    await query.edit_message_text(
        f"✅ Выбран: {server_names[server]}\n\n"
        f"Протокол: {current_protocol.upper()}",
        reply_markup=get_device_options_keyboard()
    )

async def choose_protocol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Показывает выбор протокола"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    server, protocol = db.get_user_preferences(user_id)
    
    protocol_names = {
        'wireguard': '🔷 WireGuard',
        'v2ray': '🔶 V2Ray'
    }
    
    current = protocol_names.get(protocol, "Не выбран")
    
    await query.edit_message_text(
        f"Выберите протокол:\n\n"
        f"Текущий: {current}\n\n"
        f"🔷 **WireGuard** - быстрый, стабильный\n"
        f"🔶 **V2Ray** - обход блокировок (только Сервер 1)",
        parse_mode='Markdown',
        reply_markup=get_protocol_selection_keyboard()
    )

async def select_protocol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Сохраняет выбор протокола"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    protocol = query.data.split('_')[-1]  # select_protocol_wireguard -> wireguard
    
    # Получаем текущий сервер
    current_server, _ = db.get_user_preferences(user_id)
    
    # V2Ray доступен только на сервере 1
    if protocol == 'v2ray' and current_server != 1:
        await query.answer("⚠️ V2Ray доступен только на Сервере 1!", show_alert=True)
        current_server = 1
    
    # Сохраняем выбор
    db.set_user_preferences(user_id, current_server, protocol)
    
    protocol_names = {
        'wireguard': '🔷 WireGuard',
        'v2ray': '🔶 V2Ray'
    }
    
    await query.edit_message_text(
        f"✅ Выбран протокол: {protocol_names[protocol]}\n\n"
        f"Сервер: {'🎯 TikTok (RU)' if current_server == 1 else '⚡ Скорость (NL)'}",
        reply_markup=get_device_options_keyboard()
    )
import os
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_device_keyboard, get_device_options_keyboard, get_main_keyboard
from services.vpn_service import VPNService

async def setup_vpn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📱 Выберите ваше устройство:",
        reply_markup=get_device_keyboard()
    )

async def device_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    device = query.data.replace('device_', '')
    context.user_data['selected_device'] = device
    
    device_names = {
        'android': 'Android',
        'iphone': 'iPhone',
        'ipad': 'iPad',
        'ipod': 'iPod',
        'mac': 'Mac',
        'windows': 'Windows',
        'other': 'Другое устройство'
    }
    
    await query.edit_message_text(
        f"Вы выбрали: {device_names.get(device, 'Устройство')}\n\nВыберите опцию:",
        reply_markup=get_device_options_keyboard()
    )

async def install_app_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    device = context.user_data.get('selected_device', 'other')
    
    # Получаем выбранный протокол
    _, protocol = db.get_user_preferences(user_id)
    
    download_link = VPNService.get_app_download_link(device, protocol)
    
    app_name = "V2Ray" if protocol == 'v2ray' else "WireGuard"
    
    await query.edit_message_text(
        f"📥 Скачайте приложение {app_name}:\n\n{download_link}\n\n"
        f"После установки вернитесь и получите конфиг.",
        reply_markup=get_device_options_keyboard()
    )

async def get_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    subscription = db.get_active_subscription(user_id)
    
    if not subscription:
        await query.edit_message_text(
            "❌ У вас нет активной подписки.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Получаем настройки пользователя
    server, protocol = db.get_user_preferences(user_id)
    
    # Генерируем новый ключ с учётом выбора
    is_trial = subscription[6]
    vpn_key, user_uuid = await VPNService.generate_vpn_key(user_id, server, protocol, is_trial)
    
    if not vpn_key:
        await query.edit_message_text(
            "❌ Ошибка генерации ключа. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Обновляем ключ в БД
    db.cursor.execute('''
        UPDATE subscriptions 
        SET vpn_key = ?, user_uuid = ?
        WHERE user_id = ? AND is_active = 1
    ''', (vpn_key, user_uuid, user_id))
    db.connection.commit()
    
    server_name = "🎯 TikTok (RU)" if server == 1 else "⚡ Скорость (NL)"
    protocol_name = "V2Ray" if protocol == 'v2ray' else "WireGuard"
    
    if protocol == 'v2ray':
        # V2Ray - отправляем ссылку подписки
        await query.message.reply_text(
            f"🔑 Ваша подписка V2Ray\n\n"
            f"Сервер: {server_name}\n"
            f"Протокол: {protocol_name}\n\n"
            f"Ссылка подписки:\n`{vpn_key}`\n\n"
            f"📱 Скопируйте и добавьте в приложение V2Ray",
            parse_mode='Markdown'
        )
    else:
        # WireGuard - отправляем файл конфига
        config_filename = f"wireguard_user_{user_id}_s{server}.conf"
        
        with open(f"/tmp/{config_filename}", "w") as f:
            f.write(vpn_key)
        
        try:
            with open(f"/tmp/{config_filename}", "rb") as f:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=f,
                    filename=config_filename,
                    caption=f"🔑 Ваш конфиг WireGuard\n\n"
                           f"Сервер: {server_name}\n"
                           f"Протокол: {protocol_name}\n\n"
                           f"📱 Импортируйте этот файл в WireGuard"
                )
            
            os.remove(f"/tmp/{config_filename}")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            await query.message.reply_text(
                f"🔑 Ваш конфиг:\n\n```\n{vpn_key}\n```",
                parse_mode='Markdown'
            )
    
    await query.edit_message_text(
        "✅ Конфиг отправлен!",
        reply_markup=get_main_keyboard()
    )

async def recreate_config_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """НОВАЯ: Пересоздать конфиг для пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    subscription = db.get_active_subscription(user_id)
    
    if not subscription:
        await query.edit_message_text(
            "❌ У вас нет активной подписки.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Удалить старый конфиг и peer
    old_uuid = subscription[3]
    old_config_path = f"/root/wg0-client-{old_uuid}.conf"
    
    try:
        # Удалить файл
        if os.path.exists(old_config_path):
            os.remove(old_config_path)
        
        # Пересоздать с новыми настройками
        is_trial = subscription[6]
        vpn_key, user_uuid = await VPNService.generate_vpn_key(user_id, is_trial=is_trial)
        
        if vpn_key and user_uuid:
            # Обновить в БД
            db.cursor.execute('''
                UPDATE subscriptions 
                SET vpn_key = ?, user_uuid = ?
                WHERE user_id = ? AND is_active = 1
            ''', (vpn_key, user_uuid, user_id))
            db.connection.commit()
            
            await query.edit_message_text(
                "✅ Конфиг пересоздан с исправлениями!\n\n"
                "📥 Удалите старый конфиг из WireGuard и импортируйте новый.",
                reply_markup=get_device_options_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ Ошибка пересоздания конфига.",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        print(f"Error recreating config: {e}")
        await query.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_keyboard()
        )
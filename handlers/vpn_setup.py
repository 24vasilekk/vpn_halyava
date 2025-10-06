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

async def install_app_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    device = context.user_data.get('selected_device', 'other')
    download_link = VPNService.get_app_download_link(device)
    
    await query.edit_message_text(
        f"📥 Скачайте приложение WireGuard:\n\n{download_link}\n\nПосле установки вернитесь и получите конфиг.",
        reply_markup=get_device_options_keyboard()
    )

async def get_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    subscription = db.get_active_subscription(user_id)
    
    if subscription:
        vpn_key = subscription[2]
        config_filename = f"wireguard_user_{user_id}.conf"
        
        with open(f"/tmp/{config_filename}", "w") as f:
            f.write(vpn_key)
        
        try:
            with open(f"/tmp/{config_filename}", "rb") as f:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=f,
                    filename=config_filename,
                    caption="🔑 Ваш конфиг WireGuard\n\n"
                           "📱 Импортируйте этот файл в WireGuard"
                )
            
            import os
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
    else:
        await query.edit_message_text(
            "❌ У вас нет активной подписки.",
            reply_markup=get_main_keyboard()
        )

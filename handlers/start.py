from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_main_keyboard
from services.vpn_service import VPNService
from utils.referral import extract_referrer_id, generate_referral_link
from config import TRIAL_DURATION_DAYS

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    # Проверяем реферальную ссылку
    referrer_id = None
    if context.args:
        referrer_id = extract_referrer_id(context.args[0])
    
    # Добавляем пользователя в базу
    db.add_user(user_id, username, referrer_id)
    
    # Проверяем, есть ли активная подписка
    subscription = db.get_active_subscription(user_id)
    
    if not subscription:
        # Генерируем VPN ключ и UUID (с await, так как функция async)
        vpn_key, user_uuid = await VPNService.generate_vpn_key(user_id, is_trial=True)
        
        if vpn_key and user_uuid:
            # Активируем пробный период
            db.activate_trial(user_id, vpn_key, user_uuid)
            
            # Генерируем реферальную ссылку
            bot_username = context.bot.username
            ref_link = generate_referral_link(bot_username, user_id)
            
            message = f"""
🎉 Добро пожаловать в VPN бот!

✅ Ваша тестовая подписка на {TRIAL_DURATION_DAYS} дня активирована!

🎁 Пригласите друга и получите 35% с его покупки на баланс бота!

Ваша реферальная ссылка:
{ref_link}

Выберите действие:
            """
        else:
            message = """
❌ Произошла ошибка при активации пробного периода.
Пожалуйста, попробуйте позже или обратитесь в поддержку.

Выберите действие:
            """
    else:
        message = """
👋 С возвращением!

Выберите действие:
        """
    
    await update.message.reply_text(
        message,
        reply_markup=get_main_keyboard()
    )
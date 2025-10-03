from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
from keyboards import get_main_keyboard
from services.vpn_service import VPNService
from utils.referral import calculate_referral_bonus
from config import SUBSCRIPTION_DURATION_DAYS, SUBSCRIPTION_PRICE_STARS
import uuid

async def stars_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Генерируем уникальный payload
    payment_id = str(uuid.uuid4())
    context.user_data['pending_stars_payment'] = payment_id
    
    # Сохраняем платеж в базу
    db.add_payment(user_id, SUBSCRIPTION_PRICE_STARS, payment_id, 'stars', 'pending')
    
    # Создаем инвойс для оплаты Stars
    title = "Подписка VPN на 30 дней"
    description = f"Подписка на {SUBSCRIPTION_DURATION_DAYS} дней с поддержкой 3 устройств"
    payload = payment_id
    currency = "XTR"  # Telegram Stars
    prices = [LabeledPrice("Подписка VPN", SUBSCRIPTION_PRICE_STARS)]
    
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # Пустой токен для Stars
        currency=currency,
        prices=prices
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает pre-checkout запрос перед оплатой
    """
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """
    Обрабатывает успешную оплату Stars
    """
    user_id = update.effective_user.id
    payment_info = update.message.successful_payment
    payload = payment_info.invoice_payload
    
    # Проверяем платеж в базе
    payment = db.get_payment(payload)
    
    if payment and payment[4] == 'pending':  # status column
        # Генерируем новый ключ
        vpn_key = VPNService.generate_vpn_key(user_id)
        
        # Активируем подписку
        db.add_subscription(user_id, vpn_key, SUBSCRIPTION_DURATION_DAYS)
        
        # Обновляем статус платежа
        db.update_payment_status(payload, 'paid')
        
        # Начисляем бонус рефереру
        user_data = db.get_user(user_id)
        if user_data and user_data[2]:  # referrer_id
            referrer_id = user_data[2]
            bonus = calculate_referral_bonus(150)  # Считаем от рублевого эквивалента
            db.update_balance(referrer_id, bonus)
        
        # Очищаем pending payment
        context.user_data.pop('pending_stars_payment', None)
        
        await update.message.reply_text(
            f"✅ Оплата Stars успешно обработана!\n\n"
            f"🎉 Подписка активирована на {SUBSCRIPTION_DURATION_DAYS} дней!\n\n"
            f"Используйте кнопку 'Настроить VPN' для получения ключа.",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка обработки платежа. Обратитесь в поддержку.",
            reply_markup=get_main_keyboard()
        )
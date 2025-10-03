from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_crypto_currency_keyboard, get_main_keyboard
from services.cryptobot_service import CryptoPaymentService
from services.vpn_service import VPNService
from utils.referral import calculate_referral_bonus
from config import SUBSCRIPTION_DURATION_DAYS, SUBSCRIPTION_PRICE_USDT

async def crypto_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "₿ Выберите криптовалюту для оплаты:",
        reply_markup=get_crypto_currency_keyboard()
    )

async def crypto_currency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    query = update.callback_query
    await query.answer()
    
    currency = query.data.replace('crypto_', '')
    user_id = query.from_user.id
    
    # Конвертируем сумму в зависимости от валюты
    amount_map = {
        'USDT': SUBSCRIPTION_PRICE_USDT,
        'USDC': SUBSCRIPTION_PRICE_USDT,
        'BTC': 0.000015,  # Примерный эквивалент
        'ETH': 0.00045,   # Примерный эквивалент
        'TON': 0.3        # Примерный эквивалент
    }
    
    amount = amount_map.get(currency, SUBSCRIPTION_PRICE_USDT)
    
    # Создаем платеж через CryptoBot
    crypto_service = CryptoPaymentService()
    payment_url, payload_id, invoice_id = await crypto_service.create_invoice(
        user_id, 
        amount, 
        currency
    )
    
    if not payment_url:
        await query.edit_message_text(
            "❌ Ошибка создания платежа. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        await crypto_service.close()
        return
    
    # Сохраняем платеж в базу
    db.add_payment(user_id, amount, payload_id, 'cryptobot', 'pending')
    
    # Сохраняем invoice_id для проверки
    context.user_data['pending_crypto_invoice'] = invoice_id
    context.user_data['pending_crypto_payload'] = payload_id
    
    await query.edit_message_text(
        f"₿ Оплата подписки: {amount} {currency}\n\n"
        f"📅 Срок: {SUBSCRIPTION_DURATION_DAYS} дней\n"
        f"📱 Устройства: до 3-х\n\n"
        f"Перейдите по ссылке для оплаты:\n{payment_url}\n\n"
        f"После оплаты нажмите /check_crypto_payment для проверки.",
        reply_markup=get_main_keyboard()
    )
    
    await crypto_service.close()

async def check_crypto_payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    user_id = update.effective_user.id
    invoice_id = context.user_data.get('pending_crypto_invoice')
    payload_id = context.user_data.get('pending_crypto_payload')
    
    if not invoice_id:
        await update.message.reply_text(
            "❌ Нет ожидающих крипто-платежей.",
            reply_markup=get_main_keyboard()
        )
        return
    
    crypto_service = CryptoPaymentService()
    is_paid = await crypto_service.check_invoice(invoice_id)
    
    if is_paid:
        # Генерируем новый ключ
        vpn_key = VPNService.generate_vpn_key(user_id)
        
        # Активируем подписку
        db.add_subscription(user_id, vpn_key, SUBSCRIPTION_DURATION_DAYS)
        
        # Обновляем статус платежа
        db.update_payment_status(payload_id, 'paid')
        
        # Начисляем бонус рефереру
        user_data = db.get_user(user_id)
        if user_data and user_data[2]:  # referrer_id
            referrer_id = user_data[2]
            bonus = calculate_referral_bonus(150)  # Считаем от рублевого эквивалента
            db.update_balance(referrer_id, bonus)
        
        # Очищаем pending payment
        context.user_data.pop('pending_crypto_invoice', None)
        context.user_data.pop('pending_crypto_payload', None)
        
        await update.message.reply_text(
            f"✅ Крипто-платеж успешно обработан!\n\n"
            f"🎉 Подписка активирована на {SUBSCRIPTION_DURATION_DAYS} дней!\n\n"
            f"Используйте кнопку 'Настроить VPN' для получения ключа.",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "⏳ Платеж еще не обработан. Пожалуйста, подождите немного и попробуйте снова.",
            reply_markup=get_main_keyboard()
        )
    
    await crypto_service.close()
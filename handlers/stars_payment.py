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
    """Обрабатывает pre-checkout запрос перед оплатой"""
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Обрабатывает успешную оплату Stars"""
    user_id = update.effective_user.id
    payment_info = update.message.successful_payment
    payload = payment_info.invoice_payload
    
    print(f"DEBUG: Обрабатываю платеж. User: {user_id}, Payload: {payload}")
    
    # Проверяем платеж в базе
    payment = db.get_payment(payload)
    print(f"DEBUG: Payment из БД: {payment}")
    
    if payment and payment[5] == 'pending':
        # Получаем настройки пользователя
        server, protocol = db.get_user_preferences(user_id)
        
        # Проверяем есть ли уже подписка
        existing_sub = db.get_active_subscription(user_id)
        print(f"DEBUG: Existing subscription: {existing_sub}")
        
        if existing_sub:
            print(f"DEBUG: Продлеваю подписку...")
            # Продлеваем существующую подписку на 30 дней
            from datetime import datetime, timedelta
            current_end_str = existing_sub[5]
            current_end = datetime.fromisoformat(current_end_str)
            
            if current_end < datetime.now():
                new_end = datetime.now() + timedelta(days=SUBSCRIPTION_DURATION_DAYS)
            else:
                new_end = current_end + timedelta(days=SUBSCRIPTION_DURATION_DAYS)
            
            # Генерируем новый ключ с учётом выбора
            vpn_key, user_uuid = await VPNService.generate_vpn_key(user_id, server, protocol, is_trial=False)
            
            if vpn_key and user_uuid:
                # Обновляем подписку
                db.cursor.execute('''
                    UPDATE subscriptions
                    SET end_date = ?, is_trial = 0, vpn_key = ?, user_uuid = ?
                    WHERE user_id = ? AND is_active = 1
                ''', (new_end.isoformat(), vpn_key, user_uuid, user_id))
                db.connection.commit()
        else:
            print(f"DEBUG: Подписки нет, создаю новую...")
            # Создаем новую подписку с выбранными настройками
            vpn_key, user_uuid = await VPNService.generate_vpn_key(user_id, server, protocol, is_trial=False)
            if vpn_key and user_uuid:
                db.add_subscription(user_id, vpn_key, user_uuid, SUBSCRIPTION_DURATION_DAYS)
        
        # Обновляем статус платежа
        db.update_payment_status(payload, 'paid')
        
        # Начисляем бонус рефереру
        user_data = db.get_user(user_id)
        if user_data and user_data[2]:
            referrer_id = user_data[2]
            bonus = calculate_referral_bonus(150)
            db.update_balance(referrer_id, bonus)
        
        context.user_data.pop('pending_stars_payment', None)
        
        protocol_name = "V2Ray" if protocol == 'v2ray' else "WireGuard"
        server_name = "🎯 TikTok (RU)" if server == 1 else "⚡ Скорость (NL)"
        
        await update.message.reply_text(
            f"✅ Оплата Stars успешно обработана!\n\n"
            f"🎉 Подписка продлена на {SUBSCRIPTION_DURATION_DAYS} дней!\n\n"
            f"Сервер: {server_name}\n"
            f"Протокол: {protocol_name}\n\n"
            f"Используйте кнопку 'Настроить VPN' для получения ключа.",
            reply_markup=get_main_keyboard()
        )
    else:
        print(f"DEBUG: Платеж не найден или не pending")
        await update.message.reply_text(
            "❌ Ошибка обработки платежа. Обратитесь в поддержку.",
            reply_markup=get_main_keyboard()
        )
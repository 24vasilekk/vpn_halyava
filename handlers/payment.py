from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_payment_keyboard, get_main_keyboard
from services.yookassa_service import YooKassaService
from services.vpn_service import VPNService
from utils.referral import calculate_referral_bonus
from config import SUBSCRIPTION_PRICE, SUBSCRIPTION_DURATION_DAYS

async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💳 Выберите способ оплаты подписки:",
        reply_markup=get_payment_keyboard()
    )

async def pay_yookassa_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        # Создаем платеж через ЮКассу
        payment_url, payment_id = YooKassaService.create_payment(user_id, SUBSCRIPTION_PRICE)
        
        if not payment_url:
            await query.edit_message_text(
                "❌ Ошибка создания платежа. Проверьте настройки ЮКассы в .env файле.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Сохраняем платеж в базу
        db.add_payment(user_id, SUBSCRIPTION_PRICE, payment_id, 'yookassa', 'pending')
        
        # Сохраняем payment_id в контекст для проверки
        context.user_data['pending_payment_id'] = payment_id
        
        await query.edit_message_text(
            f"💳 Оплата подписки: {SUBSCRIPTION_PRICE}₽\n\n"
            f"📅 Срок: {SUBSCRIPTION_DURATION_DAYS} дней\n"
            f"📱 Устройства: до 3-х\n\n"
            f"Перейдите по ссылке для оплаты:\n{payment_url}\n\n"
            f"После оплаты нажмите /check_payment для проверки.",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        print(f"Error in pay_yookassa_callback: {e}")
        await query.edit_message_text(
            f"❌ Ошибка: {str(e)}\n\nПроверьте настройки ЮКассы.",
            reply_markup=get_main_keyboard()
        )

async def check_payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    user_id = update.effective_user.id
    payment_id = context.user_data.get('pending_payment_id')
    
    if not payment_id:
        await update.message.reply_text(
            "❌ Нет ожидающих платежей.",
            reply_markup=get_main_keyboard()
        )
        return
    
    try:
        is_paid = YooKassaService.check_payment(payment_id)
        
        if is_paid:
            # Генерируем новый ключ
            vpn_key = VPNService.generate_vpn_key(user_id)
            
            # Активируем подписку
            db.add_subscription(user_id, vpn_key, SUBSCRIPTION_DURATION_DAYS)
            
            # Обновляем статус платежа
            db.update_payment_status(payment_id, 'paid')
            
            # Начисляем бонус рефереру
            user_data = db.get_user(user_id)
            if user_data and user_data[2]:  # referrer_id
                referrer_id = user_data[2]
                bonus = calculate_referral_bonus(SUBSCRIPTION_PRICE)
                db.update_balance(referrer_id, bonus)
            
            # Очищаем pending payment
            context.user_data.pop('pending_payment_id', None)
            
            await update.message.reply_text(
                f"✅ Платеж успешно обработан!\n\n"
                f"🎉 Подписка активирована на {SUBSCRIPTION_DURATION_DAYS} дней!\n\n"
                f"Используйте кнопку 'Настроить VPN' для получения ключа.",
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "⏳ Платеж еще не обработан. Пожалуйста, подождите немного и попробуйте снова.",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        print(f"Error in check_payment_command: {e}")
        await update.message.reply_text(
            f"❌ Ошибка проверки платежа: {str(e)}",
            reply_markup=get_main_keyboard()
        )

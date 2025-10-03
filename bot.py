import logging
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    PreCheckoutQueryHandler, 
    MessageHandler, 
    filters
)
from config import TELEGRAM_BOT_TOKEN
from database import Database
from handlers.start import start_command
from handlers.vpn_setup import (
    setup_vpn_callback, 
    device_selection_callback, 
    install_app_callback, 
    get_key_callback
)
from handlers.payment import (
    payment_callback, 
    pay_yookassa_callback, 
    check_payment_command
)
from handlers.crypto_payment import (
    crypto_payment_callback, 
    crypto_currency_callback, 
    check_crypto_payment_command
)
from handlers.stars_payment import (
    stars_payment_callback, 
    precheckout_callback, 
    successful_payment_callback
)
from handlers.help import (
    help_callback, 
    terms_callback, 
    main_menu_callback
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    """
    Главная функция запуска бота
    """
    # Инициализация базы данных
    db = Database()
    logger.info("База данных инициализирована")
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    logger.info("Приложение создано")
    
    # ========================================
    # ОБРАБОТЧИКИ КОМАНД
    # ========================================
    
    # Команда /start - приветствие и активация пробного периода
    application.add_handler(
        CommandHandler("start", lambda u, c: start_command(u, c, db))
    )
    
    # Команда /check_payment - проверка оплаты через ЮMoney
    application.add_handler(
        CommandHandler("check_payment", lambda u, c: check_payment_command(u, c, db))
    )
    
    # Команда /check_crypto_payment - проверка крипто-платежа
    application.add_handler(
        CommandHandler("check_crypto_payment", lambda u, c: check_crypto_payment_command(u, c, db))
    )
    
    logger.info("Обработчики команд добавлены")
    
    # ========================================
    # ОБРАБОТЧИКИ CALLBACK КНОПОК - VPN НАСТРОЙКА
    # ========================================
    
    # Кнопка "Настроить VPN"
    application.add_handler(
        CallbackQueryHandler(setup_vpn_callback, pattern='^setup_vpn$')
    )
    
    # Выбор устройства (Android, iPhone, iPad, etc.)
    application.add_handler(
        CallbackQueryHandler(device_selection_callback, pattern='^device_')
    )
    
    # Кнопка "Установить приложение V2RayTun"
    application.add_handler(
        CallbackQueryHandler(install_app_callback, pattern='^install_app$')
    )
    
    # Кнопка "Получить ключ"
    application.add_handler(
        CallbackQueryHandler(lambda u, c: get_key_callback(u, c, db), pattern='^get_key$')
    )
    
    logger.info("Обработчики VPN настройки добавлены")
    
    # ========================================
    # ОБРАБОТЧИКИ CALLBACK КНОПОК - ПЛАТЕЖИ
    # ========================================
    
    # Кнопка "Оплатить подписку" - выбор способа оплаты
    application.add_handler(
        CallbackQueryHandler(payment_callback, pattern='^pay_subscription$')
    )
    
    # Оплата через ЮMoney
    # Оплата через ЮКассу
    application.add_handler(
        CallbackQueryHandler(lambda u, c: pay_yookassa_callback(u, c, db), pattern='^pay_yookassa$')
    )
    
    logger.info("Обработчики платежей ЮMoney добавлены")
    
    # ========================================
    # ОБРАБОТЧИКИ CALLBACK КНОПОК - TELEGRAM STARS
    # ========================================
    
    # Оплата через Telegram Stars
    application.add_handler(
        CallbackQueryHandler(lambda u, c: stars_payment_callback(u, c, db), pattern='^pay_stars$')
    )
    
    # Pre-checkout запрос (обязательно для Stars)
    application.add_handler(
        PreCheckoutQueryHandler(precheckout_callback)
    )
    
    # Успешная оплата Stars
    application.add_handler(
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT, 
            lambda u, c: successful_payment_callback(u, c, db)
        )
    )
    
    logger.info("Обработчики Telegram Stars добавлены")
    
    # ========================================
    # ОБРАБОТЧИКИ CALLBACK КНОПОК - КРИПТОВАЛЮТЫ
    # ========================================
    
    # Кнопка "Оплатить криптой" - выбор криптовалюты
    application.add_handler(
        CallbackQueryHandler(crypto_payment_callback, pattern='^pay_crypto$')
    )
    
    # Выбор конкретной криптовалюты (BTC, ETH, USDT, etc.)
    application.add_handler(
        CallbackQueryHandler(lambda u, c: crypto_currency_callback(u, c, db), pattern='^crypto_')
    )
    
    logger.info("Обработчики CryptoBot добавлены")
    
    # ========================================
    # ОБРАБОТЧИКИ CALLBACK КНОПОК - ПОМОЩЬ И ПРАВИЛА
    # ========================================
    
    # Кнопка "Нужна помощь"
    application.add_handler(
        CallbackQueryHandler(help_callback, pattern='^help$')
    )
    
    # Кнопка "Правила использования"
    application.add_handler(
        CallbackQueryHandler(terms_callback, pattern='^terms$')
    )
    
    # Кнопка "Главное меню" (возврат в главное меню)
    application.add_handler(
        CallbackQueryHandler(main_menu_callback, pattern='^main_menu$')
    )
    
    logger.info("Обработчики помощи и правил добавлены")
    
    # ========================================
    # ОБРАБОТЧИК ОШИБОК
    # ========================================
    
    async def error_handler(update: object, context: object) -> None:
        """
        Обработчик ошибок для логирования
        """
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Опционально: отправка уведомления администратору
        try:
            if update and hasattr(update, 'effective_user'):
                user_id = update.effective_user.id
                logger.error(f"Error occurred for user {user_id}")
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Обработчик ошибок добавлен")
    
    # ========================================
    # ЗАПУСК БОТА
    # ========================================
    
    logger.info("=" * 50)
    logger.info("🚀 VPN Telegram Bot запущен!")
    logger.info("=" * 50)
    logger.info("Ожидание сообщений от пользователей...")
    
    # Запуск polling (постоянное получение обновлений от Telegram)
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True  # Игнорировать старые обновления при запуске
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        raise
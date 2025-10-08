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
from handlers.vpn_setup import (
    setup_vpn_callback, 
    device_selection_callback, 
    install_app_callback, 
    get_key_callback,
    recreate_config_callback  # ← ДОБАВИТЬ
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
from handlers.admin import (
    admin_command,
    admin_stats_callback,
    admin_trial_users_callback,
    admin_paid_users_callback,
    admin_recent_payments_callback,
    admin_expiring_soon_callback
)

from handlers.server_selection import (
    choose_server_callback,
    select_server_callback,
    choose_protocol_callback,
    select_protocol_callback
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
    
    # Команда /check_payment - проверка оплаты через ЮКассу
    application.add_handler(
        CommandHandler("check_payment", lambda u, c: check_payment_command(u, c, db))
    )
    
    # Команда /admin - админ-панель
    application.add_handler(
        CommandHandler("admin", lambda u, c: admin_command(u, c, db))
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
    
    # Кнопка "Установить приложение WireGuard"
    application.add_handler(
        CallbackQueryHandler(install_app_callback, pattern='^install_app$')
    )
    
    # Кнопка "Получить ключ"
    application.add_handler(
        CallbackQueryHandler(lambda u, c: get_key_callback(u, c, db), pattern='^get_key$')
    )
    
    # Кнопка "Обновить конфиг"
    application.add_handler(
        CallbackQueryHandler(lambda u, c: recreate_config_callback(u, c, db), pattern='^recreate_config$')
    )

    logger.info("Обработчики VPN настройки добавлены")
    
    # ========================================
    # ОБРАБОТЧИКИ ВЫБОРА СЕРВЕРА И ПРОТОКОЛА
    # ========================================
    
    # Кнопка "Выбрать сервер"
    application.add_handler(
        CallbackQueryHandler(lambda u, c: choose_server_callback(u, c, db), pattern='^choose_server$')
    )
    
    # Выбор сервера (1 или 2)
    application.add_handler(
        CallbackQueryHandler(lambda u, c: select_server_callback(u, c, db), pattern='^select_server_')
    )
    
    # Кнопка "Выбрать протокол"
    application.add_handler(
        CallbackQueryHandler(lambda u, c: choose_protocol_callback(u, c, db), pattern='^choose_protocol$')
    )
    
    # Выбор протокола (wireguard или v2ray)
    application.add_handler(
        CallbackQueryHandler(lambda u, c: select_protocol_callback(u, c, db), pattern='^select_protocol_')
    )
    
    logger.info("Обработчики выбора сервера и протокола добавлены")
    
    # ========================================
    # ОБРАБОТЧИКИ CALLBACK КНОПОК - ПЛАТЕЖИ
    # ========================================
    
    # Кнопка "Оплатить подписку" - выбор способа оплаты
    application.add_handler(
        CallbackQueryHandler(payment_callback, pattern='^pay_subscription$')
    )
    
    # Оплата через ЮКассу
    application.add_handler(
        CallbackQueryHandler(lambda u, c: pay_yookassa_callback(u, c, db), pattern='^pay_yookassa$')
    )
    
    logger.info("Обработчики платежей ЮКассу добавлены")
    
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
    # ОБРАБОТЧИКИ CALLBACK КНОПОК - АДМИН ПАНЕЛЬ
    # ========================================
    
    # Админ панель - статистика
    application.add_handler(
        CallbackQueryHandler(lambda u, c: admin_stats_callback(u, c, db), pattern='^admin_stats$')
    )
    
    # Админ панель - пробные пользователи
    application.add_handler(
        CallbackQueryHandler(lambda u, c: admin_trial_users_callback(u, c, db), pattern='^admin_trial_users$')
    )
    
    # Админ панель - платные пользователи
    application.add_handler(
        CallbackQueryHandler(lambda u, c: admin_paid_users_callback(u, c, db), pattern='^admin_paid_users$')
    )
    
    # Админ панель - последние платежи
    application.add_handler(
        CallbackQueryHandler(lambda u, c: admin_recent_payments_callback(u, c, db), pattern='^admin_recent_payments$')
    )
    
    # Админ панель - истекающие подписки (НОВАЯ)
    application.add_handler(
        CallbackQueryHandler(lambda u, c: admin_expiring_soon_callback(u, c, db), pattern='^admin_expiring_soon$')
    )
    
    logger.info("Обработчики админ-панели добавлены")
    
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
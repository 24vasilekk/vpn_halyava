from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚙️ Настроить VPN", callback_data='setup_vpn')],
        [InlineKeyboardButton("💳 Оплатить подписку", callback_data='pay_subscription')],
        [InlineKeyboardButton("❓ Нужна помощь", callback_data='help')],
        [InlineKeyboardButton("📋 Правила использования", callback_data='terms')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_device_keyboard():
    keyboard = [
        [InlineKeyboardButton("📱 Android", callback_data='device_android')],
        [InlineKeyboardButton("📱 iPhone", callback_data='device_iphone')],
        [InlineKeyboardButton("📱 iPad", callback_data='device_ipad')],
        [InlineKeyboardButton("📱 iPod", callback_data='device_ipod')],
        [InlineKeyboardButton("💻 Mac", callback_data='device_mac')],
        [InlineKeyboardButton("💻 Windows", callback_data='device_windows')],
        [InlineKeyboardButton("🖥 Другое устройство", callback_data='device_other')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_device_options_keyboard():
    keyboard = [
        [InlineKeyboardButton("📥 Установить приложение V2RayTun", callback_data='install_app')],
        [InlineKeyboardButton("🔑 Получить ключ", callback_data='get_key')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 149₽/месяц (Банковская карта)", callback_data='pay_yookassa')],
        [InlineKeyboardButton("⭐ 159 Stars/месяц", callback_data='pay_stars')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Общая статистика", callback_data='admin_stats')],
        [InlineKeyboardButton("🎁 Пробные пользователи", callback_data='admin_trial_users')],
        [InlineKeyboardButton("💎 Платные пользователи", callback_data='admin_paid_users')],
        [InlineKeyboardButton("💳 Последние платежи", callback_data='admin_recent_payments')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)
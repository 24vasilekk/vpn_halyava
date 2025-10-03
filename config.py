import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# ЮКасса (YooKassa)
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

# V2Ray
V2RAY_SERVER_IP = os.getenv('V2RAY_SERVER_IP')
V2RAY_PORT = os.getenv('V2RAY_PORT', '443')

# Подписка
SUBSCRIPTION_PRICE = 149
SUBSCRIPTION_PRICE_STARS = 159
SUBSCRIPTION_DURATION_DAYS = 30
TRIAL_DURATION_DAYS = 3
MAX_DEVICES = 3

# Реферальная программа
REFERRAL_BONUS_PERCENT = 35

# Telegra.ph
TELEGRAPH_HELP_LINK = os.getenv('TELEGRA_PH_LINK', 'https://telegra.ph/')

# Правила использования
TERMS_OF_USE = """
📋 Условия пользования сервисом:

❌ Запрещается использование сервиса для деятельности противоречащей законодательству Российской Федерации
❌ Запрещается использование сервиса для скачивания в torrent сетях
❌ Любые правонарушения совершенные через наш сервис будут преследоваться по законам Российской Федерации
❌ Логины нарушителей будут удаляться без предупреждения
❗️Услуги предоставляемые сервисом являются невозвратными.
"""
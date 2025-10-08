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

# X-UI Panel
XUI_PANEL_URL = os.getenv('XUI_PANEL_URL')
XUI_USERNAME = os.getenv('XUI_USERNAME')
XUI_PASSWORD = os.getenv('XUI_PASSWORD')

# Подписка
SUBSCRIPTION_PRICE = 5
SUBSCRIPTION_PRICE_STARS = 5
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
# В конец файла добавь:

# Marzban API (Сервер 1 - TikTok)
MARZBAN_API_URL = "https://plazavpn.ru:8000"
MARZBAN_API_USERNAME = "apibot"
MARZBAN_API_PASSWORD = os.getenv('MARZBAN_API_PASSWORD')  # Добавь в .env

# Серверы
SERVER_1_IP = "81.200.157.217"  # Россия - TikTok
SERVER_1_WG_PORT = "51820"
SERVER_1_WG_PUBLIC_KEY = "1i1KhfPy8dlFCXs5fbsqq+C19aqY9Yb1Dk3iHgRi4Xo="
SERVER_1_WG_ENDPOINT = f"{SERVER_1_IP}:{SERVER_1_WG_PORT}"

SERVER_2_IP = "72.56.69.53"  # Нидерланды - Скорость
SERVER_2_WG_PORT = "51820"
SERVER_2_WG_PUBLIC_KEY = "njg2vVf0idKU2Ifame+QAjR67VlXfpk3shxXHOo4hlU="
SERVER_2_WG_ENDPOINT = f"{SERVER_2_IP}:{SERVER_2_WG_PORT}"
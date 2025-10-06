from config import REFERRAL_BONUS_PERCENT, SUBSCRIPTION_PRICE

def calculate_referral_bonus(amount=SUBSCRIPTION_PRICE):
    """
    Рассчитывает реферальный бонус
    """
    return amount * (REFERRAL_BONUS_PERCENT / 100)

def extract_referrer_id(start_param):
    """
    Извлекает ID реферера из параметра start
    """
    if start_param and start_param.startswith('ref_'):
        try:
            return int(start_param.replace('ref_', ''))
        except ValueError:
            return None
    return None

def generate_referral_link(bot_username, user_id):
    """
    Генерирует реферальную ссылку
    """
    return f"https://t.me/{bot_username}?start=ref_{user_id}"
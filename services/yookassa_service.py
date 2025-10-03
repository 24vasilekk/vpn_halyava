from yookassa import Configuration, Payment
import uuid
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, SUBSCRIPTION_PRICE

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

class YooKassaService:
    @staticmethod
    def create_payment(user_id, amount=SUBSCRIPTION_PRICE):
        """
        Создает платеж через ЮКассу
        """
        payment_id = str(uuid.uuid4())
        
        try:
            payment = Payment.create({
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://t.me/plazavpn_bot"
                },
                "capture": True,
                "description": f"Подписка VPN на 30 дней для пользователя {user_id}",
                "metadata": {
                    "user_id": user_id
                }
            }, payment_id)
            
            return payment.confirmation.confirmation_url, payment.id
        except Exception as e:
            print(f"Error creating YooKassa payment: {e}")
            return None, None
    
    @staticmethod
    def check_payment(payment_id):
        """
        Проверяет статус платежа
        """
        try:
            payment = Payment.find_one(payment_id)
            return payment.status == "succeeded"
        except Exception as e:
            print(f"Error checking payment: {e}")
            return False
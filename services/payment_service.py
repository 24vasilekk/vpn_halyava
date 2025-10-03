from yoomoney import Quickpay, Client
from config import YOOMONEY_TOKEN, YOOMONEY_WALLET, SUBSCRIPTION_PRICE
import uuid

class PaymentService:
    def __init__(self):
        self.token = YOOMONEY_TOKEN
        self.wallet = YOOMONEY_WALLET
    
    def create_payment(self, user_id, amount=SUBSCRIPTION_PRICE):
        """
        Создает платежную форму ЮMoney
        """
        payment_id = str(uuid.uuid4())
        
        quickpay = Quickpay(
            receiver=self.wallet,
            quickpay_form="shop",
            targets=f"Подписка VPN на 30 дней",
            paymentType="SB",
            sum=amount,
            label=payment_id
        )
        
        return quickpay.redirected_url, payment_id
    
    def check_payment(self, payment_id):
        """
        Проверяет статус платежа
        """
        try:
            client = Client(self.token)
            history = client.operation_history(label=payment_id)
            
            for operation in history.operations:
                if operation.label == payment_id and operation.status == "success":
                    return True
            return False
        except Exception as e:
            print(f"Error checking payment: {e}")
            return False
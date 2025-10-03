from aiocryptopay import AioCryptoPay, Networks
from config import CRYPTOBOT_TOKEN, SUBSCRIPTION_PRICE_USDT
import uuid

class CryptoPaymentService:
    def __init__(self):
        self.crypto = AioCryptoPay(token=CRYPTOBOT_TOKEN, network=Networks.MAIN_NET)
    
    async def create_invoice(self, user_id, amount=SUBSCRIPTION_PRICE_USDT, currency='USDT'):
        """
        Создает счет для оплаты через CryptoBot
        """
        try:
            invoice_id = str(uuid.uuid4())
            
            invoice = await self.crypto.create_invoice(
                asset=currency,
                amount=amount,
                description=f"Подписка VPN на 30 дней",
                payload=invoice_id
            )
            
            return invoice.bot_invoice_url, invoice_id, invoice.invoice_id
        except Exception as e:
            print(f"Error creating crypto invoice: {e}")
            return None, None, None
    
    async def check_invoice(self, invoice_id):
        """
        Проверяет статус платежа
        """
        try:
            invoices = await self.crypto.get_invoices(invoice_ids=invoice_id)
            
            if invoices and len(invoices) > 0:
                invoice = invoices[0]
                if invoice.status == "paid":
                    return True
            return False
        except Exception as e:
            print(f"Error checking invoice: {e}")
            return False
    
    async def get_balance(self):
        """
        Получает баланс кошелька CryptoBot
        """
        try:
            balance = await self.crypto.get_balance()
            return balance
        except Exception as e:
            print(f"Error getting balance: {e}")
            return None
    
    async def close(self):
        """
        Закрывает соединение
        """
        await self.crypto.close()
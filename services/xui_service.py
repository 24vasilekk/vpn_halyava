import aiohttp
import json
from config import XUI_PANEL_URL, XUI_USERNAME, XUI_PASSWORD

class XUIService:
    def __init__(self):
        self.panel_url = XUI_PANEL_URL
        self.username = XUI_USERNAME
        self.password = XUI_PASSWORD
        self.session = None
        self.cookie = None
    
    async def login(self):
        """Авторизация в панели X-UI"""
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {
                    'username': self.username,
                    'password': self.password
                }
                async with session.post(
                    f"{self.panel_url}/login", 
                    data=login_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('success'):
                            # Сохраняем cookies для последующих запросов
                            cookies = resp.cookies
                            return cookies
            return None
        except Exception as e:
            print(f"Error logging into X-UI: {e}")
            return None
    
    async def get_inbound_id(self, cookies):
        """Получает ID первого inbound для добавления клиентов"""
        try:
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.post(
                    f"{self.panel_url}/panel/api/inbounds/list",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('success') and result.get('obj'):
                            # Берем первый inbound
                            inbounds = result['obj']
                            if inbounds and len(inbounds) > 0:
                                return inbounds[0]['id']
            return None
        except Exception as e:
            print(f"Error getting inbound ID: {e}")
            return None
    
    async def add_client(self, user_id, uuid, email, expiry_time=0):
        """
        Добавляет клиента в X-UI панель
        
        Args:
            user_id: ID пользователя Telegram
            uuid: UUID для V2Ray
            email: Email клиента (обычно user_id)
            expiry_time: Время истечения в миллисекундах (0 = без ограничений)
        
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            # Авторизуемся
            cookies = await self.login()
            if not cookies:
                print("Failed to login to X-UI")
                return False
            
            # Получаем ID inbound
            inbound_id = await self.get_inbound_id(cookies)
            if not inbound_id:
                print("Failed to get inbound ID")
                return False
            
            # Формируем данные клиента
            client_data = {
                "id": inbound_id,
                "settings": json.dumps({
                    "clients": [{
                        "id": uuid,
                        "email": email,
                        "totalGB": 0,  # 0 = без ограничений
                        "expiryTime": expiry_time,
                        "enable": True,
                        "tgId": str(user_id),
                        "subId": ""
                    }]
                })
            }
            
            # Отправляем запрос на добавление клиента
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.post(
                    f"{self.panel_url}/panel/api/inbounds/addClient",
                    json=client_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('success'):
                            print(f"✅ Client {email} added successfully to X-UI")
                            return True
                        else:
                            print(f"❌ Failed to add client: {result.get('msg')}")
                            return False
            
            return False
        except Exception as e:
            print(f"Error adding client to X-UI: {e}")
            return False
    
    async def delete_client(self, user_id, uuid):
        """
        Удаляет клиента из X-UI панели
        
        Args:
            user_id: ID пользователя Telegram
            uuid: UUID клиента
        
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            # Авторизуемся
            cookies = await self.login()
            if not cookies:
                return False
            
            # Получаем ID inbound
            inbound_id = await self.get_inbound_id(cookies)
            if not inbound_id:
                return False
            
            # Формируем данные для удаления
            delete_data = {
                "id": inbound_id,
                "uuid": uuid
            }
            
            # Отправляем запрос на удаление
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.post(
                    f"{self.panel_url}/panel/api/inbounds/delClient/{uuid}",
                    json=delete_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('success'):
                            print(f"✅ Client {uuid} deleted successfully from X-UI")
                            return True
            
            return False
        except Exception as e:
            print(f"Error deleting client from X-UI: {e}")
            return False
    
    async def get_client_traffic(self, email):
        """
        Получает статистику трафика клиента
        
        Args:
            email: Email клиента
        
        Returns:
            dict: Статистика клиента или None
        """
        try:
            cookies = await self.login()
            if not cookies:
                return None
            
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.get(
                    f"{self.panel_url}/panel/api/inbounds/getClientTraffics/{email}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('success'):
                            return result.get('obj')
            
            return None
        except Exception as e:
            print(f"Error getting client traffic: {e}")
            return None
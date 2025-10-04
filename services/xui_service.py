import aiohttp
import json
from config import XUI_PANEL_URL, XUI_USERNAME, XUI_PASSWORD

print(f"🔍 XUI Service loaded. Panel URL: {XUI_PANEL_URL}")

class XUIService:
    def __init__(self):
        self.panel_url = XUI_PANEL_URL
        self.username = XUI_USERNAME
        self.password = XUI_PASSWORD
    
    async def login(self):
        """Авторизация в панели 3X-UI"""
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
                            cookies = resp.cookies
                            print("✅ Successfully logged into 3X-UI")
                            return cookies
                    print(f"❌ Login failed: status {resp.status}")
            return None
        except Exception as e:
            print(f"❌ Error logging into 3X-UI: {e}")
            return None
    
    async def get_inbounds(self, cookies):
        """Получает список всех inbounds"""
        url = f"{self.panel_url}/xui/inbound/list"
        print(f"🔍 DEBUG get_inbounds: Формируемый URL = {url}")
        try:
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.post(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    print(f"🔍 DEBUG: Response status = {resp.status}, Real URL = {resp.url}")
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('success'):
                            inbounds = result.get('obj', [])
                            print(f"✅ Found {len(inbounds)} inbounds")
                            return inbounds
            return None
        except Exception as e:
            print(f"❌ Error getting inbounds: {e}")
            return None
    
    async def add_client(self, user_id, uuid, email, expiry_time=0):
        """
        Добавляет клиента в 3X-UI панель
        
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
                print("❌ Failed to login to 3X-UI")
                return False
            
            # Получаем список inbounds чтобы найти ID
            inbounds = await self.get_inbounds(cookies)
            if not inbounds or len(inbounds) == 0:
                print("❌ No inbounds found. Create one in 3X-UI panel first!")
                return False
            
            # Берем первый inbound
            inbound_id = inbounds[0]['id']
            print(f"✅ Using inbound ID: {inbound_id}")
            
            # Формируем данные клиента для 3X-UI
            settings = {
                "clients": [{
                    "id": uuid,
                    "alterId": 0,
                    "email": email,
                    "limitIp": 3,  # Лимит устройств (3 устройства)
                    "totalGB": 0,  # 0 = безлимит трафика
                    "expiryTime": expiry_time,  # 0 = без ограничения по времени
                    "enable": True,
                    "tgId": str(user_id),
                    "subId": ""
                }]
            }
            
            data = {
                "id": inbound_id,
                "settings": json.dumps(settings)
            }
            
            # Отправляем запрос на добавление клиента
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.post(
                    f"{self.panel_url}/xui/inbound/addClient",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('success'):
                            print(f"✅ Client {email} (UUID: {uuid}) added successfully to 3X-UI")
                            return True
                        else:
                            print(f"❌ Failed to add client: {result.get('msg')}")
                            return False
                    else:
                        print(f"❌ HTTP error {resp.status}")
                        return False
            
        except Exception as e:
            print(f"❌ Error adding client to 3X-UI: {e}")
            return False
    
    async def delete_client(self, user_id, uuid):
        """
        Удаляет клиента из 3X-UI панели
        
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
                print("❌ Failed to login to 3X-UI")
                return False
            
            # Получаем список inbounds
            inbounds = await self.get_inbounds(cookies)
            if not inbounds or len(inbounds) == 0:
                print("❌ No inbounds found")
                return False
            
            # Берем первый inbound
            inbound_id = inbounds[0]['id']
            
            # Формируем данные для удаления
            data = {
                "id": inbound_id,
                "uuid": uuid
            }
            
            # Отправляем запрос на удаление
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.post(
                    f"{self.panel_url}/xui/inbound/delClient/{uuid}",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('success'):
                            print(f"✅ Client {uuid} deleted successfully from 3X-UI")
                            return True
                        else:
                            print(f"❌ Failed to delete: {result.get('msg')}")
                    else:
                        print(f"❌ HTTP error {resp.status}")
            
            return False
        except Exception as e:
            print(f"❌ Error deleting client from 3X-UI: {e}")
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
                    f"{self.panel_url}/xui/inbound/clientStat/{email}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('success'):
                            return result.get('obj')
            
            return None
        except Exception as e:
            print(f"❌ Error getting client traffic: {e}")
            return None
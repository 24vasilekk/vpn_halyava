import aiohttp
from config import XUI_PANEL_URL, XUI_USERNAME, XUI_PASSWORD

print(f"🔍 Marzban Service loaded. Panel URL: {XUI_PANEL_URL}")

class XUIService:
    def __init__(self):
        self.panel_url = XUI_PANEL_URL
        self.username = XUI_USERNAME
        self.password = XUI_PASSWORD
        self.token = None
    
    async def login(self):
        """Авторизация в Marzban"""
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {
                    'username': self.username,
                    'password': self.password,
                    'grant_type': 'password'
                }
                async with session.post(
                    f"{self.panel_url}/api/admin/token",
                    data=login_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.token = result.get('access_token')
                        print("✅ Successfully logged into Marzban")
                        return self.token
                    print(f"❌ Login failed: status {resp.status}")
            return None
        except Exception as e:
            print(f"❌ Error logging into Marzban: {e}")
            return None
    
    async def add_client(self, user_id, uuid, email, expiry_time=0):
        """Добавляет пользователя в Marzban и возвращает реальный UUID"""
        try:
            token = await self.login()
            if not token:
                print("❌ Failed to login to Marzban")
                return False, None
            
            user_data = {
                "username": email,
                "proxies": {
                    "vmess": {
                        "id": uuid
                    }
                },
                "data_limit": 0,
                "expire": 0,
                "status": "active"
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.panel_url}/api/user",
                    json=user_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    print(f"🔍 DEBUG: status = {resp.status}")
                    if resp.status == 200:
                        result = await resp.json()
                        # Получаем реальный UUID из ответа Marzban
                        real_uuid = result.get('proxies', {}).get('vmess', {}).get('id', uuid)
                        print(f"✅ User {email} added to Marzban")
                        print(f"🔑 Real UUID from Marzban: {real_uuid}")
                        return True, real_uuid
                    elif resp.status == 409:
                        # Пользователь уже существует - удаляем и создаем заново
                        print(f"⚠️ User {email} already exists, deleting and recreating...")
                        await self.delete_client(user_id, uuid)
                        
                        # Пробуем создать снова
                        async with session.post(
                            f"{self.panel_url}/api/user",
                            json=user_data,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as resp2:
                            if resp2.status == 200:
                                result = await resp2.json()
                                real_uuid = result.get('proxies', {}).get('vmess', {}).get('id', uuid)
                                print(f"✅ User {email} recreated successfully")
                                print(f"🔑 Real UUID from Marzban: {real_uuid}")
                                return True, real_uuid
                            else:
                                text = await resp2.text()
                                print(f"❌ Failed to recreate user: {text}")
                                return False, None
                    else:
                        text = await resp.text()
                        print(f"❌ Failed to add user: {text}")
                        return False, None
        
        except Exception as e:
            print(f"❌ Error adding client: {e}")
            return False, None
    
    async def delete_client(self, user_id, uuid):
        """Удаляет пользователя из Marzban"""
        try:
            token = await self.login()
            if not token:
                return False
            
            email = f"user_{user_id}"
            headers = {'Authorization': f'Bearer {token}'}
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.panel_url}/api/user/{email}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        print(f"✅ User {email} deleted from Marzban")
                        return True
                    return False
        except Exception as e:
            print(f"❌ Error deleting client: {e}")
            return False
    
    async def get_inbounds(self, cookies):
        """Заглушка для совместимости"""
        return [{'id': 1}]
    
    async def get_client_traffic(self, email):
        """Получает статистику пользователя"""
        try:
            token = await self.login()
            if not token:
                return None
            
            headers = {'Authorization': f'Bearer {token}'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.panel_url}/api/user/{email}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
            return None
        except Exception as e:
            print(f"❌ Error getting client traffic: {e}")
            return None
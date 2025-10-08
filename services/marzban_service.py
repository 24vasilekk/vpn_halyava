import requests
from typing import Optional, Tuple
from datetime import datetime, timedelta

class MarzbanService:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
    
    def _get_token(self) -> str:
        """Получить JWT токен"""
        if self.token:
            return self.token
        
        response = requests.post(
            f"{self.base_url}/api/admin/token",
            data={
                "username": self.username,
                "password": self.password
            }
        )
        
        if response.status_code == 200:
            self.token = response.json()['access_token']
            return self.token
        else:
            raise Exception(f"Failed to get token: {response.text}")
    
    def create_user(self, user_id: int, duration_days: int = 30) -> Tuple[Optional[str], Optional[str]]:
        """Создать пользователя V2Ray в Marzban"""
        try:
            token = self._get_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            username = f"user_{user_id}"
            expire_timestamp = int((datetime.now() + timedelta(days=duration_days)).timestamp())
            
            # Создаём пользователя (обновлённый формат)
            user_data = {
                "username": username,
                "proxies": {
                    "vless": {
                        "flow": ""
                    },
                    "vmess": {}
                },
                "data_limit": 0,  # Безлимит
                "expire": expire_timestamp,
                "status": "active",
                "inbounds": {
                    "vless": ["VLESS TCP"],
                    "vmess": ["VMess TCP"]
                }
            }
            
            print(f"DEBUG: Отправляю запрос: {user_data}")
            
            response = requests.post(
                f"{self.base_url}/api/user",
                headers=headers,
                json=user_data
            )
            
            print(f"DEBUG: Status code: {response.status_code}")
            print(f"DEBUG: Response: {response.text}")
            
            if response.status_code == 200:
                user_info = response.json()
                print(f"DEBUG: User info: {user_info}")
                
                # Получаем subscription_url из links
                if 'links' in user_info and len(user_info['links']) > 0:
                    subscription_url = user_info['links'][0]
                elif 'subscription_url' in user_info:
                    subscription_url = user_info['subscription_url']
                else:
                    subscription_url = f"{self.base_url}/sub/{username}"
                
                return subscription_url, username
            else:
                print(f"Error creating user: {response.text}")
                return None, None
                
        except Exception as e:
            print(f"Error in create_user: {e}")
            import traceback
            traceback.print_exc()
            return None, None
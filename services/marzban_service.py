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
            
            # Проверяем существует ли пользователь
            check_response = requests.get(
                f"{self.base_url}/api/user/{username}",
                headers=headers
            )
            
            if check_response.status_code == 200:
                # Пользователь существует - получаем его данные
                print(f"DEBUG: Пользователь существует, получаю ссылки")
                user_info = check_response.json()
                
                # Получаем прямые ссылки VLESS/VMess из links
                if 'links' in user_info and len(user_info['links']) > 0:
                    # Возвращаем все ссылки как одну строку (разделённые переносом)
                    all_links = '\n'.join(user_info['links'])
                    return all_links, username
                else:
                    # Fallback - subscription URL
                    subscription_url = f"{self.base_url}/sub/{username}"
                    return subscription_url, username
            
            # Создаём нового пользователя
            user_data = {
                "username": username,
                "proxies": {
                    "vless": {
                        "flow": ""
                    },
                    "vmess": {}
                },
                "data_limit": 0,
                "expire": expire_timestamp,
                "status": "active",
                "inbounds": {
                    "vless": ["VLESS TCP"],
                    "vmess": ["VMess TCP"]
                }
            }
            
            print(f"DEBUG: Создаю нового пользователя")
            
            response = requests.post(
                f"{self.base_url}/api/user",
                headers=headers,
                json=user_data
            )
            
            print(f"DEBUG: Status code: {response.status_code}")
            
            if response.status_code == 200:
                user_info = response.json()
                print(f"DEBUG: User created: {user_info.keys()}")
                
                # Получаем прямые ссылки
                if 'links' in user_info and len(user_info['links']) > 0:
                    all_links = '\n'.join(user_info['links'])
                    return all_links, username
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
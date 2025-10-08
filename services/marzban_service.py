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
            
            subscription_token = None
            
            if check_response.status_code == 200:
                # Пользователь существует
                print(f"DEBUG: Пользователь существует")
                user_info = check_response.json()
                subscription_token = user_info.get('subscription_url', '').split('/')[-1]
                
                if not subscription_token:
                    subscription_token = username
            else:
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
                
                if response.status_code != 200:
                    print(f"Error creating user: {response.text}")
                    return None, None
                
                user_info = response.json()
                subscription_token = user_info.get('subscription_url', '').split('/')[-1]
                
                if not subscription_token:
                    subscription_token = username
            
            # Получаем конфиги из subscription endpoint
            import base64
            sub_response = requests.get(f"{self.base_url}/sub/{subscription_token}")
            
            if sub_response.status_code == 200:
                # Декодируем base64
                try:
                    decoded = base64.b64decode(sub_response.text).decode('utf-8')
                    # Каждая строка - это отдельный конфиг
                    configs = [line.strip() for line in decoded.split('\n') if line.strip()]
                    
                    if configs:
                        # Возвращаем все конфиги
                        all_configs = '\n\n'.join(configs)
                        return all_configs, username
                except Exception as e:
                    print(f"DEBUG: Ошибка декодирования: {e}")
            
            # Fallback - просто subscription URL
            subscription_url = f"{self.base_url}/sub/{subscription_token}"
            return subscription_url, username
                
        except Exception as e:
            print(f"Error in create_user: {e}")
            import traceback
            traceback.print_exc()
            return None, None
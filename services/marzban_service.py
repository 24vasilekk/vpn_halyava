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
                # Пользователь существует - возвращаем subscription URL
                user_info = check_response.json()
                subscription_url = user_info.get('subscription_url', '')
                
                if subscription_url:
                    return subscription_url, username
                else:
                    # Fallback
                    return f"{self.base_url}/sub/{username}", username
            
            # Создаём нового пользователя
            user_data = {
                "username": username,
                "proxies": {
                    "vless": {"flow": ""},
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
            
            response = requests.post(
                f"{self.base_url}/api/user",
                headers=headers,
                json=user_data
            )
            
            if response.status_code != 200:
                print(f"Error creating user: {response.text}")
                return None, None
            
            user_info = response.json()
            subscription_url = user_info.get('subscription_url', '')
            
            if subscription_url:
                return subscription_url, username
            else:
                return f"{self.base_url}/sub/{username}", username
                
        except Exception as e:
            print(f"Error in create_user: {e}")
            import traceback
            traceback.print_exc()
            return None, None
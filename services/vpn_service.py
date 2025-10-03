import uuid
import base64
import json
from config import V2RAY_SERVER_IP, V2RAY_PORT
from services.xui_service import XUIService

class VPNService:
    @staticmethod
    async def generate_vpn_key(user_id, is_trial=False):
        """
        Генерирует уникальный ключ V2Ray для пользователя и добавляет в X-UI
        
        Args:
            user_id: ID пользователя Telegram
            is_trial: Пробный период или нет
        
        Returns:
            tuple: (vmess_link, user_uuid) или (None, None) если ошибка
        """
        # Генерируем UUID для пользователя
        user_uuid = str(uuid.uuid4())
        
        # Добавляем клиента в X-UI панель
        xui = XUIService()
        email = f"user_{user_id}"
        
        # expiry_time = 0 означает без ограничений по времени
        # Управление временем происходит через базу данных бота
        success = await xui.add_client(user_id, user_uuid, email, expiry_time=0)
        
        if not success:
            print(f"❌ Failed to add user {user_id} to X-UI")
            return None, None
        
        # Формируем конфигурацию V2Ray (vmess://)
        config = {
            "v": "2",
            "ps": f"VPN-{'Trial' if is_trial else 'Paid'}-{user_id}",
            "add": V2RAY_SERVER_IP,
            "port": V2RAY_PORT,
            "id": user_uuid,
            "aid": "0",
            "net": "tcp",
            "type": "none",
            "host": "",
            "path": "",
            "tls": ""
        }
        
        # Конвертируем в строку vmess://
        config_json = json.dumps(config)
        encoded_config = base64.b64encode(config_json.encode()).decode()
        vmess_link = f"vmess://{encoded_config}"
        
        print(f"✅ VPN key generated for user {user_id} (UUID: {user_uuid})")
        
        return vmess_link, user_uuid
    
    @staticmethod
    async def delete_vpn_key(user_id, user_uuid):
        """
        Удаляет клиента из X-UI панели
        
        Args:
            user_id: ID пользователя Telegram
            user_uuid: UUID клиента
        
        Returns:
            bool: True если успешно
        """
        xui = XUIService()
        return await xui.delete_client(user_id, user_uuid)
    
    @staticmethod
    def get_app_download_link(device_type):
        """
        Возвращает ссылку на скачивание приложения V2Ray для разных устройств
        """
        links = {
            'android': 'https://play.google.com/store/apps/details?id=com.v2ray.ang',
            'iphone': 'https://apps.apple.com/app/shadowrocket/id932747118',
            'ipad': 'https://apps.apple.com/app/shadowrocket/id932747118',
            'ipod': 'https://apps.apple.com/app/shadowrocket/id932747118',
            'mac': 'https://github.com/yanue/V2rayU/releases',
            'windows': 'https://github.com/2dust/v2rayN/releases',
            'other': 'https://www.v2ray.com/en/welcome/download.html'
        }
        return links.get(device_type, links['other'])
import uuid
import base64
from config import V2RAY_SERVER_IP, V2RAY_PORT

class VPNService:
    @staticmethod
    def generate_vpn_key(user_id):
        """
        Генерирует уникальный ключ V2Ray для пользователя
        """
        # Генерируем UUID для пользователя
        user_uuid = str(uuid.uuid4())
        
        # Формируем конфигурацию V2Ray (пример vmess://)
        config = {
            "v": "2",
            "ps": f"VPN-User-{user_id}",
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
        import json
        config_json = json.dumps(config)
        encoded_config = base64.b64encode(config_json.encode()).decode()
        vmess_link = f"vmess://{encoded_config}"
        
        return vmess_link
    
    @staticmethod
    def get_app_download_link(device_type):
        """
        Возвращает ссылку на скачивание приложения V2RayTun для разных устройств
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
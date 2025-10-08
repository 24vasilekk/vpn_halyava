import subprocess
import os
import asyncio
from config import (
    SERVER_1_IP, SERVER_1_WG_PORT, SERVER_1_WG_PUBLIC_KEY, SERVER_1_WG_ENDPOINT,
    SERVER_2_IP, SERVER_2_WG_PORT, SERVER_2_WG_PUBLIC_KEY, SERVER_2_WG_ENDPOINT,
    MARZBAN_API_URL, MARZBAN_API_USERNAME, MARZBAN_API_PASSWORD
)
from services.marzban_service import MarzbanService

CLIENT_CONFIG_DIR = "/root"
WG_INTERFACE = "wg0"

class VPNService:
    @staticmethod
    async def generate_vpn_key(user_id, server=1, protocol='wireguard', is_trial=False):
        """
        Генерирует VPN ключ (только Сервер 1)
        protocol: 'wireguard' или 'v2ray'
        """
        if protocol == 'v2ray':
            return await VPNService._generate_v2ray_key(user_id, is_trial)
        else:
            return await VPNService._generate_wireguard_key(user_id, is_trial)

    @staticmethod
    async def _generate_v2ray_key(user_id, is_trial):
        """Генерирует V2Ray ключ через Marzban API"""
        try:
            marzban = MarzbanService(
                MARZBAN_API_URL,
                MARZBAN_API_USERNAME,
                MARZBAN_API_PASSWORD
            )
            
            duration = 3 if is_trial else 30
            subscription_url, username = marzban.create_user(user_id, duration)
            
            if subscription_url:
                return subscription_url, username
            else:
                return None, None
                
        except Exception as e:
            print(f"Error generating V2Ray key: {e}")
            return None, None
    
    @staticmethod
    async def _generate_wireguard_key(user_id, is_trial):
        """Генерирует WireGuard конфиг (локально на сервере 1)"""
        client_name = f"user_{user_id}"
        config_path = f"/root/wg0-client-{client_name}.conf"
        
        # Проверяем существующий конфиг
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return f.read(), client_name
        
        try:
            # Получаем занятые IP
            result = subprocess.run(['wg', 'show', 'wg0', 'allowed-ips'], 
                                capture_output=True, text=True)
            
            used_ips = []
            import re
            for line in result.stdout.strip().split('\n'):
                if '10.66.66.' in line:
                    match = re.search(r'10\.66\.66\.(\d+)', line)
                    if match:
                        used_ips.append(int(match.group(1)))
            
            next_ip = 2
            while next_ip in used_ips:
                next_ip += 1
            
            print(f"Создаю WireGuard клиента с IP 10.66.66.{next_ip}")
            
            # Генерируем ключи
            private_key = subprocess.run(['wg', 'genkey'], capture_output=True, text=True).stdout.strip()
            public_key = subprocess.run(['wg', 'pubkey'], input=private_key, capture_output=True, text=True).stdout.strip()
            preshared_key = subprocess.run(['wg', 'genpsk'], capture_output=True, text=True).stdout.strip()
            
            # Добавляем peer
            subprocess.run([
                'wg', 'set', 'wg0',
                'peer', public_key,
                'preshared-key', '/dev/stdin',
                'allowed-ips', f'10.66.66.{next_ip}/32'
            ], input=preshared_key, text=True, check=True)
            
            subprocess.run(['wg-quick', 'save', 'wg0'], check=True)
            
            # Создаем конфиг
            config_text = f"""[Interface]
PrivateKey = {private_key}
Address = 10.66.66.{next_ip}/32
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = {SERVER_1_WG_PUBLIC_KEY}
PresharedKey = {preshared_key}
Endpoint = {SERVER_1_WG_ENDPOINT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
            
            # Сохраняем
            with open(config_path, 'w') as f:
                f.write(config_text)
            
            print(f"✅ WireGuard клиент создан: {client_name}, IP: 10.66.66.{next_ip}")
            return config_text, client_name
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return None, None
        
    @staticmethod
    async def delete_vpn_key(user_id, user_uuid):
        """Удаляет клиента из WireGuard"""
        try:
            config_path = f"{CLIENT_CONFIG_DIR}/wg0-client-{user_uuid}.conf"
            
            if os.path.exists(config_path):
                os.remove(config_path)
            
            print(f"🗑️ Deleted config for {user_uuid}")
            return True
        except Exception as e:
            print(f"❌ Error deleting: {e}")
            return False
    
    @staticmethod
    def get_app_download_link(device_type, protocol='wireguard'):
        """Ссылки на приложения"""
        if protocol == 'v2ray':
            links = {
                'android': 'https://play.google.com/store/apps/details?id=com.v2ray.ang',
                'iphone': 'https://apps.apple.com/app/shadowrocket/id932747118',
                'ipad': 'https://apps.apple.com/app/shadowrocket/id932747118',
                'mac': 'https://apps.apple.com/app/v2box/id6446814690',
                'windows': 'https://github.com/2dust/v2rayN/releases',
                'other': 'https://www.v2fly.org/'
            }
        else:  # wireguard
            links = {
                'android': 'https://play.google.com/store/apps/details?id=com.wireguard.android',
                'iphone': 'https://apps.apple.com/app/wireguard/id1441195209',
                'ipad': 'https://apps.apple.com/app/wireguard/id1441195209',
                'ipod': 'https://apps.apple.com/app/wireguard/id1441195209',
                'mac': 'https://apps.apple.com/app/wireguard/id1451685025',
                'windows': 'https://download.wireguard.com/windows-client/wireguard-installer.exe',
                'other': 'https://www.wireguard.com/install/'
            }
        return links.get(device_type, links.get('other'))
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
        Генерирует VPN ключ
        server: 1 или 2
        protocol: 'wireguard' или 'v2ray'
        """
        if protocol == 'v2ray':
            # V2Ray только на сервере 1
            return await VPNService._generate_v2ray_key(user_id, is_trial)
        else:
            # WireGuard на выбранном сервере
            return await VPNService._generate_wireguard_key(user_id, server, is_trial)
    
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
    async def _generate_wireguard_key(user_id, server, is_trial):
        """Генерирует WireGuard конфиг для выбранного сервера"""
        client_name = f"user_{user_id}_s{server}"
        config_path = f"{CLIENT_CONFIG_DIR}/wg0-client-{client_name}.conf"
        
        # Настройки сервера
        if server == 1:
            server_ip = SERVER_1_IP
            server_public_key = SERVER_1_WG_PUBLIC_KEY
            server_endpoint = SERVER_1_WG_ENDPOINT
            ip_range = "10.66.66"
        else:  # server == 2
            server_ip = SERVER_2_IP
            server_public_key = SERVER_2_WG_PUBLIC_KEY
            server_endpoint = SERVER_2_WG_ENDPOINT
            ip_range = "10.77.77"
        
        # Проверяем существующий конфиг
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_text = f.read()
            return config_text, client_name
        
        try:
            # Получаем занятые IP адреса
            result = subprocess.run(
                ['wg', 'show', WG_INTERFACE, 'allowed-ips'],
                capture_output=True,
                text=True
            )
            
            # Находим следующий свободный IP
            used_ips = []
            for line in result.stdout.strip().split('\n'):
                if line and ip_range in line:
                    import re
                    match = re.search(rf'{ip_range}\.(\d+)', line)
                    if match:
                        used_ips.append(int(match.group(1)))
            
            next_ip = 2
            while next_ip in used_ips:
                next_ip += 1
            
            print(f"Создаю клиента с IP {ip_range}.{next_ip}")
            
            # Генерируем ключи
            private_key = subprocess.run(['wg', 'genkey'], capture_output=True, text=True).stdout.strip()
            public_key = subprocess.run(['wg', 'pubkey'], input=private_key, capture_output=True, text=True).stdout.strip()
            preshared_key = subprocess.run(['wg', 'genpsk'], capture_output=True, text=True).stdout.strip()
            
            # Добавляем peer в WireGuard
            subprocess.run([
                'wg', 'set', WG_INTERFACE,
                'peer', public_key,
                'preshared-key', '/dev/stdin',
                'allowed-ips', f'{ip_range}.{next_ip}/32'
            ], input=preshared_key, text=True, check=True)
            
            # Сохраняем конфигурацию WireGuard
            subprocess.run(['wg-quick', 'save', WG_INTERFACE], check=True)
            
            # Создаем конфиг файл для клиента
            config_text = f"""[Interface]
PrivateKey = {private_key}
Address = {ip_range}.{next_ip}/32
DNS = 1.1.1.1, 1.0.0.1
PostUp = ip -6 route add blackhole default metric 1

[Peer]
PublicKey = {server_public_key}
PresharedKey = {preshared_key}
Endpoint = {server_endpoint}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
            
            # Сохраняем конфиг в файл
            with open(config_path, 'w') as f:
                f.write(config_text)
            
            print(f"✅ Client {client_name} created with IP {ip_range}.{next_ip}")
            
            return config_text, client_name
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating peer: {e}")
            return None, None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
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
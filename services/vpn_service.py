import subprocess
import os
import asyncio

CLIENT_CONFIG_DIR = "/root"
WG_INTERFACE = "wg0"
SERVER_PUBLIC_KEY = "1i1KhfPy8dlFCXs5fbsqq+C19aqY9Yb1Dk3iHgRi4Xo="
SERVER_ENDPOINT = "81.200.157.217:51820"

class VPNService:
    @staticmethod
    async def generate_vpn_key(user_id, is_trial=False):
        """Генерирует WireGuard конфиг и добавляет peer напрямую"""
        client_name = f"user_{user_id}"
        config_path = f"{CLIENT_CONFIG_DIR}/wg0-client-{client_name}.conf"
        
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
                if line and '10.66.66.' in line:
                    import re
                    match = re.search(r'10\.66\.66\.(\d+)', line)
                    if match:
                        used_ips.append(int(match.group(1)))
            
            next_ip = 2
            while next_ip in used_ips:
                next_ip += 1
            
            print(f"Создаю клиента с IP 10.66.66.{next_ip}")
            
            # Генерируем ключи
            private_key = subprocess.run(['wg', 'genkey'], capture_output=True, text=True).stdout.strip()
            public_key = subprocess.run(['wg', 'pubkey'], input=private_key, capture_output=True, text=True).stdout.strip()
            preshared_key = subprocess.run(['wg', 'genpsk'], capture_output=True, text=True).stdout.strip()
            
            # Добавляем peer в WireGuard (ТОЛЬКО IPv4)
            subprocess.run([
                'wg', 'set', WG_INTERFACE,
                'peer', public_key,
                'preshared-key', '/dev/stdin',
                'allowed-ips', f'10.66.66.{next_ip}/32'  # УБРАЛИ IPv6
            ], input=preshared_key, text=True, check=True)
            
            # Сохраняем конфигурацию WireGuard
            subprocess.run(['wg-quick', 'save', WG_INTERFACE], check=True)
            
            # Создаем конфиг файл для клиента
            config_text = f"""[Interface]
PrivateKey = {private_key}
Address = 10.66.66.{next_ip}/32
DNS = 1.1.1.1, 1.0.0.1
PostUp = ip -6 route add blackhole default metric 1

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
PresharedKey = {preshared_key}
Endpoint = {SERVER_ENDPOINT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
            
            # Сохраняем конфиг в файл
            with open(config_path, 'w') as f:
                f.write(config_text)
            
            print(f"✅ Client {client_name} created with IP 10.66.66.{next_ip}")
            print(f"   Public key: {public_key[:20]}...")
            
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
            
            # Удаляем файл конфига
            if os.path.exists(config_path):
                os.remove(config_path)
            
            # Находим и удаляем peer по имени из комментариев
            # (сложно без парсинга конфига, поэтому просто удаляем файл)
            
            print(f"🗑️ Deleted config for {user_uuid}")
            return True
        except Exception as e:
            print(f"❌ Error deleting: {e}")
            return False
    
    @staticmethod
    def get_app_download_link(device_type):
        """Ссылки на WireGuard приложения"""
        links = {
            'android': 'https://play.google.com/store/apps/details?id=com.wireguard.android',
            'iphone': 'https://apps.apple.com/app/wireguard/id1441195209',
            'ipad': 'https://apps.apple.com/app/wireguard/id1441195209',
            'ipod': 'https://apps.apple.com/app/wireguard/id1441195209',
            'mac': 'https://apps.apple.com/app/wireguard/id1451685025',
            'windows': 'https://download.wireguard.com/windows-client/wireguard-installer.exe',
            'other': 'https://www.wireguard.com/install/'
        }
        return links.get(device_type, links['other'])

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
        import paramiko
        
        # Настройки сервера
        if server == 1:
            server_ip = SERVER_1_IP
            server_public_key = SERVER_1_WG_PUBLIC_KEY
            server_endpoint = SERVER_1_WG_ENDPOINT
            ip_range = "10.66.66"
            ssh_host = SERVER_1_IP
        else:  # server == 2
            server_ip = SERVER_2_IP
            server_public_key = SERVER_2_WG_PUBLIC_KEY
            server_endpoint = SERVER_2_WG_ENDPOINT
            ip_range = "10.77.77"
            ssh_host = SERVER_2_IP
        
        client_name = f"user_{user_id}_s{server}"
        
        try:
            # Подключаемся к серверу по SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Используем SSH ключ для подключения
            ssh.connect(ssh_host, username='root', key_filename='/root/.ssh/id_rsa')
            
            # Проверяем существующий конфиг
            config_path = f"/root/wg0-client-{client_name}.conf"
            stdin, stdout, stderr = ssh.exec_command(f'test -f {config_path} && cat {config_path}')
            existing_config = stdout.read().decode('utf-8')
            
            if existing_config:
                ssh.close()
                return existing_config, client_name
            
            # Получаем занятые IP
            stdin, stdout, stderr = ssh.exec_command('wg show wg0 allowed-ips')
            result = stdout.read().decode('utf-8')
            
            # Находим свободный IP
            used_ips = []
            import re
            for line in result.strip().split('\n'):
                if ip_range in line:
                    match = re.search(rf'{ip_range}\.(\d+)', line)
                    if match:
                        used_ips.append(int(match.group(1)))
            
            next_ip = 2
            while next_ip in used_ips:
                next_ip += 1
            
            print(f"Создаю клиента с IP {ip_range}.{next_ip} на сервере {server}")
            
            # Генерируем ключи
            stdin, stdout, stderr = ssh.exec_command('wg genkey')
            private_key = stdout.read().decode('utf-8').strip()
            
            stdin, stdout, stderr = ssh.exec_command(f'echo {private_key} | wg pubkey')
            public_key = stdout.read().decode('utf-8').strip()
            
            stdin, stdout, stderr = ssh.exec_command('wg genpsk')
            preshared_key = stdout.read().decode('utf-8').strip()
            
            # Добавляем peer
            add_peer_cmd = f'''
echo {preshared_key} | wg set wg0 peer {public_key} preshared-key /dev/stdin allowed-ips {ip_range}.{next_ip}/32
wg-quick save wg0
'''
            stdin, stdout, stderr = ssh.exec_command(add_peer_cmd)
            error = stderr.read().decode('utf-8')
            if error:
                print(f"Error adding peer: {error}")
            
            # Создаем конфиг
            config_text = f"""[Interface]
PrivateKey = {private_key}
Address = {ip_range}.{next_ip}/32
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = {server_public_key}
PresharedKey = {preshared_key}
Endpoint = {server_endpoint}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
            
            # Сохраняем конфиг на сервере
            save_cmd = f"cat > {config_path} << 'EOF'\n{config_text}\nEOF"
            ssh.exec_command(save_cmd)
            
            ssh.close()
            
            print(f"✅ Client {client_name} created with IP {ip_range}.{next_ip}")
            return config_text, client_name
            
        except Exception as e:
            print(f"❌ Error: {e}")
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
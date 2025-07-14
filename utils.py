from datetime import datetime
import os
from colorama import Fore, Style
import platform
import random

def reset_terminal_display():
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def print_timestamped_message(message):
    timestamp = datetime.now().strftime('%H:%M:%S') # Format baru: HH:MM:SS
    print(f"{Fore.BLUE}[{timestamp}]{Style.RESET_ALL} {message}")

def convert_seconds_to_time_string(total_seconds):
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{int(hours):02}:{int(minutes):02}:{int(secs):02}"

def read_json_file_data(file_path):
    try:
        import json
        with open(file_path, 'r', encoding='utf-8') as file_handle:
            return json.load(file_handle)
    except FileNotFoundError:
        print(f"{Fore.RED}Error: {file_path} not found.{Style.RESET_ALL}")
        return None
    except json.JSONDecodeError:
        print(f"{Fore.RED}Error: Invalid JSON in {file_path}.{Style.RESET_ALL}")
        return None

def extract_wallet_address_info(private_key_entry: str):
    from eth_account import Account
    try:
        
        wallet_account = Account.from_key(private_key_entry)
        full_address = wallet_account.address
        return full_address, f"{full_address[:6]}...{full_address[-4:]}"
    except Exception:
        
        return None, f"{private_key_entry[:6]}...{private_key_entry[-4:]}" if len(private_key_entry) >= 10 else "Invalid Key"

def validate_proxy_url_format(proxy_endpoint: str):
    if not (proxy_endpoint.startswith("http://") or proxy_endpoint.startswith("https://") or proxy_endpoint.startswith("socks5://")):
        raise ValueError("Invalid proxy format. Must start with http://, https://, or socks5://")
    return proxy_endpoint

def generate_random_browser_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/108.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/108.0",
    ]
    return random.choice(user_agents)

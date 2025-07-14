from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from aiohttp_socks import ProxyConnector
from eth_account.messages import encode_defunct
from eth_utils import to_hex
from eth_account import Account
from datetime import datetime, timezone
from colorama import *
import asyncio, uuid, json, os
import time
import random

from utils import (
    reset_terminal_display,
    print_timestamped_message,
    convert_seconds_to_time_string,
    read_json_file_data,
    extract_wallet_address_info,
    validate_proxy_url_format,
    generate_random_browser_agent
)

class ProtocolTaskManager:
    def __init__(self) -> None:
        self.AUTH_SERVICE_URL = "https://auth.privy.io"
        self.MAIN_API_URL = "https://api.app.wardenprotocol.org/api"
        self.CHAT_SERVICE_URL = "https://warden-app-agents-prod-new-d1025b697dc25df9a5654bc047bbe875.us.langgraph.app"
        
        self.auth_header_storage = {}
        self.api_header_storage = {}
        self.chat_header_storage = {}
        
        self.proxy_collection = []
        self.proxy_rotation_index = 0
        self.wallet_proxy_mapping = {}
        self.session_tokens = {}

    def show_startup_banner(self):
        reset_terminal_display()
        now = datetime.now()
        date_str = now.strftime('%d.%m.%y')
        time_str = now.strftime('%H:%M:%S')


    async def initialize_proxy_config(self, enable_proxy_mode: bool):
        proxy_file_path = "proxy.txt"
        try:
            if not os.path.exists(proxy_file_path):
                print_timestamped_message(f"{Fore.RED + Style.BRIGHT}File {proxy_file_path} Not Found.{Style.RESET_ALL}")
                return
            with open(proxy_file_path, 'r') as file_reader:
                self.proxy_collection = [line.strip() for line in file_reader.read().splitlines() if line.strip()]
            
            if not self.proxy_collection:
                print_timestamped_message(f"{Fore.RED + Style.BRIGHT}No Proxies Found. Running without proxy.{Style.RESET_ALL}")
                return

            print_timestamped_message(
                f"{Fore.YELLOW + Style.BRIGHT}Loaded Proxies: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxy_collection)}{Style.RESET_ALL}"
            )
            
            # 显示代理类型统计
            proxy_type_stats = {}
            for proxy_entry in self.proxy_collection:
                protocol_type = proxy_entry.split('://')[0] if '://' in proxy_entry else 'unknown'
                proxy_type_stats[protocol_type] = proxy_type_stats.get(protocol_type, 0) + 1
            
            stats_summary = ', '.join([f"{protocol}: {count}" for protocol, count in proxy_type_stats.items()])
            print_timestamped_message(f"{Fore.CYAN}Proxy Types: {Fore.WHITE}{stats_summary}{Style.RESET_ALL}")
        
        except Exception as error:
            print_timestamped_message(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {error}{Style.RESET_ALL}")
            self.proxy_collection = []

    def fetch_assigned_proxy(self, wallet_address):
        if wallet_address not in self.wallet_proxy_mapping:
            if not self.proxy_collection:
                return None
            proxy_endpoint = validate_proxy_url_format(self.proxy_collection[self.proxy_rotation_index])
            self.wallet_proxy_mapping[wallet_address] = proxy_endpoint
            self.proxy_rotation_index = (self.proxy_rotation_index + 1) % len(self.proxy_collection)
        return self.wallet_proxy_mapping[wallet_address]

    def switch_proxy_for_wallet(self, wallet_address):
        if not self.proxy_collection:
            return None
        proxy_endpoint = validate_proxy_url_format(self.proxy_collection[self.proxy_rotation_index])
        self.wallet_proxy_mapping[wallet_address] = proxy_endpoint
        self.proxy_rotation_index = (self.proxy_rotation_index + 1) % len(self.proxy_collection)
        return proxy_endpoint
        
    def create_auth_signature(self, private_key: str, wallet_addr: str, nonce_data: str):
        try:
            current_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            auth_message = f"app.wardenprotocol.org wants you to sign in with your Ethereum account:\n{wallet_addr}\n\nBy signing, you are proving you own this wallet and logging in. This does not initiate a transaction or cost any fees.\n\nURI: https://app.wardenprotocol.org\nVersion: 1\nChain ID: 1\nNonce: {nonce_data}\nIssued At: {current_timestamp}\nResources:\n- https://privy.io"
            message_encoded = encode_defunct(text=auth_message)
            message_signed = Account.sign_message(message_encoded, private_key=private_key)
            hex_signature = to_hex(message_signed.signature)

            auth_payload = {
                "message":auth_message,
                "signature":hex_signature,
                "chainId":"eip155:1",
                "walletClientType":"metamask",
                "connectorType":"injected",
                "mode":"login-or-sign-up"
            }

            return auth_payload
        except Exception as error:
            raise Exception(f"Failed to generate authentication payload: {str(error)}")

    def build_chat_request_data(self, message_content: str):
        try:
            request_payload = {
                "input":{
                    "messages":[{
                        "id":str(uuid.uuid4()),
                        "type":"human",
                        "content":message_content
                    }]
                },
                "metadata":{
                    "addresses":[]
                },
                "stream_mode":[
                    "values",
                    "messages-tuple",
                    "custom"
                ],
                "stream_resumable":True,
                "assistant_id":"agent",
                "on_disconnect":"continue"
            }

            return request_payload
        except Exception as error:
            return None
        
    def prompt_proxy_selection(self):
        while True:
            try:
                print_timestamped_message(f"{Fore.CYAN + Style.BRIGHT}─" * 40)
                print_timestamped_message(f"{Fore.WHITE}[1]{Fore.CYAN} Run with Private Proxy")
                print_timestamped_message(f"{Fore.WHITE}[2]{Fore.CYAN} Run without Proxy")
                print_timestamped_message(f"{Fore.CYAN + Style.BRIGHT}─" * 40)
                choice_input = int(input(f"{Fore.GREEN + Style.BRIGHT}Choose an option (1 or 2): {Style.RESET_ALL}").strip())

                if choice_input in [1, 2]:
                    proxy_type_display = (
                        "Private Proxy" if choice_input == 1 else 
                        "No Proxy"
                    )
                    print_timestamped_message(f"{Fore.GREEN + Style.BRIGHT}Mode selected: {proxy_type_display}{Style.RESET_ALL}")
                    break
                else:
                    print_timestamped_message(f"{Fore.RED + Style.BRIGHT}Invalid input. Please enter 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print_timestamped_message(f"{Fore.RED + Style.BRIGHT}Invalid input. Please enter a number (1 or 2).{Style.RESET_ALL}")

        should_rotate = False
        if choice_input == 1:
            while True:
                rotate_input_str = input(f"{Fore.GREEN + Style.BRIGHT}Rotate Invalid Proxy? (y/n): {Style.RESET_ALL}").strip().lower()

                if rotate_input_str in ["y", "n"]:
                    should_rotate = (rotate_input_str == "y")
                    break
                else:
                    print_timestamped_message(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return choice_input, should_rotate
    
    async def test_network_connectivity(self, proxy_endpoint=None):
        connection_handler = ProxyConnector.from_url(proxy_endpoint) if proxy_endpoint else None
        try:
            async with ClientSession(connector=connection_handler, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url="https://api.ipify.org?format=json", ssl=False) as response:
                    response.raise_for_status()
                    ip_response = await response.json()
                    detected_ip = ip_response.get('ip', 'Unknown')
                    
                    if proxy_endpoint:
                        print_timestamped_message(f"{Fore.CYAN}Current IP via proxy: {Fore.WHITE}{detected_ip}{Style.RESET_ALL}")
                    else:
                        print_timestamped_message(f"{Fore.CYAN}Current IP (direct): {Fore.WHITE}{detected_ip}{Style.RESET_ALL}")
                    
                    return True
        except (Exception, ClientResponseError) as error:
            error_class = type(error).__name__
            print_timestamped_message(
                f"{Fore.RED}Connection Status: Failed {Style.RESET_ALL}({Fore.YELLOW}{error_class}: {str(error)}{Style.RESET_ALL})"
            )
            return None
    
    async def obtain_auth_nonce(self, wallet_addr: str, proxy_endpoint=None, retry_count=5):
        request_url = f"{self.AUTH_SERVICE_URL}/api/v1/siwe/init"
        request_data = json.dumps({"address":wallet_addr})
        request_headers = {
            **self.auth_header_storage[wallet_addr],
            "Content-Length": str(len(request_data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt_num in range(retry_count):
            connection_handler = ProxyConnector.from_url(proxy_endpoint) if proxy_endpoint else None
            try:
                async with ClientSession(connector=connection_handler, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=request_url, headers=request_headers, data=request_data, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as error:
                if attempt_num < retry_count - 1:
                    await asyncio.sleep(5)
                    continue
                print_timestamped_message(
                    f"{Fore.RED}Nonce Retrieval Failed {Style.RESET_ALL}({Fore.YELLOW}{str(error)}{Style.RESET_ALL})"
                )

        return None
    
    async def execute_wallet_authentication(self, private_key: str, wallet_addr: str, nonce_data: str, proxy_endpoint=None, retry_count=5):
        request_url = f"{self.AUTH_SERVICE_URL}/api/v1/siwe/authenticate"
        request_data = json.dumps(self.create_auth_signature(private_key, wallet_addr, nonce_data))
        request_headers = {
            **self.auth_header_storage[wallet_addr],
            "Content-Length": str(len(request_data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt_num in range(retry_count):
            connection_handler = ProxyConnector.from_url(proxy_endpoint) if proxy_endpoint else None
            try:
                async with ClientSession(connector=connection_handler, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=request_url, headers=request_headers, data=request_data, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as error:
                if attempt_num < retry_count - 1:
                    await asyncio.sleep(5)
                    continue
                print_timestamped_message(
                    f"{Fore.RED}Authentication Failed {Style.RESET_ALL}({Fore.YELLOW}{str(error)}{Style.RESET_ALL})"
                )

        return None
    
    async def retrieve_wallet_balance(self, wallet_addr: str, proxy_endpoint=None, retry_count=5):
        url = f"{self.MAIN_API_URL}/tokens/user/me"
        headers = {
            **self.api_header_storage[wallet_addr],
            "Authorization": f"Bearer {self.session_tokens[wallet_addr]}"
        }
        await asyncio.sleep(3)
        for attempt in range(retry_count):
            connector = ProxyConnector.from_url(proxy_endpoint) if proxy_endpoint else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                print_timestamped_message(
                    f"{Fore.RED}Balance Fetch Failed {Style.RESET_ALL}({Fore.YELLOW}{str(e)}{Style.RESET_ALL})"
                )

        return None
    
    async def process_daily_checkin(self, wallet_addr: str, proxy_endpoint=None, retry_count=5):
        url = f"{self.MAIN_API_URL}/tokens/activity"
        data = json.dumps({
            "activityType":"LOGIN",
            "metadata":{
                "action":"user_login",
                "timestamp":datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            }
        })
        headers = {
            **self.api_header_storage[wallet_addr],
            "Authorization": f"Bearer {self.session_tokens[wallet_addr]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retry_count):
            connector = ProxyConnector.from_url(proxy_endpoint) if proxy_endpoint else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                print_timestamped_message(
                    f"{Fore.RED}Check-in Activity Failed {Style.RESET_ALL}({Fore.YELLOW}{str(e)}{Style.RESET_ALL})"
                )

        return None
    
    async def execute_game_task(self, wallet_addr: str, proxy_endpoint=None, retry_count=5):
        url = f"{self.MAIN_API_URL}/tokens/activity"
        data = json.dumps({
            "activityType":"GAME_PLAY",
            "metadata":{
                "action":"user_game",
                "timestamp":datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            }
        })
        headers = {
            **self.api_header_storage[wallet_addr],
            "Authorization": f"Bearer {self.session_tokens[wallet_addr]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retry_count):
            connector = ProxyConnector.from_url(proxy_endpoint) if proxy_endpoint else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                print_timestamped_message(
                    f"{Fore.RED}Game Activity Failed {Style.RESET_ALL}({Fore.YELLOW}{str(e)}{Style.RESET_ALL})"
                )

        return None
    
    async def initialize_agent_thread(self, wallet_address: str, proxy_addr=None, retries=5):
        url = f"{self.CHAT_SERVICE_URL}/threads"
        data = json.dumps({"metadata":{}})
        headers = {
            **self.chat_header_storage[wallet_address],
            "Authorization": f"Bearer {self.session_tokens[wallet_address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy_addr) if proxy_addr else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                print_timestamped_message(
                    f"{Fore.YELLOW}[AI Chat Init]: {Fore.RED}Failed {Style.RESET_ALL}({Fore.YELLOW}{str(e)}{Style.RESET_ALL})"
                )

        return None

    async def execute_agent_stream(self, wallet_address: str, thread_id: str, message_content: str, proxy_addr=None, retries=5):
        url = f"{self.CHAT_SERVICE_URL}/threads/{thread_id}/runs/stream"
        data = json.dumps(self.build_chat_request_data(message_content))
        headers = {
            **self.chat_header_storage[wallet_address],
            "Authorization": f"Bearer {self.session_tokens[wallet_address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }

        await asyncio.sleep(3)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy_addr) if proxy_addr else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                        response.raise_for_status()
                        result_content = ""

                        async for line in response.content:
                            line = line.decode("utf-8").strip()

                            if not line or line.startswith(":"):
                                continue

                            if line.startswith("data: "):
                                try:
                                    json_data = json.loads(line[6:])
                                    messages = json_data.get("messages", [])
                                    for msg in messages:
                                        if msg.get("type") == "ai":
                                            result_content += msg.get("content", "")
                                except json.JSONDecodeError:
                                    continue
                        
                        return result_content if result_content else None

            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                print_timestamped_message(
                    f"{Fore.YELLOW}[AI Chat Response]: {Fore.RED}Failed {Style.RESET_ALL}({Fore.YELLOW}{str(e)}{Style.RESET_ALL})"
                )

        return None
    
    async def submit_chat_activity(self, wallet_address: str, message_length: int, proxy_addr=None, retries=5):
        url = f"{self.MAIN_API_URL}/tokens/activity"
        data = json.dumps({
            "activityType":"CHAT_INTERACTION",
            "metadata":{
                "action":"user_chat",
                "message_length":message_length,
                "timestamp":datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            }
        })
        headers = {
            **self.api_header_storage[wallet_address],
            "Authorization": f"Bearer {self.session_tokens[wallet_address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy_addr) if proxy_addr else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                print_timestamped_message(
                    f"{Fore.YELLOW}[AI Chat Send]: {Fore.RED}Failed {Style.RESET_ALL}({Fore.YELLOW}{str(e)}{Style.RESET_ALL})"
                )

        return None
            
    async def validate_proxy_connection(self, wallet_addr: str, proxy_enabled: bool, rotation_enabled: bool):
        while True:
            current_proxy = self.fetch_assigned_proxy(wallet_addr) if proxy_enabled and self.proxy_collection else None
            proxy_display = current_proxy if current_proxy else "None (Direct)"
            print_timestamped_message(
                f"{Fore.WHITE}Proxy Used: {Fore.YELLOW}{proxy_display}{Style.RESET_ALL}"
            )

            # 测试代理连接
            if current_proxy:
                print_timestamped_message(f"{Fore.CYAN}Testing proxy connection...{Style.RESET_ALL}")
            
            connection_valid = await self.test_network_connectivity(current_proxy)
            
            if current_proxy and connection_valid:
                print_timestamped_message(f"{Fore.GREEN}Proxy connection successful ✓{Style.RESET_ALL}")
            elif current_proxy and not connection_valid:
                print_timestamped_message(f"{Fore.RED}Proxy connection failed ✗{Style.RESET_ALL}")
            
            if not connection_valid:
                if rotation_enabled and proxy_enabled and self.proxy_collection:
                    print_timestamped_message(f"{Fore.YELLOW}Switching proxy for {extract_wallet_address_info(wallet_addr)[1]}...{Style.RESET_ALL}")
                    current_proxy = self.switch_proxy_for_wallet(wallet_addr)
                    new_proxy_display = current_proxy if current_proxy else "None (Direct)"
                    print_timestamped_message(f"{Fore.WHITE}New Proxy: {Fore.YELLOW}{new_proxy_display}{Style.RESET_ALL}")
                    await asyncio.sleep(5)
                    continue
                elif proxy_enabled and not self.proxy_collection:
                    print_timestamped_message(f"{Fore.RED}No proxies available, proceeding without proxy.{Style.RESET_ALL}")
                    return True
                else:
                    return False
            
            return True

    async def authenticate_wallet_session(self, private_key: str, wallet_addr: str, proxy_enabled: bool, rotation_enabled: bool):
        connection_status = await self.validate_proxy_connection(wallet_addr, proxy_enabled, rotation_enabled)
        if connection_status:
            selected_proxy = self.fetch_assigned_proxy(wallet_addr) if proxy_enabled else None

            nonce_result = await self.obtain_auth_nonce(wallet_addr, selected_proxy)
            if nonce_result:
                extracted_nonce = nonce_result["nonce"]

                auth_result = await self.execute_wallet_authentication(private_key, wallet_addr, extracted_nonce, selected_proxy)
                if auth_result:
                    self.session_tokens[wallet_addr] = auth_result["token"]

                    print_timestamped_message(
                        f"{Fore.GREEN}Login Status: Success!{Style.RESET_ALL}"
                    )
                    return True

        return False

    async def process_wallet_activities(self, private_key: str, wallet_address: str, chat_questions: list, use_proxy_option: bool, rotate_proxy_option: bool):
        login_successful = await self.perform_user_login(private_key, wallet_address, use_proxy_option, rotate_proxy_option)
        if login_successful:
            assigned_proxy = self.get_next_available_proxy(wallet_address) if use_proxy_option else None

            user_data = await self.fetch_user_token_data(wallet_address, assigned_proxy)
            if user_data:
                current_balance = user_data.get("token", {}).get("pointsTotal", 0)

                print_timestamped_message(
                    f"{Fore.WHITE}Current Balance: {Fore.YELLOW}{current_balance} PUMPs{Style.RESET_ALL}"
                )

            checkin_result = await self.submit_checkin_activity(wallet_address, assigned_proxy)
            if checkin_result:
                activity_id_checkin = checkin_result.get("activityId", None)

                if activity_id_checkin:
                    print_timestamped_message(
                        f"{Fore.GREEN}Daily Check-In: Activity Recorded.{Style.RESET_ALL}"
                    )
                else:
                    message_checkin = checkin_result.get("message", "Unknown Status")
                    print_timestamped_message(
                        f"{Fore.YELLOW}Daily Check-In: {message_checkin}{Style.RESET_ALL}"
                    )

            game_result = await self.submit_game_activity(wallet_address, assigned_proxy)
            if game_result:
                activity_id_game = game_result.get("activityId", None)
                if activity_id_game:
                    print_timestamped_message(
                        f"{Fore.GREEN}Game Play: Activity Recorded.{Style.RESET_ALL}"
                    )
                else:
                    message_game = game_result.get("message", "Unknown Status")
                    print_timestamped_message(
                        f"{Fore.YELLOW}Game Play: {message_game}{Style.RESET_ALL}"
                    )

            print_timestamped_message(f"{Fore.CYAN}Initiating AI Chat...{Style.RESET_ALL}")

            ai_chat_completed = False
            for _ in range(3):
                thread_info = await self.initialize_agent_thread(wallet_address, assigned_proxy)
                if thread_info:
                    thread_identifier = thread_info.get("thread_id")
                    chosen_message = random.choice(chat_questions)
                    message_len = int(len(chosen_message))

                    print_timestamped_message(
                        f"{Fore.BLUE}  [Q]: {Fore.WHITE}{chosen_message}{Style.RESET_ALL}"
                    )

                    chat_response = await self.execute_agent_stream(wallet_address, thread_identifier, chosen_message, assigned_proxy)
                    if chat_response:
                        print_timestamped_message(
                            f"{Fore.MAGENTA}  [A]: {Fore.WHITE}{chat_response}{Style.RESET_ALL}"
                        )

                        submit_chat_result = await self.submit_chat_activity(wallet_address, message_len, assigned_proxy)
                        if submit_chat_result:
                            activity_id_chat = submit_chat_result.get("activityId", None)
                            if activity_id_chat:
                                print_timestamped_message(
                                    f"{Fore.GREEN}  Chat Activity: Sent Successfully.{Style.RESET_ALL}"
                                )
                                ai_chat_completed = True
                                break
                            else:
                                message_chat = submit_chat_result.get("message", "Unknown Status")
                                print_timestamped_message(
                                    f"{Fore.YELLOW}  Chat Activity: {message_chat}{Style.RESET_ALL}"
                                )
                if not ai_chat_completed:
                    print_timestamped_message(f"{Fore.YELLOW}  Retrying AI Chat...{Style.RESET_ALL}")
                    await asyncio.sleep(5)

            if not ai_chat_completed:
                print_timestamped_message(f"{Fore.RED}Failed to complete AI Chat activity after multiple attempts.{Style.RESET_ALL}")
                    
    async def run_bot_main_loop(self):
        init(autoreset=True)

        try:
            with open('accounts.txt', 'r') as file:
                account_keys = [line.strip() for line in file if line.strip()]
            
            self.display_welcome_screen()
            
            proxy_mode_choice, should_rotate_proxies = self.get_user_choice_for_proxy()
            use_private_proxy = (proxy_mode_choice == 1)

            chat_questions_list = read_json_file_data("question_lists.json")
            if not chat_questions_list:
                print_timestamped_message(f"{Fore.RED}No Questions Loaded. Please check 'question_lists.json'.{Style.RESET_ALL}")
                return

            if use_private_proxy:
                await self.load_proxies_from_file(use_private_proxy)
                if not self.proxy_list and use_private_proxy:
                    print_timestamped_message(f"{Fore.YELLOW}Warning: Private proxy selected, but no proxies found in proxy.txt. Running without proxy.{Style.RESET_ALL}")
                    use_private_proxy = False

            while True:
                self.display_welcome_screen()
                print_timestamped_message(f"{Fore.WHITE}Total Accounts: {Fore.CYAN}{len(account_keys)}{Style.RESET_ALL}")
                print_timestamped_message(f"{Fore.WHITE}Proxy Rotation: {Fore.CYAN}{'Enabled' if should_rotate_proxies and use_private_proxy else 'Disabled'}{Style.RESET_ALL}\n")

                for key_entry in account_keys:
                    if key_entry:
                        wallet_address, masked_address = extract_wallet_address_info(key_entry)
                        
                        print_timestamped_message(f"{Fore.BLUE}=== Processing Account [{masked_address}] ==={Style.RESET_ALL}")

                        if not wallet_address:
                            print_timestamped_message(
                                f"{Fore.RED}Status: Invalid Private Key or Library Version Not Supported.{Style.RESET_ALL}"
                            )
                            print_timestamped_message(f"{Fore.BLUE}======================================={Style.RESET_ALL}\n")
                            continue

                        random_user_agent = generate_random_browser_agent()

                        self.auth_header_storage[wallet_address] = {
                            "Accept": "application/json",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://app.wardenprotocol.org",
                            "Privy-App-Id": "cm7f00k5c02tibel0m4o9tdy1",
                            "Privy-Ca-Id": str(uuid.uuid4()),
                            "Privy-Client": "react-auth:2.13.8",
                            "Referer": "https://app.wardenprotocol.org/", 
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "cross-site",
                            "Sec-Fetch-Storage-Access": "active",
                            "User-Agent": random_user_agent
                        }

                        self.api_header_storage[wallet_address] = {
                            "Accept": "*/*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://app.wardenprotocol.org",
                            "Referer": "https://app.wardenprotocol.org/", 
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-site",
                            "User-Agent": random_user_agent
                        }

                        self.chat_header_storage[wallet_address] = {
                            "Accept": "*/*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://app.wardenprotocol.org",
                            "Referer": "https://app.wardenprotocol.org/", 
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "cross-site",
                            "User-Agent": random_user_agent,
                            "X-Api-Key": "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"
                        }

                        await self.process_wallet_activities(key_entry, wallet_address, chat_questions_list, use_private_proxy, should_rotate_proxies)
                        print_timestamped_message(f"{Fore.BLUE}=== Account Processing Finished ==={Style.RESET_ALL}\n")
                        await asyncio.sleep(5)

                print_timestamped_message(f"{Fore.GREEN}All accounts processed. Entering cooldown phase...{Style.RESET_ALL}")
                cooldown_seconds = 24 * 60 * 60
                while cooldown_seconds > 0:
                    formatted_cooldown = convert_seconds_to_time_string(cooldown_seconds)
                    print(
                        f"{Fore.CYAN}Next cycle in: {Fore.YELLOW}[{formatted_cooldown}]{Style.RESET_ALL}"
                        f"{Fore.WHITE} | {Fore.BLUE}Press CTRL+C to quit.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    cooldown_seconds -= 1
                print_timestamped_message(f"\n{Fore.GREEN}Initiating next processing cycle...{Style.RESET_ALL}")

        except FileNotFoundError:
            print_timestamped_message(f"{Fore.RED}Error: 'accounts.txt' file not found. Please create this file with your private keys.{Style.RESET_ALL}")
            return
        except Exception as e:
            print_timestamped_message(f"{Fore.RED}An unexpected error occurred in main loop: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    init(autoreset=True)

    try:
        bot_instance = WardenAutomation()
        asyncio.run(bot_instance.run_bot_main_loop())
    except KeyboardInterrupt:
        print(
            f"\n{Fore.RED}>> Bot Terminated by User.{Style.RESET_ALL}                                       "                              
        )
    except Exception as e:
        print(
            f"\n{Fore.RED}>> An unhandled error occurred: {e}{Style.RESET_ALL}                                       "                              
        )
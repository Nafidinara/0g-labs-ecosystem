import os
import sys
import asyncio
import random
import time
from web3 import Web3
from web3connect import connect
from eth_account import Account
from colorama import init, Fore, Style
from eth_abi import abi

# Khởi tạo colorama
init(autoreset=True)

# Độ rộng viền
BORDER_WIDTH = 80

# Constants
NETWORK_URL = "https://evmrpc-testnet.0g.ai"
CHAIN_ID = 16600
EXPLORER_URL = "https://chainscan-newton.0g.ai/tx/0x"
ROUTER_ADDRESS = "0xE233D75Ce6f04C04610947188DEC7C55790beF3b"

# Token configurations
TOKENS = {
    "USDT": {"address": "0x9A87C2412d500343c073E5Ae5394E3bE3874F76b", "decimals": 18},
    "BTC": {"address": "0x1e0d871472973c562650e991ed8006549f8cbefc", "decimals": 18},
    "ETH": {"address": "0xce830D0905e0f7A9b300401729761579c5FB6bd6", "decimals": 18},
}

# Router ABI cho swap
ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "internalType": "struct ISwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    }
]

# ERC20 ABI cho approve và balance
ERC20_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "address", "name": "", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Từ vựng song ngữ
LANG = {
    'vi': {
        'title': '✨ SWAP TOKEN - OG LABS TESTNET ✨',
        'info': 'ℹ Thông tin',
        'found': 'Tìm thấy',
        'wallets': 'ví',
        'select_swap_type': '✦ CHỌN KIỂU SWAP',
        'random_option': '1. Swap token ngẫu nhiên',
        'manual_option': '2. Swap token thủ công',
        'choice_prompt': 'Nhập lựa chọn (1 hoặc 2): ',
        'enter_swap_count': '✦ NHẬP SỐ LƯỢNG SWAP',
        'swap_count_prompt': 'Số lần swap (mặc định 1): ',
        'enter_amount': '✦ NHẬP SỐ LƯỢNG TOKEN SWAP',
        'amount_prompt': 'Số lượng token (mặc định 0.1): ',
        'select_manual_swap': '✦ CHỌN CẶP SWAP THỦ CÔNG',
        'start_random': '✨ BẮT ĐẦU {swap_count} SWAP NGẪU NHIÊN',
        'start_manual': '✨ BẮT ĐẦU SWAP THỦ CÔNG',
        'processing_wallet': '⚙ XỬ LÝ VÍ',
        'swap': 'Swap',
        'approving': 'Đang approve token...',
        'swapping': 'Đang thực hiện swap...',
        'success': '✅ Swap thành công!',
        'failure': '❌ Swap thất bại',
        'address': 'Địa chỉ ví',
        'gas': 'Gas',
        'block': 'Khối',
        'balance': 'Số dư',
        'pausing': 'Tạm nghỉ',
        'seconds': 'giây',
        'completed': '🏁 HOÀN THÀNH: {successful}/{total} SWAP THÀNH CÔNG',
        'error': 'Lỗi',
        'invalid_number': 'Vui lòng nhập số hợp lệ',
        'swap_count_error': 'Số lần swap phải lớn hơn 0',
        'amount_error': 'Số lượng token phải lớn hơn 0',
        'invalid_choice': 'Lựa chọn không hợp lệ',
        'connect_success': '✅ Thành công: Đã kết nối mạng OG Labs Testnet',
        'connect_error': '❌ Không thể kết nối RPC',
        'web3_error': '❌ Kết nối Web3 thất bại',
        'pvkey_not_found': '❌ File pvkey.txt không tồn tại',
        'pvkey_empty': '❌ Không tìm thấy private key hợp lệ',
        'pvkey_error': '❌ Đọc pvkey.txt thất bại',
        'no_balance': '❌ Không đủ số dư token hoặc A0GI để swap',
        'selected': 'Đã chọn',
        'manual_swap_options': {
            1: '1. Swap USDT -> ETH',
            2: '2. Swap ETH -> USDT',
            3: '3. Swap USDT -> BTC',
            4: '4. Swap BTC -> USDT',
            5: '5. Swap BTC -> ETH',
            6: '6. Swap ETH -> BTC',
        },
        'manual_swap_prompt': 'Chọn cặp swap (1-6): ',
    },
    'en': {
        'title': '✨ SWAP TOKEN - OG LABS TESTNET ✨',
        'info': 'ℹ Info',
        'found': 'Found',
        'wallets': 'wallets',
        'select_swap_type': '✦ SELECT SWAP TYPE',
        'random_option': '1. Random token swap',
        'manual_option': '2. Manual token swap',
        'choice_prompt': 'Enter choice (1 or 2): ',
        'enter_swap_count': '✦ ENTER NUMBER OF SWAPS',
        'swap_count_prompt': 'Number of swaps (default 1): ',
        'enter_amount': '✦ ENTER TOKEN AMOUNT TO SWAP',
        'amount_prompt': 'Token amount (default 0.1): ',
        'select_manual_swap': '✦ SELECT MANUAL SWAP PAIR',
        'start_random': '✨ STARTING {swap_count} RANDOM SWAPS',
        'start_manual': '✨ STARTING MANUAL SWAP',
        'processing_wallet': '⚙ PROCESSING WALLET',
        'swap': 'Swap',
        'approving': 'Approving token...',
        'swapping': 'Performing swap...',
        'success': '✅ Swap successful!',
        'failure': '❌ Swap failed',
        'address': 'Wallet address',
        'gas': 'Gas',
        'block': 'Block',
        'balance': 'Balance',
        'pausing': 'Pausing',
        'seconds': 'seconds',
        'completed': '🏁 COMPLETED: {successful}/{total} SWAPS SUCCESSFUL',
        'error': 'Error',
        'invalid_number': 'Please enter a valid number',
        'swap_count_error': 'Number of swaps must be greater than 0',
        'amount_error': 'Token amount must be greater than 0',
        'invalid_choice': 'Invalid choice',
        'connect_success': '✅ Success: Connected to OG Labs Testnet',
        'connect_error': '❌ Failed to connect to RPC',
        'web3_error': '❌ Web3 connection failed',
        'pvkey_not_found': '❌ pvkey.txt file not found',
        'pvkey_empty': '❌ No valid private keys found',
        'pvkey_error': '❌ Failed to read pvkey.txt',
        'no_balance': '❌ Insufficient token or A0GI balance for swap',
        'selected': 'Selected',
        'manual_swap_options': {
            1: '1. Swap USDT -> ETH',
            2: '2. Swap ETH -> USDT',
            3: '3. Swap USDT -> BTC',
            4: '4. Swap BTC -> USDT',
            5: '5. Swap BTC -> ETH',
            6: '6. Swap ETH -> BTC',
        },
        'manual_swap_prompt': 'Select swap pair (1-6): ',
    }
}

def update_lang_dictionary():
    # Add these new keys to your existing LANG dictionary
    LANG['vi']['enter_percentage'] = '✦ NHẬP PHẦN TRĂM MUỐN SWAP'
    LANG['vi']['percentage_prompt'] = 'Phần trăm token muốn swap (mặc định 50%): '
    LANG['vi']['percentage_error'] = 'Phần trăm phải từ 1 đến 100'
    LANG['vi']['selected_percent'] = 'Đã chọn: {percent}% token'
    LANG['vi']['calculating_amount'] = 'Đang tính toán số lượng token ({percent}% của {balance}): {amount} {symbol}'
    
    LANG['en']['enter_percentage'] = '✦ ENTER PERCENTAGE TO SWAP'
    LANG['en']['percentage_prompt'] = 'Percentage of token to swap (default 50%): '
    LANG['en']['percentage_error'] = 'Percentage must be between 1 and 100'
    LANG['en']['selected_percent'] = 'Selected: {percent}% of tokens'
    LANG['en']['calculating_amount'] = 'Calculating amount ({percent}% of {balance}): {amount} {symbol}'

# Hàm hiển thị viền đẹp mắt
def print_border(text: str, color=Fore.CYAN, width=BORDER_WIDTH):
    text = text.strip()
    if len(text) > width - 4:
        text = text[:width - 7] + "..."
    padded_text = f" {text} ".center(width - 2)
    print(f"{color}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    print(f"{color}║{padded_text}║{Style.RESET_ALL}")
    print(f"{color}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")

# Replace the get_swap_amount function with get_swap_percentage
def get_swap_percentage(language: str = 'en') -> float:
    print_border(LANG[language]['enter_percentage'], Fore.YELLOW)
    while True:
        try:
            percent_input = input(f"{Fore.YELLOW}  > {LANG[language]['percentage_prompt']}{Style.RESET_ALL}")
            percent = float(percent_input) if percent_input.strip() else 50.0
            if percent <= 0 or percent > 100:
                print(f"{Fore.RED}  ✖ {LANG[language]['error']}: {LANG[language]['percentage_error']}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}  ✔ {LANG[language]['selected_percent'].format(percent=percent)}{Style.RESET_ALL}")
                return percent
        except ValueError:
            print(f"{Fore.RED}  ✖ {LANG[language]['error']}: {LANG[language]['invalid_number']}{Style.RESET_ALL}")

# Hàm hiển thị phân cách
def print_separator(color=Fore.MAGENTA):
    print(f"{color}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")

# Hàm kiểm tra private key hợp lệ
def is_valid_private_key(key: str) -> bool:
    key = key.strip()
    if not key.startswith('0x'):
        key = '0x' + key
    try:
        bytes.fromhex(key.replace('0x', ''))
        return len(key) == 66
    except ValueError:
        return False

# Hàm đọc private keys từ file pvkey.txt
def load_private_keys(file_path: str = "pvkey.txt", language: str = 'en') -> list:
    try:
        if not os.path.exists(file_path):
            print(f"{Fore.RED}  ✖ {LANG[language]['pvkey_not_found']}{Style.RESET_ALL}")
            with open(file_path, 'w') as f:
                f.write("# Thêm private keys vào đây, mỗi key trên một dòng\n# Ví dụ: 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef\n")
            sys.exit(1)
        
        valid_keys = []
        with open(file_path, 'r') as f:
            for i, line in enumerate(f, 1):
                key = line.strip()
                if key and not key.startswith('#'):
                    if is_valid_private_key(key):
                        if not key.startswith('0x'):
                            key = '0x' + key
                        valid_keys.append((i, key))
                    else:
                        print(f"{Fore.YELLOW}  ⚠ {LANG[language]['error']}: Dòng {i} - {key} {LANG[language]['invalid_choice']}{Style.RESET_ALL}")
        
        if not valid_keys:
            print(f"{Fore.RED}  ✖ {LANG[language]['pvkey_empty']}{Style.RESET_ALL}")
            sys.exit(1)
        
        return valid_keys
    except Exception as e:
        print(f"{Fore.RED}  ✖ {LANG[language]['pvkey_error']}: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

# Hàm kết nối Web3
def connect_web3(language: str = 'en'):
    try:
        w3 = Web3(Web3.HTTPProvider(NETWORK_URL))
        if w3.is_connected():
            print(f"{Fore.GREEN}  ✔ {LANG[language]['connect_success']} | Chain ID: {w3.eth.chain_id}{Style.RESET_ALL}")
            return w3
        else:
            print(f"{Fore.RED}  ✖ {LANG[language]['connect_error']}{Style.RESET_ALL}")
            sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}  ✖ {LANG[language]['web3_error']}: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

# Hàm approve token
# Add nonce handling to the swap_tokens function
async def swap_tokens(w3: Web3, private_key: str, token_in: str, token_out: str, amount_in: int, token_in_symbol: str, token_out_symbol: str, language: str = 'en'):
    account = Account.from_key(private_key)
    router_contract = w3.eth.contract(address=Web3.to_checksum_address(ROUTER_ADDRESS), abi=ROUTER_ABI)

    try:
        # Approve token trước khi swap
        if not await approve_token(w3, private_key, token_in, ROUTER_ADDRESS, amount_in, language):
            return False

        # Chuẩn bị tham số swap
        swap_params = {
            "tokenIn": Web3.to_checksum_address(token_in),
            "tokenOut": Web3.to_checksum_address(token_out),
            "fee": 3000,  # 0.3%
            "recipient": account.address,
            "deadline": int(time.time()) + 1800,  # 30 phút
            "amountIn": amount_in,
            "amountOutMinimum": 0,
            "sqrtPriceLimitX96": 0,
        }

        # Get transaction parameters
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = w3.to_wei('70', 'gwei')  # Fixed gas price
        
        # RESTORE ORIGINAL GAS ESTIMATION LOGIC
        try:
            estimated_gas = router_contract.functions.exactInputSingle(swap_params).estimate_gas({
                'from': account.address,
                'value': 0
            })
            gas_limit = int(estimated_gas * 1.2)
            print(f"{Fore.YELLOW}  - Gas ước lượng: {estimated_gas} | Gas limit sử dụng: {gas_limit}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}  - Không thể ước lượng gas: {str(e)}. Dùng gas mặc định: 500000{Style.RESET_ALL}")
            gas_limit = 500000  # Higher default gas limit

        # Check if user has enough A0GI for gas
        balance = w3.from_wei(w3.eth.get_balance(account.address), 'ether')
        required_balance = w3.from_wei(gas_limit * gas_price, 'ether')
        if balance < required_balance:
            print(f"{Fore.RED}  ✖ {LANG[language]['no_balance']} (Cần: {required_balance:.6f} A0GI, Có: {balance:.6f} A0GI){Style.RESET_ALL}")
            return False

        # Function to execute transaction with nonce handling
        async def execute_transaction_with_nonce_handling(nonce=None):
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # If nonce isn't provided, get it from the network
                    if nonce is None:
                        nonce = w3.eth.get_transaction_count(account.address)
                    
                    # Build transaction
                    tx = router_contract.functions.exactInputSingle(swap_params).build_transaction({
                        'from': account.address,
                        'nonce': nonce,
                        'gas': gas_limit,
                        'gasPrice': gas_price,
                        'chainId': CHAIN_ID,
                    })
                    
                    print(f"{Fore.CYAN}  > {LANG[language]['swapping']} (Nonce: {nonce}){Style.RESET_ALL}")
                    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    tx_link = f"{EXPLORER_URL}{tx_hash.hex()}"
                    receipt = await asyncio.get_event_loop().run_in_executor(None, lambda: w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180))
                    
                    return True, receipt, tx_hash, tx_link
                
                except Exception as e:
                    error_str = str(e)
                    if "invalid nonce" in error_str.lower():
                        # Extract expected nonce from error message
                        try:
                            # Parse the error message to get the expected nonce
                            # Format: 'invalid nonce; got X, expected Y, ...'
                            expected_nonce_str = error_str.split('expected ')[1].split(',')[0]
                            expected_nonce = int(expected_nonce_str)
                            print(f"{Fore.YELLOW}  ⚠ Nonce không hợp lệ. Thử lại với nonce: {expected_nonce}{Style.RESET_ALL}")
                            nonce = expected_nonce
                            retry_count += 1
                            # No need to sleep here as we're using the correct nonce
                        except:
                            # If we can't parse the expected nonce, get a fresh one from network
                            print(f"{Fore.YELLOW}  ⚠ Nonce không hợp lệ. Đang lấy nonce mới từ mạng...{Style.RESET_ALL}")
                            await asyncio.sleep(2)  # Wait a bit before getting a fresh nonce
                            nonce = w3.eth.get_transaction_count(account.address)
                            retry_count += 1
                    else:
                        # Other error not related to nonce
                        print(f"{Fore.RED}  ✖ Swap thất bại: {str(e)}{Style.RESET_ALL}")
                        return False, None, None, None
            
            # If we've exhausted retries
            print(f"{Fore.RED}  ✖ Swap thất bại sau {max_retries} lần thử{Style.RESET_ALL}")
            return False, None, None, None

        # Execute transaction with nonce handling
        success, receipt, tx_hash, tx_link = await execute_transaction_with_nonce_handling()
        
        if success and receipt.status == 1:
            # Get token balances after swap to calculate amount received
            try:
                # Try to extract amountOut from logs, but handle missing logs gracefully
                amount_out = 0
                if receipt.logs and len(receipt.logs) > 0:
                    try:
                        amount_out_data = receipt.logs[0].data[-32:]  # Lấy amountOut từ log
                        amount_out = int.from_bytes(amount_out_data, 'big')
                    except (IndexError, Exception) as e:
                        print(f"{Fore.YELLOW}  ⚠ Không thể lấy số lượng token ra từ logs: {str(e)}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}  ⚠ Giao dịch thành công nhưng không có logs để lấy số lượng token ra{Style.RESET_ALL}")
                
                # Get post-swap balances
                token_in_balance = w3.eth.contract(address=Web3.to_checksum_address(token_in), abi=ERC20_ABI).functions.balanceOf(account.address).call() / 10**18
                token_out_balance = w3.eth.contract(address=Web3.to_checksum_address(token_out), abi=ERC20_ABI).functions.balanceOf(account.address).call() / 10**18
                
                print(f"{Fore.GREEN}  ✔ {LANG[language]['success']}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    - {LANG[language]['address']}: {account.address}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    - Số lượng vào: {amount_in / 10**18:.6f} {token_in_symbol}{Style.RESET_ALL}")
                if amount_out > 0:
                    print(f"{Fore.YELLOW}    - Số lượng ra: {amount_out / 10**18:.6f} {token_out_symbol}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    - {LANG[language]['balance']} {token_in_symbol}: {token_in_balance:.6f}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    - {LANG[language]['balance']} {token_out_symbol}: {token_out_balance:.6f}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    - {LANG[language]['gas']}: {receipt['gasUsed']}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    - {LANG[language]['block']}: {receipt['blockNumber']}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    - Tx: {tx_link}{Style.RESET_ALL}")
                return True
            except Exception as e:
                # If we can't get the output amount, still report success but mention the error
                print(f"{Fore.GREEN}  ✔ {LANG[language]['success']} (Không thể lấy chi tiết: {str(e)}){Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    - Tx: {tx_link}{Style.RESET_ALL}")
                return True
        else:
            if tx_link:
                print(f"{Fore.RED}  ✖ {LANG[language]['failure']} | Tx: {tx_link}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}  ✖ {LANG[language]['failure']}{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}  ✖ Swap thất bại: {str(e)}{Style.RESET_ALL}")
        return False

# Modify the approve_token function to handle nonce errors too
async def approve_token(w3: Web3, private_key: str, token_address: str, spender: str, amount: int, language: str = 'en'):
    account = Account.from_key(private_key)
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
    
    try:
        allowance = token_contract.functions.allowance(account.address, spender).call()
        if allowance >= amount:
            print(f"{Fore.GREEN}  ✔ Đã có allowance đủ cho {spender}{Style.RESET_ALL}")
            return True

        # Set max approval amount (2^256 - 1)
        max_approval = 2**256 - 1
        print(f"{Fore.YELLOW}  > Setting unlimited approval (max uint256){Style.RESET_ALL}")
        
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = w3.to_wei('70', 'gwei')  # Fixed gas price
        
        # RESTORE ORIGINAL GAS ESTIMATION LOGIC
        try:
            estimated_gas = token_contract.functions.approve(spender, max_approval).estimate_gas({
                'from': account.address
            })
            gas_limit = int(estimated_gas * 1.2)
        except Exception as e:
            print(f"{Fore.YELLOW}  - Không thể ước lượng gas cho approve: {str(e)}. Dùng gas mặc định: 100000{Style.RESET_ALL}")
            gas_limit = 100000

        # Function to execute approve with nonce handling
        async def execute_approve_with_nonce_handling(nonce=None):
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # If nonce isn't provided, get it from the network
                    if nonce is None:
                        nonce = w3.eth.get_transaction_count(account.address)
                    
                    # Build transaction with max approval
                    tx = token_contract.functions.approve(spender, max_approval).build_transaction({
                        'from': account.address,
                        'nonce': nonce,
                        'gas': gas_limit,
                        'gasPrice': gas_price,
                        'chainId': CHAIN_ID,
                    })
                    
                    print(f"{Fore.CYAN}  > {LANG[language]['approving']} (Nonce: {nonce}){Style.RESET_ALL}")
                    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    receipt = await asyncio.get_event_loop().run_in_executor(None, lambda: w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180))
                    
                    return True, receipt, tx_hash
                
                except Exception as e:
                    error_str = str(e)
                    if "invalid nonce" in error_str.lower():
                        # Extract expected nonce from error message
                        try:
                            # Parse the error message to get the expected nonce
                            expected_nonce_str = error_str.split('expected ')[1].split(',')[0]
                            expected_nonce = int(expected_nonce_str)
                            print(f"{Fore.YELLOW}  ⚠ Nonce không hợp lệ. Thử lại với nonce: {expected_nonce}{Style.RESET_ALL}")
                            nonce = expected_nonce
                            retry_count += 1
                        except:
                            # If we can't parse the expected nonce, get a fresh one from network
                            print(f"{Fore.YELLOW}  ⚠ Nonce không hợp lệ. Đang lấy nonce mới từ mạng...{Style.RESET_ALL}")
                            await asyncio.sleep(2)
                            nonce = w3.eth.get_transaction_count(account.address)
                            retry_count += 1
                    else:
                        # Other error not related to nonce
                        print(f"{Fore.RED}  ✖ Approve thất bại: {str(e)}{Style.RESET_ALL}")
                        return False, None, None
            
            # If we've exhausted retries
            print(f"{Fore.RED}  ✖ Approve thất bại sau {max_retries} lần thử{Style.RESET_ALL}")
            return False, None, None

        # Execute transaction with nonce handling
        success, receipt, tx_hash = await execute_approve_with_nonce_handling()
        
        if success and receipt.status == 1:
            print(f"{Fore.GREEN}  ✔ Approve thành công | Tx: {EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}")
            return True
        else:
            if tx_hash:
                print(f"{Fore.RED}  ✖ Approve thất bại | Tx: {EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}  ✖ Approve thất bại{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}  ✖ Approve thất bại: {str(e)}{Style.RESET_ALL}")
        return False

# Hàm nhập số lượng swap
def get_swap_count(language: str = 'en') -> int:
    print_border(LANG[language]['enter_swap_count'], Fore.YELLOW)
    while True:
        try:
            swap_count_input = input(f"{Fore.YELLOW}  > {LANG[language]['swap_count_prompt']}{Style.RESET_ALL}")
            swap_count = int(swap_count_input) if swap_count_input.strip() else 1
            if swap_count <= 0:
                print(f"{Fore.RED}  ✖ {LANG[language]['error']}: {LANG[language]['swap_count_error']}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}  ✔ {LANG[language]['selected']}: {swap_count} swaps{Style.RESET_ALL}")
                return swap_count
        except ValueError:
            print(f"{Fore.RED}  ✖ {LANG[language]['error']}: {LANG[language]['invalid_number']}{Style.RESET_ALL}")

# Hàm nhập số lượng token swap
def get_swap_amount(language: str = 'en') -> float:
    print_border(LANG[language]['enter_amount'], Fore.YELLOW)
    while True:
        try:
            amount_input = input(f"{Fore.YELLOW}  > {LANG[language]['amount_prompt']}{Style.RESET_ALL}")
            amount = float(amount_input) if amount_input.strip() else 0.1
            if amount <= 0:
                print(f"{Fore.RED}  ✖ {LANG[language]['error']}: {LANG[language]['amount_error']}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}  ✔ {LANG[language]['selected']}: {amount} token{Style.RESET_ALL}")
                return amount
        except ValueError:
            print(f"{Fore.RED}  ✖ {LANG[language]['error']}: {LANG[language]['invalid_number']}{Style.RESET_ALL}")

# Hàm hiển thị số dư
def display_balances(w3: Web3, account_address: str, language: str = 'en'):
    print(f"{Fore.YELLOW}  - {LANG[language]['balance']} USDT: {(w3.eth.contract(address=Web3.to_checksum_address(TOKENS['USDT']['address']), abi=ERC20_ABI).functions.balanceOf(account_address).call() / 10**18):.6f}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  - {LANG[language]['balance']} ETH: {(w3.eth.contract(address=Web3.to_checksum_address(TOKENS['ETH']['address']), abi=ERC20_ABI).functions.balanceOf(account_address).call() / 10**18):.6f}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  - {LANG[language]['balance']} BTC: {(w3.eth.contract(address=Web3.to_checksum_address(TOKENS['BTC']['address']), abi=ERC20_ABI).functions.balanceOf(account_address).call() / 10**18):.6f}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  - {LANG[language]['balance']} A0GI: {(w3.from_wei(w3.eth.get_balance(account_address), 'ether')):.6f}{Style.RESET_ALL}")

# Swap ngẫu nhiên
async def random_swap(w3: Web3, private_key: str, swap_count: int, percent: float, wallet_index: int, language: str = 'en'):
    account = Account.from_key(private_key)
    successful_swaps = 0
    
    for swap_num in range(swap_count):
        print(f"{Fore.CYAN}  > {LANG[language]['swap']} {swap_num + 1}/{swap_count}{Style.RESET_ALL}")
        
        # Hiển thị số dư
        display_balances(w3, account.address, language)
        
        # Lấy danh sách token có số dư
        token_balances = {}
        for symbol, token_data in TOKENS.items():
            contract = w3.eth.contract(address=Web3.to_checksum_address(token_data['address']), abi=ERC20_ABI)
            balance = contract.functions.balanceOf(account.address).call()
            token_balances[symbol] = balance
        
        tokens_with_balance = [symbol for symbol, balance in token_balances.items() if balance > 0]
        if not tokens_with_balance:
            print(f"{Fore.RED}  ✖ {LANG[language]['no_balance']}{Style.RESET_ALL}")
            break

        token_in_symbol = random.choice(tokens_with_balance)
        token_in_address = TOKENS[token_in_symbol]["address"]
        balance_wei = token_balances[token_in_symbol]
        balance = balance_wei / 10**TOKENS[token_in_symbol]["decimals"]
        
        # Calculate amount based on percentage of balance
        amount = balance * (percent / 100)
        amount_in = int(amount * 10**TOKENS[token_in_symbol]["decimals"])
        
        if amount_in <= 0:
            print(f"{Fore.RED}  ✖ {LANG[language]['no_balance']} (Số dư quá nhỏ: {balance} {token_in_symbol}){Style.RESET_ALL}")
            break
            
        # Show calculation details
        print(f"{Fore.YELLOW}  > {LANG[language]['calculating_amount'].format(percent=percent, balance=balance, amount=amount, symbol=token_in_symbol)}{Style.RESET_ALL}")

        if token_in_symbol == "USDT":
            token_out_symbol = random.choice(["ETH", "BTC"])
        else:
            token_out_symbol = "USDT"
        token_out_address = TOKENS[token_out_symbol]["address"]

        if await swap_tokens(w3, private_key, token_in_address, token_out_address, amount_in, token_in_symbol, token_out_symbol, language):
            successful_swaps += 1
        
        if swap_num < swap_count - 1:
            delay = random.uniform(10, 30)
            print(f"{Fore.YELLOW}  ℹ {LANG[language]['pausing']} {delay:.2f} {LANG[language]['seconds']}{Style.RESET_ALL}")
            await asyncio.sleep(delay)
        print_separator()
    
    return successful_swaps
    
# Modified manual_swap function with the new flow
async def manual_swap(w3: Web3, private_key: str, wallet_index: int, language: str = 'en', pair_choice=None, percent=None):
    account = Account.from_key(private_key)
    
    # 1. First display balances for this wallet
    print_separator()
    print(f"{Fore.CYAN}  > Available token balances for this wallet:{Style.RESET_ALL}")
    display_balances(w3, account.address, language)
    print_separator()
    
    # 2. Use provided pair choice or ask for it
    if pair_choice is None:
        print_border(LANG[language]['select_manual_swap'], Fore.YELLOW)
        for i in range(1, 7):
            print(f"{Fore.GREEN}    ├─ {LANG[language]['manual_swap_options'][i]}{Style.RESET_ALL}" if i < 6 else 
                f"{Fore.GREEN}    └─ {LANG[language]['manual_swap_options'][i]}{Style.RESET_ALL}")
        
        while True:
            try:
                pair_choice = int(input(f"{Fore.YELLOW}  > {LANG[language]['manual_swap_prompt']}{Style.RESET_ALL}"))
                if pair_choice in range(1, 7):
                    break
                print(f"{Fore.RED}  ✖ {LANG[language]['invalid_choice']}{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}  ✖ {LANG[language]['invalid_number']}{Style.RESET_ALL}")

    pairs = {
        1: ("USDT", "ETH"), 2: ("ETH", "USDT"), 3: ("USDT", "BTC"),
        4: ("BTC", "USDT"), 5: ("BTC", "ETH"), 6: ("ETH", "BTC")
    }
    
    token_in_symbol, token_out_symbol = pairs[pair_choice]
    token_in_address = TOKENS[token_in_symbol]["address"]
    token_out_address = TOKENS[token_out_symbol]["address"]
    
    print(f"{Fore.GREEN}  ✔ Using pair: {token_in_symbol} -> {token_out_symbol}{Style.RESET_ALL}")
    
    # 3. Get the current balance of the selected token
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_in_address), abi=ERC20_ABI)
    balance_wei = token_contract.functions.balanceOf(account.address).call()
    balance = balance_wei / 10**TOKENS[token_in_symbol]["decimals"]
    
    if balance <= 0:
        print(f"{Fore.RED}  ✖ {LANG[language]['no_balance']} (Không có {token_in_symbol} để swap){Style.RESET_ALL}")
        return 0
    
    # 4. Use provided percentage or ask for it
    if percent is None:
        percent = get_swap_percentage(language)
    else:
        print(f"{Fore.GREEN}  ✔ {LANG[language]['selected_percent'].format(percent=percent)}{Style.RESET_ALL}")
    
    # 5. Calculate actual amount based on percentage
    amount = balance * (percent / 100)
    amount_in = int(amount * 10**TOKENS[token_in_symbol]["decimals"])
    
    # 6. Show calculation details
    print(f"{Fore.YELLOW}  > {LANG[language]['calculating_amount'].format(percent=percent, balance=balance, amount=amount, symbol=token_in_symbol)}{Style.RESET_ALL}")
    
    # 7. Execute swap with calculated amount (using original gas settings)
    success = await swap_tokens(w3, private_key, token_in_address, token_out_address, amount_in, token_in_symbol, token_out_symbol, language)
    return 1 if success else 0

async def run_swaptokenzerodex(language: str = 'en'):
    # Update the language dictionary with new keys
    update_lang_dictionary()
    
    print_border(LANG[language]['title'], Fore.CYAN)
    print()

    private_keys = load_private_keys('pvkey.txt', language)
    print(f"{Fore.YELLOW}  {LANG[language]['info']}: {LANG[language]['found']} {len(private_keys)} {LANG[language]['wallets']}{Style.RESET_ALL}")
    print()

    w3 = connect_web3(language)
    print_separator()

    while True:
        print_border(LANG[language]['select_swap_type'], Fore.YELLOW)
        print(f"{Fore.GREEN}    ├─ {LANG[language]['random_option']}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}    └─ {LANG[language]['manual_option']}{Style.RESET_ALL}")
        choice = input(f"{Fore.YELLOW}  > {LANG[language]['choice_prompt']}{Style.RESET_ALL}").strip()

        if choice in ['1', '2']:
            break
        print(f"{Fore.RED}  ✖ {LANG[language]['invalid_choice']}{Style.RESET_ALL}")
        print()

    if choice == '1':
        # For random swaps, ask for number of swaps and percentage instead of absolute amount
        swap_count = get_swap_count(language)
        percent = get_swap_percentage(language)  # Now using percentage for random swaps too
    else:
        # For manual swap, we'll ask for pair and percentage once for all wallets
        # Display sample balances from the first wallet to help with decision
        if private_keys:
            first_account = Account.from_key(private_keys[0][1])
            print(f"{Fore.CYAN}  > Sample balances from first wallet:{Style.RESET_ALL}")
            display_balances(w3, first_account.address, language)
            print_separator()
        
        # Ask for swap pair once
        print_border(LANG[language]['select_manual_swap'], Fore.YELLOW)
        for i in range(1, 7):
            print(f"{Fore.GREEN}    ├─ {LANG[language]['manual_swap_options'][i]}{Style.RESET_ALL}" if i < 6 else 
                f"{Fore.GREEN}    └─ {LANG[language]['manual_swap_options'][i]}{Style.RESET_ALL}")
        
        while True:
            try:
                pair_choice = int(input(f"{Fore.YELLOW}  > {LANG[language]['manual_swap_prompt']}{Style.RESET_ALL}"))
                if pair_choice in range(1, 7):
                    break
                print(f"{Fore.RED}  ✖ {LANG[language]['invalid_choice']}{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}  ✖ {LANG[language]['invalid_number']}{Style.RESET_ALL}")
        
        # Get percentage once
        percent = get_swap_percentage(language)
        swap_count = 1

    print_separator()

    total_swaps = swap_count * len(private_keys) if choice == '1' else len(private_keys)
    successful_swaps = 0

    for i, (profile_num, private_key) in enumerate(private_keys, 1):
        print_border(f"{LANG[language]['processing_wallet']} {profile_num} ({i}/{len(private_keys)})", Fore.MAGENTA)
        conn = connect(private_key)
        print()
        
        if choice == '1':
            print_border(LANG[language]['start_random'].format(swap_count=swap_count), Fore.CYAN)
            successful_swaps += await random_swap(w3, private_key, swap_count, percent, i, language)  # Pass percent instead of amount
        else:
            print_border(LANG[language]['start_manual'], Fore.CYAN)
            # Pass the selected pair and percentage to the function
            successful_swaps += await manual_swap(w3, private_key, i, language, pair_choice, percent)
        print()

    print_border(LANG[language]['completed'].format(successful=successful_swaps, total=total_swaps), Fore.GREEN)
    print()


if __name__ == "__main__":
    asyncio.run(run_swaptokenzerodex('vi'))  # Ngôn ngữ mặc định là Tiếng Việt, đổi thành 'en' nếu muốn tiếng Anh

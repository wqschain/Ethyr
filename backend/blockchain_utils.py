from web3 import Web3
from web3.exceptions import ContractLogicError, InvalidAddress
from web3.types import ChecksumAddress
import aiohttp
import asyncio
from typing import Dict, List, Optional, Union, Any
import json
from pathlib import Path
from eth_typing import HexStr
from eth_utils import to_checksum_address, is_address
from config import Config
from datetime import datetime, timedelta
import time

# Use the singleton Config instance
config = Config()

# Initialize Web3 with Alchemy provider
w3 = config.w3  # Use the Web3 instance from config

# Add necessary ABIs
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalHolders",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

async def fetch_address_data(address: str) -> Dict:
    try:
        # Initialize response
        response = {
            'type': 'Unknown',
            'risk_score': 0.0,
            'risk_tier': 'Unknown',
            'explanation': [],
            'summary': {},
            'features': {},
            'is_contract': False,
            'is_token': False,
            'token_info': None,
            'wallet_metrics': None,
            'defi_activity': None
        }

        try:
            # Check if address is contract
            is_contract_addr = await is_contract(address)
            response['is_contract'] = is_contract_addr
            response['type'] = 'Contract' if is_contract_addr else 'Wallet'
            
            if is_contract_addr:
                # Get contract age and creation info
                contract_age = await get_contract_age(address)
                if contract_age:
                    response['summary'].update({
                        'creation_date': contract_age['creation_date'],
                        'contract_age_days': contract_age['age_days']
                    })
                
                # Get contract specific data
                contract_info = await get_contract_info(address)
                if contract_info:
                    response['summary'].update({
                        'verified': contract_info['is_verified'],
                        'contract_name': contract_info['contract_name']
                    })
                
                # Get token info if it's a token contract
                token_info = await get_token_info(address)
                
                if token_info:
                    # Get market data for the token
                    market_data = await get_token_market_data(address)
                    if market_data:
                        token_info.update(market_data)
                    
                    # Get holder info
                    holder_info = await get_token_holders_info(address)
                    if holder_info:
                        token_info.update(holder_info)
                    
                    # Get mint activity
                    mint_info = await get_mint_activity(address)
                    if mint_info:
                        token_info.update(mint_info)
                    
                    response['type'] = 'Token'
                    response['is_token'] = True
                    response['token_info'] = token_info
                    
                    # Update summary with token info
                    response['summary'].update({
                        'total_supply': token_info.get('total_supply'),
                        'total_holders': token_info.get('total_holders'),
                        'market_cap': token_info.get('market_cap'),
                        'price_usd': token_info.get('price_usd'),
                        'total_liquidity_eth': token_info.get('total_liquidity_eth'),
                        'volume_24h': token_info.get('volume_24h')
                    })
                else:
                    response['is_token'] = False
                
                # Check liquidity lock for tokens
                if response['type'] == 'Token':
                    lock_info = await check_liquidity_lock(address)
                    if lock_info:
                        response['summary'].update({
                            'lp_locked': lock_info['lp_locked']
                        })
                
                # Get burn events
                burn_events = await get_burn_events(address)
                response['summary']['burn_events'] = burn_events
                
                # Get 24h transfer volume
                transfer_volume = await get_24h_transfer_volume(address)
                response['summary']['transfer_volume_24h'] = transfer_volume
                
                # Add features for risk assessment
                response['features'] = {
                    'verified_contract': contract_info.get('is_verified', False) if contract_info else False,
                    'owner_address': await get_creator_info(address),
                    'is_owner_deployer': await compare_owner_deployer(address),  # Implemented comparison
                    'has_mint_privileges': mint_info.get('has_mint_privileges', False) if 'mint_info' in locals() else False,
                    'mint_event_count': mint_info.get('mint_event_count', 0) if 'mint_info' in locals() else 0,
                    'honeypot_result': await simulate_honeypot(address),
                    'lp_locked': lock_info.get('lp_locked', False) if 'lock_info' in locals() else False,
                    'contract_age_days': contract_age.get('age_days', 0) if contract_age else 0,
                    'burn_event_count': burn_events,
                    'transfer_volume_24h': transfer_volume,
                    'is_contract': True
                }
                
                # Calculate risk score based on features
                risk_factors = []
                risk_score = 0.0
                
                # Unverified contract
                if not response['features']['verified_contract']:
                    risk_score += 0.35
                    risk_factors.append("The contract source code is not verified on Etherscan, making it difficult to audit its functionality. (Impact: 0.35)")
                
                # Unlocked liquidity
                if not response['features']['lp_locked'] and response['is_token']:
                    risk_score += 0.30
                    risk_factors.append("The liquidity is not locked, allowing for potential rug pulls or token dumps. (Impact: 0.30)")
                
                # New contract
                if response['features']['contract_age_days'] < 30:
                    risk_score += 0.20
                    risk_factors.append("This is a newly deployed contract with limited history and community trust. (Impact: 0.20)")
                
                # Mint privileges
                if response['features']['has_mint_privileges']:
                    risk_score += 0.15
                    risk_factors.append("The contract has minting privileges, which could be used to inflate the token supply. (Impact: 0.15)")
                
                # Honeypot risk
                if response['features']['honeypot_result']:
                    risk_score += 0.25
                    risk_factors.append("The contract shows patterns similar to known honeypot scams. (Impact: 0.25)")
                
                # Risk factor combinations
                if not response['features']['verified_contract'] and response['features']['contract_age_days'] < 30:
                    risk_score += 0.15
                    risk_factors.append("\nRisk Factor Combinations:")
                    risk_factors.append("- Combined impact of unverified_contract and new_contract increases overall risk by 15%")
                
                # Cap risk score at 0.99
                risk_score = min(risk_score, 0.99)
                
                # Add analysis overview
                overview = f"Analysis Overview: This is an {'unverified' if not response['features']['verified_contract'] else 'verified'} "
                overview += f"contract created {response['features']['contract_age_days']} days ago. "
                overview += f"Liquidity is {'not ' if not response['features']['lp_locked'] else ''}locked. "
                overview += f"Honeypot test {'failed' if response['features']['honeypot_result'] else 'passed'}. "
                overview += f"There were {response['features']['burn_event_count']} burn events"
                
                response['explanation'] = [
                    overview,
                    f"Risk Assessment: This address has been classified as {'High Risk' if risk_score > 0.7 else 'Moderate Risk' if risk_score > 0.3 else 'Safe'} with a risk score of {risk_score:.2f}",
                    "\nDetected Risk Factors:"
                ]
                response['explanation'].extend(risk_factors)
                response['explanation'].append("\nRecommendation: " + (
                    "Exercise extreme caution when interacting with this address. Consider avoiding transactions unless you fully understand the risks."
                    if risk_score > 0.7 else
                    "Proceed with caution and conduct thorough due diligence before any significant interactions."
                    if risk_score > 0.3 else
                    "This address appears to be relatively safe based on our analysis, but always exercise normal caution."
                ))
                
                response['risk_score'] = risk_score
                response['risk_tier'] = 'High Risk' if risk_score > 0.7 else 'Moderate Risk' if risk_score > 0.3 else 'Safe'
                
            else:
                # Get wallet metrics
                wallet_metrics = await get_wallet_metrics(address)
                if wallet_metrics:
                    response['summary'].update(wallet_metrics)
                    response['wallet_metrics'] = wallet_metrics
                
                # Get DeFi activity for wallets
                defi_activity = await get_defi_interactions(address)
                if defi_activity:
                    response['summary'].update(defi_activity)
                    response['defi_activity'] = defi_activity
                
                response['features'] = {
                    'verified_contract': False,
                    'owner_address': None,
                    'is_owner_deployer': False,
                    'has_mint_privileges': False,
                    'mint_event_count': 0,
                    'honeypot_result': False,
                    'lp_locked': False,
                    'contract_age_days': 0,
                    'burn_event_count': 0,
                    'transfer_volume_24h': 0,
                    'is_contract': False
                }

            return response

        except Exception as inner_e:
            return {
                'type': 'Error',
                'risk_score': 0.0,
                'risk_tier': 'Unknown',
                'explanation': [f"Error processing address: {str(inner_e)}"],
                'summary': {},
                'features': {},
                'is_contract': False,
                'is_token': False,
                'token_info': None,
                'wallet_metrics': None,
                'defi_activity': None
            }

    except Exception as e:
        return {
            'type': 'Error',
            'risk_score': 0.0,
            'risk_tier': 'Unknown',
            'explanation': [f"Critical error: {str(e)}"],
            'summary': {},
            'features': {},
            'is_contract': False,
            'is_token': False,
            'token_info': None,
            'wallet_metrics': None,
            'defi_activity': None
        }

async def fetch_transactions(address: str, limit: int = 100) -> List[Dict]:
    """Fetch recent transactions for an address"""
    try:
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'page': '1',
            'offset': str(limit),
            'sort': 'desc',
            'apikey': config.etherscan_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1':
                        return data['result']
                return []
    except Exception as e:
        return []

async def fetch_contract_data(address: str) -> Optional[Dict]:
    """Fetch contract data from Etherscan"""
    try:
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
            'apikey': config.etherscan_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1' and data['result']:
                        return {
                            'is_verified': bool(data['result'][0].get('SourceCode')),
                            'contract_name': data['result'][0].get('ContractName'),
                            'compiler_version': data['result'][0].get('CompilerVersion'),
                            'source_code': data['result'][0].get('SourceCode', '')[:1000]  # Truncate for efficiency
                        }
                return None
    except Exception as e:
        return None

async def get_contract_creator(address: str) -> Optional[str]:
    """Get the creator address of a contract"""
    try:
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'page': '1',
            'offset': '1',
            'sort': 'asc',
            'apikey': config.etherscan_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1' and data['result']:
                        return data['result'][0].get('from')
                return None
    except Exception as e:
        return None

async def get_token_info(address: str) -> Dict:
    """
    Get ERC20/ERC721 token information using Alchemy's token API
    """
    try:
        # Use Alchemy's getTokenMetadata endpoint
        async with aiohttp.ClientSession() as session:
            params = {
                'contractAddress': address
            }
            headers = {
                'accept': 'application/json',
                'content-type': 'application/json'
            }
            url = f"{config.alchemy_url}/getTokenMetadata"
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        return {
                            'name': data.get('name', ''),
                            'symbol': data.get('symbol', ''),
                            'decimals': int(data.get('decimals', 18)),
                            'total_supply': int(data.get('totalSupply', 0))
                        }
        
        # Fallback to contract calls if Alchemy fails
        erc20_abi = json.loads('[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]')
        
        contract = w3.eth.contract(address=address, abi=erc20_abi)
        
        name = await contract.functions.name().call()
        symbol = await contract.functions.symbol().call()
        decimals = await contract.functions.decimals().call()
        total_supply = await contract.functions.totalSupply().call()
        
        return {
            'name': name,
            'symbol': symbol,
            'decimals': decimals,
            'total_supply': total_supply
        }
            
    except Exception as e:
        return {}

async def is_contract(address: str) -> bool:
    """Check if address is a contract"""
    try:
        code = await w3.eth.get_code(address)
        return code != '0x' and code != b''
    except Exception as e:
        return False

async def get_contract_info(address: str) -> Dict:
    """Fetch contract information from Etherscan."""
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "module": "contract",
                "action": "getsourcecode",
                "address": address,
                "apikey": config.ETHERSCAN_API_KEY
            }
            async with session.get(config.ETHERSCAN_URL, params=params) as response:
                data = await response.json()
                
                if data["status"] != "1":
                    return {"is_verified": False, "contract_name": None, "compiler": None}
                
                result = data["result"][0]
                return {
                    "is_verified": bool(result["SourceCode"]),
                    "contract_name": result["ContractName"],
                    "compiler": result["CompilerVersion"]
                }
    except Exception:
        return {"is_verified": False, "contract_name": None, "compiler": None}

async def get_creator_info(address: str) -> Optional[str]:
    """Get the contract creator address from Etherscan."""
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "module": "contract",
                "action": "getcontractcreator",
                "contractaddresses": address,
                "apikey": config.ETHERSCAN_API_KEY
            }
            async with session.get(config.ETHERSCAN_URL, params=params) as response:
                data = await response.json()
                
                if data["status"] == "1" and data["result"]:
                    return data["result"][0]["contractCreator"]
                return None
    except Exception:
        return None

async def get_mint_activity(address: str) -> Dict:
    """Get mint activity for a contract"""
    try:
        # Get contract code and ABI
        code = await get_contract_code(address)
        if code == '0x':
            return {"mint_event_count": 0, "has_mint_privileges": False}
            
        # Check for mint function signatures
        mint_signatures = [
            '0x40c10f19',  # mint(address,uint256)
            '0xa0712d68',  # mint(uint256)
            '0x6a627842'   # mint(address)
        ]
        
        has_mint = any(sig in code for sig in mint_signatures)
        
        # Get mint events
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'startblock': '0',
            'endblock': '99999999',
            'sort': 'desc',
            'apikey': config.etherscan_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1':
                        mint_count = len([tx for tx in data['result'] if tx['from'] == '0x0000000000000000000000000000000000000000'])
                        return {
                            "mint_event_count": mint_count,
                            "has_mint_privileges": has_mint
                        }
        
        return {"mint_event_count": 0, "has_mint_privileges": has_mint}
    except Exception as e:
        return {'mint_event_count': 0, 'has_mint_privileges': False}

async def simulate_honeypot(address: str) -> bool:
    """Simulate if contract might be a honeypot"""
    try:
        # Basic honeypot check - look for suspicious patterns
        code = await get_contract_code(address)
        if not code or code == '0x':
            return False
            
        # Check for common honeypot patterns
        suspicious_patterns = [
            '0x8d80ff0a',  # Selfdestruct function
            '0xf8b2cb4f',  # Balance check
            '0x70a08231'   # balanceOf
        ]
        
        return any(pattern in code.lower() for pattern in suspicious_patterns)
    except Exception as e:
        return False

async def get_token_holders_info(address: str) -> Dict:
    """
    Get token holder statistics using batched requests
    """
    try:
        # Get block number from 24h ago
        block_24h_ago = await get_block_number_24h_ago()
        
        # Fetch transfers in batches
        transfers = await batch_fetch_transfers(address, block_24h_ago)
        
        if not transfers:
            return {
                'holder_activity': {
                    'active_addresses': 0,
                    'buy_sell_ratio': '0:0',
                    'avg_transaction': 0
                },
                'whale_analysis': {
                    'large_transactions': 0,
                    'accumulation_events': 0,
                    'disposal_events': 0
                },
                'contract_interactions': {
                    'defi_interactions': 0,
                    'unique_contracts': 0,
                    'top_contracts': []
                },
                'trading_patterns': {
                    'avg_holding_time': '0s',
                    'active_pairs': 0
                }
            }
        
        # Get token decimals for proper value calculation
        decimals = 18  # default
        try:
            token_contract = w3.eth.contract(address=address, abi=ERC20_ABI)
            decimals = await token_contract.functions.decimals().call()
        except Exception:
            pass
            
        # Process transfers to get unique addresses and transaction data
        unique_addresses = set()
        buy_count = 0
        sell_count = 0
        total_amount = 0
        large_tx_count = 0
        accumulation_events = 0
        disposal_events = 0
        
        # Define whale threshold (0.1% of total supply or $100k worth, whichever is less)
        total_supply = float(transfers[0].get('total_supply', 0)) if transfers else 0
        whale_threshold_supply = total_supply * 0.001 if total_supply > 0 else 0
        
        # Get current price for USD threshold
        price_usd = 0
        try:
            market_data = await get_token_market_data(address)
            if market_data and 'price_usd' in market_data:
                price_usd = market_data['price_usd']
        except Exception:
            pass
            
        whale_threshold_usd = 100000 / price_usd if price_usd > 0 else float('inf')
        whale_threshold = min(whale_threshold_supply, whale_threshold_usd)
        
        # Track address balances
        address_balances = {}
        
        for transfer in transfers:
            from_addr = transfer.get('from', '').lower()
            to_addr = transfer.get('to', '').lower()
            amount = float(transfer.get('value', 0))
            
            # Update unique addresses
            if from_addr and from_addr != address.lower():
                unique_addresses.add(from_addr)
            if to_addr and to_addr != address.lower():
                unique_addresses.add(to_addr)
            
            # Track balances
            if from_addr != address.lower():
                address_balances[from_addr] = address_balances.get(from_addr, 0) - amount
                if from_addr not in KNOWN_PROTOCOLS:
                    disposal_events += 1
            
            if to_addr != address.lower():
                address_balances[to_addr] = address_balances.get(to_addr, 0) + amount
                if to_addr not in KNOWN_PROTOCOLS:
                    accumulation_events += 1
            
            # Count buys/sells (excluding contract interactions)
            if from_addr in KNOWN_PROTOCOLS:
                buy_count += 1
            elif to_addr in KNOWN_PROTOCOLS:
                sell_count += 1
            
            # Track large transactions
            if amount > whale_threshold:
                large_tx_count += 1
            
            total_amount += amount
        
        # Calculate metrics
        avg_transaction = total_amount / len(transfers) if transfers else 0
        
        return {
            'holder_activity': {
                'active_addresses': len(unique_addresses),
                'buy_sell_ratio': f"{buy_count}:{sell_count}",
                'avg_transaction': avg_transaction
            },
            'whale_analysis': {
                'large_transactions': large_tx_count,
                'accumulation_events': accumulation_events,
                'disposal_events': disposal_events
            },
            'contract_interactions': await get_contract_interactions(address, transfers),
            'trading_patterns': {
                'avg_holding_time': await calculate_avg_holding_time(transfers),
                'active_pairs': len([addr for addr in unique_addresses if addr in KNOWN_PROTOCOLS])
            }
        }
        
    except Exception as e:
        return {}

async def calculate_avg_holding_time(transfers: List[Dict]) -> str:
    """Calculate average holding time between transfers"""
    try:
        from datetime import datetime
        
        # Sort transfers by timestamp
        def parse_timestamp(transfer):
            # Handle ISO format timestamp from Alchemy
            timestamp_str = transfer.get('metadata', {}).get('blockTimestamp', '0')
            try:
                dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                return int(dt.timestamp())
            except (ValueError, TypeError):
                return 0
                
        sorted_transfers = sorted(transfers, key=parse_timestamp)
        
        # Calculate time differences
        time_diffs = []
        for i in range(1, len(sorted_transfers)):
            curr_time = parse_timestamp(sorted_transfers[i])
            prev_time = parse_timestamp(sorted_transfers[i-1])
            if curr_time > prev_time:
                time_diffs.append(curr_time - prev_time)
        
        if not time_diffs:
            return '0s'
        
        # Calculate average
        avg_seconds = sum(time_diffs) / len(time_diffs)
        
        # Format the time
        if avg_seconds < 60:
            return f"{int(avg_seconds)}s"
        elif avg_seconds < 3600:
            return f"{int(avg_seconds/60)}m"
        elif avg_seconds < 86400:
            return f"{int(avg_seconds/3600)}h"
        else:
            return f"{int(avg_seconds/86400)}d"
            
    except Exception as e:
        return "0s"

# Add known DEX and protocol addresses
KNOWN_PROTOCOLS = {
    # Uniswap V2
    '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': 'Uniswap V2: Router',
    '0x811beed0119b4afce20d2583eb608c6f7af1954f': 'Uniswap V2: SHIB-WETH',
    
    # SushiSwap
    '0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f': 'SushiSwap: Router',
    '0x24d3dd4a62e29770cf98810b09f89d3a90279e7a': 'SushiSwap: SHIB-WETH',
    
    # ShibaSwap
    '0x03f7724180aa6b939894b5ca4314783b0b36b329': 'ShibaSwap: Router',
    
    # 1inch
    '0x1111111254fb6c44bac0bed2854e76f90643097d': '1inch Router',
    
    # General DeFi
    '0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9': 'Aave: Lending Pool',
    '0x7b39917f9562c8bc83c7a6c2950ff571375d505d': 'Bone: ShibaSwap Token',
    '0x8faf958e36c6970497386118030e6297fff8d275': 'Leash: ShibaSwap Token'
}

async def get_contract_interactions(address: str, transfers: List[Dict]) -> Dict:
    """Analyze contract interactions from transfers"""
    try:
        contract_counts = {}
        defi_interactions = 0
        
        # Process transfers sequentially to avoid race conditions
        for transfer in transfers:
            contract_addr = transfer.get('to', '').lower()
            if contract_addr and contract_addr != address.lower():
                if contract_addr not in contract_counts:
                    contract_counts[contract_addr] = {
                        'count': 0,
                        'name': 'Unknown Contract',
                        'verified': False
                    }
                contract_counts[contract_addr]['count'] += 1
                
                # Check if this is a DeFi protocol
                if contract_addr in KNOWN_PROTOCOLS:
                    defi_interactions += 1
        
        # Sort contracts by interaction count
        sorted_contracts = sorted(
            [{'address': addr, **info} for addr, info in contract_counts.items()],
            key=lambda x: (-x['count'], x['address'])  # Sort by count desc, then address for stability
        )
        
        return {
            'defi_interactions': defi_interactions,
            'unique_contracts': len(contract_counts),
            'top_contracts': sorted_contracts[:10]  # Return top 10 contracts
        }
    except Exception as e:
        return {}

async def get_trading_patterns(address: str, transfers: List[Dict]) -> Dict:
    """Analyze trading patterns"""
    try:
        dex_volume = {'Buys': 0, 'Sells': 0}
        pairs = {}
        holding_times = []
        
        # Track when addresses received tokens
        address_first_received = {}
        
        for tx in transfers:
            if not (tx.get('from') and tx.get('to') and tx.get('metadata', {}).get('blockTimestamp')):
                continue
                
            # Convert value from hex and normalize by decimals
            value = float(int(tx['value'], 16)) if isinstance(tx['value'], str) and tx['value'].startswith('0x') else float(tx['value'])
            
            from_addr = tx['from'].lower()
            to_addr = tx['to'].lower()
            
            # Parse timestamp correctly
            try:
                timestamp = int(datetime.strptime(tx['metadata']['blockTimestamp'], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp())
            except ValueError:
                continue
            
            # Track holding times for non-DEX addresses
            if to_addr not in KNOWN_PROTOCOLS:
                if to_addr not in address_first_received:
                    address_first_received[to_addr] = timestamp
                elif from_addr in address_first_received:
                    holding_time = timestamp - address_first_received[from_addr]
                    if holding_time > 0:  # Ignore negative or zero holding times
                        holding_times.append(holding_time)
            
            # Track trading pairs and DEX volume
            if from_addr in KNOWN_PROTOCOLS or to_addr in KNOWN_PROTOCOLS:
                pair_key = f"{KNOWN_PROTOCOLS.get(from_addr, from_addr)}_{KNOWN_PROTOCOLS.get(to_addr, to_addr)}"
                pairs[pair_key] = pairs.get(pair_key, 0) + value
                
                if from_addr in KNOWN_PROTOCOLS and 'Uniswap' in KNOWN_PROTOCOLS[from_addr] or 'SushiSwap' in KNOWN_PROTOCOLS[from_addr]:
                    dex_volume['Buys'] += value
                elif to_addr in KNOWN_PROTOCOLS and 'Uniswap' in KNOWN_PROTOCOLS[to_addr] or 'SushiSwap' in KNOWN_PROTOCOLS[to_addr]:
                    dex_volume['Sells'] += value
        
        return {
            'avg_holding_time': sum(holding_times) / len(holding_times) if holding_times else 0,
            'active_pairs': len(pairs),
            'dex_distribution': dex_volume
        }
    except Exception as e:
        return {}

async def get_block_number_24h_ago() -> int:
    """Helper function to get block number from 24h ago"""
    try:
        # Get current block
        current_block = await w3.eth.block_number
        
        # Get current block timestamp
        current_block_data = await w3.eth.get_block(current_block)
        current_time = current_block_data['timestamp']
        
        # Calculate target time (24h ago)
        target_time = current_time - 86400
        
        # Binary search for block number
        left = max(0, current_block - 7200)  # Approx 24h worth of blocks
        right = current_block
        
        while left <= right:
            mid = (left + right) // 2
            block_data = await w3.eth.get_block(mid)
            block_time = block_data['timestamp']
            
            if abs(block_time - target_time) < 300:  # Within 5 minutes
                return mid
            elif block_time < target_time:
                left = mid + 1
            else:
                right = mid - 1
        
        return left  # Return closest block
    except Exception as e:
        return 0

async def get_transaction_count(address: str) -> int:
    """Get total transaction count for an address"""
    try:
        params = {
            'module': 'proxy',
            'action': 'eth_getTransactionCount',
            'address': address,
            'tag': 'latest',
            'apikey': config.etherscan_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('result'):
                        # Convert hex to int
                        return int(data['result'], 16)
                
                # Fallback to txlist if proxy endpoint fails
                params = {
                    'module': 'account',
                    'action': 'txlist',
                    'address': address,
                    'startblock': '0',
                    'endblock': '99999999',
                    'page': '1',
                    'offset': '1',  # We only need count
                    'sort': 'asc',
                    'apikey': config.etherscan_api_key
                }
                
                async with session.get(config.etherscan_api, params=params) as fallback_response:
                    fallback_data = await fallback_response.json()
                    if fallback_data['status'] == '1':
                        return int(fallback_data.get('result', []))
        
        return 0
    except Exception as e:
        return 0

async def get_token_market_data(address: str) -> Dict:
    """Get token market data from on-chain sources"""
    try:
        # Initialize default response
        market_data = {
            'market_cap': 0.0,
            'price_usd': 0.0,
            'price_eth': 0.0,
            'volume_24h': 0.0,
            'total_liquidity_eth': 0.0,
            'main_pool_address': None,
            'dex_data': []  # List of all DEX pools
        }
        
        # Get ETH price in USD from Etherscan
        eth_price = 0.0
        try:
            params = {
                'module': 'stats',
                'action': 'ethprice',
                'apikey': config.etherscan_api_key
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(config.etherscan_api, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['status'] == '1' and data['result']:
                            eth_price = float(data['result']['ethusd'])
        except Exception as e:
            pass
        
        # List of DEX factories to check
        dex_factories = [
            {
                'name': 'Uniswap V2',
                'factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
                'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                'abi': UNISWAP_FACTORY_ABI,
                'version': 'v2'
            },
            {
                'name': 'SushiSwap',
                'factory': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
                'router': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
                'abi': UNISWAP_FACTORY_ABI,
                'version': 'v2'
            },
            {
                'name': 'Uniswap V3',
                'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
                'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'abi': UNISWAP_V3_FACTORY_ABI,
                'version': 'v3'
            },
            {
                'name': 'PancakeSwap',
                'factory': '0x1097053Fd2ea711dad45caCcc45EfF7548fCB362',
                'router': '0x13f4EA83D0bd40E75C8222255bc855a974568Dd4',
                'abi': PANCAKESWAP_FACTORY_ABI,
                'version': 'v2'
            }
        ]
        
        weth_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        total_liquidity_eth = 0.0
        total_volume_24h = 0.0
        main_pool_address = None
        max_liquidity = 0.0
        
        # Get token decimals
        token_contract = w3.eth.contract(address=address, abi=ERC20_ABI)
        try:
            token_decimals = await token_contract.functions.decimals().call()
        except Exception:
            token_decimals = 18  # Default to 18 if not found
        
        # Process DEX data
        for dex in dex_factories:
            try:
                factory = w3.eth.contract(address=dex['factory'], abi=dex['abi'])
                
                if dex['version'] == 'v3':
                    # Handle Uniswap V3 pools
                    fee_tiers = [100, 500, 3000, 10000]  # Common fee tiers
                    for fee in fee_tiers:
                        try:
                            pool_address = await factory.functions.getPool(address, weth_address, fee).call()
                            if pool_address and pool_address != "0x0000000000000000000000000000000000000000":
                                pool_contract = w3.eth.contract(address=pool_address, abi=UNISWAP_V3_POOL_ABI)
                                slot0 = await pool_contract.functions.slot0().call()
                                liquidity = await pool_contract.functions.liquidity().call()
                                
                                # Calculate liquidity and price for V3 pool
                                sqrtPriceX96 = slot0[0]
                                price = (sqrtPriceX96 * sqrtPriceX96 * (10 ** (18 - token_decimals))) / (2 ** 192)
                                
                                eth_reserve = liquidity * price / (10 ** 18)
                                token_reserve = liquidity / (10 ** token_decimals)
                                
                                # Get pool volume
                                pool_volume = await get_v3_pool_volume(pool_address, token_decimals)
                                total_volume_24h += pool_volume
                                
                                # Add to total liquidity
                                total_liquidity_eth += eth_reserve
                                
                                # Track main pool
                                if eth_reserve > max_liquidity:
                                    max_liquidity = eth_reserve
                                    main_pool_address = pool_address
                                    market_data['price_eth'] = price
                                    market_data['price_usd'] = price * eth_price
                                
                                # Add to DEX data
                                market_data['dex_data'].append({
                                    'dex': f"{dex['name']} ({fee/10000}%)",
                                    'pair_address': pool_address,
                                    'liquidity_eth': eth_reserve,
                                    'token_reserve': token_reserve,
                                    'price_eth': price,
                                    'price_usd': price * eth_price,
                                    'volume_24h': pool_volume
                                })
                        except Exception as e:
                            pass
                else:
                    # Handle V2-style pools
                    pair_address = await factory.functions.getPair(address, weth_address).call()
                    
                    if pair_address and pair_address != "0x0000000000000000000000000000000000000000":
                        pair_contract = w3.eth.contract(address=pair_address, abi=UNISWAP_PAIR_ABI)
                        reserves = await pair_contract.functions.getReserves().call()
                        token0 = await pair_contract.functions.token0().call()
                        
                        # Calculate liquidity
                        if token0.lower() == address.lower():
                            eth_reserve = reserves[1] / 1e18
                            token_reserve = reserves[0] / (10 ** token_decimals)
                        else:
                            eth_reserve = reserves[0] / 1e18
                            token_reserve = reserves[1] / (10 ** token_decimals)
                        
                        # Calculate price
                        if token_reserve > 0:
                            price_eth = eth_reserve / token_reserve
                            price_usd = price_eth * eth_price
                        else:
                            price_eth = 0
                            price_usd = 0
                        
                        # Get pool volume
                        pool_volume = await get_v2_pool_volume(pair_address, token_decimals)
                        total_volume_24h += pool_volume
                        
                        # Add to total liquidity
                        total_liquidity_eth += eth_reserve
                        
                        # Track main pool
                        if eth_reserve > max_liquidity:
                            max_liquidity = eth_reserve
                            main_pool_address = pair_address
                            market_data['price_eth'] = price_eth
                            market_data['price_usd'] = price_usd
                        
                        # Add to DEX data
                        market_data['dex_data'].append({
                            'dex': dex['name'],
                            'pair_address': pair_address,
                            'liquidity_eth': eth_reserve,
                            'token_reserve': token_reserve,
                            'price_eth': price_eth,
                            'price_usd': price_usd,
                            'volume_24h': pool_volume
                        })
            except Exception as e:
                pass
        
        # Get CEX volume from CoinGecko
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses={address}&vs_currencies=usd&include_24hr_vol=true") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and address.lower() in data:
                            cex_volume = data[address.lower()].get('usd_24h_vol', 0)
                            total_volume_24h += cex_volume / eth_price  # Convert USD volume to ETH
        except Exception as e:
            pass
        
        # Update market data
        market_data['total_liquidity_eth'] = total_liquidity_eth
        market_data['main_pool_address'] = main_pool_address
        market_data['volume_24h'] = total_volume_24h
        
        # Calculate market cap if we have price and total supply
        if market_data['price_usd'] > 0:
            try:
                total_supply = await token_contract.functions.totalSupply().call()
                market_data['market_cap'] = (total_supply / (10 ** token_decimals)) * market_data['price_usd']
            except Exception as e:
                pass
        
        return market_data
        
    except Exception as e:
        return {}

async def get_v2_pool_volume(pair_address: str, token_decimals: int) -> float:
    """Get 24h volume for a V2 pool"""
    try:
        # Get block from 24h ago
        block_24h = await get_block_number_24h_ago()
        
        # Get transfers for this pool
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': pair_address,
            'startblock': str(block_24h),
            'endblock': '99999999',
            'sort': 'desc',
            'apikey': config.etherscan_api_key
        }
        
        volume = 0.0
        processed_txs = set()  # Track processed transaction hashes
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1' and data['result']:
                        for tx in data['result']:
                            # Only count each transaction once
                            if tx['hash'] not in processed_txs:
                                value = int(tx['value']) / (10 ** token_decimals)
                                volume += value
                                processed_txs.add(tx['hash'])
        
        return volume
    except Exception as e:
        return 0.0

async def get_v3_pool_volume(pool_address: str, token_decimals: int) -> float:
    """Get 24h volume for a V3 pool"""
    try:
        # Get block from 24h ago
        block_24h = await get_block_number_24h_ago()
        
        # Get swap events for this pool
        pool_contract = w3.eth.contract(address=pool_address, abi=UNISWAP_V3_POOL_ABI)
        swap_filter = await pool_contract.events.Swap.create_filter(
            fromBlock=block_24h,
            toBlock='latest'
        )
        
        events = await swap_filter.get_all_entries()
        volume = 0.0
        
        for event in events:
            # For each swap, take the absolute value of the token amount
            amount0 = abs(int(event['args']['amount0'])) / (10 ** token_decimals)
            amount1 = abs(int(event['args']['amount1'])) / 1e18  # WETH decimals
            volume += max(amount0, amount1)  # Take the larger of the two amounts
        
        return volume
    except Exception as e:
        return 0.0

# Add Uniswap ABIs
UNISWAP_FACTORY_ABI = [
    {
        "constant": "true",
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"}
        ],
        "name": "getPair",
        "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
        "payable": "false",
        "stateMutability": "view",
        "type": "function"
    }
]

UNISWAP_PAIR_ABI = [
    {
        "constant": "true",
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "blockTimestampLast", "type": "uint32"}
        ],
        "payable": "false",
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": "true",
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": "false",
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": "true",
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": "false",
        "stateMutability": "view",
        "type": "function"
    }
]

UNISWAP_V3_FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

UNISWAP_V3_POOL_ABI = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": "false",
        "inputs": [
            {"indexed": "true", "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": "true", "internalType": "address", "name": "recipient", "type": "address"},
            {"indexed": "false", "internalType": "int256", "name": "amount0", "type": "int256"},
            {"indexed": "false", "internalType": "int256", "name": "amount1", "type": "int256"},
            {"indexed": "false", "internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"indexed": "false", "internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"indexed": "false", "internalType": "int24", "name": "tick", "type": "int24"}
        ],
        "name": "Swap",
        "type": "event"
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

PANCAKESWAP_FACTORY_ABI = [
    {
        "constant": "true",
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"}
        ],
        "name": "getPair",
        "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
        "payable": "false",
        "stateMutability": "view",
        "type": "function"
    }
]

async def get_contract_code(address: str) -> str:
    """Get contract bytecode from Ethereum network"""
    try:
        # Convert address to checksum format
        address = Web3.to_checksum_address(address)
        
        # Get code using eth_getCode
        code = await w3.eth.get_code(address, "latest")
        return code.hex()
    except Exception as e:
        return ""

async def get_contract_age(address: str) -> Dict:
    """Get contract creation date and age"""
    try:
        # Try contract creation endpoint first
        async with aiohttp.ClientSession() as session:
            creation_params = {
            'module': 'contract',
            'action': 'getcontractcreation',
            'contractaddresses': address,
            'apikey': config.etherscan_api_key
        }
        
            async with session.get(config.etherscan_api, params=creation_params) as creation_response:
                if creation_response.status == 200:
                    creation_data = await creation_response.json()
                    if creation_data['status'] == '1' and creation_data['result']:
                        # Get the creation transaction
                        creation_tx = creation_data['result'][0]['txHash']
                        
                        # Get transaction details to get timestamp
                        tx_params = {
                            'module': 'proxy',
                            'action': 'eth_getTransactionByHash',
                            'txhash': creation_tx,
                            'apikey': config.etherscan_api_key
                        }
                        
                        async with session.get(config.etherscan_api, params=tx_params) as tx_response:
                            tx_data = await tx_response.json()
                            if tx_data.get('result'):
                                # Get block details to get timestamp
                                block_number = int(tx_data['result']['blockNumber'], 16)
                                block_params = {
                                    'module': 'block',
                                    'action': 'getblockreward',
                                    'blockno': str(block_number),
                                    'apikey': config.etherscan_api_key
                                }
                                
                                async with session.get(config.etherscan_api, params=block_params) as block_response:
                                    block_data = await block_response.json()
                                    if block_data['status'] == '1' and block_data['result']:
                                        creation_time = int(block_data['result']['timeStamp'])
                                        current_time = int(datetime.now().timestamp())
                                        age_days = (current_time - creation_time) // 86400
                                        
                                        return {
                                            'creation_date': datetime.fromtimestamp(creation_time).isoformat(),
                                            'age_days': age_days
                                        }
        
            # If contract creation endpoint fails, try verified contract info
            params = {
                'module': 'contract',
                'action': 'getsourcecode',
                'address': address,
                'apikey': config.etherscan_api_key
            }
            
            async with session.get(config.etherscan_api, params=params) as source_response:
                source_data = await source_response.json()
                if source_data['status'] == '1' and source_data['result']:
                    creation_time = int(source_data['result'][0].get('ContractCreated', 0))
                    if creation_time > 0:
                        current_time = int(datetime.now().timestamp())
                        age_days = (current_time - creation_time) // 86400
        return {
                            'creation_date': datetime.fromtimestamp(creation_time).isoformat(),
                            'age_days': age_days
        }
        
        return {
            'creation_date': None,
            'age_days': 0
        }
    except Exception as e:
        return {}

async def get_burn_events(address: str) -> int:
    """Get number of burn events"""
    try:
        # Get burn events (transfers to zero address)
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': config.ZERO_ADDRESS,
            'startblock': '0',
            'endblock': '99999999',
            'sort': 'desc',
            'apikey': config.etherscan_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1':
                        return len([tx for tx in data['result'] if tx['from'].lower() == address.lower()])
                return 0
    except Exception as e:
        return 0

async def get_24h_transfer_volume(address: str) -> float:
    """Get transfer volume in the last 24 hours using Alchemy"""
    try:
        # Get block from 24h ago
        block_24h = await get_block_number_24h_ago()
        
        # Use Alchemy's getAssetTransfers endpoint
        async with aiohttp.ClientSession() as session:
            params = {
                'fromBlock': hex(block_24h),
                'toBlock': 'latest',
                'contractAddresses': [address],
                'category': ['erc20'],
                'withMetadata': True,
                'excludeZeroValue': True
            }
            headers = {
                'accept': 'application/json',
                'content-type': 'application/json'
            }
            url = f"{config.alchemy_url}/getAssetTransfers"
            
            async with session.post(url, json=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and 'transfers' in data:
                        total_volume = sum(
                            float(transfer.get('value', 0))
                            for transfer in data['transfers']
                        )
                        return total_volume
        
        # Fallback to Etherscan if Alchemy fails
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'startblock': str(block_24h),
            'endblock': '99999999',
            'sort': 'desc',
            'apikey': config.etherscan_api_key
        }
        
        total_volume = 0.0
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1' and data['result']:
                        for tx in data['result']:
                            if tx['contractAddress'].lower() == address.lower():
                                decimals = int(tx['tokenDecimal'])
                                value = int(tx['value']) / (10 ** decimals)
                                total_volume += value
                        
        return total_volume
    except Exception as e:
        return 0.0

async def check_liquidity_lock(address: str) -> Dict:
    """Check if liquidity is locked"""
    try:
        # Get contract transactions
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': '0',
            'endblock': '99999999',
            'sort': 'desc',
            'apikey': config.etherscan_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1':
                        # Look for transfers to known locker contracts
                        locker_contracts = [
                            '0x663a5c229c09b049e36dcc11a9b0d4a8eb9db214',  # Unicrypt
                            '0x7ee058420e5937496f5a2096f04caa7721cf70cc',  # Team Finance
                            '0x70c1d0a424ee6d05c1c87ad1b36b1b0946d64e05'   # PinkLock
                        ]
                        
                        for tx in data['result']:
                            if tx['to'].lower() in locker_contracts:
                                return {"lp_locked": True}
        
        return {"lp_locked": False}
    except Exception as e:
        return {'lp_locked': False}

async def get_wallet_metrics(address: str) -> Dict:
    """Get comprehensive wallet metrics"""
    try:
        # Get current block and time
        current_block = await w3.eth.get_block('latest')
        current_time = current_block['timestamp']
        
        # Initialize metrics
        metrics = {
            'balance': float(Web3.from_wei(await w3.eth.get_balance(address), 'ether')),
            'total_transactions': 0,
            'first_tx_timestamp': None,
            'last_tx_timestamp': None,
            'unique_interacted_addresses': 0,
            'incoming_tx_count': 0,
            'outgoing_tx_count': 0,
            'failed_tx_count': 0,
            'total_received_eth': 0.0,
            'total_sent_eth': 0.0,
            'avg_gas_used': 0.0,
            'total_gas_spent_eth': 0.0,
            'token_holdings': [],
            'defi_interactions': set(),
            'nft_holdings': 0,
            'nft_transactions': 0,
            'wallet_age_days': 0
        }
        
        # Track unique addresses in a set
        unique_addresses = set()
        
        async with aiohttp.ClientSession() as session:
            # Get normal transactions
            tx_params = {
                'module': 'account',
                'action': 'txlist',
                'address': address,
                'startblock': '0',
                'endblock': str(current_block['number']),
                'sort': 'asc',
                'apikey': config.etherscan_api_key
            }
            
            # Get internal transactions
            internal_params = {
                'module': 'account',
                'action': 'txlistinternal',
                'address': address,
                'startblock': '0',
                'endblock': str(current_block['number']),
                'sort': 'asc',
                'apikey': config.etherscan_api_key
            }
            
            # Fetch both normal and internal transactions
            async with session.get(config.etherscan_api, params=tx_params) as tx_response, \
                       session.get(config.etherscan_api, params=internal_params) as internal_response:
                
                tx_data = await tx_response.json()
                internal_data = await internal_response.json()
                
                total_gas = 0
                valid_tx_count = 0
                
                # Process normal transactions
                if tx_data['status'] == '1' and tx_data['result']:
                    for tx in tx_data['result']:
                        try:
                            tx_timestamp = int(tx['timeStamp'])
                            
                            # Validate timestamp is not in the future
                            if tx_timestamp > current_time:
                                continue
                            
                            # Update first and last transaction timestamps
                            if metrics['first_tx_timestamp'] is None or tx_timestamp < metrics['first_tx_timestamp']:
                                metrics['first_tx_timestamp'] = tx_timestamp
                            if metrics['last_tx_timestamp'] is None or tx_timestamp > metrics['last_tx_timestamp']:
                                metrics['last_tx_timestamp'] = tx_timestamp
                            
                            # Track unique addresses
                            if tx['from'] and Web3.is_address(tx['from']):
                                unique_addresses.add(tx['from'].lower())
                            if tx['to'] and Web3.is_address(tx['to']):
                                unique_addresses.add(tx['to'].lower())
                            
                            # Count transactions
                            if tx['from'].lower() == address.lower():
                                metrics['outgoing_tx_count'] += 1
                                if tx['value'] and tx['value'].isdigit():
                                    metrics['total_sent_eth'] += float(Web3.from_wei(int(tx['value']), 'ether'))
                            elif tx['to'] and tx['to'].lower() == address.lower():
                                metrics['incoming_tx_count'] += 1
                                if tx['value'] and tx['value'].isdigit():
                                    metrics['total_received_eth'] += float(Web3.from_wei(int(tx['value']), 'ether'))
                            
                            # Track failed transactions
                            if tx['isError'] == '1':
                                metrics['failed_tx_count'] += 1
                            
                            # Calculate gas
                            if tx['gasUsed'] and tx['gasUsed'].isdigit() and tx['gasPrice'] and tx['gasPrice'].isdigit():
                                gas_used = int(tx['gasUsed'])
                                gas_price = int(tx['gasPrice'])
                                total_gas += gas_used
                                metrics['total_gas_spent_eth'] += float(Web3.from_wei(gas_used * gas_price, 'ether'))
                            
                            valid_tx_count += 1
                            
                        except Exception as e:
                            continue
                
                # Process internal transactions
                if internal_data['status'] == '1' and internal_data['result']:
                    for tx in internal_data['result']:
                        try:
                            tx_timestamp = int(tx['timeStamp'])
                            
                            # Validate timestamp is not in the future
                            if tx_timestamp > current_time:
                                continue
                            
                            # Update first and last transaction timestamps
                            if metrics['first_tx_timestamp'] is None or tx_timestamp < metrics['first_tx_timestamp']:
                                metrics['first_tx_timestamp'] = tx_timestamp
                            if metrics['last_tx_timestamp'] is None or tx_timestamp > metrics['last_tx_timestamp']:
                                metrics['last_tx_timestamp'] = tx_timestamp
                            
                            # Track unique addresses
                            if tx['from'] and Web3.is_address(tx['from']):
                                unique_addresses.add(tx['from'].lower())
                            if tx['to'] and Web3.is_address(tx['to']):
                                unique_addresses.add(tx['to'].lower())
                            
                            # Count value transfers
                            if tx['from'].lower() == address.lower():
                                if tx['value'] and tx['value'].isdigit():
                                    metrics['total_sent_eth'] += float(Web3.from_wei(int(tx['value']), 'ether'))
                            elif tx['to'] and tx['to'].lower() == address.lower():
                                if tx['value'] and tx['value'].isdigit():
                                    metrics['total_received_eth'] += float(Web3.from_wei(int(tx['value']), 'ether'))
                            
                        except Exception as e:
                            continue
                
                # Calculate average gas
                metrics['avg_gas_used'] = total_gas / valid_tx_count if valid_tx_count > 0 else 0
                
                # Update total transactions
                metrics['total_transactions'] = valid_tx_count
                
                # Update unique addresses (excluding self)
                unique_addresses.discard(address.lower())
                metrics['unique_interacted_addresses'] = len(unique_addresses)
        
        # Calculate wallet age in days
        if metrics['first_tx_timestamp']:
            metrics['wallet_age_days'] = (current_time - metrics['first_tx_timestamp']) // 86400
        
        # Format timestamps to human readable format
        if metrics['first_tx_timestamp']:
            first_dt = datetime.fromtimestamp(metrics['first_tx_timestamp'])
            metrics['first_tx_timestamp'] = first_dt.strftime('%m/%d/%Y')
        if metrics['last_tx_timestamp']:
            last_dt = datetime.fromtimestamp(metrics['last_tx_timestamp'])
            metrics['last_tx_timestamp'] = last_dt.strftime('%m/%d/%Y')
        
        return metrics
    except Exception as e:
        return {}

async def get_defi_interactions(address: str) -> Dict:
    """Get DeFi protocol interactions"""
    try:
        # Known DeFi protocol addresses (add more as needed)
        defi_protocols = {
            '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': 'Uniswap V2 Router',
            '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45': 'Uniswap V3 Router',
            '0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f': 'Sushiswap Router',
            '0x1111111254fb6c44bac0bed2854e76f90643097d': '1inch Router',
            '0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9': 'Aave V2 Lending Pool',
            '0x7b5C526B7F8dfdff278b4a3e045083FBA4028790': 'Aave V3 Pool',
            '0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b': 'Compound Comptroller'
        }
        
        interactions = {
            'protocols': {},
            'total_interactions': 0,
            'total_value_locked': 0.0,
            'last_interaction': None
        }
        
        # Get all transactions involving DeFi protocols
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': '0',
            'endblock': '99999999',
            'sort': 'desc',
            'apikey': config.etherscan_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1' and data['result']:
                        transactions = data['result']
                        
                        for tx in transactions:
                            # Check if transaction involves a known DeFi protocol
                            protocol_addr = tx['to'].lower()
                            if protocol_addr in defi_protocols:
                                protocol_name = defi_protocols[protocol_addr]
                                
                                # Initialize protocol data if not exists
                                if protocol_name not in interactions['protocols']:
                                    interactions['protocols'][protocol_name] = {
                                        'interaction_count': 0,
                                        'total_value': 0.0,
                                        'last_interaction': None
                                    }
                                
                                # Update protocol metrics
                                protocol_data = interactions['protocols'][protocol_name]
                                protocol_data['interaction_count'] += 1
                                protocol_data['total_value'] += float(Web3.from_wei(int(tx['value']), 'ether'))
                                
                                # Update timestamps
                                tx_timestamp = datetime.fromtimestamp(int(tx['timeStamp'])).isoformat()
                                if not protocol_data['last_interaction'] or tx_timestamp > protocol_data['last_interaction']:
                                    protocol_data['last_interaction'] = tx_timestamp
                                
                                if not interactions['last_interaction'] or tx_timestamp > interactions['last_interaction']:
                                    interactions['last_interaction'] = tx_timestamp
                                
                                interactions['total_interactions'] += 1
                                interactions['total_value_locked'] += float(Web3.from_wei(int(tx['value']), 'ether'))
        
        # Get token approvals for DeFi protocols
        token_params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'startblock': '0',
            'endblock': '99999999',
            'sort': 'desc',
            'apikey': config.etherscan_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=token_params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1' and data['result']:
                        token_txs = data['result']
                        
                        for tx in token_txs:
                            protocol_addr = tx['to'].lower()
                            if protocol_addr in defi_protocols:
                                protocol_name = defi_protocols[protocol_addr]
                                
                                # Initialize protocol data if not exists
                                if protocol_name not in interactions['protocols']:
                                    interactions['protocols'][protocol_name] = {
                                        'interaction_count': 0,
                                        'total_value': 0.0,
                                        'last_interaction': None
                                    }
                                
                                # Update protocol metrics
                                protocol_data = interactions['protocols'][protocol_name]
                                protocol_data['interaction_count'] += 1
                                
                                # Calculate token value in ETH (simplified)
                                token_value = float(tx['value']) / (10 ** int(tx['tokenDecimal']))
                                protocol_data['total_value'] += token_value
                                
                                # Update timestamps
                                tx_timestamp = datetime.fromtimestamp(int(tx['timeStamp'])).isoformat()
                                if not protocol_data['last_interaction'] or tx_timestamp > protocol_data['last_interaction']:
                                    protocol_data['last_interaction'] = tx_timestamp
                                
                                if not interactions['last_interaction'] or tx_timestamp > interactions['last_interaction']:
                                    interactions['last_interaction'] = tx_timestamp
                                
                                interactions['total_interactions'] += 1
                                interactions['total_value_locked'] += token_value
        
        return interactions
    except Exception as e:
        return {}

async def batch_verify_contracts(addresses: List[str]) -> Dict[str, Dict]:
    """
    Batch verify multiple contracts at once
    """
    async def fetch_batch(addr_batch):
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': ','.join(addr_batch),
            'apikey': config.etherscan_api_key
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(config.etherscan_api, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return {'result': []}
    
    # Split addresses into batches of 5 (Etherscan's limit for this endpoint)
    batches = [addresses[i:i + 5] for i in range(0, len(addresses), 5)]
    tasks = [fetch_batch(batch) for batch in batches]
    results = await asyncio.gather(*tasks)
    
    # Combine results
    verified_contracts = {}
    for result in results:
        if 'result' in result and isinstance(result['result'], list):
            for contract in result['result']:
                if contract.get('ContractName'):  # Only add if contract is verified
                    verified_contracts[contract['ContractAddress'].lower()] = contract
                
    return verified_contracts

async def batch_fetch_transfers(address: str, from_block: int, batch_size: int = 100) -> List[Dict]:
    """
    Fetch transfer events in batches to reduce API calls
    """
    transfers = []
    current_block = await w3.eth.block_number
    
    # Create batch of requests
    batch_requests = []
    for start_block in range(from_block, current_block, 10000):  # Process in 10k block chunks
        end_block = min(start_block + 9999, current_block)
        batch_requests.append({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "alchemy_getAssetTransfers",
            "params": [{
                "fromBlock": hex(start_block),
                "toBlock": hex(end_block),
                "withMetadata": True,
                "excludeZeroValue": True,
                "contractAddresses": [address],
                "category": ["erc20"],
                "maxCount": hex(batch_size)
            }]
        })
    
    # Execute batch requests concurrently
    async def fetch_batch(params):
        async with aiohttp.ClientSession() as session:
            headers = {
                'accept': 'application/json',
                'content-type': 'application/json'
            }
            async with session.post(config.alchemy_url, json=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'result' in data and 'transfers' in data['result']:
                        return data['result']['transfers']
                return []
    
    tasks = [fetch_batch(req) for req in batch_requests]
    results = await asyncio.gather(*tasks)
    
    # Process results
    for batch_transfers in results:
        transfers.extend(batch_transfers)
            
    return transfers[:batch_size]  # Return only requested amount 

async def compare_owner_deployer(address: str) -> bool:
    """Compare if the contract owner is the same as the deployer"""
    try:
        creator = await get_contract_creator(address)
        owner = await get_creator_info(address)
        return creator and owner and creator.lower() == owner.lower()
    except Exception:
        return False
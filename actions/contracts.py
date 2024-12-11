import json
from shared_data.shared_data import web3
from actions.get_abi import get_contract_abi

UNISWAP_ROUTER_ADDRESS = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
UNISWAP_ROUTER_ABI = """
[
    {
        "name": "exactInputSingle",
        "type": "function",
        "inputs": [
            {"name": "params", "type": "tuple", "components": [
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"},
                {"name": "fee", "type": "uint24"},
                {"name": "recipient", "type": "address"},
                {"name": "deadline", "type": "uint256"},
                {"name": "amountIn", "type": "uint256"},
                {"name": "amountOutMinimum", "type": "uint256"},
                {"name": "sqrtPriceLimitX96", "type": "uint160"}
            ]}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    }
]
"""

# load uniswap router contract
uniswap_router = web3.eth.contract(address=UNISWAP_ROUTER_ADDRESS, abi=json.loads(UNISWAP_ROUTER_ABI))

# Check if connected to Alchemy
if not web3.is_connected():
    raise Exception("Failed to connect to Alchemy!")

# Load a smart contract dynamically
def load_contract(contract_address):
    try:
        abi = get_contract_abi(contract_address)
        contract = web3.eth.contract(address=contract_address, abi=json.loads(abi))
        return contract
    except Exception as e:
        raise Exception(f"Failed to load contract: {e}")

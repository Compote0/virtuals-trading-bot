from shared_data.shared_data import web3
from actions.contracts import load_contract

def create_wallet():
    """
    Creates a new wallet with an address and a private key.
    """
    account = web3.eth.account.create()
    return {
        "address": account.address,
        "private_key": account._private_key.hex()
    }

def check_balance(wallet_address, contract_address=None):
    """
    Checks the ETH balance and, if a contract address is provided, the token balance.
    """
    try:
        eth_balance = web3.eth.get_balance(wallet_address) / (10 ** 18)  # Convert from wei to ETH
        if contract_address:
            contract = load_contract(contract_address)
            token_balance = contract.functions.balanceOf(wallet_address).call() / (10 ** 18)
        else:
            token_balance = 0.0
        return eth_balance, token_balance
    except Exception as e:
        raise Exception(f"Error checking balance: {e}")

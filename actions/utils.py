from decimal import Decimal
from shared_data.shared_data import web3
from actions.contracts import load_contract

# Calculate total fees for swap
def calculate_total_fees(amount_to_swap, gas_price_gwei, gas_limits):
    gas_price = web3.to_wei(gas_price_gwei, "gwei")
    service_fee = Decimal(amount_to_swap) * Decimal("0.01")
    gas_cost = sum(gas_limits) * gas_price
    total_fees = web3.from_wei(service_fee + gas_cost, "ether")
    return {
        "service_fee": web3.from_wei(service_fee, "ether"),
        "gas_cost": web3.from_wei(gas_cost, "ether"),
        "total_fees": total_fees
    }

# Calculate fees
def calculate_fees(eth_amount):
    eth_amount_decimal = Decimal(eth_amount)
    fee_amount = eth_amount_decimal * Decimal("0.01")
    amount_after_fee = eth_amount_decimal - fee_amount
    return fee_amount, amount_after_fee

# Check ETH and token balance
def check_balance(wallet_address, contract_address=None):
    try:
        eth_balance = web3.eth.get_balance(wallet_address) / (10 ** 18)
        if contract_address:
            contract = load_contract(contract_address)
            token_balance = contract.functions.balanceOf(wallet_address).call() / (10 ** 18)
        else:
            token_balance = 0.0
        return eth_balance, token_balance
    except Exception as e:
        raise Exception(f"Error checking balance: {e}")

from decimal import Decimal
from shared_data.shared_data import web3, user_gwei_preferences, fee_recipient, weth_address, virtual_token_address
from actions.contracts import uniswap_router
from actions.utils import calculate_fees, load_contract

def send_fees(wallet, fee_recipient, fee_amount, gas_price, nonce):
    """
    Send fees to the specified address.
    """
    tx_fee_transfer = {
        "from": wallet["address"],
        "to": web3.to_checksum_address(fee_recipient),
        "value": web3.to_wei(fee_amount, "ether"),
        "gas": 21000,  # Simple transfer
        "gasPrice": gas_price,
        "nonce": nonce,
    }
    print("[DEBUG] Fee Transaction:", tx_fee_transfer)

    signed_fee_transfer = web3.eth.account.sign_transaction(tx_fee_transfer, wallet["private_key"])
    print("[DEBUG] Signed Fee Transaction:", signed_fee_transfer)

    raw_transaction = getattr(signed_fee_transfer, "raw_transaction", None)
    if not raw_transaction:
        raise Exception("[ERROR] Missing raw_transaction in the signed transaction.")

    tx_hash_fee_transfer = web3.eth.send_raw_transaction(raw_transaction)
    print("[DEBUG] Fee Transaction Hash:", tx_hash_fee_transfer.hex())
    web3.eth.wait_for_transaction_receipt(tx_hash_fee_transfer)
    return tx_hash_fee_transfer

def swap_eth_to_weth(wallet, eth_amount, gas_price, nonce):
    """
    Deposit ETH into the WETH contract to obtain WETH.
    """
    weth_abi = [
        {
            "constant": False,
            "inputs": [],
            "name": "deposit",
            "outputs": [],
            "payable": True,
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    weth_contract = web3.eth.contract(address=weth_address, abi=weth_abi)

    tx = weth_contract.functions.deposit().build_transaction({
        "from": wallet["address"],
        "value": web3.to_wei(eth_amount, "ether"),
        "gas": 100000,  
        "gasPrice": gas_price,
        "nonce": nonce,
    })

    print("[DEBUG] WETH Deposit Transaction:", tx)

    signed_tx = web3.eth.account.sign_transaction(tx, wallet["private_key"])
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print("[DEBUG] WETH Deposit Transaction Hash:", tx_hash.hex())
    web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash

def swap_weth_to_virtual(wallet, amount_in, gas_price, nonce):
    """
    Swap WETH to Virtual Token via Uniswap.
    """
    params = {
        "tokenIn": weth_address,
        "tokenOut": virtual_token_address,
        "fee": 3000,  
        "recipient": wallet["address"],
        "deadline": web3.eth.get_block("latest")["timestamp"] + 600,
        "amountIn": web3.to_wei(amount_in, "ether"),
        "amountOutMinimum": 1,  
        "sqrtPriceLimitX96": 0,
    }
    print("[DEBUG] WETH to Virtual Params:", params)

    tx = uniswap_router.functions.exactInputSingle(params).build_transaction({
        "from": wallet["address"],
        "nonce": nonce,
        "gas": 250000,
        "gasPrice": gas_price,
    })

    print("[DEBUG] WETH to Virtual Transaction:", tx)

    signed_tx = web3.eth.account.sign_transaction(tx, wallet["private_key"])
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print("[DEBUG] WETH to Virtual Transaction Hash:", tx_hash.hex())

    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    if receipt.status == 0:
        raise Exception("WETH to Virtual swap transaction failed.")
    return tx_hash

def swap_virtual_to_token(wallet, token_address, gas_price, nonce):
    """
    Swap Virtual Token to the Target Token via Uniswap.
    """
    virtual_contract = load_contract(virtual_token_address)
    virtual_balance = virtual_contract.functions.balanceOf(wallet["address"]).call()
    
    if virtual_balance <= 0:
        raise Exception("Insufficient Virtual Token balance for the swap.")

    print("[DEBUG] Virtual Token Balance:", virtual_balance)

    params_virtual_to_token = {
        "tokenIn": web3.to_checksum_address(virtual_token_address),
        "tokenOut": web3.to_checksum_address(token_address),
        "fee": 3000,
        "recipient": wallet["address"],
        "deadline": web3.eth.get_block("latest")["timestamp"] + 600,
        "amountIn": virtual_balance,
        "amountOutMinimum": 1,  
        "sqrtPriceLimitX96": 0,
    }
    print("[DEBUG] Virtual to Token Params:", params_virtual_to_token)

    tx_virtual_to_token = uniswap_router.functions.exactInputSingle(params_virtual_to_token).build_transaction({
        "from": wallet["address"],
        "nonce": nonce,
        "gas": 250000,
        "gasPrice": gas_price,
    })
    print("[DEBUG] Virtual to Token Transaction:", tx_virtual_to_token)

    signed_virtual_to_token = web3.eth.account.sign_transaction(tx_virtual_to_token, wallet["private_key"])
    tx_hash_virtual_to_token = web3.eth.send_raw_transaction(signed_virtual_to_token.raw_transaction)

    print("[DEBUG] Virtual to Token Transaction Hash:", tx_hash_virtual_to_token.hex())

    receipt = web3.eth.wait_for_transaction_receipt(tx_hash_virtual_to_token, timeout=300)
    if receipt.status == 0:
        raise Exception("Swap transaction failed.")

    return tx_hash_virtual_to_token

def swap_eth_to_token(wallet, token_address, eth_amount):
    """
    Orchestrate swaps from ETH → WETH → Virtual → Target Token with fees.
    """
    try:
        gas_price = web3.to_wei(user_gwei_preferences.get(wallet["chat_id"], 20), "gwei")
        nonce = web3.eth.get_transaction_count(wallet["address"])

        fee_amount, amount_after_fee = calculate_fees(eth_amount)

        send_fees(wallet, fee_recipient, fee_amount, gas_price, nonce)
        nonce += 1

        swap_eth_to_weth(wallet, amount_after_fee, gas_price, nonce)
        nonce += 1

        swap_weth_to_virtual(wallet, amount_after_fee, gas_price, nonce)
        nonce += 1

        tx_hash = swap_virtual_to_token(wallet, token_address, gas_price, nonce)
        return tx_hash.hex()

    except Exception as e:
        raise Exception(f"Swap failed: {e}")

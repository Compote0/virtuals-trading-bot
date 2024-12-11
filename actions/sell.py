from shared_data.shared_data import web3, user_gwei_preferences
from actions.contracts import uniswap_router, load_contract

def swap_token_to_virtual(wallet, token_address, token_amount, gas_price, nonce):
    """
    step 1 : Swap Token → Virtual Token
    """
    virtual_token_address = "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"
    params = {
        "tokenIn": token_address,
        "tokenOut": virtual_token_address,
        "fee": 3000,  # Uniswap Fee
        "recipient": wallet["address"],
        "deadline": web3.eth.get_block("latest")["timestamp"] + 600,
        "amountIn": token_amount,
        "amountOutMinimum": 1,  # Minimum output tokens
        "sqrtPriceLimitX96": 0,
    }
    print("[DEBUG] Params Token to Virtual:", params)

    tx = uniswap_router.functions.exactInputSingle(params).build_transaction({
        "from": wallet["address"],
        "nonce": nonce,
        "gas": 250000,
        "gasPrice": gas_price,
    })

    signed_tx = web3.eth.account.sign_transaction(tx, wallet["private_key"])
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    print("[DEBUG] Token to Virtual TX Hash:", tx_hash.hex())
    return tx_hash.hex()


def swap_virtual_to_weth(wallet, token_amount, gas_price, nonce):
    """
    step 2 :Swap Virtual Token → WETH
    """
    virtual_token_address = "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"
    weth_address = "0x4200000000000000000000000000000000000006"
    params = {
        "tokenIn": virtual_token_address,
        "tokenOut": weth_address,
        "fee": 3000,  # Uniswap Fee
        "recipient": wallet["address"],
        "deadline": web3.eth.get_block("latest")["timestamp"] + 600,
        "amountIn": token_amount,
        "amountOutMinimum": 1,  # Minimum output tokens
        "sqrtPriceLimitX96": 0,
    }
    print("[DEBUG] Params Virtual to WETH:", params)

    tx = uniswap_router.functions.exactInputSingle(params).build_transaction({
        "from": wallet["address"],
        "nonce": nonce,
        "gas": 250000,
        "gasPrice": gas_price,
    })

    signed_tx = web3.eth.account.sign_transaction(tx, wallet["private_key"])
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    print("[DEBUG] Virtual to WETH TX Hash:", tx_hash.hex())
    return tx_hash.hex()


def swap_weth_to_eth(wallet, gas_price, nonce):
    """
    step 3 : Swap WETH → ETH
    """
    weth_address = "0x4200000000000000000000000000000000000006"
    weth_contract = web3.eth.contract(address=weth_address, abi=[
        {
            "constant": False,
            "inputs": [{"name": "wad", "type": "uint256"}],
            "name": "withdraw",
            "outputs": [],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ])
    weth_balance = weth_contract.functions.balanceOf(wallet["address"]).call()
    if weth_balance <= 0:
        raise Exception("Insufficient WETH balance for the swap to ETH.")

    tx = weth_contract.functions.withdraw(weth_balance).build_transaction({
        "from": wallet["address"],
        "nonce": nonce,
        "gas": 100000,
        "gasPrice": gas_price,
    })

    signed_tx = web3.eth.account.sign_transaction(tx, wallet["private_key"])
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    print("[DEBUG] WETH to ETH TX Hash:", tx_hash.hex())
    return tx_hash.hex()


def execute_swap_to_eth(wallet, token_address, token_amount):
    """
    Orchestrator to manage sell : Token → Virtual → WETH → ETH flow.
    """
    try:
        gas_price = web3.to_wei(user_gwei_preferences.get(wallet["chat_id"], 10), "gwei")
        nonce = web3.eth.get_transaction_count(wallet["address"])

        # step 1: Token → Virtuals
        swap_token_to_virtual(wallet, token_address, token_amount, gas_price, nonce)
        nonce += 1

        # step 2 : Virtuals → WETH
        swap_virtual_to_weth(wallet, token_amount, gas_price, nonce)
        nonce += 1

        # step 3 : WETH → ETH
        tx_hash = swap_weth_to_eth(wallet, gas_price, nonce)

        return tx_hash

    except Exception as e:
        raise Exception(f"Swap to ETH failed: {e}")

import requests
from telebot import types
from shared_data.shared_data import bot, user_wallets, user_gwei_preferences
from actions.contracts import load_contract
from actions.buy import swap_eth_to_token
from actions.utils import calculate_total_fees
from decimal import Decimal

def buy_wallets_menu(wallets):
    """
    menu to show available wallets for manual buy	
    """
    markup = types.InlineKeyboardMarkup()
    if wallets:
        for idx, wallet in enumerate(wallets):
            address_short = f"{wallet['address'][:6]}...{wallet['address'][-4:]}"
            markup.add(types.InlineKeyboardButton(
                f"Wallet {idx + 1}: {address_short}",
                callback_data=f"manual_buy_wallet_{idx}"
            ))
    markup.add(types.InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu"))
    return markup

def process_token_address_reply(reply_message, wallet, bot_message_id):
    """
    Processes the user's reply with the token address.
    Deletes both messages (bot message and user response).
    Show Token informations
    """
    try:
        token_address = reply_message.text.strip()

        if not token_address.startswith("0x") or len(token_address) != 42:
            bot.send_message(reply_message.chat.id, "⚠️ Invalid token address. Please try again.")
            return

        bot.delete_message(reply_message.chat.id, bot_message_id)
        bot.delete_message(reply_message.chat.id, reply_message.message_id)

        contract = load_contract(token_address)
        token_details = get_token_details(contract)

        wallet["last_token_address"] = token_address

        # token details
        bot.send_message(
            reply_message.chat.id,
            f"*Token Information:*\n"
            f"🔹 {token_details.get('name', 'N/A')} ({token_details.get('symbol', 'N/A')})\n"
            f"🔹 `{token_details.get('contract_address', 'N/A')}`\n\n"
            f"🔹 Price (USD): ${round(token_details.get('price_usd', 0), 4)}\n"
            f"💧 Liquidity: ${round(token_details.get('liquidity_usd', 0), 2):,}\n\n"
            f"📊 MarketCap: `${round(token_details.get('market_cap', 0), 2):,}`\n\n",
            parse_mode="Markdown",
            reply_markup=buy_menu(wallet, {"ticker": token_details.get('symbol', 'N/A'), "contract": token_address})
        )
    except Exception as e:
        bot.send_message(reply_message.chat.id, f"⚠️ Error loading token information: {e}")



def manual_buy_menu(wallet):
    """
    Displays a message requesting a token address to begin purchasing
    """
    sent_message = bot.send_message(
        wallet["chat_id"],
        "Manual Buyer / Autosniper\n"
        "Paste in a token address below to start buying\n"
        "e.g. `0x6982508145454Ce325dDbE47a25d4ec3d2311933`",
        parse_mode="Markdown"
    )

    bot.register_next_step_handler(sent_message, process_token_address_reply, wallet, sent_message.message_id)



def buy_menu(wallet, token_info):
    """
    Generates a menu to display purchase options after obtaining token information,
    arranged in two columns, with a button for Gwei presets.
    """
    markup = types.InlineKeyboardMarkup(row_width=2)

    # btns for token selection
    amounts = [0.01, 0.02, 0.05, 0.1]
    buttons = [
        types.InlineKeyboardButton(f"💰 Buy {amount} ETH", callback_data=f"buy_{amount}_{wallet['address']}")
        for amount in amounts
    ]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("💵 Custom Buy", callback_data=f"custom_buy_{wallet['address']}"))

    # btns for Gwei settings
    current_gwei = user_gwei_preferences.get(wallet["chat_id"], 10)  
    gwei_presets = [1, 5, 10]
    gwei_buttons = [
        types.InlineKeyboardButton(
            f"{preset} Gwei {'🟢' if preset == current_gwei else ''}",
            callback_data=f"preset_gwei_{preset}_{wallet['address']}"
        ) for preset in gwei_presets
    ]
    markup.add(
        types.InlineKeyboardButton("⛽ Set Gas:", callback_data=f"custom_gwei_{wallet['address']}"),
        *gwei_buttons
    )

    markup.add(types.InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu"))
    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith("preset_gwei_"))
def handle_gwei_preset(call):
    """
    Manages the selection of a Gwei preset.
    """
    data = call.data.split("_")
    preset_gwei = int(data[2])
    wallet_address = data[3]
    chat_id = call.message.chat.id

    # update user_gwei_preferences with the new preset value
    user_gwei_preferences[chat_id] = preset_gwei

    bot.answer_callback_query(call.id, f"{preset_gwei} Gwei successfully set!", show_alert=False)

    # update the menu global
    wallet = next((w for w in user_wallets.get(chat_id, []) if w["address"] == wallet_address), None)
    if wallet:
        token_info = {"name": "N/A"}  
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=buy_menu(wallet, token_info)
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("custom_gwei_"))
def handle_custom_gwei_prompt(call):
    """
    Displays a prompt for the user to enter a custom Gwei amount.
    """
    wallet_address = call.data.split("_")[-1]
    bot.send_message(
        call.message.chat.id,
        "Enter the custom Gwei value (1-500):",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_custom_gwei, wallet_address, call)


def process_custom_gwei(message, wallet_address, call):
    """
    Validates and saves the custom Gwei value supplied by the user.
    """
    chat_id = message.chat.id
    try:
        gwei_value = int(message.text.strip())
        if gwei_value < 1 or gwei_value > 500:
            raise ValueError("Invalid Gwei value. Enter a number between 1 and 500.")
        user_gwei_preferences[chat_id] = gwei_value

        # send success message
        bot.answer_callback_query(call.id, f"{gwei_value} Gwei successfully set!", show_alert=False)

        # update the menu global
        wallet = next((w for w in user_wallets.get(chat_id, []) if w["address"] == wallet_address), None)
        if wallet:
            token_info = {"name": "N/A"}  
            bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=buy_menu(wallet, token_info)
            )
    except ValueError as e:
        bot.send_message(chat_id, f"⚠️ {e}\nPlease try again.")
        handle_custom_gwei_prompt(call)
    except Exception as e:
        print(f"Error processing custom Gwei: {e}")



@bot.callback_query_handler(func=lambda call: call.data == "manual_buy")
def manual_buy_handler(call):
    """
    handle manual buy and ask user to select a wallet.
    """
    wallets = user_wallets.get(call.message.chat.id, [])
    if not wallets:
        bot.send_message(
            call.message.chat.id,
            "No wallets available. Please create a wallet first.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")
            )
        )
        return
    bot.edit_message_text(
        "Select a wallet for Manual Buy:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=buy_wallets_menu(wallets)
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("manual_buy_wallet_"))
def select_wallet_for_buy(call):
    """
    handle wallet selection for manual buy.
    """
    wallet_idx = int(call.data.split("_")[-1])
    wallet = user_wallets.get(call.message.chat.id, [])[wallet_idx]
    wallet["chat_id"] = call.message.chat.id  
    manual_buy_menu(wallet)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_token_address, wallet)


def fetch_dexscreener_data(token_address):
    """
    get data token with dex screener.
    """
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "pairs" in data and data["pairs"]:
                pair = data["pairs"][0]
                price_usd = float(pair.get("priceUsd", 0))
                liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0))
                return price_usd, liquidity_usd
        return 0, 0
    except Exception as e:
        print(f"Error fetching data from DEX Screener: {e}")
        return 0, 0

def get_token_details(contract, uniswap_pair_contract=None):
    """
    Retrieves token details via calls to its accessible functions.
    Includes MarketCap and Liquidity information if available.
    """
    try:
        # main infos
        try:
            name = contract.functions.name().call()
        except Exception as e:
            print(f"Error fetching name: {e}")
            name = "N/A"

        try:
            symbol = contract.functions.symbol().call()
        except Exception as e:
            print(f"Error fetching symbol: {e}")
            symbol = "N/A"

        try:
            decimals = contract.functions.decimals().call()
        except Exception as e:
            print(f"Error fetching decimals: {e}")
            decimals = 18  # default to 20

        try:
            total_supply = contract.functions.totalSupply().call() / (10 ** decimals)
        except Exception as e:
            print(f"Error fetching totalSupply: {e}")
            total_supply = 0

        # get price and liquidity with dexscreener
        price_usd, liquidity_usd = fetch_dexscreener_data(contract.address)

        # mcap calculation
        market_cap = total_supply * price_usd

        # tax information
        try:
            buy_tax = contract.functions.projectBuyTaxBasisPoints().call() / 100 if hasattr(contract.functions, "projectBuyTaxBasisPoints") else "N/A"
        except Exception as e:
            print(f"Error fetching buy tax: {e}")
            buy_tax = "N/A"

        try:
            sell_tax = contract.functions.projectSellTaxBasisPoints().call() / 100 if hasattr(contract.functions, "projectSellTaxBasisPoints") else "N/A"
        except Exception as e:
            print(f"Error fetching sell tax: {e}")
            sell_tax = "N/A"

        # cotnract address
        contract_address = contract.address if hasattr(contract, "address") else "N/A"

        # return collected data
        return {
            "name": name,
            "symbol": symbol,
            "decimals": decimals,
            "total_supply": total_supply,
            "buy_tax": buy_tax,
            "sell_tax": sell_tax,
            "price_usd": price_usd,
            "liquidity_usd": liquidity_usd,
            "market_cap": round(market_cap, 2),
            "contract_address": contract_address,
        }
    except Exception as e:
        print(f"Error fetching token details: {e}")
        return {}


def process_token_address(message, wallet):
    """
    handle token address and show token info with the abi.
    """
    token_address = message.text.strip()
    if not token_address.startswith("0x") or len(token_address) != 42:
        bot.send_message(message.chat.id, "Invalid token address. Please try again.")
        return

    try:
        contract = load_contract(token_address)
        token_details = get_token_details(contract)

        wallet["last_token_address"] = token_address

        # define gwei parameters
        amount_to_swap = 0.05  # ETH Amount to swap
        gas_price_gwei = user_gwei_preferences.get(wallet["chat_id"], 20)  # gas defined by user
        gas_limits = [21000, 100000, 250000]  # gas limits

        # fees calculation
        fees = calculate_total_fees(amount_to_swap, gas_price_gwei, gas_limits)

        # show token info
        bot.send_message(
            message.chat.id,
            f"*Token Information:*\n"
            f"🔹 {token_details.get('name', 'N/A')} ({token_details.get('symbol', 'N/A')})\n"
            f"🔹 `{token_details.get('contract_address', 'N/A')}`\n\n"
            f"🔹 Pool info:\n"
            f"🦄 DEX: UniSwap V2\n"
            f"🔹 Fees: B {token_details.get('buy_tax', 'N/A')}% | S {token_details.get('sell_tax', 'N/A')}%\n"
            f"🔹 Total Supply: {token_details.get('total_supply', 'N/A')} tokens\n"
            f"🔹 Price (USD): ${round(token_details.get('price_usd', 0), 4)}\n"
            f"💧 Liquidity: ${round(token_details.get('liquidity_usd', 0), 2):,}\n"
            f"📊 MarketCap: `${round(token_details.get('market_cap', 0), 2):,}`\n\n",
            parse_mode="Markdown",
            reply_markup=buy_menu(wallet, {"ticker": {token_details.get('name', 'N/A')}, "contract": token_address})
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"Error loading token information: {e}")







@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_token(call):
    """
    Handle buy token with a custom amount
    """
    _, eth_amount, wallet_address = call.data.split("_")
    wallet = next((w for w in user_wallets.get(call.message.chat.id, []) if w["address"] == wallet_address), None)

    if not wallet:
        bot.send_message(call.message.chat.id, "Wallet not found. Please try again.")
        return

    try:
        token_address = wallet.get("last_token_address")
        if not token_address:
            bot.send_message(call.message.chat.id, "No token address found. Please start again.")
            return

        tx_hash = swap_eth_to_token(wallet, token_address, Decimal(eth_amount))

        bot.send_message(
            call.message.chat.id,
            f"Order completed! 🎉\nTransaction hash: `{tx_hash}`",
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")
            )
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Error during swap: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("custom_buy_"))
def custom_buy_handler(call):
    """
    handle buy token asking user for a custom amount.
    """
    wallet_address = call.data.split("_")[-1]
    bot.send_message(
        call.message.chat.id,
        "Enter the amount of ETH to spend:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_custom_buy, wallet_address)


def process_custom_buy(message, wallet_address):
    try:
        eth_amount = float(message.text.strip())
        if eth_amount <= 0:
            raise ValueError("Amount must be positive.")

        if not user_wallets:
            bot.send_message(message.chat.id, "No wallets found. Please create a wallet first.")
            return

        if isinstance(user_wallets, dict):
            wallet = next(
                (wallet for wallets in user_wallets.values() for wallet in wallets if wallet["address"] == wallet_address),
                None
            )
        elif isinstance(user_wallets, list):
            wallet = next((wallet for wallet in user_wallets if wallet["address"] == wallet_address), None)
        else:
            raise ValueError("Invalid wallet data structure.")

        if not wallet:
            bot.send_message(message.chat.id, "Wallet not found. Please try again.")
            return

        token_address = wallet.get("last_token_address")
        if not token_address:
            bot.send_message(message.chat.id, "No token address found. Please start again.")
            return

        tx_hash = swap_eth_to_token(wallet, token_address, eth_amount)

        bot.send_message(
            message.chat.id,
            f"Custom buy completed! 🎉\nTransaction hash: `{tx_hash}`",
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")
            )
        )
    except ValueError as e:
        bot.send_message(message.chat.id, f"⚠️ Invalid input: {e}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error during custom buy: {e}")




@bot.callback_query_handler(func=lambda call: call.data.startswith("set_gwei_"))
def set_gwei_handler(call):
    """
    handle gwei preset.
    """
    wallet_address = call.data.split("_")[-1]
    bot.send_message(
        call.message.chat.id,
        "Enter the custom Gwei value:\n\n"
        "🔹 **Recommended ranges:**\n"
        "   - **Low:** 0.1-5 Gwei (slow, suitable for low traffic)\n"
        "   - **Moderate:** 5-10 Gwei (balanced speed and cost)\n"
        "   - **High:** 10-100+ Gwei (fast, for congested networks)\n\n"
        "❗ **Note:** Values below 1 Gwei may not work, and excessively high values will increase transaction costs.\n"
        "Example: `20` (for 20 Gwei)",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_custom_gwei, wallet_address)


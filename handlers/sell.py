import requests
from telebot import types
from shared_data.shared_data import bot, user_wallets, user_gwei_preferences
from actions.contracts import load_contract
from actions.sell import execute_swap_to_eth
from actions.utils import calculate_total_fees


def wallets_menu(wallets):
    """
    generate a menu for manual sell
    """
    markup = types.InlineKeyboardMarkup()
    for idx, wallet in enumerate(wallets):
        address_short = f"{wallet['address'][:6]}...{wallet['address'][-4:]}"
        markup.add(types.InlineKeyboardButton(
            f"Wallet {idx + 1}: {address_short}",
            callback_data=f"manual_sell_wallet_{idx}"
        ))
    markup.add(types.InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu"))
    return markup


def sell_menu(wallet, token_info, position_info):
    """
    Generates a menu to display sales options with buttons to sell by percentage or initial
    """
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Buttons to sell by percentage
    percentages = [25, 50, 100]
    buttons = [
        types.InlineKeyboardButton(
            f"Sell {percentage}%",
            callback_data=f"sell_{percentage}_{wallet['address']}_{token_info['contract']}"
        )
        for percentage in percentages
    ]
    buttons.append(
        types.InlineKeyboardButton(
            "Sell Initials", 
            callback_data=f"sell_initial_{wallet['address']}_{token_info['contract']}"
        )
    )
    markup.add(*buttons)

    # buttons for Gwei settings
    current_gwei = user_gwei_preferences.get(wallet["chat_id"], 10)  # default value
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

    markup.add(types.InlineKeyboardButton("⬅️ Back to Positions", callback_data="positions_menu"))
    return markup


@bot.callback_query_handler(func=lambda call: call.data == "manual_sell")
def manual_sell_handler(call):
    """
    Manages the “Manual Sell” action and displays a list of available wallets.
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
        "Select a wallet for Manual Sell:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=wallets_menu(wallets)
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("manual_sell_wallet_"))
def select_wallet_for_sell(call):
    """
    Displays the positions associated with the portfolio for selling a token
    """
    wallet_idx = int(call.data.split("_")[-1])
    wallets = user_wallets.get(call.message.chat.id, [])
    wallet = wallets[wallet_idx]

    positions = wallet.get("positions", [])  
    if not positions:
        bot.send_message(call.message.chat.id, "No positions found in this wallet.")
        return

    markup = types.InlineKeyboardMarkup()
    for idx, position in enumerate(positions):
        markup.add(types.InlineKeyboardButton(
            f"Position {idx + 1}: {position['token_name']}",
            callback_data=f"sell_position_{idx}_{wallet['address']}"
        ))
    bot.edit_message_text(
        "Select a position to sell:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("sell_position_"))
def sell_position_handler(call):
    """
    Manages the selection of a specific position to sell
    """
    _, position_idx, wallet_address = call.data.split("_")
    wallet = next((w for w in user_wallets.get(call.message.chat.id, []) if w["address"] == wallet_address), None)

    if not wallet:
        bot.send_message(call.message.chat.id, "Wallet not found.")
        return

    # get position info
    position_idx = int(position_idx)
    position = wallet["positions"][position_idx]
    token_info = {"name": position["token_name"], "contract": position["token_address"]}
    position_info = {
        "balance": position["balance"],
        "value_usd": position["value_usd"]
    }

    # show sell menu
    bot.send_message(
        call.message.chat.id,
        f"Token: {token_info['name']}\n"
        f"Balance: {position_info['balance']} tokens\n"
        f"Value: ${position_info['value_usd']}",
        reply_markup=sell_menu(wallet, token_info, position_info)
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("sell_"))
def handle_sell(call):
    """
    Manages the sale of a percentage or the initial amount.
    """
    _, percentage, wallet_address, token_address = call.data.split("_")

    wallet = next((w for w in user_wallets.get(call.message.chat.id, []) if w["address"] == wallet_address), None)
    if not wallet:
        bot.send_message(call.message.chat.id, "Wallet not found. Please try again.")
        return

    # get contract and token balance
    contract = load_contract(token_address)
    token_balance = contract.functions.balanceOf(wallet["address"]).call()
    if token_balance <= 0:
        bot.send_message(call.message.chat.id, "No tokens to sell.")
        return

    # calculate amount to sell
    if percentage == "initial":
        sell_amount = wallet.get("initial_investment", 0)
    else:
        sell_amount = (token_balance * int(percentage)) // 100

    try:
        tx_hash = execute_swap_to_eth(wallet, token_address, sell_amount)
        bot.send_message(
            call.message.chat.id,
            f"Sell completed! 🎉\nTransaction hash: `{tx_hash}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Error during sell: {e}")

from telebot import types
from shared_data.shared_data import bot, user_wallets  
from actions.wallets import create_wallet, check_balance


# Wallets menu layout
# handlers/wallets.py

from telebot import types

def wallets_menu(wallets):
    """
    Generate a menu for selecting a wallet.
    """
    markup = types.InlineKeyboardMarkup()
    if wallets:
        for idx, wallet in enumerate(wallets):
            wallet_balance = wallet.get("balance", 0.0)
            address_short = f"{wallet['address'][:6]}...{wallet['address'][-4:]}"
            markup.add(types.InlineKeyboardButton(
                f"Wallet {idx + 1}: {address_short} ({wallet_balance:.4f} ETH)",
                callback_data=f"wallet_{idx}"
            ))
    markup.add(types.InlineKeyboardButton("➕ Create Wallet", callback_data="create_wallet"))
    markup.add(types.InlineKeyboardButton("⬅️ Go Back", callback_data="main_menu"))
    return markup


@bot.callback_query_handler(func=lambda call: call.data == "wallets")
def wallets_handler(call):
    # get users wallets
    wallets = [
        {
            "address": wallet["address"],
            "balance": check_balance(wallet["address"], None)[0]  # ETH balance
        }
        for wallet in user_wallets.get(call.message.chat.id, [])
    ]
    bot.edit_message_text(
        "Here are your wallets:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=wallets_menu(wallets)
    )

@bot.callback_query_handler(func=lambda call: call.data == "create_wallet")
def create_wallet_handler(call):
    # Create a new wallet and add it to the user's wallets list
    wallet = create_wallet()
    user_wallets.setdefault(call.message.chat.id, []).append(wallet)
    wallets = [
        {
            "address": wallet["address"],
            "balance": 0.0  # Default ETH balance for new wallets
        }
        for wallet in user_wallets.get(call.message.chat.id, [])
    ]
    bot.edit_message_text(
        "Wallet created successfully! Here are your wallets:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=wallets_menu(wallets)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("wallet_"))
def wallet_details_handler(call):
    # Get wallet details for the selected wallet
    wallet_idx = int(call.data.split("_")[-1])
    wallet = user_wallets.get(call.message.chat.id, [])[wallet_idx]
    bot.edit_message_text(
        f"**Wallet Details:**\n\n"
        f"**Address:**\n`{wallet['address']}`\n\n"
        f"**Private Key:**\n`{wallet['private_key']}`\n\n"
        "⚠️ *Keep your private key secure and do not share it!*",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("⬅️ Go Back", callback_data="wallets")
        )
    )

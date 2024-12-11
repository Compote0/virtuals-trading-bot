# handlers/positions.py

from telebot import types
from shared_data.shared_data import bot, user_wallets, user_positions  
from actions.menus import display_positions

@bot.callback_query_handler(func=lambda call: call.data == "positions")
def positions_handler(call):
    # get users wallets
    wallets = user_wallets.get(call.message.chat.id, [])
    if not wallets:
        bot.send_message(
            call.message.chat.id,
            "No wallets found. Please create a wallet first.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("⬅️ Go Back", callback_data="main_menu")
            )
        )
        return

    bot.edit_message_text(
        "Select a wallet to view its positions:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=positions_menu(wallets)
    )

def positions_menu(wallets):
    """
    generate a menu for wallet selection.
    """
    markup = types.InlineKeyboardMarkup()
    if wallets:
        for idx, wallet in enumerate(wallets):
            address_short = f"{wallet['address'][:6]}...{wallet['address'][-4:]}"
            markup.add(types.InlineKeyboardButton(
                f"Wallet {idx + 1}: {address_short}",
                callback_data=f"positions_wallet_{idx}"
            ))
    markup.add(types.InlineKeyboardButton("⬅️ Go Back", callback_data="main_menu"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("positions_wallet_"))
def wallet_positions_handler(call):
    """
    show positions for a specific wallet.
    """
    wallet_idx = int(call.data.split("_")[-1])
    wallets = user_wallets.get(call.message.chat.id, [])
    if wallet_idx >= len(wallets):
        bot.send_message(call.message.chat.id, "Invalid wallet selection.")
        return

    wallet = wallets[wallet_idx]
    wallet_address = wallet["address"]
    positions = user_positions.get(wallet_address, [])

    bot.edit_message_text(
        f"Positions for Wallet {wallet_idx + 1}:\n\n{display_positions(positions)}",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("⬅️ Go Back", callback_data="positions")
        )
    )

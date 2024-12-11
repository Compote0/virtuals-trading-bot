from telebot import types


# Generate positions menu for wallets
def positions_menu(wallets):
    """
    Generates an inline menu to display available positions in wallets.
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

def display_positions(positions):
    """
    Generates a formatted string to display wallet positions.
    """
    if not positions:  
        return "No positions yet."

    positions_text = "**Positions:**\n"
    for position in positions:
        positions_text += (
            f"- Token: {position.get('token', 'Unknown')}\n"
            f"  Amount: {position.get('amount', 0)}\n"
            f"  Value: {position.get('value', 0)} ETH\n\n"
        )
    return positions_text

from shared_data.shared_data import bot  
from handlers import wallets, positions, buy, sell  
from telebot import types
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telebot.types import BotCommand

def setup_bot_commands(bot):
    """
    Set up commands for suggestions in the Telegram input field.
    """
    commands = [
        BotCommand("start", "Start the bot")
        # BotCommand("wallets", "Manage your wallets"),
        # BotCommand("positions", "View your positions"),
        # BotCommand("manual_buy", "Buy tokens manually"),
        # BotCommand("manual_sell", "Sell tokens manually")
    ]
    bot.set_my_commands(commands)

setup_bot_commands(bot)

# main menu
def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 Wallets", callback_data="wallets"))
    markup.add(types.InlineKeyboardButton("📊 Positions", callback_data="positions"))
    markup.add(types.InlineKeyboardButton("💰 Manual Buy", callback_data="manual_buy"))
    markup.add(types.InlineKeyboardButton("🔻 Manual Sell", callback_data="manual_sell"))
    markup.add(types.InlineKeyboardButton("Close", callback_data="close"))
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Welcome to the Virtuals Trading Bot! Use the options below to navigate.",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def return_to_main_menu(call):
    bot.edit_message_text(
        "Welcome back to the Virtuals Trading Bot! Use the options below to navigate.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "close")
def close_menu(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    bot.polling()

from web3 import Web3
from telebot import TeleBot
from dotenv import load_dotenv
import os

# load dotenv 
load_dotenv()

# alchemy config
ALCHEMY_URL = os.getenv("ALCHEMY_URL")
web3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

# init telegram bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)

fee_recipient = ""
virtual_token_address = "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"
weth_address = "0x4200000000000000000000000000000000000006"


# store user data (temporary, a DB is better. If process is stopped, all data is lost)
user_wallets = {}
user_positions = {}  
user_gwei_preferences = {}  

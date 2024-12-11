import requests
from dotenv import load_dotenv
import os

load_dotenv()

BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")

def get_contract_abi(contract_address):
    url = f"https://api.basescan.org/api"
    params = {
        "module": "contract",
        "action": "getabi",
        "address": contract_address,
        "apikey": BASESCAN_API_KEY
    }
    
    print(f"[DEBUG] Sending request to {url} with params: {params}")
    
    response = requests.get(url, params=params)
    data = response.json()
    
    print(f"[DEBUG] Response received: {data}")
    
    if data["status"] == "1":  
        abi = data["result"]
        # abi log
        print(f"[DEBUG] ABI successfully retrieved: {abi[:500]}...")  # show only first 500 characters
        return abi
    else:
        error_message = data["result"]
        print(f"[ERROR] Error retrieving ABI: {error_message}")
        raise Exception(f"Error retrieving ABI: {error_message}")

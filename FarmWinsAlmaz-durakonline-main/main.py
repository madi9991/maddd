import os
import time
import threading
import requests
from durakonline import durakonline
from secrets import token_hex
from datetime import datetime

MAIN_TOKEN = os.environ.get("MAIN_TOKEN")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not MAIN_TOKEN or not BOT_TOKEN:
    raise RuntimeError("Environment variables MAIN_TOKEN and BOT_TOKEN must be set. See README for details.")
COUNT: int = 20

DEBUG_MODE: bool = False
SERVERS: [] = [
    "u1"
]

class Almaz:

    games: int = 0
    accounts: [] = []

    def __init__(self):
        self.pages = [
            self.acc,
        ]
    def start_game(self, main, bot, server_id: str, count: int = 1000):
        self.games += 1
        self.log("Create 1 thread", f"{server_id}")
        game = bot.game.create(100, "1", 2, 52)
        main.game.join("1", game.id)
        main._get_data("game")
        for i in range(count):
            self.log(f"{i+1} game", f"{server_id}")
            main.game.ready()
            bot.game.ready()

            for i in range(4):
                try:
                    main_cards = main._get_data("hand")["cards"]
                except:
                    pass
                try:
                    bot_cards = bot._get_data("hand")["cards"]
                except:
                    pass
                mode = bot._get_data("mode")
                if mode["0"] == 1:
                    bot.game.turn(bot_cards[0])
                    time.sleep(.1)
                    main.game.take()
                    time.sleep(.1)
                    bot.game._pass()
                else:
                    main.game.turn(main_cards[0])
                    time.sleep(.1)
                    bot.game.take()
                    time.sleep(.1)
                    main.game._pass()
            bot.game.surrender()
            bot._get_data("game_over")
        main.game.leave(game.id)
        self.log("Leave", "MAIN")
        self.games -= 1
        if not self.games:
            data = main._get_data("uu")
            while data["k"] != "points":
                data = main._get_data("uu")
            self.log(f"Balance: {data.get('v')}\n", "MAIN")

    def start(self):
        page_type = 1
        self.pages[page_type-1]("$u")
        
    def acc(self, token: str):
        for server_id in SERVERS:
            main = durakonline.Client(MAIN_TOKEN, server_id=server_id, tag="[MAIN]", debug=DEBUG_MODE)
            bot = durakonline.Client(BOT_TOKEN, server_id=server_id, tag="[BOT]", debug=DEBUG_MODE)
            threading.Thread(target=self.start_game, args=(main, bot, server_id, COUNT, )).start()

    def log(self, message: str, tag: str = "MAIN") -> None:
        print(f">> [{tag}] [{datetime.now().strftime('%H:%M:%S')}] {message}")

if __name__ == "__main__":
    Almaz().start()
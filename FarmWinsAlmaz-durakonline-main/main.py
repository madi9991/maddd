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
    def start_game(self, main, bot, server_id: str, count: int = 1000, winner: str = "main"):
        """
        Play `count` games on `server_id`. `winner` should be 'main' or 'bot' and
        determines which account will surrender to give the win.
        """
        if winner not in ("main", "bot"):
            raise ValueError("winner must be 'main' or 'bot'")
        self.games += 1
        self.log("Create 1 thread", f"{server_id}")
        game = bot.game.create(100, "1", 2, 52)
        main.game.join("1", game.id)
        main._get_data("game")
        for i in range(count):
            self.log(f"{i+1} game (winner={winner})", f"{server_id}")
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
            # surrender depending on chosen winner
            if winner == "main":
                bot.game.surrender()
            else:
                main.game.surrender()
            # wait for game over on both clients
            bot._get_data("game_over")
            main._get_data("game_over")
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
        
    def run_sequence(self, main, bot, server_id):
        # First make MAIN win COUNT games, then BOT win COUNT games
        self.log(f"Starting sequence: MAIN -> BOT ({COUNT} wins each)", server_id)
        try:
            self.start_game(main, bot, server_id, COUNT, winner="main")
        except Exception as e:
            self.log(f"Error during MAIN series: {e}", "ERROR")

        # Reinitialize clients to avoid stale state affecting the second series
        try:
            self.log("Reinitializing clients before BOT series", server_id)
            try:
                main.close_connection()
            except Exception:
                pass
            try:
                bot.close_connection()
            except Exception:
                pass
            time.sleep(1)
            main = durakonline.Client(MAIN_TOKEN, server_id=server_id, tag="[MAIN]", debug=DEBUG_MODE)
            bot = durakonline.Client(BOT_TOKEN, server_id=server_id, tag="[BOT]", debug=DEBUG_MODE)
        except Exception as e:
            self.log(f"Error reinitializing clients: {e}", "ERROR")

        try:
            self.start_game(main, bot, server_id, COUNT, winner="bot")
        except Exception as e:
            self.log(f"Error during BOT series: {e}", "ERROR")

        # Log balances for verification
        try:
            data_main = main._get_data("uu")
            while data_main["k"] != "points":
                data_main = main._get_data("uu")
            self.log(f"MAIN balance after both series: {data_main.get('v')}", "MAIN")
        except Exception as e:
            self.log(f"Couldn't read MAIN balance: {e}", "ERROR")
        try:
            data_bot = bot._get_data("uu")
            while data_bot["k"] != "points":
                data_bot = bot._get_data("uu")
            self.log(f"BOT balance after both series: {data_bot.get('v')}", "BOT")
        except Exception as e:
            self.log(f"Couldn't read BOT balance: {e}", "ERROR")

        self.log("Sequence complete", server_id)

    def acc(self, token: str):
        for server_id in SERVERS:
            main = durakonline.Client(MAIN_TOKEN, server_id=server_id, tag="[MAIN]", debug=DEBUG_MODE)
            bot = durakonline.Client(BOT_TOKEN, server_id=server_id, tag="[BOT]", debug=DEBUG_MODE)
            threading.Thread(target=self.run_sequence, args=(main, bot, server_id)).start()

    def log(self, message: str, tag: str = "MAIN") -> None:
        print(f">> [{tag}] [{datetime.now().strftime('%H:%M:%S')}] {message}")

if __name__ == "__main__":
    Almaz().start()
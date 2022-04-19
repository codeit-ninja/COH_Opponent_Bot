import logging

from Classes.COHOpponentBot_GameData import GameData
from Classes.COHOpponentBot_GUI import GUI

# Program Entry Starts here
# Default error logging log file location:
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    format='%(asctime)s (%(threadName)-10s) [%(levelname)s] %(message)s',
    filename='COH_Opponent_Bot.log',
    filemode="w",
    level=logging.INFO)

GameData.clearOverlayHTML()

main = GUI()

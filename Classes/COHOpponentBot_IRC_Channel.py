import threading
import logging
import re

from socket import socket
from threading import Thread
from tkinter import END
from Classes.COHOpponentBot_IRC_Client import IRC_Client

from Classes.COHOpponentBot_Settings import Settings
from Classes.COHOpponentBot_GameData import GameData


class IRC_Channel(threading.Thread):
    """Iplements an IRC Channel Connection. Checks User Commands."""

    def __init__(
        self,
        ircClient: IRC_Client,
        ircSocket: socket,
        queue,
        channel,
        settings=None
            ):
        Thread.__init__(self)
        self.ircClient = ircClient
        self.running = True
        self.ircSocket = ircSocket
        self.queue = queue
        self.channel = channel

        self.settings = settings
        if not settings:
            self.settings = Settings()

        self.gameData = GameData(self.ircClient, settings=self.settings)

    def run(self):
        self.ircSocket.send(('JOIN ' + self.channel + '\r\n').encode("utf8"))
        while self.running:
            line = self.queue.get()
            line = str.rstrip(line)
            line = str.split(line)
            if (line[0] == "EXITTHREAD"):
                self.close()
            if (line[0] == "OPPONENT"):
                self.check_for_user_command("self", "opp")
            if (line[0] == "TEST"):
                self.test_output()
            if (line[0] == "IWON"):
                self.ircClient.SendPrivateMessageToIRC("!i won")
            if (line[0] == "ILOST"):
                self.ircClient.SendPrivateMessageToIRC("!i lost")
            if (line[0] == "CLEAROVERLAY"):
                GameData.clear_overlay_HTML()
            if (
                len(line) >= 4
                and "PRIVMSG" == line[2]
                and "jtv" not in line[0]
            ):
                # call function to handle user message
                self.user_message(line)

    def user_message(self, line):
        # Dissect out the useful parts of the raw data line
        # into username and message and remove certain characters
        msgFirst = line[1]
        msgUserName = msgFirst[1:]
        msgUserName = msgUserName.split("!")[0]
        # msgType = line [1];
        # msgChannel = line [3]
        msgMessage = " ".join(line[4:])
        msgMessage = msgMessage[1:]
        messageString = str(msgUserName) + " : " + str(msgMessage)
        logging.info(str(messageString).encode('utf8'))

        # Check for UserCommands
        self.check_for_user_command(msgUserName, msgMessage)

        if (
            msgMessage == "exit"
            and msgUserName == self.ircClient.adminUserName
        ):
            self.ircClient.send_private_message_to_IRC("Exiting")
            self.close()

    def check_for_user_command(self, userName, message):
        logging.info("Checking For User Comamnd")
        try:
            if (
                bool(re.match(r"^(!)?opponent(\?)?$", message.lower()))
                or bool(re.match(r"^(!)?place your bets$", message.lower()))
                or bool(re.match(r"^(!)?opp(\?)?$", message.lower()))
            ):

                self.gameData = GameData(
                    ircClient=self.ircClient,
                    settings=self.settings
                )
                if self.gameData.get_data_from_game():
                    self.gameData.output_opponent_data()
                else:
                    self.ircClient.send_private_message_to_IRC(
                        "Can't find the opponent right now."
                    )

            user = str(userName).lower()
            admin = str(self.settings.privatedata.get('adminUserName'))
            channel = str(self.settings.data.get('channel'))
            if (
                message.lower() == "test"
                and user == admin.lower()
                or user == channel.lower()
            ):
                self.ircClient.send_private_message_to_IRC(
                    "I'm here! Pls give me mod to prevent twitch"
                    " from autobanning me for spam if I have to send"
                    " a few messages quickly."
                )
                self.ircClient.output.insert(
                    END,
                    f"Oh hi again, I heard you in the {self.channel[1:]}"
                    " channel.\n"
                )

            if (bool(re.match(r"^(!)?gameinfo(\?)?$", message.lower()))):
                self.game_info()

            if (bool(re.match(r"^(!)?story(\?)?$", message.lower()))):
                self.story()

            if (bool(re.match(r"^(!)?debug(\?)?$", message.lower()))):
                self.print_info_to_debug()

        except Exception as e:
            logging.error("Problem in CheckForUserCommand")
            logging.error(str(e))
            logging.exception("Exception : ")

    def print_info_to_debug(self):
        try:
            self.gameData = GameData(
                self.ircClient,
                settings=self.settings
            )
            self.gameData.get_data_from_game()
            self.gameData.get_mapDescriptionFull_from_UCS_file()
            self.gameData.get_mapNameFull_from_UCS_file()
            logging.info(self.gameData)
            self.ircClient.send_private_message_to_IRC(
                "GameData saved to log file."
            )
        except Exception as e:
            logging.error("Problem in PrintInfoToDebug")
            logging.error(str(e))
            logging.exception("Exception : ")

    def game_info(self):
        self.gameData = GameData(self.ircClient, settings=self.settings)
        if self.gameData.get_data_from_game():
            self.ircClient.send_private_message_to_IRC(
                f"Map : {self.gameData.mapNameFull},"
                f" High Resources : {self.gameData.highResources},"
                f" Automatch : {self.gameData.automatch},"
                f" Slots : {self.gameData.slots},"
                f" Players : {self.gameData.numberOfPlayers}."
            )

    def story(self):
        self.gameData = GameData(self.ircClient, settings=self.settings)
        logging.info(str(self.gameData))
        if self.gameData.get_data_from_game():
            logging.info(str(self.gameData))
            # Requires parsing the map description from
            # the UCS file this takes time so must be done first
            self.gameData.get_mapDescriptionFull_from_UCS_file()
            self.ircClient.send_private_message_to_IRC(
                "{}.".format(self.gameData.mapDescriptionFull))

    def test_output(self):
        if not self.gameData:
            self.gameData = GameData(
                self.ircClient,
                settings=self.settings
            )
            self.gameData.get_data_from_game()
        self.gameData.test_output()

    def close(self):
        self.running = False
        logging.info("Closing Channel " + str(self.channel) + " thread.")

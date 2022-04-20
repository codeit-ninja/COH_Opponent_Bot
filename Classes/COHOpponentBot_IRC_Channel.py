import threading
import logging
import re

from threading import Thread
from tkinter import END

from Classes.COHOpponentBot_Parameters import Parameters
from Classes.COHOpponentBot_GameData import GameData


class IRC_Channel(threading.Thread):
    def __init__(self, ircClient, irc, queue, channel, parameters=None):
        Thread.__init__(self)
        self.ircClient = ircClient
        self.running = True
        self.irc = irc
        self.queue = queue
        self.channel = channel

        self.parameters = parameters
        if not parameters:
            self.parameters = Parameters()

        self.gameData = GameData(self.ircClient, parameters=self.parameters)

    def run(self):
        self.irc.send(('JOIN ' + self.channel + '\r\n').encode("utf8"))
        while self.running:
            line = self.queue.get()
            line = str.rstrip(line)
            line = str.split(line)
            if (line[0] == "EXITTHREAD"):
                self.close()
            if (line[0] == "OPPONENT"):
                self.CheckForUserCommand("self", "opp")
            if (line[0] == "TEST"):
                self.testOutput()
            if (line[0] == "IWON"):
                self.ircClient.SendPrivateMessageToIRC("!i won")
            if (line[0] == "ILOST"):
                self.ircClient.SendPrivateMessageToIRC("!i lost")
            if (line[0] == "CLEAROVERLAY"):
                GameData.clearOverlayHTML()
            if (
                len(line) >= 4
                and "PRIVMSG" == line[2]
                and "jtv" not in line[0]
            ):
                # call function to handle user message
                self.UserMessage(line)

    def UserMessage(self, line):
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
        self.CheckForUserCommand(msgUserName, msgMessage)

        if (
            msgMessage == "exit"
            and msgUserName == self.ircClient.adminUserName
        ):
            self.ircClient.SendPrivateMessageToIRC("Exiting")
            self.close()

    def CheckForUserCommand(self, userName, message):
        logging.info("Checking For User Comamnd")
        try:
            if (
                bool(re.match(r"^(!)?opponent(\?)?$", message.lower()))
                or bool(re.match(r"^(!)?place your bets$", message.lower()))
                or bool(re.match(r"^(!)?opp(\?)?$", message.lower()))
            ):

                self.gameData = GameData(
                    ircClient=self.ircClient,
                    parameters=self.parameters
                )
                if self.gameData.GetDataFromGame():
                    self.gameData.outputOpponentData()
                else:
                    self.ircClient.SendPrivateMessageToIRC(
                        "Can't find the opponent right now."
                    )

            user = str(userName).lower()
            admin = str(self.parameters.privatedata.get('adminUserName'))
            channel = str(self.parameters.data.get('channel'))
            if (
                message.lower() == "test"
                and user == admin.lower()
                or user == channel.lower()
            ):
                self.ircClient.SendPrivateMessageToIRC(
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
                self.gameInfo()

            if (bool(re.match(r"^(!)?story(\?)?$", message.lower()))):
                self.story()

            if (bool(re.match(r"^(!)?debug(\?)?$", message.lower()))):
                self.PrintInfoToDebug()

        except Exception as e:
            logging.error("Problem in CheckForUserCommand")
            logging.error(str(e))
            logging.exception("Exception : ")

    def PrintInfoToDebug(self):
        try:
            self.gameData = GameData(
                self.ircClient,
                parameters=self.parameters
            )
            self.gameData.GetDataFromGame()
            self.gameData.GetMapDescriptionFromUCSFile()
            self.gameData.GetMapNameFullFromUCSFile()
            logging.info(self.gameData)
            self.ircClient.SendPrivateMessageToIRC(
                "GameData saved to log file."
            )
        except Exception as e:
            logging.error("Problem in PrintInfoToDebug")
            logging.error(str(e))
            logging.exception("Exception : ")

    def gameInfo(self):
        self.gameData = GameData(self.ircClient, parameters=self.parameters)
        if self.gameData.GetDataFromGame():
            self.ircClient.SendPrivateMessageToIRC(
                f"Map : {self.gameData.mapNameFull},"
                f" High Resources : {self.gameData.highResources},"
                f" Automatch : {self.gameData.automatch},"
                f" Slots : {self.gameData.slots},"
                f" Players : {self.gameData.numberOfPlayers}."
            )

    def story(self):
        self.gameData = GameData(self.ircClient, parameters=self.parameters)
        logging.info(str(self.gameData))
        if self.gameData.GetDataFromGame():
            logging.info(str(self.gameData))
            # Requires parsing the map description from
            # the UCS file this takes time so must be done first
            self.gameData.GetMapDescriptionFromUCSFile()
            self.ircClient.SendPrivateMessageToIRC(
                "{}.".format(self.gameData.mapDescriptionFull))

    def testOutput(self):
        if not self.gameData:
            self.gameData = GameData(
                self.ircClient,
                parameters=self.parameters
            )
            self.gameData.GetDataFromGame()
        self.gameData.TestOutput()

    def close(self):
        self.running = False
        logging.info("Closing Channel " + str(self.channel) + " thread.")

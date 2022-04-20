import logging
import threading

from Classes.COHOpponentBot_Parameters import Parameters
from Classes.COHOpponentBot_GameData import GameData
from Classes.COHOpponentBot_IRC_Client import IRC_Client
from Classes.COHOpponentBot_StatsRequest import StatsRequest


class MemoryMonitor(threading.Thread):

    def __init__(
        self, pollInterval=10,
        ircClient: IRC_Client = None,
        parameters=None
                ):
        threading.Thread.__init__(self)
        try:
            logging.info("Memory Monitor Started!")
            self.running = True

            self.parameters = parameters
            if not parameters:
                self.parameters = Parameters()

            self.pm = None
            self.baseAddress = None
            self.gameInProgress = False

            self.ircClient = ircClient
            self.pollInterval = int(pollInterval)
            self.event = threading.Event()
            self.gameData = None
            self.winLostTimer = None

        except Exception as e:
            logging.error("In FileMonitor __init__")
            logging.error(str(e))
            logging.exception("Exception : ")

    def run(self):
        try:
            while self.running:
                self.GetGameData()
                if self.gameInProgress:

                    if self.gameData.gameInProgress != self.gameInProgress:
                        # coh was running and now its not (game over)
                        self.GameOver()
                else:
                    if self.gameData.gameInProgress != self.gameInProgress:
                        # coh wasn't running and now it is (game started)
                        self.GameStarted()

                # set local gameInProgress flag to it can be compared with
                # any changes to it in the next loop
                self.gameInProgress = self.gameData.gameInProgress
                self.event.wait(self.pollInterval)
        except Exception as e:
            logging.error("In FileMonitor run")
            logging.error(str(e))
            logging.exception("Exception : ")

    def GetGameData(self):
        try:
            self.gameData = GameData(
                ircClient=self.ircClient,
                parameters=self.parameters)
            self.gameData.GetDataFromGame()
        except Exception as e:
            logging.error("In getGameData")
            logging.info(str(e))
            logging.exception("Exception : ")

    def GameStarted(self):
        try:
            self.gameData.outputOpponentData()
            self.PostSteamNumber()
            self.PostData()
            self.StartBets()

        except Exception as e:
            logging.info("Problem in GameStarted")
            logging.error(str(e))
            logging.exception("Exception : ")

    def PostSteamNumber(self):
        try:
            channel = str(self.parameters.data.get('channel'))
            steamNumber = str(self.parameters.data.get('steamNumber'))
            message = f"!setsteam,{channel},{steamNumber}"
            self.ircClient.SendMessageToOpponentBotChannelIRC(message)
        except Exception as e:
            logging.error("Problem in PostSteamNumber")
            logging.exception("Exception : ")
            logging.error(str(e))

    def PostData(self):
        # Sending to cohopponentbot channel about game,
        # this requires parsing mapName First
        try:
            message = self.gameData.GetGameDescriptionString()
            self.ircClient.SendMessageToOpponentBotChannelIRC(message)

        except Exception as e:
            logging.error("Problem in PostData")
            logging.error(str(e))
            logging.exception("Exception : ")

    def GameOver(self):
        try:
            # Get Win/Lose from server after 50 seconds
            if self.parameters.data.get('writeIWonLostInChat'):
                self.winLostTimer = threading.Timer(50.0, self.GetWinLose)
                self.winLostTimer.start()
            # Clear the overlay
            if (self.parameters.data.get('clearOverlayAfterGameOver')):
                self.ircClient.queue.put("CLEAROVERLAY")
        except Exception as e:
            logging.info("Problem in GameOver")
            logging.error(str(e))
            logging.exception("Exception : ")

    def GetWinLose(self):
        try:
            statnumber = self.parameters.data.get('steamNumber')
            statRequest = StatsRequest()
            statRequest.getMatchHistoryFromServer(statnumber)
            mostRecentWin = statRequest.getPlayerWinLastMatch(statnumber)
            if mostRecentWin:
                self.ircClient.SendPrivateMessageToIRC("!I won")
            else:
                self.ircClient.SendPrivateMessageToIRC("!I lost")

        except Exception as e:
            logging.info("Problem in GetWinLose")
            logging.error(str(e))
            logging.exception("Exception : ")

    def StartBets(self):

        info = (
            f"Size of self.gameData.playerList "
            f"in StartBets {len(self.gameData.playerList)}"
        )
        logging.info(info)
        if (bool(self.parameters.data.get('writePlaceYourBetsInChat'))):
            ps = ""
            outputList = []
            if self.gameData:
                if self.gameData.playerList:
                    if len(self.gameData.playerList) == 2:
                        # if two player make sure the streamer is put first
                        for player in self.gameData.playerList:
                            output = player.name
                            output += " "
                            output += player.faction.name
                            outputList.append(output)
                        # player list does not have steam numbers.
                        # Need to aquire these from warning.log
                        ps = f"{outputList[1]} Vs. {outputList[0]}"
                        pls = self.gameData.playerList[0].stats
                        if pls:
                            sn = str(self.parameters.data.get('steamNumber'))
                            psn = str(pls.steamNumber)
                            if sn == psn:
                                ps = f"{outputList[0]} Vs. {outputList[1]}"

                    message = "!startbets {}".format(ps)
                    self.ircClient.SendPrivateMessageToIRC(message)

    def Close(self):
        logging.info("Memory Monitor Closing!")
        self.running = False
        # break out of loops if waiting
        if self.event:
            self.event.set()
        # if timer is running and program is closed then cancel the timer
        # and call getwinlose early.
        if self.winLostTimer:
            self.winLostTimer.cancel()
            # self.GetWinLose()

    def Find_between(self, s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""

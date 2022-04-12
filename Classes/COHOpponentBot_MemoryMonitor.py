import logging
import threading

from COHOpponentBot_IRC_Client import IRC_Client
from Classes.COHOpponentBot_Parameters import Parameters
from Classes.COHOpponentBot_GameData import GameData


class MemoryMonitor(threading.Thread):

	def __init__(self, pollInterval = 30, ircClient : IRC_Client = None , parameters = None):
		threading.Thread.__init__(self)
		try:
			logging.info("Memory Monitor Started!")
			self.running = True

			if parameters:
				self.parameters = parameters
			else:
				self.parameters = Parameters()

			self.pm = None
			self.baseAddress = None
			self.gameInProgress = None

			self.ircClient = ircClient
			self.pollInterval = int(pollInterval)
			self.event = threading.Event()
			self.gameData = None

		except Exception as e:
			logging.error("In FileMonitor __init__")
			logging.error(str(e))
			logging.exception("Exception : ")

	def run(self):
		try:
			while self.running:
				self.getGameData()
				if self.gameInProgress:
					
					if self.gameData.gameInProgress != self.gameInProgress:
						#coh was running and now its not (game over)
						self.gameInProgress = self.gameData.gameInProgress
						self.GameOver()
				else:
					if self.gameData.gameInProgress != self.gameInProgress:
						#coh wasn't running and now it is (game started)
						self.gameInProgress = self.gameData.gameInProgress
						self.GameStarted()

				self.event.wait(self.pollInterval)
			#self.join()
		except Exception as e:
			logging.error("In FileMonitor run")
			logging.error(str(e))
			logging.exception("Exception : ")

	def getGameData(self):
		try:
			self.gameData = GameData(ircClient=self.ircClient, parameters=self.parameters)
			self.gameData.getDataFromGame()
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
			message = "!setsteam,{},{}".format(str(self.parameters.data['channel']), str(self.parameters.data['steamNumber']))
			self.ircClient.SendMessageToOpponentBotChannelIRC(message)
		except Exception as e:
			logging.error("Problem in PostSteamNumber")
			logging.exception("Exception : ")
			logging.error(str(e))

	def PostData(self):
		try:
			message = self.gameData.gameDescriptionString
			self.ircClient.SendMessageToOpponentBotChannelIRC(message)

		except Exception as e:
			logging.error("Problem in PostData")
			logging.error(str(e))
			logging.exception("Exception : ")

	def GameOver(self):
		try:
			if (self.parameters.data.get('clearOverlayAfterGameOver')):
				self.ircClient.queue.put("CLEAROVERLAY")
		except Exception as e:
			logging.info("Problem in GameOver")
			logging.error(str(e))
			logging.exception("Exception : ")

	def StartBets(self):
		try:
			logging.info("Size of self.gameData.playerList in StartBets {}".format(len(self.gameData.playerList)))
			if (bool(self.parameters.data.get('writePlaceYourBetsInChat'))):

				playerString = ""
				outputList = []
				if self.gameData:
					if self.gameData.playerList:
						if len(self.gameData.playerList) == 2: # if two player make sure the streamer is put first
							for player in self.gameData.playerList:
								outputList.append(player.name + " " + player.faction.name)
							# player list does not have steam numbers. Need to aquire these from warning.log
							playerString = "{} Vs. {}".format(outputList[1], outputList[0])	
							if self.gameData.playerList[0].stats:
								if (str(self.parameters.data.get('steamNumber')) == str(self.gameData.playerList[0].stats.steamNumber)):			
									playerString = "{} Vs. {}".format(outputList[0], outputList[1])									
						self.ircClient.SendPrivateMessageToIRC("!startbets {}".format(playerString))
		except Exception as e:
			logging.error("Problem in StartBets")
			logging.error(str(e))
			logging.exception("Exception : ")
	
	def close(self):
		logging.info("Memory Monitor Closing!")
		self.running = False
		# break out of loops if waiting
		if self.event:
			self.event.set()

	def find_between(self, s, first, last ):
		try:
			start = s.index( first ) + len( first )
			end = s.index( last, start )
			return s[start:end]
		except ValueError:
			return ""

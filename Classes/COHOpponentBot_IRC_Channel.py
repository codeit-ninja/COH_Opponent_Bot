from decimal import *
from random import choice
from pymem.process import module_from_name # required for urllib certificates
from tkinter import *
import threading
from threading import Thread
import logging
import re

from Classes.COHOpponentBot_Parameters import Parameters
from Classes.COHOpponentBot_GameData import GameData

class IRC_Channel(threading.Thread):
	def __init__(self, ircClient, irc, queue, channel, parameters = None):
		Thread.__init__(self)
		self.ircClient = ircClient
		self.running = True
		self.irc = irc
		self.queue = queue
		self.channel = channel

		if parameters:
			self.parameters = parameters
		else:
			self.parameters = Parameters()	

		self.gameData = GameData(self.ircClient, parameters=self.parameters)
		
	def run(self):
		self.irc.send(('JOIN ' + self.channel + '\r\n').encode("utf8"))
		while self.running:
			line = self.queue.get()
			line=str.rstrip(line)
			line=str.split(line)
			if (line[0] == "EXITTHREAD"):
				self.close()
			if (line[0] == "OPPONENT"):
				self.CheckForUserCommand("self","opp")
			if (line[0] == "TEST"):
				self.testOutput()
			if (line[0] == "IWON"):
				self.ircClient.SendPrivateMessageToIRC("!i won")
			if (line[0] == "ILOST"):
				self.ircClient.SendPrivateMessageToIRC("!i lost")
			if (line[0] == "CLEAROVERLAY"):
				GameData.clearOverlayHTML()
			if (len(line) >= 4) and ("PRIVMSG" == line[2]) and not ("jtv" in line[0]):
				#call function to handle user message
				self.UserMessage(line)

	def UserMessage(self, line):
		# Dissect out the useful parts of the raw data line into username and message and remove certain characters
		msgFirst = line[1]
		msgUserName = msgFirst[1:]
		msgUserName = msgUserName.split("!")[0]
		#msgType = line [1];
		#msgChannel = line [3]
		msgMessage = " ".join(line [4:])
		msgMessage = msgMessage[1:]
		messageString = str(msgUserName) + " : " + str(msgMessage)
		logging.info (str(messageString).encode('utf8'))

		#Check for UserCommands
		self.CheckForUserCommand(msgUserName, msgMessage)
		
	
		if (msgMessage == "exit") and (msgUserName == self.ircClient.adminUserName):
			self.ircClient.SendPrivateMessageToIRC("Exiting")
			self.close()

	def CheckForUserCommand(self, userName, message):
		logging.info("Checking For User Comamnd")
		try:
			if (bool(re.match(r"^(!)?opponent(\?)?$", message.lower())) or bool(re.match(r"^(!)?place your bets$" , message.lower())) or bool(re.match(r"^(!)?opp(\?)?$", message.lower()))):

				self.gameData = GameData(ircClient= self.ircClient, parameters=self.parameters)
				if self.gameData.getDataFromGame():
					self.gameData.outputOpponentData()


			if (message.lower() == "test") and ((str(userName).lower() == str(self.parameters.privatedata.get('adminUserName')).lower()) or (str(userName) == str(self.parameters.data.get('channel')).lower())):
				self.ircClient.SendPrivateMessageToIRC("I'm here! Pls give me mod to prevent twitch from autobanning me for spam if I have to send a few messages quickly.")
				#self.ircClient.SendWhisperToIRC("Whisper Test", "xcoinbetbot")
				self.ircClient.output.insert(END, "Oh hi again, I heard you in the " +self.channel[1:] + " channel.\n")

			if (bool(re.match("^(!)?gameinfo(\?)?$", message.lower()))):
				self.gameInfo()

			if (bool(re.match("^(!)?story(\?)?$", message.lower()))):
				self.story()

			if (bool(re.match("^(!)?testoutput(\?)?$", message.lower()))):
				self.ircClient.SendMessageToOpponentBotChannelIRC("!start,Test Message.")



		except Exception as e:
			logging.error("Problem in CheckForUserCommand")
			logging.error(str(e))
			logging.exception("Exception : ")

	def gameInfo(self):
		self.gameData = GameData(self.ircClient, parameters=self.parameters)
		if self.gameData.getDataFromGame():
			self.ircClient.SendPrivateMessageToIRC("Map : {}, Mod : {}, Start : {}, High Resources : {}, Automatch : {}, Slots : {}, Players : {}.".format(self.gameData.mapFullName,self.gameData.modName,self.gameData.randomStart,self.gameData.highResources, self.gameData.automatch, self.gameData.slots,  self.gameData.numberOfPlayers))

	def story(self):
		self.gameData = GameData(self.ircClient, parameters=self.parameters)
		if self.gameData.getDataFromGame():
			self.ircClient.SendPrivateMessageToIRC("{}.".format(self.gameData.mapDescription))


	def testOutput(self):
		if not self.gameData:
			self.gameData = GameData(self.ircClient)
		self.gameData.testOutput()

	def close(self):
		self.running = False
		logging.info("Closing Channel " + str(self.channel) + " thread.")


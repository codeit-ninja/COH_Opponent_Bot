from json import encoder
import time
import socket
import string
import sys
import json
from typing import Match # for loading json's for emoticons
import urllib.request # more for loadings jsons from urls
import collections # for deque
from decimal import *
import operator # for sorting dictionary by value
from random import choice
import os # to allow directory exists checking etc.
import os.path
import ssl
import pymem
from pymem.process import module_from_name # required for urllib certificates
import requests
#import pymysql # for mysql 
#import all secret parameters from parameters file
from COHOpponentBot_Parameters import Parameters
#import the GUI
from tkinter import *
import threading
from threading import Thread
from datetime import datetime
from enum import Enum
from queue import Queue # to talk to the threads
import logging
import re
from overlayTemplates import OverlayTemplates
import html
import ctypes
from mem_edit import Process
import mem_edit
import binascii
from functools import partial


#Here are the message lines held until sent
messageDeque = collections.deque()
toSend = False


class IRCClient(threading.Thread):
	
	def __init__(self, output, consoleDisplayBool, parameters = None):

		Thread.__init__(self)

		self.output = output

		self.displayConsoleOut = consoleDisplayBool

		if parameters:
			self.parameters = parameters
		else:
			self.parameters = Parameters()	

		self.adminUserName = self.parameters.privatedata.get('adminUserName')	# This username will be able to use admin commands, exit the program and bypass some limits.
		

		#use botusername or get default if not set
		if (self.parameters.data.get('botUserName') == ""):
			self.nick = self.parameters.privatedata.get('IRCnick')				#This value is the username used to connect to IRC eg: "xcomreborn".
		else:
			self.nick = self.parameters.data.get('botUserName')
		
		self.channel = "#" + self.parameters.data.get('channel').lower() 		#The channel name for your channel eg: "#xcomreborn".
		
		#use botoauthkey or get default if not set
		if (self.parameters.data.get('botOAuthKey') == ""):
			self.password = self.parameters.privatedata.get('IRCpassword')			
		else:
			self.password = self.parameters.data.get('botOAuthKey')
		
		self.server = self.parameters.privatedata.get('IRCserver')
		self.port = self.parameters.privatedata.get('IRCport')
		self.relicServerProxy = self.parameters.privatedata.get('relicServerProxy')
	
		#create IRC socket
		try:
			self.irc = socket.socket()
		except Exception as e:
			logging.error("A problem occurred trying to connect")
			logging.error("In IRCClient")
			logging.error(str(e))
			self.irc.close()
			sys.exit(0)
		
		#irc send message buffer
		self.ircMessageBuffer = collections.deque()

		self.running = True
		

		# Start checking send buffer every 3 seconds.

		self.CheckIRCSendBufferEveryThreeSeconds() # only call this once.	
		

		self.irc.connect((self.server, self.port))

		#sends variables for connection to twitch chat
		self.irc.send(('PASS ' + self.password + '\r\n').encode("utf8"))
		self.irc.send(('USER ' + self.nick + '\r\n').encode("utf8"))
		self.irc.send(('NICK ' + self.nick + '\r\n').encode("utf8"))
		self.irc.send(('CAP REQ :twitch.tv/membership' + '\r\n').encode("utf8")) # sends a twitch specific request necessary to recieve mode messages
		self.irc.send(('CAP REQ :twitch.tv/tags'+ '\r\n').encode("utf8")) # sends a twitch specific request for extra data contained in the PRIVMSG changes the way it is parsed
		self.irc.send(('CAP REQ :twitch.tv/commands' + '\r\n').encode("utf8")) # supposidly adds whispers
		



		#start sub thread that uses shared Queue to communicate 
		# pass it irc for messaging, channel to join and queue
		self.queue = Queue()
		self.channelThread = IRC_Channel(self, self.irc, self.queue, self.channel, parameters=self.parameters)
		self.channelThread.start()

		#
		# Array to hold all the new threads	only neccessary if adding more channels
		#
		#threads = {}
		#threads[self.channel] = self.channelThread
		
		
		
	def run(self):
		self.running = True
		timeoutTimer = threading.Timer(5, self.connectionTimedOut)
		timeoutTimer.start()
		#create readbuffer to hold strings from IRC
		readbuffer = ""	
		self.irc.setblocking(0)	
		
		# This is the main loop
		while self.running:
			try:
				#maintain non blocking recieve buffer from IRC
				readbuffer= readbuffer+self.irc.recv(1024).decode("utf-8")
				temp=str.split(readbuffer, "\n")
				readbuffer=temp.pop( )
				for line in temp:
					self.queue.put(line)
					# send copy of recieved line to channel thread
					line=str.rstrip(line)
					line=str.split(line)
					logging.info (str(line).encode('utf8'))
					if (self.displayConsoleOut):
						try:
							message = "".join(line) + "\n"
							self.SendToOutputField(message)
						except Exception as e:
							logging.error("In run")
							logging.error(str(e))

					if (len(line) >= 3) and ("JOIN" == line[1]) and (":"+self.nick.lower()+"!"+self.nick.lower()+"@"+self.nick.lower()+".tmi.twitch.tv" == line[0]):
						#cancel auto closing the thread
						timeoutTimer.cancel()
						try:
							message = "Joined "+self.channel+" successfully.\n"
							self.SendToOutputField(message)
							message = "You can type 'test' in the " +self.channel[1:]+ " channel to say hello!\n"
							self.SendToOutputField(message)
						except Exception as e:
							logging.error(str(e))
							logging.exception("Stack : ")

					if(line[0]=="PING"):
						self.irc.send(("PONG %s\r\n" % line[0]).encode("utf8"))
			except Exception as e:
				pass

	def connectionTimedOut(self):
		try:
			message = "Connection to "+self.channel+" timed out, was the channel spelt correctly and is port 6667 open?\n"
			self.SendToOutputField(message)
		except Exception as e:
			logging.error(str(e))
			logging.exception("Stack : ")
		self.close()

	def close(self):
		self.queue.put("EXITTHREAD")
		self.running = False
		logging.info("in close in thread")
		try:
			# send closing message immediately
			self.irc.send(("PRIVMSG " + self.channel + " :" + str("closing opponent bot") + "\r\n").encode('utf8'))
		except Exception as e:
			logging.error("In close")
			logging.error(str(e))
			
	def AssurePathExists(self, path):
		dir = os.path.dirname(path)
		if not os.path.exists(dir):
			os.makedirs(dir)
					
	def CheckIRCSendBufferEveryThreeSeconds(self):
		if (self.running == True): 
			threading.Timer(3.0, self.CheckIRCSendBufferEveryThreeSeconds).start()
		self.IRCSendCalledEveryThreeSeconds()
	# above is the send to IRC timer loop that runs every three seconds
	
	def SendPrivateMessageToIRC(self, message):
		self.ircMessageBuffer.append(message)   # removed this to stop message being sent to IRC
		self.SendToOutputField(message) # output message to text window

	def SendToOutputField(self, message):
		try:
			#First strip characters outside of range that cannot be handled by tkinter output field
			char_list = '' 
			for x in range(len(message)): 
				if ord(message[x]) in range(65536):
					char_list += message[x]
			message = char_list
		except Exception as e:
			logging.error(str(e))
			logging.exception("Stack : ")
		try:
			self.output.insert(END, message + "\n")
		except Exception as e:
			logging.error(str(e))
			logging.exception("Stack : ")

	def IRCSendCalledEveryThreeSeconds(self):
		if (self.ircMessageBuffer):
			try:
				self.irc.send(("PRIVMSG " + self.channel + " :" + str(self.ircMessageBuffer.popleft()) + "\r\n").encode('utf8'))
			except Exception as e:
				logging.error("IRC send error:")
				logging.error("In IRCSendCalledEveryThreeSeconds")
				logging.error(str(e))
	#above is called by the timer every three seconds and checks for items in buffer to be sent, if there is one it'll send it



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
				self.ircClient.SendPrivateMessageToIRC("!"+str(self.parameters.data.get('steamAlias')) +" won")
			if (line[0] == "ILOST"):
				self.ircClient.SendPrivateMessageToIRC("!"+str(self.parameters.data.get('steamAlias')) +" lost")
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
			if (bool(re.match("^(!)?opponent(\?)?$", message.lower())) or bool(re.match("^(!)?place your bets$" , message.lower())) or bool(re.match("^(!)?opp(\?)?$", message.lower()))):
				logging.info("Got Opponent")
				self.gameData = GameData(ircClient= self.ircClient, parameters=self.parameters)
				if self.gameData.getDataFromGame():
					self.gameData.outputOpponentData()


			if (message.lower() == "test") and ((str(userName).lower() == str(self.parameters.privatedata.get('adminUserName')).lower()) or (str(userName) == str(self.parameters.data.get('channel')).lower())):
				self.ircClient.SendPrivateMessageToIRC("I'm here! Pls give me mod to prevent twitch from autobanning me for spam if I have to send a few messages quickly.")
				self.ircClient.output.insert(END, "Oh hi again, I heard you in the " +self.channel[1:] + " channel.\n")

			if (bool(re.match("^(!)?gameinfo(\?)?$", message.lower()))):
				self.gameInfo()
		except Exception as e:
			logging.error("Problem in CheckForUserCommand")
			logging.error(str(e))
			logging.exception("Stack :")

	def gameInfo(self):
		self.gameData = GameData(self.ircClient, parameters=self.parameters)
		if self.gameData.getDataFromGame():
			self.ircClient.SendPrivateMessageToIRC("Map : {}, Mod : {}, Start : {}, High Resources : {}, Automatch : {}, Slots : {}, Players : {}.".format(self.gameData.mapFullName,self.gameData.modName,self.gameData.randomStart,self.gameData.highResources, self.gameData.automatch, self.gameData.slots,  self.gameData.numberOfPlayers))

	def testOutput(self):
		if not self.gameData:
			self.gameData = GameData(self.ircClient)
		self.gameData.testOutput()

	def close(self):
		self.running = False
		logging.info("Closing Channel " + str(self.channel) + " thread.")




class StatsRequest:
	def __init__(self, parameters = None):
		if parameters:
			self.parameters = parameters
		else:
			self.parameters = Parameters()	
		
	def returnStats(self, statnumber):
		
		try:
			logging.info ("got statnumber : " + str(statnumber))
			#check stat number is 17 digit int
			stringLength = len(statnumber)
			assert(stringLength == 17)
			assert(int(statnumber))
			if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
				ssl._create_default_https_context = ssl._create_unverified_context
			response = urllib.request.urlopen(self.parameters.privatedata['relicServerProxy']+str(statnumber)).read()
			statdata = json.loads(response.decode('utf-8'))
			if (statdata['result']['message'] == "SUCCESS"):
				logging.info ("statdata load succeeded")
				playerStats = PlayerStat(statdata, statnumber)
			return playerStats
		except Exception as e:
			logging.info("Problem in returnStats")
			logging.info(str(e))
			logging.exception("Stack : ")


class MemoryMonitor(threading.Thread):

	def __init__(self, pollInterval = 30, ircClient = None, parameters = None):
		Thread.__init__(self)
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
		except Exception as e:
			logging.error("In FileMonitor run")
			logging.error(str(e))

	def getGameData(self):
		try:
			self.gameData = GameData(ircClient=self.ircClient, parameters=self.parameters)
			self.gameData.getDataFromGame()
		except Exception as e:
			logging.error("In getGameData")
			logging.info(str(e))
			logging.exception("Stack :")

	def GameStarted(self):
		try:
			self.gameData.outputOpponentData()
			self.StartBets()

		except Exception as e:
			logging.info("Problem in GameStarted")
			logging.error(str(e))
			logging.exception("Stack :")

	def GameOver(self):
		try:
			if (self.parameters.data.get('clearOverlayAfterGameOver')):
				self.ircClient.queue.put("CLEAROVERLAY")
		except Exception as e:
			logging.info("Problem in GameOver")
			logging.error(str(e))
			logging.exception("Stack :")

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
			logging.exception("Stack : ")
	
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


class FileMonitor (threading.Thread):

	def __init__(self, filePath, pollInterval = 30, ircClient = None, parameters = None):
		Thread.__init__(self)
		try:
			logging.info("File Monitor Started!")
			self.running = True

			if parameters:
				self.parameters = parameters
			else:
				self.parameters = Parameters()	

			self.ircClient = ircClient
			self.filePointer = 0
			self.pollInterval = int(pollInterval)
			self.filePath = filePath
			self.event = threading.Event()
			f = open(self.filePath, 'r' , encoding='ISO-8859-1')
			f.readlines()
			self.filePointer = f.tell()
			f.close()
			logging.info("Initialzing with file length : " + str(self.filePointer) + "\n")

		except Exception as e:
			logging.error("In FileMonitor __init__")
			logging.error(str(e))

	def run(self):
		try:
			logging.info ("Started monitoring File : " + str(self.filePath) + "\n")
			while self.running:
				lines = []
				clearOverlay = False
				f = open(self.filePath, 'r' , encoding='ISO-8859-1')
				f.seek(self.filePointer)
				lines = f.readlines()
				self.filePointer = f.tell()
				f.close()

				for line in lines:

					if ("Win notification" in line):
						#Check if streamer won
						theSteamNumber = self.find_between(line ,"/steam/" , "]")
						if (str(self.parameters.data.get('steamNumber')) == str(theSteamNumber)):
							logging.info("STREAMER WON\n")
							if (self.parameters.data.get('writeIWonLostInChat')):
								self.ircClient.queue.put("IWON")
							if (self.parameters.data.get('clearOverlayAfterGameOver')):
								clearOverlay = True
					if ("Loss notification" in line):
						#Check if streamer lost
						theSteamNumber = self.find_between(line ,"/steam/" , "]")
						if (str(self.parameters.data.get('steamNumber')) == str(theSteamNumber)):
							logging.info("STREAMER LOST\n")
							if (self.parameters.data.get('writeIWonLostInChat')):
								self.ircClient.queue.put("ILOST")
							if (self.parameters.data.get('clearOverlayAfterGameOver')):
								clearOverlay = True

				if (self.parameters.data.get('clearOverlayAfterGameOver')):
					if (clearOverlay):
						self.ircClient.queue.put("CLEAROVERLAY")
				self.event = threading.Event()
				self.event.wait(timeout = self.pollInterval)
			logging.info ("File Monitoring Ended.\n")
		except Exception as e:
			logging.error("In FileMonitor run")
			logging.error(str(e))

	def close(self):
		logging.info("File Monitor Closing!")
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

class PlayerStat:

	def __init__(self, statdata, steamNumber):

		# steamNumber is required in addition to statData to compare the steamNumber to the internal profiles that can contain other profile info
		self.leaderboardData = {}

		self.totalWins = 0
		self.totalLosses = 0		
		self.totalWLRatio = None

		self.steamNumber = steamNumber
		self.profile_id = None
		self.alias = None
		self.country = None
		self.steamString = None
		self.steamProfileAddress = None
		
		statString = "/steam/"+str(steamNumber)

		if statdata:
			if (statdata['result']['message'] == "SUCCESS"):

				if statdata['statGroups'][0]['members'][0]['alias']:
					for item in statdata['statGroups']:
						for value in item['members']:
							if (value.get('name') == statString):
								self.profile_id = value.get('profile_id')
								self.alias = value.get('alias')
								self.steamString = value.get('name')
								self.country = value.get('country')
				if statdata.get('leaderboardStats'):
					#print(json.dumps(statdata, indent=4, sort_keys= True))
					# following number compare to leaderboard_id
					# 0 is basic american 
					# 1 is basic wher 
					# 2 is basic commonWeath
					# 3 is basic pe
					# 4 is american 1v1
					# 5 is wher 1v1
					# 6 is commonWeath 1v1
					# 7 is pe 1v1
					# 8 is american 2v2
					# 9 is wher 2v2
					# 10 is commonweath 2v2
					# 11 is pe 2v2
					# 12 is american 3v3
					# 13 is wher 3v3
					# 14 is commonWeath 3v3
					# 15 is pe 3v3
					for item in statdata['leaderboardStats']:
						#print(item)
						if item.get('leaderboard_id') == 0:
							self.leaderboardData[0] = factionResult(faction = Faction.US, matchType = MatchType.BASIC, name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 1:
							self.leaderboardData[1] = factionResult(faction = Faction.WM, matchType = MatchType.BASIC, name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 2:
							self.leaderboardData[2] = factionResult(faction = Faction.CW, matchType = MatchType.BASIC, name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 3:
							self.leaderboardData[3] = factionResult(faction = Faction.PE, matchType = MatchType.BASIC, name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 4:
							self.leaderboardData[4] = factionResult(faction = Faction.US, matchType = MatchType.ONES, name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 5:
							self.leaderboardData[5] = factionResult(faction = Faction.WM, matchType = MatchType.ONES, name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 6:
							self.leaderboardData[6] = factionResult(faction = Faction.CW, matchType = MatchType.ONES, name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 7:
							self.leaderboardData[7] = factionResult(faction = Faction.PE, matchType = MatchType.ONES, name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 8:
							self.leaderboardData[8] = factionResult(faction = Faction.US, matchType = MatchType.TWOS, name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 9:
							self.leaderboardData[9] = factionResult(faction = Faction.WM, matchType = MatchType.TWOS, name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 10:
							self.leaderboardData[10] = factionResult(faction = Faction.CW, matchType = MatchType.TWOS, name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 11:
							self.leaderboardData[11] = factionResult(faction = Faction.PE, matchType = MatchType.TWOS, name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 12:
							self.leaderboardData[12] = factionResult(faction = Faction.US, matchType = MatchType.THREES, name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 13:
							self.leaderboardData[13] = factionResult(faction = Faction.WM, matchType = MatchType.THREES, name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 14:
							self.leaderboardData[14] = factionResult(faction = Faction.CW, matchType = MatchType.THREES, name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 15:
							self.leaderboardData[15] = factionResult(faction = Faction.PE, matchType = MatchType.THREES, name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('ranklevel'), lastMatch = item.get('lastMatchDate'))
		

			for value in self.leaderboardData:
				try:
					self.totalWins += int(self.leaderboardData[value].wins)
				except Exception as e:
					logging.error("problem with totalwins value : " + str(value) +" data : "+ str(self.leaderboardData[value].wins))
					pass						
				try:
					self.totalLosses += int(self.leaderboardData[value].losses)
				except Exception as e:
					logging.error("problem with totallosses value : " + str(value) +" data : "+ str(self.leaderboardData[value].losses))
					pass

			self.totalWins = str(self.totalWins)
			self.totalLosses = str(self.totalLosses)

			try:
				if (int(self.totalLosses) > 0):
					self.totalWLRatio = str(round(int(self.totalWins)/int(self.totalLosses), 2))

			except Exception as e:
				logging.exception("In cohStat creating totalWLRatio")
				logging.error(str(e))

			if self.steamString:
				self.steamNumber = str(self.steamString).replace("/steam/", "")
				self.steamProfileAddress = "https://steamcommunity.com/profiles/" + str(self.steamNumber)


	
	def __str__(self):

		output = ""
		for value in self.leaderboardData:
			output += str(self.leaderboardData[value])

		output += "steamNumber : " + str(self.steamNumber) + "\n"
		output += "profile_id : " + str(self.profile_id) + "\n"
		output += "alias : " + str(self.alias) + "\n"
		output += "country : " + str(self.country) + "\n"
		output += "steamString : " + str(self.steamString) + "\n"
		output += "steamProfileAddress : " + str(self.steamProfileAddress) + "\n"

		output += "Totals\n"
		output += "Wins : " + str(self.totalWins) + "\n"
		output += "Losses : " + str(self.totalLosses) + "\n"
		output += "W/L Ratio : " + str(self.totalWLRatio) + "\n"

		return output


class Faction(Enum):
	US = 0
	WM = 1
	CW = 2
	PE = 3

class MatchType(Enum):
	BASIC = 0
	ONES = 1
	TWOS = 2
	THREES = 3


class factionResult:

	def __init__(self, faction = None, matchType = '-1',name = '-1', nameShort = '-1',leaderboard_id = '-1', wins = '-1', losses = '-1', streak = '-1', disputes = '-1', drops = '-1', rank = '-1', rankLevel = '-1', lastMatch = '-1'):
		self.faction = faction 
		self.matchType = re.sub(r"^-1\b", "None", str(matchType))
		self.name = name
		self.nameShort = nameShort
		self.id = leaderboard_id
		self.wins = re.sub(r"^-1\b", "None" ,str(wins))
		self.losses = re.sub(r"^-1\b", "None" ,str(losses))
		self.streak = re.sub(r"^-1\b", "None" ,str(streak))
		self.disputes = re.sub(r"^-1\b", "None" ,str(disputes))
		self.drops = re.sub(r"^-1\b", "None" ,str(drops))
		self.rank = re.sub(r"^-1\b", "None" ,str(rank))
		self.rankLevel = re.sub(r"^-1\b", "None" ,str(rankLevel))
		self.lastMatch = re.sub(r"^-1\b", "None" ,str(lastMatch))
		self.lastTime = None
		self.winLossRatio = None
		try:
			if self.lastMatch:
				ts = int(self.lastMatch)
				self.lastTime = str(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
		except Exception as e:
			#logging.exception("In factionResult Creating timestamp")
			logging.error(str(e))
		try:
			if (int(self.losses) != 0):
				self.winLossRatio = str(round(int(self.wins)/int(self.losses), 2))
			else:
				if(int(self.wins) > 0):
					self.winLossRatio = "Unbeaten"
		except Exception as e:
			logging.error("In factionResult Creating winLossRatio")
			logging.error(str(e))	


	def __str__(self):
		output = "Faction : " + str(self.name) + "\n"
		output += "Faction : " + str(self.faction) + "\n"
		output += "matchType : " + str(self.matchType) + "\n"
		output += "Short Name : "+ str(self.nameShort) + "\n"
		output += "Wins : " + str(self.wins) + "\n"
		output += "Losses : " + str(self.losses) + "\n"
		output += "Streak : " + str(self.streak) + "\n"
		output += "Disputes : " + str(self.disputes) + "\n"
		output += "Drops : " + str(self.drops) + "\n"
		output += "Rank : " + str(self.rank) + "\n"
		output += "Level : " + str(self.rankLevel) + "\n"
		output += "Last Time : " + str(self.lastMatch) + "\n"

		return output


class Player:

	def __init__(self, name = None, factionString = None, faction = None):
		self.name = name
		self.factionString = factionString
		self.faction = faction
		self.stats = None # This will be None for computers but point to a playerStat Object for players

		if self.factionString == "axis":
			self.faction = Faction.WM
		if self.factionString == "allies":
			self.faction = Faction.US
		if self.factionString == "allies_commonwealth":
			self.faction = Faction.CW
		if self.factionString == "axis_panzer_elite":
			self.faction = Faction.PE
	
	def __str__(self):
		output = "name : {}\n".format(str(self.name))
		output += "factionString : {}\n".format(str(self.factionString))
		output += "faction : {}\n".format(str(self.faction))
		output += "stats : {}\n".format(str(self.stats))
		return output

	def __repr__(self):
		return str(self)

class GameMonitor():

	def __init__(self, ircClient = None, parameters = None):

		if parameters:
			self.parameters = parameters
		else:
			self.parameters = Parameters()	

		self.ircClient = ircClient		


class GameData():

	def __init__(self, ircClient = None, parameters = None):

		if parameters:
			self.parameters = parameters
		else:
			self.parameters = Parameters()	

		self.playerList = []
		self.numberOfHumans = 0
		self.numberOfComputers = 0
		self.easyCPUCount = 0
		self.normalCPUCount = 0
		self.hardCPUCount = 0
		self.expertCPUCount = 0

		self.numberOfPlayers = 0
		self.slots = 0

		self.matchType = MatchType.BASIC
		self.ircClient = ircClient

		self.cohRunning = False
		self.gameInProgress = False

		self.gameStartedDate = None

		self.cohMemoryAddress = None

		self.ircStringOutputList = [] # This holds a list of IRC string outputs.

		self.randomStart = None
		self.highResources = None
		self.VPCount = None
		self.automatch = None
		self.mapFullName = None
		self.modName = None

		self.pm = None
		self.baseAddress = None


	def getDataFromGame(self):
		try:
			if not self.getCOHMemoryAddress():
				return False

			mpPointerAddress = 0x00901EA8
			mpOffsets=[0xC,0xC,0x18,0x10,0x24,0x18,0x264]

			# not used but for reference
			muniPointerAddress = 0x00901EA8
			muniOffsets=[0xC,0xC,0x18,0x10,0x24,0x18,0x26C]

			# not used but for reference
			fuelPointerAddress = 0x00901EA8
			fuelOffsets = [0xC,0xC,0x18,0x10,0x24,0x18,0x268]

			cohrecReplayAddress = 0x00902030
			cohrecOffsets = [0x28,0x160,0x4,0x84,0x24,0x110,0x0]

			# check game is running by accessing player mp
			mp = self.pm.read_float(self.GetPtrAddr(self.baseAddress + mpPointerAddress, mpOffsets))

			# access replay data in game memory
			replayData = self.pm.read_bytes(self.GetPtrAddr(self.baseAddress + cohrecReplayAddress, cohrecOffsets), 4000)

			# if the above executes without throwing an error then game is in progress.
			self.gameInProgress = True

			cohreplayparser = COH_Replay_Parser(parameters=self.parameters)
			cohreplayparser.data = bytearray(replayData)
			cohreplayparser.processData()
			print(cohreplayparser)	

			self.gameStartedDate = cohreplayparser.localDate

			if self.randomStart:
				self.randomStart = "Random"
			else:
				self.randomStart = "Fixed"
			self.highResources = cohreplayparser.highResources
			self.VPCount = cohreplayparser.VPCount
			if cohreplayparser.matchType.lower() == "automatch":
				self.automatch = True
			else:
				self.automatch = False
			if cohreplayparser.mapNameFull:
				self.mapFullName = cohreplayparser.mapNameFull
			else:
				self.mapFullName = cohreplayparser.mapName
			self.modName = cohreplayparser.modName

			for item in cohreplayparser.playerList:
				username = item['name']
				factionString = item['faction']
				player = Player(name=username,factionString=factionString)
				self.playerList.append(player)

			statList = self.getStatsFromGame()

			print(statList)

			for player in self.playerList:
				if statList:
					for stat in statList:
						try:
							logging.info("userName from alias : {}".format(str(stat.alias).encode('utf-16le')))
							logging.info("userName from game : {}".format(str(player.name).encode('utf-16le')))
							if str(stat.alias).encode('utf-16le') == str(player.name).encode('utf-16le'):
								player.stats = stat						
						except Exception as e:
							logging.error(str(e))
							logging.exception("Stack : ")

							#Assign Streamer name from steam alias and streamer steam Number 
							try:
								if self.parameters.data.get('steamNumber') == player.stats.steamNumber:
									self.parameters.data['steamAlias'] = player.stats.alias
									self.parameters.save()
							except Exception as e:
								logging.error(str(e))
								logging.exception("Stack : ")			

			self.numberOfHumans = sum(item.stats is not None for item in self.playerList)

			cpuCounter = 0
			easyCounter = 0
			normalCounter = 0
			hardCounter = 0
			expertCounter = 0

			for item in self.playerList:
				if (item.stats is None):
					if ("CPU" in item.name): 
						cpuCounter += 1
					if ("Easy" in item.name):
						easyCounter += 1
					if ("Normal" in item.name):
						normalCounter += 1
					if ("Hard" in item.name):
						hardCounter += 1
					if ("Expert" in item.name):
						expertCounter += 1
				
			self.numberOfComputers = cpuCounter
			self.numberOfPlayers = cpuCounter + self.numberOfHumans
			self.easyCPUCount = easyCounter
			self.normalCPUCount = normalCounter
			self.hardCPUCount = hardCounter
			self.expertCPUCount = expertCounter

			self.slots = len(cohreplayparser.playerList)

			#set the current MatchType
			self.matchType = MatchType.BASIC
			if (int(self.numberOfComputers) > 0):
				self.matchType = MatchType.BASIC
			if (0 <= int(self.slots) <= 2) and (int(self.numberOfComputers) == 0):
				self.matchType = MatchType.ONES
			if (3 <= int(self.slots) <= 4) and (int(self.numberOfComputers) == 0):
				self.matchType = MatchType.TWOS
			if (5 <= int(self.slots) <= 6) and (int(self.numberOfComputers) == 0):
				self.matchType = MatchType.THREES

			return True



		except Exception as e:
			logging.info("Problem in getDataFromGame")
			logging.info(str(e))
			logging.exception("Stack : ")
			self.gameInProgress = False
			return False

	def GetPtrAddr(self, base, offsets):
		try:
			if self.pm:
				addr = self.pm.read_int(base)
				for i in offsets:
					if i != offsets[-1]:
						addr = self.pm.read_int(addr + i)
				return addr + offsets[-1]
		except Exception as e:
			logging.info("Problem in GetPtrAddr")
			logging.info(str(e))
			logging.exception("Stack : ")
	

	def getCOHMemoryAddress(self):
		
		try:
			self.pm = pymem.Pymem("RelicCOH.exe")
			self.baseAddress = module_from_name(self.pm.process_handle, "RelicCOH.exe").lpBaseOfDll
			self.cohRunning = True
			return True
		except Exception as e:
			#logging.info(str(e))
			self.cohRunning = False
			return False
			
	
	# rewrite function below to remove memory search.

	def getStatsFromGame(self):
		try:

			self.cohMemoryAddress = Process.get_pid_by_name('RelicCOH.exe')

			with Process.open_process(self.cohMemoryAddress) as p:
				steamNumberList = []
				for player in self.playerList:
					name = bytearray(str(player.name).encode('utf-16le'))
					buff = bytes(name)
					if buff:
						#print(player.name)
						#print(len(player.name))
						#print(name)
						#print(buff)
						replayMemoryAddress = p.search_all_memory(buff)
						for address in replayMemoryAddress:
							try:
								data_dump = p.read_memory(address-56, (ctypes.c_byte * 48)())	
								data_dump = bytearray(data_dump)
								steamNumber = data_dump.decode('utf-16le').strip()
								if "/steam/" in steamNumber:
									print(steamNumber[7:24])
									int(steamNumber[7:24]) # throws exception if steam number is not a number
									steamNumberList.append(str(steamNumber[7:24]))
									break
							except Exception as e:
								pass
				statList = []
				for item in steamNumberList:
					statRquest = StatsRequest(parameters= self.parameters)
					stat = statRquest.returnStats(item)
					statList.append(stat)
				return statList
		except Exception as e:
			logging.error(str(e))
			logging.exception("Stack : ")

	def testOutput(self):
		steamNumber = self.parameters.data.get('steamNumber')
		statsRequest = StatsRequest(parameters=self.parameters)
		streamerStats = statsRequest.returnStats(str(steamNumber))
		streamerPlayer = Player(name = self.parameters.data.get('channel'))
		streamerPlayer.stats = streamerStats
		if streamerPlayer.stats:
			self.ircClient.SendToOutputField("Streamer Full Stat list formatted according to Custom Chat Output Preformat:")
			self.ircClient.SendToOutputField(self.parameters.data.get('customStringPreFormat'))

			for match in MatchType:
				for faction in Faction:
					for value in streamerPlayer.stats.leaderboardData:
						if (str(streamerPlayer.stats.leaderboardData[value].faction) == str(faction)) and (str(streamerPlayer.stats.leaderboardData[value].matchType) == str(match)):
							self.matchType = match
							streamerPlayer.faction = faction
							stringFormattingDictionary = self.populateStringFormattingDictionary(streamerPlayer)
							customPreFormattedOutputString = self.parameters.data.get('customStringPreFormat')
							theString = self.formatPreFormattedString(customPreFormattedOutputString, stringFormattingDictionary)
							outputList = list(self.split_by_n(theString, 500))
							for item in outputList:
								self.ircClient.SendToOutputField(item)
		else:
			self.ircClient.SendToOutputField("I could not get stats from the stat server using steam# {} it might be down or the steam# might be invalid.".format(steamNumber))


	def getStatsFromLogFile(self):

		steamNumberList = []

		with open(self.parameters.data.get('logPath') , encoding='ISO-8859-1') as f:
			content = f.readlines()

		for item in content:

			if ('detected successful game start' in item):
				steamNumberList = []

			if ("match started") in item.lower():
				logging.info (item)
				# dictionary containing player number linked to steamnumber
				steamNumber = self.find_between(item, "steam/", "]")
				steamNumberList.append(steamNumber)			

		statsList = []

		statRequest = StatsRequest(parameters= self.parameters)
		for steamNumber in steamNumberList:
			stat = statRequest.returnStats(str(steamNumber))
			statsList.append(stat)

		return statsList


	def outputOpponentData(self):

		print("In outputOpponentData")

		# Prepare outputs
		axisTeam = []
		alliesTeam = []

		#not sure if they need clearing but apparently the lists are sometimes persistent?
		axisTeam.clear()
		alliesTeam.clear()

		if self.playerList:
			for item in self.playerList:
				if (str(item.faction) == str(Faction.US)) or (str(item.faction)== str(Faction.CW)):
					alliesTeam.append(item)
				if (str(item.faction) == str(Faction.WM)) or (str(item.faction)== str(Faction.PE)):
					axisTeam.append(item)

			#logging.info("players in allies team : " +str(len(alliesTeam)))
			#logging.info("players in axis team : " + str(len(axisTeam)))

			# output each player to file
			if (self.parameters.data.get('useOverlayPreFormat')):
				self.saveOverlayHTML(axisTeam, alliesTeam)

			# output to chat if customoutput ticked
			if (self.parameters.data.get('useCustomPreFormat')):	
				if (int(self.numberOfComputers) > 0):
					self.ircStringOutputList.append("Game with " + str(self.numberOfComputers) + " computer AI, ("+str(self.easyCPUCount)+") Easy, ("+str(self.normalCPUCount)+") Normal, ("+str(self.hardCPUCount)+") Hard, ("+str(self.expertCPUCount)+") Expert.")	
				for item in self.playerList:
					#check if item has stats if not it is a computer
					if item.stats:
						if(item.stats.steamNumber == self.parameters.data.get('steamNumber')):
							if (self.parameters.data.get('showOwn')):
								self.ircStringOutputList = self.ircStringOutputList + self.createCustomOutput(item)
						else:
							self.ircStringOutputList = self.ircStringOutputList + self.createCustomOutput(item)					
				for item in self.ircStringOutputList:
					self.ircClient.SendPrivateMessageToIRC(str(item)) # outputs the information to IRC


	def createCustomOutput(self, player):
		stringFormattingDictionary = self.populateStringFormattingDictionary(player)
		customPreFormattedOutputString = self.parameters.data.get('customStringPreFormat')
		theString = self.formatPreFormattedString(customPreFormattedOutputString, stringFormattingDictionary)
		outputList = list(self.split_by_n(theString, 500))
		if (self.parameters.data.get('showSteamProfile')):
			outputList.append("Steam profile " + str(player.stats.steamProfileAddress))
		return outputList

	def populateStringFormattingDictionary(self, player, overlay = False):
		prefixDiv = ""
		postfixDivClose = ""
		if overlay:
			prefixDiv = '<div class = "textVariables">'
			postfixDivClose = '</div>'
		stringFormattingDictionary = dict(self.parameters.stringFormattingDictionary)
		#stringFormattingDictionary = {} # create a new dictionary
		nameDiv = ""
		factionDiv = ""
		matchDiv = ""
		countryDiv = ""
		totalWinsDiv = ""
		totalLossesDiv = ""
		totalWinLossRatioDiv = ""
		winsDiv = ""
		lossesDiv = ""
		disputesDiv = ""
		streakDiv = ""
		dropsDiv = ""
		rankDiv = ""
		levelDiv = ""
		wlRatioDiv = ""

		if overlay:
			nameDiv = '<div class = "name">'
			factionDiv = '<div class = "faction">'
			matchDiv = '<div class = "matchtype">'
			countryDiv = '<div class = "country">'
			totalWinsDiv = '<div class = "totalwins">'
			totalLossesDiv = '<div class = "totallosses">'
			totalWinLossRatioDiv = '<div class = "totalwlratio">'
			winsDiv = '<div class = "wins">'
			lossesDiv = '<div class = "losses">'
			disputesDiv = '<div class = "disputes">'
			streakDiv = '<div class = "streak">'
			dropsDiv = '<div class = "drops">'
			rankDiv = '<div class = "rank">'
			levelDiv = '<div class = "level">'
			wlRatioDiv = '<div class = "wlratio">'

		playerName = self.sanatizeUserName(player.name)
		stringFormattingDictionary['$NAME$'] =  prefixDiv + nameDiv + str(playerName) + postfixDivClose + postfixDivClose
		
		if overlay:
			stringFormattingDictionary['$NAME$'] =  prefixDiv + nameDiv + str(html.escape(playerName)) + postfixDivClose + postfixDivClose
		
		if type(player.faction) is Faction:
			stringFormattingDictionary['$FACTION$'] =  prefixDiv + factionDiv + str(player.faction.name) + postfixDivClose + postfixDivClose

		if (self.matchType == MatchType.BASIC):
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + matchDiv + "Basic" + postfixDivClose + postfixDivClose
		if (self.matchType == MatchType.ONES):
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + matchDiv + "1v1" + postfixDivClose + postfixDivClose
		if (self.matchType == MatchType.TWOS):
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + matchDiv + "2v2" + postfixDivClose + postfixDivClose
		if (self.matchType == MatchType.THREES):
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + matchDiv + "3v3" + postfixDivClose + postfixDivClose

		# if a computer it will have no stats
		if player.stats:
			stringFormattingDictionary['$COUNTRY$'] =  prefixDiv + countryDiv + str(player.stats.country) + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$TOTALWINS$'] =  prefixDiv + totalWinsDiv + str(player.stats.totalWins) + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$TOTALLOSSES$'] =  prefixDiv + totalLossesDiv + str(player.stats.totalLosses) + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$TOTALWLRATIO$'] =  prefixDiv + totalWinLossRatioDiv + str(player.stats.totalWLRatio) + postfixDivClose + postfixDivClose


			#set default null values for all parameters in dictionary
			stringFormattingDictionary['$WINS$'] =  prefixDiv + winsDiv + "0" + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$LOSSES$'] =  prefixDiv + lossesDiv + "0" + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$DISPUTES$'] =  prefixDiv + disputesDiv + "0" + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$STREAK$'] =  prefixDiv + streakDiv + "0" + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$DROPS$'] =  prefixDiv + dropsDiv + "0" + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$RANK$'] =  prefixDiv + rankDiv + "-" + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$LEVEL$'] =  prefixDiv + levelDiv + "0" + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$WLRATIO$'] =  prefixDiv + wlRatioDiv + "-" + postfixDivClose	+ postfixDivClose	

			for value in player.stats.leaderboardData:
				if (str(player.stats.leaderboardData[value].matchType) == str(self.matchType)):
					if (str(player.stats.leaderboardData[value].faction) == str(player.faction)):
				
						stringFormattingDictionary['$WINS$'] =  prefixDiv + winsDiv + str(player.stats.leaderboardData[value].wins) + postfixDivClose + postfixDivClose
						stringFormattingDictionary['$LOSSES$'] =  prefixDiv + lossesDiv + str(player.stats.leaderboardData[value].losses) + postfixDivClose + postfixDivClose
						stringFormattingDictionary['$DISPUTES$'] =  prefixDiv + disputesDiv + str(player.stats.leaderboardData[value].disputes) + postfixDivClose + postfixDivClose
						stringFormattingDictionary['$STREAK$'] =  prefixDiv + streakDiv + str(player.stats.leaderboardData[value].streak) + postfixDivClose + postfixDivClose
						stringFormattingDictionary['$DROPS$'] =  prefixDiv + dropsDiv + str(player.stats.leaderboardData[value].drops) + postfixDivClose + postfixDivClose
						stringFormattingDictionary['$RANK$'] =  prefixDiv + rankDiv + str(player.stats.leaderboardData[value].rank) + postfixDivClose + postfixDivClose
						stringFormattingDictionary['$LEVEL$'] =  prefixDiv + levelDiv + str(player.stats.leaderboardData[value].rankLevel) + postfixDivClose + postfixDivClose
						stringFormattingDictionary['$WLRATIO$'] =  prefixDiv + wlRatioDiv + str(player.stats.leaderboardData[value].winLossRatio) + postfixDivClose + postfixDivClose
					 

		return stringFormattingDictionary

	def populateImageFormattingDictionary(self, player):
		imageOverlayFormattingDictionary = self.parameters.imageOverlayFormattingDictionary
		
		#faction icons
		if player.faction:
			fileExists = False
			factionIcon = ""
			if type(player.faction) is Faction:
				factionIcon = "OverlayImages\\Armies\\" + str(player.faction.name).lower() + ".png"
				fileExists = os.path.isfile(factionIcon)
			logging.info(factionIcon)
			if fileExists:
				imageOverlayFormattingDictionary['$FACTIONICON$'] = '<div class = "factionflagimg"><img src="{0}" ></div>'.format(factionIcon)
				logging.info(imageOverlayFormattingDictionary.get('$FACTIONICON$'))
			else:
				imageOverlayFormattingDictionary['$FACTIONICON$'] = '<div class = "factionflagimg"><img src="data:," alt></div>'		

		# if a computer it will have no stats therefore no country flag or rank
		if player.stats:
			# set default values for flags and faction rank
			imageOverlayFormattingDictionary['$FLAGICON$'] = '<div class = "countryflagimg"><img src="data:," alt></div>'
			imageOverlayFormattingDictionary['$LEVELICON$'] = '<div class = "rankimg"><img src="data:," alt></div>'
			levelIcon = "OverlayImages\\Ranks\\no_rank_yet.png"
			fileExists = os.path.isfile(levelIcon)
			if fileExists:
				imageOverlayFormattingDictionary['$LEVELICON$'] =  '<div class = "rankimg"><img src="{0}" ></div>'.format(levelIcon)


			if player.stats.country:
				countryIcon = "OverlayImages\\Flagssmall\\" + str(player.stats.country).lower() + ".png"
				fileExists = os.path.isfile(countryIcon)
				if fileExists:
					imageOverlayFormattingDictionary['$FLAGICON$'] = '<div class = "countryflagimg"><img src="{0}" ></div>'.format(countryIcon)
				else:
					imageOverlayFormattingDictionary['$FLAGICON$'] = '<div class = "countryflagimg"><img src="data:," alt></div>'

			#rank icons
			for value in player.stats.leaderboardData:
				if (str(player.stats.leaderboardData[value].matchType) == str(self.matchType)):
					if (str(player.stats.leaderboardData[value].faction) == str(player.faction)):
						iconPrefix = ""
						if str(player.faction) == str(Faction.PE):
							iconPrefix = "panzer_"
						if str(player.faction) == str(Faction.CW):
							iconPrefix = "brit_"
						if str(player.faction) == str(Faction.US):
							iconPrefix = "us_"
						if str(player.faction) == str(Faction.WM):
							iconPrefix = "heer_"												
						level = str(player.stats.leaderboardData[value].rankLevel).zfill(2)
						levelIcon = "OverlayImages\\Ranks\\" + iconPrefix + level + ".png"
						logging.info("levelIcon : " + str(levelIcon))
						fileExists = os.path.isfile(levelIcon)
						if fileExists:
							imageOverlayFormattingDictionary['$LEVELICON$'] =  '<div class = "rankimg"><img src="{0}" ></div>'.format(levelIcon)
							logging.info(imageOverlayFormattingDictionary.get('$LEVELICON$'))
						else:
							imageOverlayFormattingDictionary['$LEVELICON$'] = '<div class = "rankimg"><img src="data:," alt></div>'
		else:
			#default no image
			imageOverlayFormattingDictionary['$FLAGICON$'] = '<div class = "countryflagimg"><img src="data:," alt></div>'
			imageOverlayFormattingDictionary['$LEVELICON$'] = '<div class = "rankimg"><img src="data:," alt></div>'


		return imageOverlayFormattingDictionary

	def sanatizeUserName(self, userName):
		try:
			#remove ! from start of userName for example !opponent
			if "!" == userName[0]:
				userName = userName[1:]
			# add 1 extra whitespace to username if it starts with . or / using rjust to prevent . and / twitch chat commands causing problems
			if (bool(re.match("""^[/\.]""" , userName))):
				userName = str(userName.rjust(len(userName)+1))
			# escape any single quotes
			userName = userName.replace("'","\'")
			# escape any double quotes
			userName = userName.replace('"', '\"')
			return userName
		except Exception as e:
			logging.error("Problem in sanitizeUserName")
			logging.exception("Stack :")

	def formatPreFormattedString(self, theString, stringFormattingDictionary, overlay = False):

		if overlay:
			prefixDiv = '<div class = "nonVariableText">'
			postfixDiv = '</div>'

			#compile a pattern for all the keys
			pattern = re.compile(r'(' + '|'.join(re.escape(key) for key in stringFormattingDictionary.keys()) + r')')

			logging.info("pattern " + str(pattern))
			#split the string to include the dictionary keys
			fullSplit = re.split(pattern, theString)
			
			logging.info("fullSplit " + str(fullSplit))
			
			#Then replace the Non key values with the postfix and prefix
			for x in range(len(fullSplit)):
				if not fullSplit[x] in stringFormattingDictionary.keys():
					fullSplit[x] = prefixDiv + fullSplit[x] + postfixDiv

			#This string can then be processed to replace the keys with their appropriate values
			theString = "".join(fullSplit)


		# I'm dammed if I know how this regular expression works but it does.
		pattern = re.compile(r'(?<!\w)(' + '|'.join(re.escape(key) for key in stringFormattingDictionary.keys()) + r')(?!\w)')
		result = pattern.sub(lambda x: stringFormattingDictionary[x.group()], theString)
		return result

	def saveOverlayHTML(self, axisTeamList, alliesTeamList):
		try:
			team1 = ""
			team2 = ""
			team1List = []
			team2List = []

			team1List.clear()
			team2List.clear()

			#by default player team is allies unless the player is steam number is present in the axisTeamList
			team1List = alliesTeamList
			team2List = axisTeamList

			for item in axisTeamList:
				if item.stats:
					if (str(self.parameters.data.get('steamNumber')) == str(item.stats.steamNumber)):
						logging.info ("Player team is AXIS")
						team1List = axisTeamList
						team2List = alliesTeamList

			useOverlayPreFormat = bool(self.parameters.data.get('useOverlayPreFormat'))
			if (useOverlayPreFormat):
				for item in team1List:
					preFormattedString = self.parameters.data.get('overlayStringPreFormatLeft')
					# first substitute all the text in the preformat
					stringFormattingDictionary = self.populateStringFormattingDictionary(item, overlay = True)
					#theString = self.formatPreFormattedString(preFormattedString, stringFormattingDictionary, overlay = True)
					# second substitue all the html images if used
					stringFormattingDictionary.update(self.populateImageFormattingDictionary(item))
					theString = self.formatPreFormattedString(preFormattedString, stringFormattingDictionary, overlay= True)
					team1 += str(theString) + str("<BR>") + "\n"
				for item in team2List:
					preFormattedString = self.parameters.data.get('overlayStringPreFormatRight')
					# first substitute all the text in the preformat
					stringFormattingDictionary.clear()
					stringFormattingDictionary = self.populateStringFormattingDictionary(item, overlay = True)
					#theString = self.formatPreFormattedString(preFormattedString, stringFormattingDictionary,overlay = True)
					# second substitue all the html images if used
					stringFormattingDictionary.update(self.populateImageFormattingDictionary(item))
					theString = self.formatPreFormattedString(preFormattedString, stringFormattingDictionary, overlay= True)
					team2 += str(theString) + str("<BR>") + "\n"
			else:
			
				for item in team1List:
					team1 += str(item.name) + str("<BR>") + "\n"
				for item in team2List:
					team2 += str(item.name) + str("<BR>") + "\n"
				
			htmlOutput = OverlayTemplates().overlayhtml.format(team1, team2)
			# create output overlay from template
			with open("overlay.html" , 'w', encoding="utf-8") as outfile:
				outfile.write(htmlOutput)
				logging.info("Creating Overlay File\n")
			#check if css file exists and if not output the default template to folder
			if not (os.path.isfile("overlaystyle.css")):
				with open("overlaystyle.css" , 'w' , encoding="utf-8") as outfile:
					outfile.write(OverlayTemplates().overlaycss)
		except Exception as e:
			logging.error(str(e))

	@staticmethod
	def clearOverlayHTML():
		try:
			htmlOutput = OverlayTemplates().overlayhtml.format("", "")
			# create output overlay from template
			with open("overlay.html" , 'w') as outfile:
				outfile.write(htmlOutput)
		except Exception as e:
			logging.error(str(e))

	def split_by_n(self, seq, n):
		'''A generator to divide a sequence into chunks of n units.'''
		while seq:
			yield seq[:n]
			seq = seq[n:]

	def find_between(self, s, first, last ):
		try:
			start = s.index( first ) + len( first )
			end = s.index( last, start )
			return s[start:end]
		except ValueError:
			return ""

	def __str__(self):
		output = "GameData : \n"
		output += "Time Last Game Started : {}\n".format(str(self.gameStartedDate))
		output += "player List : {}\n".format(str(self.playerList)) 
		output += "Number Of Players : {}\n".format(str(self.numberOfPlayers))
		output += "Number Of Computers : {}\n".format(str(self.numberOfComputers)) 
		output += "Easy CPU : {}\n".format(str(self.easyCPUCount)) 
		output += "Normal CPU : {}\n".format(str(self.normalCPUCount)) 
		output += "Hard CPU : {}\n".format(str(self.hardCPUCount)) 
		output += "Expert CPU : {}\n".format(str(self.expertCPUCount))
		output += "Number Of Humans : {}\n".format(str(self.numberOfHumans))
		output += "Match Type : {}\n".format(str(self.matchType.name))
		output += "Slots : {}\n".format(str(self.slots))


		output += "COH running : {}\n".format(str(self.cohRunning)) 
		output += "Game In Progress : {}\n".format(str(self.gameInProgress)) 

		return output

	def __repr__(self):
		return str(self)



class COH_Replay_Parser:
	"""Parses a company of heroes 1 replay to extract as much useful information from it as possible."""

	def __init__(self, filePath = None, parameters = None) -> None:


		if parameters:
			self.parameters = parameters
		else:
			self.parameters = Parameters()	

		self.filePath = filePath

		self.fileVersion = None
		self.chunkyVersion = None
		self.randomStart = None
		self.highResources = None
		self.VPCount = None
		self.matchType = None
		self.localDate = None
		self.unknownDate = None
		self.replayName = None
		self.gameVersion = None
		self.modName = None
		self.mapName = None
		self.mapNameFull = None
		self.mapDescription = None
		self.mapDescriptionFull = None
		self.mapFileName = None
		self.mapWidth = None
		self.mapHeight = None
		self.playerList = []

		self.data = None
		self.dataIndex = 0

		if filePath:
			self.load(self.filePath)

	def read_UnsignedLong4Bytes(self) -> int:
		"""Reads 4 bytes as an unsigned long int."""
		try:
			if self.data:
				fourBytes = bytearray(self.data[self.dataIndex:self.dataIndex+4])
				self.dataIndex += 4
				theInt = int.from_bytes(fourBytes, byteorder='little', signed=False)
				return theInt
		except Exception as e:
			logging.error("Failed to read 4 bytes")
			logging.exception("Stack Trace: ")

	def read_Bytes(self, numberOfBytes):
		"""reads a number of bytes from the data array"""
		try:
			if self.data:
				output = bytearray(self.data[self.dataIndex:self.dataIndex+numberOfBytes])
				self.dataIndex += numberOfBytes
				return output
		except Exception as e:
			logging.error("Failed to Read bytes")
			logging.exception("Stack Trace: ")


	def read_LengthString(self):
		"""Reads the first 4 bytes containing the string length and then the rest of the string."""
		try:
			if self.data:
				stringLength = self.read_UnsignedLong4Bytes()
				theString = self.read_2ByteString(stringLength =stringLength)
				return theString
		except Exception as e:
			logging.error("Failed to read a string of specified length")
			logging.exception("Stack Trace: ")

	def read_2ByteString(self, stringLength=0 ) -> str:
		"""Reads a 2byte encoded little-endian string of specified length."""
		try:
			if self.data:
				theBytes = bytearray(self.data[self.dataIndex:self.dataIndex+(stringLength*2)])
				self.dataIndex += stringLength*2
				theString = theBytes.decode('utf-16le')
				return theString
		except Exception as e:
			logging.error("Failed to read a string of specified length")
			logging.exception("Stack Trace: ")            

	def read_LengthASCIIString(self) -> str:
		"""Reads ASCII string, the length defined by the first four bytes."""
		try:
			if self.data:
				stringLength = self.read_UnsignedLong4Bytes()
				theString = self.read_ASCIIString(stringLength=stringLength)
				return theString
		except Exception as e:
			logging.error("Failed to read a string of specified length")
			logging.exception("Stack Trace: ")  

	def read_ASCIIString(self, stringLength=0) -> str:
		"""Reads a byte array of spcified length and attempts to convert it into a string."""
		try:
			if self.data:
				theBytes = bytearray(self.data[self.dataIndex:self.dataIndex+stringLength])
				self.dataIndex += stringLength
				theString = theBytes.decode('ascii')
				return theString
		except Exception as e:
			logging.error("Failed to read a string of specified length")
			logging.exception("Stack Trace: ")  

	def read_NULLTerminated_2ByteString(self) -> str:
		"""Reads a Utf-16 little endian character string until the first two byte NULL value."""
		try:
			if self.data:
				characters = ""
				for character in iter(partial(self.read_Bytes, 2) , bytearray(b"\x00\x00")):
					characters += bytearray(character).decode('utf-16le')
				return characters    
		except Exception as e:
			logging.error("Failed to read a string of specified length")
			logging.exception("Stack Trace: ")  

	def read_NULLTerminated_ASCIIString(self) -> str:
		"""Reads a byte array until the first NULL and converts to a string."""
		try:
			if self.data:
				characters = ""
				for character in iter(partial(self.read_Bytes, 1) , bytearray(b"\x00")):
					characters += bytearray(character).decode('ascii')
				return characters  
		except Exception as e:
			logging.error("Failed to read a string of specified length")
			logging.exception("Stack Trace: ")  

	def seek(self, numberOfBytes, relative = 0):
		"""Moves the file index a number of bytes forward or backward"""
		try:
			numberOfBytes = int(numberOfBytes)
			relative = int(relative)
			if relative == 0:
				assert(0 <= numberOfBytes <= len(self.data))
				self.dataIndex = numberOfBytes
			if relative == 1:
				assert(0 <= (numberOfBytes+self.dataIndex) <= len(self.data))
				self.dataIndex += numberOfBytes
			if relative == 2:
				assert(0 <= (len(self.data) - numberOfBytes) <= len(self.data))
				self.dataIndex = len(self.data) - numberOfBytes
		except Exception as e:
			logging.error("Failed move file Index")
			logging.exception("Stack Trace: ")
			return None          



	def load(self, filePath = ""):
		with open(filePath, "rb") as fileHandle:
			self.data = fileHandle.read()
		self.processData()

	def processData(self):

		#Process the file Header
		self.fileVersion = self.read_UnsignedLong4Bytes()

		cohrec = self.read_ASCIIString(stringLength= 8)

		self.localDate = self.read_NULLTerminated_2ByteString()

		self.seek(76,0)

		firstRelicChunkyAddress = self.dataIndex

		relicChunky = self.read_ASCIIString(stringLength=12)

		unknown = self.read_UnsignedLong4Bytes()

		self.chunkyVersion = self.read_UnsignedLong4Bytes() # 3

		unknown = self.read_UnsignedLong4Bytes()

		self.chunkyHeaderLength = self.read_UnsignedLong4Bytes()
		
		self.seek(-28,1) # sets file pointer back to start of relic chunky
		self.seek(self.chunkyHeaderLength, 1) # seeks to begining of FOLDPOST

		self.seek(firstRelicChunkyAddress, 0)
		self.seek(96,1) # move pointer to the position of the second relic chunky
		secondRelicChunkyAddress = self.dataIndex

		relicChunky = self.read_ASCIIString(stringLength=12)

		unknown = self.read_UnsignedLong4Bytes()
		chunkyVersion = self.read_UnsignedLong4Bytes() # 3
		unknown = self.read_UnsignedLong4Bytes()
		chunkLength = self.read_UnsignedLong4Bytes()
		
		self.seek(secondRelicChunkyAddress, 0)
		self.seek(chunkLength, 1) # seek to position of first viable chunk

		self.parseChunk(0)
		self.parseChunk(0)

		#get mapname and mapdescription from ucs file if they exist there
		self.mapNameFull = UCS(parameters=self.parameters).compareUCS(self.mapName)
		self.mapDescriptionFull = UCS(parameters=self.parameters).compareUCS(self.mapDescription)


	def parseChunk(self, level):

		chunkType = self.read_ASCIIString(stringLength= 8) # Reads FOLDFOLD, FOLDDATA, DATASDSC, DATAINFO etc

		chunkVersion = self.read_UnsignedLong4Bytes()

		chunkLength = self.read_UnsignedLong4Bytes()

		chunkNameLength = self.read_UnsignedLong4Bytes()

		self.seek(8,1)

		chunkName = ""
		if chunkNameLength > 0:
			chunkName = self.read_ASCIIString(stringLength=chunkNameLength)

		chunkStart = self.dataIndex

		#Here we start a recusive loop
		if chunkType:
			if (chunkType.startswith("FOLD")):

				while (self.dataIndex < (chunkStart + chunkLength )):
					self.parseChunk(level=level+1)

		if (chunkType == "DATASDSC") and (int(chunkVersion) == 2004):

			unknown = self.read_UnsignedLong4Bytes()
			self.unknownDate = self.read_LengthString()
			unknown = self.read_UnsignedLong4Bytes()
			unknown = self.read_UnsignedLong4Bytes()
			unknown = self.read_UnsignedLong4Bytes()
			self.modName = self.read_LengthASCIIString() 
			self.mapFileName = self.read_LengthASCIIString()
			unknown = self.read_UnsignedLong4Bytes()
			unknown = self.read_UnsignedLong4Bytes()
			unknown = self.read_UnsignedLong4Bytes()
			unknown = self.read_UnsignedLong4Bytes()
			unknown = self.read_UnsignedLong4Bytes()
			self.mapName = self.read_LengthString()
			
			value = self.read_UnsignedLong4Bytes() 
			if value != 0: # test to see if data is replicated or not
				unknown = self.read_2ByteString(value)
			self.mapDescription = self.read_LengthString()
			unknown = self.read_UnsignedLong4Bytes()
			self.mapWidth = self.read_UnsignedLong4Bytes()
			self.mapHeight = self.read_UnsignedLong4Bytes()
			unknown = self.read_UnsignedLong4Bytes()
			unknown = self.read_UnsignedLong4Bytes()
			unknown = self.read_UnsignedLong4Bytes() 

		if(chunkType == "DATABASE") and (int(chunkVersion == 11)):

			self.seek(16, 1)

			self.randomStart = (self.read_UnsignedLong4Bytes() == 0)
			
			COLS = self.read_UnsignedLong4Bytes()
			
			self.highResources = (self.read_UnsignedLong4Bytes() == 1)

			TSSR = self.read_UnsignedLong4Bytes()
			
			self.VPCount = 250 * (1 << (int)(self.read_UnsignedLong4Bytes()))

			self.seek(5, 1)

			self.replayName = self.read_LengthString()

			self.seek(8, 1)

			self.VPGame = (self.read_UnsignedLong4Bytes() ==  0x603872a3)

			self.seek(23 , 1)

			self.read_LengthASCIIString()

			self.seek(4,1)

			self.read_LengthASCIIString()

			self.seek(8,1)

			if (self.read_UnsignedLong4Bytes() == 2):
				self.read_LengthASCIIString()
				self.gameVersion = self.read_LengthASCIIString()
			self.read_LengthASCIIString()
			self.matchType = self.read_LengthASCIIString()

		if(chunkType == "DATAINFO") and (chunkVersion == 6):

			userName = self.read_LengthString()
			self.read_UnsignedLong4Bytes()
			self.read_UnsignedLong4Bytes()
			faction = self.read_LengthASCIIString()
			self.read_UnsignedLong4Bytes()
			self.read_UnsignedLong4Bytes()
			self.playerList.append({'name':userName,'faction':faction})


		self.seek(chunkStart + chunkLength, 0)

	def __str__(self) -> str:
		output = "Data:\n"
		output += "fileVersion : {}\n".format(self.fileVersion)
		output += "chunkyVersion : {}\n".format(self.chunkyVersion)
		output += "randomStart : {}\n".format(self.randomStart)
		output += "highResources : {}\n".format(self.highResources)
		output += "VPCount : {}\n".format(self.VPCount)
		output += "matchType : {}\n".format(self.matchType)
		output += "localDate : {}\n".format(self.localDate)
		output += "unknownDate : {}\n".format(self.unknownDate)
		output += "replayName : {}\n".format(self.replayName)
		output += "gameVersion : {}\n".format(self.gameVersion)
		output += "modName : {}\n".format(self.modName)
		output += "mapName : {}\n".format(self.mapName)
		output += "mapNameFull : {}\n".format(self.mapNameFull)
		output += "mapDescription : {}\n".format(self.mapDescription)
		output += "mapDescriptionFull : {}\n".format(self.mapDescriptionFull)
		output += "mapFileName : {}\n".format(self.mapFileName)
		output += "mapWidth : {}\n".format(self.mapWidth)
		output += "mapHeight : {}\n".format(self.mapHeight)
		output += "playerList : {}\n".format(len(self.playerList))
		output += "playerList : {}\n".format(self.playerList)
		return output

class UCS:
	def __init__(self, parameters = None) -> None:
		
		if parameters:
			self.parameters = parameters
		else:
			self.parameters = Parameters()	

		self.ucsPath = self.parameters.data.get('cohUCSPath')

	def compareUCS(self, compareString):
		try:
			if (os.path.isfile(self.ucsPath)):
				linenumber = 1
				with open(self.ucsPath, 'r',  encoding='utf16') as f:	
					for line in f:
						linenumber += 1
						firstString = str(line.split('\t')[0])
						if str(compareString[1:].strip()) == str(firstString):
							if len(line.split('\t')) > 1:
								return " ".join(line.split()[1:])
		except Exception as e:
			logging.error(str(e))
			logging.exception("Stack : ")

# to use this file without the GUI be sure to have the parameters file in the same directory and uncomment below
#myIRC = IRCClient()

import time
import socket
import string
import sys
import threading
import json # for loading json's for emoticons
import urllib.request # more for loadings jsons from urls
import collections # for deque
from decimal import *
import operator # for sorting dictionary by value
from random import choice
import os # to allow directory exists checking etc.
import os.path
import ssl # required for urllib certificates
import requests
#import pymysql # for mysql 
#import all secret parameters from parameters file
from IRCBetBot_Parameters import Parameters
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


#Because python floating point arthmatic is a nightmare
TWOPLACES = Decimal(10) ** -2

#Here are the message lines held until sent
messageDeque = collections.deque()
toSend = False




class IRCClient(threading.Thread):
	
	def __init__(self, output, consoleDisplayBool):

		Thread.__init__(self)

		self.output = output

		self.displayConsoleOut = consoleDisplayBool

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
		self.channelThread = IRC_Channel(self, self.irc, self.queue, self.channel)
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
							self.output.insert(END, "".join(line) + "\n")
						except Exception as e:
							logging.error("In run")
							logging.error(str(e))

					if (len(line) >= 3) and ("JOIN" == line[1]) and (":"+self.nick.lower()+"!"+self.nick.lower()+"@"+self.nick.lower()+".tmi.twitch.tv" == line[0]):
						#cancel auto closing the thread
						timeoutTimer.cancel()
						self.output.insert(END, "Joined "+self.channel+" successfully.\n")
						self.output.insert(END, "You can type 'test' in the " +self.channel[1:]+ " channel to say hello!\n")

					if(line[0]=="PING"):
						self.irc.send(("PONG %s\r\n" % line[0]).encode("utf8"))
			except Exception as e:
				pass

	def connectionTimedOut(self):
		self.output.insert(END, "Connection to "+self.channel+" timed out, was the channel spelt correctly and is port 6667 open?\n")
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
		self.output.insert(END, message + "\n") # output message to text window

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
	def __init__(self, ircClient, irc, queue, channel):
		Thread.__init__(self)
		self.ircClient = ircClient
		self.running = True
		self.irc = irc
		self.queue = queue
		self.channel = channel
		self.parameters = Parameters()
		self.myHandleCOHlogFile = None
		
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
			if (line[0] == "STARTBETS"):
				self.StartBets()
			if (line[0] == "IWON"):
				self.ircClient.SendPrivateMessageToIRC("!"+str(self.parameters.data.get('channel')) +" won")
			if (line[0] == "ILOST"):
				self.ircClient.SendPrivateMessageToIRC("!"+str(self.parameters.data.get('channel')) +" lost")
			if (line[0] == "CLEAROVERLAY"):
				HandleCOHlogFile.clearOverlayHTML()
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

	def StartBets(self):
		if (self.parameters.data.get('writePlaceYourBetsInChat')):
			playerString = ""
			outputList = []
			self.myHandleCOHlogFile = HandleCOHlogFile(self.ircClient)
			self.myHandleCOHlogFile.populatePlayerList()
			playerList = self.myHandleCOHlogFile.playerList
			if playerList:
				if len(playerList) == 2: # if two player make sure the streamer is put first
					for player in playerList:
						outputList.append(player.name + " " + player.faction.name)
					# player list does not have steam numbers. Need to aquire these from warning.log
					if (str(self.parameters.data.get('steamNumber')) == str(playerList[0].stats.steamNumber)):			
						playerString = "{} Vs. {}".format(outputList[0], outputList[1])
					else:
						playerString = "{} Vs. {}".format(outputList[1], outputList[0])			
				self.ircClient.SendPrivateMessageToIRC("!startbets {}".format(playerString))
				# need to reimplement the readlog

	def CheckForUserCommand(self, userName, message):
		if (bool(re.match("^(!)?opponent(\?)?$", message.lower())) or bool(re.match("^(!)?place your bets$" , message.lower())) or bool(re.match("^(!)?opp(\?)?$", message.lower()))):
			self.myHandleCOHlogFile = HandleCOHlogFile(self.ircClient)
			self.myHandleCOHlogFile.populatePlayerList()
			self.myHandleCOHlogFile.outputOpponentData()


		if (message.lower() == "test") and ((str(userName).lower() == str(self.parameters.privatedata.get('adminUserName')).lower()) or (str(userName) == str(self.parameters.data.get('channel')).lower())):
			self.ircClient.SendPrivateMessageToIRC("I'm here! Pls give me mod to prevent twitch from autobanning me for spam if I have to send a few messages quickly.")
			self.ircClient.output.insert(END, "Oh hi again, I heard you in the " +self.channel[1:] + " channel.\n")

	def close(self):
		self.running = False
		logging.info("Closing Channel " + str(self.channel) + " thread.")




class StatsRequest:
	def __init__(self):
		self.parameters = Parameters()		
		
	def returnStats(self, statnumber):
		logging.info ("got statnumber : " + str(statnumber))
		#statString = "/steam/" + str(statnumber)
		if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
			ssl._create_default_https_context = ssl._create_unverified_context
		response = urllib.request.urlopen(self.parameters.privatedata['relicServerProxy']+str(statnumber)).read()
		statdata = json.loads(response.decode('utf-8'))
		#print(json.dumps(statdata, indent=4, sort_keys= True))
		if (statdata['result']['message'] == "SUCCESS"):
			logging.info ("statdata load succeeded")
			playerStats = playerStat(statdata, statnumber)
			#print("playerStats : " + str(playerStats))
			return playerStats

class FileMonitor (threading.Thread):

	def __init__(self, filePath, pollInterval, opponentBot):
		Thread.__init__(self)
		try:
			logging.info("File Monitor Started!")
			self.running = True
			self.parameters = Parameters()
			self.opponentBot = opponentBot
			self.filePointer = 0
			self.pollInterval = int(pollInterval)
			self.filePath = filePath
			self.event = threading.Event()
			self.startingMissonEvent = threading.Event()
			f = open(self.filePath, 'r' , encoding='ISO-8859-1')
			f.readlines()
			self.filePointer = f.tell()
			f.close()
			logging.info("Initialzing with file length : " + str(len(self.filePointer)) + "\n")

		except Exception as e:
			logging.error("In FileMonitor __init__")
			logging.error(str(e))

	def run(self):
		try:
			logging.info ("Started monitoring File : " + str(self.filePath) + "\n")
			while self.running:
				lines = []
				clearOverlay = False
				print("current File index = : " + str(self.filePointer) + "\n")
				f = open(self.filePath, 'r' , encoding='ISO-8859-1')
				f.seek(self.filePointer)
				lines = f.readlines()
				self.filePointer = f.tell()
				f.close()
				print("new File index = : " + str(self.filePointer) + "\n")
				for line in lines:
					if ("GAME -- Starting mission..." in line):
						self.startingMissonEvent.wait(timeout= 30) # allow extra seconds for computer AI info to load if the game is a human vs ai game
						if (self.opponentBot):
							#trigger the opponent command in the opponentbot thread
							self.opponentBot.queue.put("OPPONENT")
							self.opponentBot.queue.put("STARTBETS")

					if ("Win notification" in line):
						#Check if streamer won
						theSteamNumber = self.find_between(line ,"/steam/" , "]")
						if (str(self.parameters.data.get('steamNumber')) == str(theSteamNumber)):
							logging.info("STREAMER WON\n")
							if (self.parameters.data.get('writeIWonLostInChat')):
								self.opponentBot.queue.put("IWON")
							if (self.parameters.data.get('clearOverlayAfterGameOver')):
								clearOverlay = True
					if ("Loss notification" in line):
						#Check if streamer lost
						theSteamNumber = self.find_between(line ,"/steam/" , "]")
						if (str(self.parameters.data.get('steamNumber')) == str(theSteamNumber)):
							logging.info("STREAMER LOST\n")
							if (self.parameters.data.get('writeIWonLostInChat')):
								self.opponentBot.queue.put("ILOST")
							if (self.parameters.data.get('clearOverlayAfterGameOver')):
								clearOverlay = True
					if ('GAME -- Ending mission (Game over)' in line):
						if (self.parameters.data.get('clearOverlayAfterGameOver')):
								clearOverlay = True

				if (self.parameters.data.get('clearOverlayAfterGameOver')):
					if (clearOverlay):
						self.opponentBot.queue.put("CLEAROVERLAY")
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
		if self.startingMissonEvent:
			self.startingMissonEvent.set()

	def find_between(self, s, first, last ):
		try:
			start = s.index( first ) + len( first )
			end = s.index( last, start )
			return s[start:end]
		except ValueError:
			return ""

class HandleCOHlogFile:
	

	def __init__(self, ircClient):

		self.parameters = Parameters()
		self.logPath = self.parameters.data['logPath']
		self.data = []
		self.numberOfHumans = 0
		self.numberOfComputers = 0
		self.easyCPUCount = 0
		self.normalCPUCount = 0
		self.hardCPUCount = 0
		self.expertCPUCount = 0

		self.numberOfPlayers = 0
		self.numberOfSlots = 0
		self.mapSize = 0

		self.matchType = MatchType.BASIC
		self.ircClient = ircClient

		self.playerList = []
	
	def populatePlayerList(self):
		logging.info("In loadLog")
		with open(self.logPath, encoding='ISO-8859-1') as f:
			content = f.readlines()
		logging.info(self.parameters.data['steamNumber'])
		steamNumberList = []

		for item in content:
			if ('detected successful game start' in item):
				steamNumberList.clear()

			if ("match started") in item.lower():
				logging.info (item)
				# dictionary containing player number linked to steamnumber
				steamNumber = self.find_between(item, "steam/", "]")
				steamNumberList.append(steamNumber)

			#if("GAME -- Beginning playback") in item:
			#	self.isReplay = True

			if (("GAME -- ***") in item):
				#self.isReplay = False
				self.numberOfHumans = 0
				self.numberOfComputers = 0
				self.easyCPUCount = 0
				self.normalCPUCount = 0
				self.hardCPUCount = 0
				self.expertCPUCount = 0
				
				# need to reverse the string to get the humans bit out uniquely or other strings in the line can interfere with the parsing
				reverseString = item[::-1]
				self.numberOfHumans = self.find_between(reverseString, "snamuH " , "(")
				#print("humans  = " + str(self.numberOfHumans) + "\n")
				self.numberOfComputers = self.find_between(item, "Humans, ", " Computers")
			if ("PerformanceRecorder::StartRecording") in item:
					self.mapSize = 0
					self.mapSize = self.find_between(item, "game size " , "\n")
			
			if ("Player CPU - Expert" in item):
				self.expertCPUCount += 1
			if ("Player CPU - Hard" in item):
				self.hardCPUCount += 1
			if ("Player CPU - Normal" in item):
				self.normalCPUCount += 1
			if ("Player CPU - Easy" in item):
				self.easyCPUCount += 1

			# clear the steam number list if a new game is found in the file
			if ("AutoMatchForm - Starting game") in item:
				steamNumberList.clear()

				logging.info("CLEARING PLAYER LIST\n")
			
		#self.numberOfHumans = len(steamNumberList)
		appMemReader = ApplicationMemoryReader()
		self.playerList = appMemReader.getFactions()
		#contains all players including computers and empty Slots with no userName
		self.numberOfSlots = len(self.playerList)

		#remove players from list where they have no name eg: slots
		for item in self.playerList:
			if (item.name == ""):
				self.playerList.remove(item)

		self.numberOfPlayers = len(self.playerList)
		
		if (steamNumberList):
			for item in steamNumberList:
				# get playerStats for each human player
				myStatRequest = StatsRequest()
				playerStats = myStatRequest.returnStats(item)
				for player in self.playerList:
					if (player.name == playerStats.alias):
						player.stats = playerStats

		logging.info("FULL PLAYERSTATLIST\n")
		for item in self.playerList:
			logging.info(item)

		#set the current MatchType
		self.matchType = MatchType.BASIC
		if (int(self.numberOfComputers) > 0):
			self.matchType = MatchType.BASIC
		if (0 <= int(self.mapSize) <= 2) and (int(self.numberOfComputers) == 0):
			self.matchType = MatchType.ONES
		if (3 <= int(self.mapSize) <= 4) and (int(self.numberOfComputers) == 0):
			self.matchType = MatchType.TWOS
		if (5 <= int(self.mapSize) <= 6) and (int(self.numberOfComputers) == 0):
			self.matchType = MatchType.THREES		


	def outputOpponentData(self):

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

			logging.info("players in allies team : " +str(len(alliesTeam)))
			logging.info("players in axis team : " + str(len(axisTeam)))

			# output each player to file
			if (self.parameters.data.get('useOverlayPreFormat')):
				self.saveOverlayHTML(axisTeam, alliesTeam)

			# output to chat if customoutput ticked
			if (self.parameters.data.get('useCustomPreFormat')):	
				if (int(self.numberOfComputers) > 0):
					self.data.append("Game with " + str(self.numberOfComputers) + " computer AI, ("+str(self.easyCPUCount)+") Easy, ("+str(self.normalCPUCount)+") Normal, ("+str(self.hardCPUCount)+") Hard, ("+str(self.expertCPUCount)+") Expert.")	
				for item in self.playerList:
					#check if item has stats if not it is a computer
					if item.stats:
						if(item.stats.steamNumber == self.parameters.data.get('steamNumber')):
							if (self.parameters.data.get('showOwn')):
								self.data = self.data + self.createCustomOutput(item)
						else:
							self.data = self.data + self.createCustomOutput(item)					
				for item in self.data:
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
			prefixDiv = '<div id = "textVariables">'
			postfixDivClose = '</div>'
		stringFormattingDictionary = dict(self.parameters.stringFormattingDictionary)
		#stringFormattingDictionary = {} # create a new dictionary
		stringFormattingDictionary['$NAME$'] =  prefixDiv + str(player.name) + postfixDivClose 
		if (bool(re.match("""^[/\.]""" , player.name))):
			stringFormattingDictionary['$NAME$'] =  prefixDiv + str(player.name.rjust(len(player.name)+1)) + postfixDivClose 
		# add 1 extra whitespace to username if it starts with . or / using rjust to prevent . and / twitch chat commands causing problems
		if overlay:
			stringFormattingDictionary['$NAME$'] =  prefixDiv + str(html.escape(player.name)) + postfixDivClose
		if type(player.faction) is Faction:
			stringFormattingDictionary['$FACTION$'] =  prefixDiv + str(player.faction.name) + postfixDivClose

		if (self.matchType == MatchType.BASIC):
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + "Basic" + postfixDivClose
		if (self.matchType == MatchType.ONES):
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + "1v1" + postfixDivClose
		if (self.matchType == MatchType.TWOS):
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + "2v2" + postfixDivClose
		if (self.matchType == MatchType.THREES):
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + "3v3" + postfixDivClose

		# if a computer it will have no stats
		if player.stats:
			stringFormattingDictionary['$COUNTRY$'] =  prefixDiv + str(player.stats.country) + postfixDivClose
			stringFormattingDictionary['$TOTALWINS$'] =  prefixDiv + str(player.stats.totalWins) + postfixDivClose
			stringFormattingDictionary['$TOTALLOSSES$'] =  prefixDiv + str(player.stats.totalLosses) + postfixDivClose
			stringFormattingDictionary['$TOTALWLRATIO$'] =  prefixDiv + str(player.stats.totalWLRatio) + postfixDivClose


			#set default null values for all parameters in dictionary
			stringFormattingDictionary['$WINS$'] =  prefixDiv + "" + postfixDivClose
			stringFormattingDictionary['$LOSSES$'] =  prefixDiv + "" + postfixDivClose
			stringFormattingDictionary['$DISPUTES$'] =  prefixDiv + "" + postfixDivClose
			stringFormattingDictionary['$STREAK$'] =  prefixDiv + "" + postfixDivClose
			stringFormattingDictionary['$DROPS$'] =  prefixDiv + "" + postfixDivClose
			stringFormattingDictionary['$RANK$'] =  prefixDiv + "" + postfixDivClose
			stringFormattingDictionary['$LEVEL$'] =  prefixDiv + "" + postfixDivClose
			stringFormattingDictionary['$WLRATIO$'] =  prefixDiv + "" + postfixDivClose			

			for value in player.stats.leaderboardData:
				if (str(player.stats.leaderboardData[value].matchType) == str(self.matchType)):
					if (str(player.stats.leaderboardData[value].faction) == str(player.faction)):
				
						stringFormattingDictionary['$WINS$'] =  prefixDiv + str(player.stats.leaderboardData[value].wins) + postfixDivClose
						stringFormattingDictionary['$LOSSES$'] =  prefixDiv + str(player.stats.leaderboardData[value].losses) + postfixDivClose
						stringFormattingDictionary['$DISPUTES$'] =  prefixDiv + str(player.stats.leaderboardData[value].disputes) + postfixDivClose
						stringFormattingDictionary['$STREAK$'] =  prefixDiv + str(player.stats.leaderboardData[value].streak) + postfixDivClose
						stringFormattingDictionary['$DROPS$'] =  prefixDiv + str(player.stats.leaderboardData[value].drops) + postfixDivClose
						stringFormattingDictionary['$RANK$'] =  prefixDiv + str(player.stats.leaderboardData[value].rank) + postfixDivClose
						stringFormattingDictionary['$LEVEL$'] =  prefixDiv + str(player.stats.leaderboardData[value].rankLevel) + postfixDivClose
						stringFormattingDictionary['$WLRATIO$'] =  prefixDiv + str(player.stats.leaderboardData[value].winLossRatio) + postfixDivClose
					 

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
				imageOverlayFormattingDictionary['$FACTIONICON$'] = '<div id = "factionflagimg"><img src="{0}" height = "30"></div>'.format(factionIcon)
				logging.info(imageOverlayFormattingDictionary.get('$FACTIONICON$'))
			else:
				imageOverlayFormattingDictionary['$FACTIONICON$'] = '<div id = "factionflagimg"><img height = "30"></div>'		

		# if a computer it will have no stats therefore no country flag or rank
		if player.stats:
			# set default values for flags and faction rank
			imageOverlayFormattingDictionary['$FLAGICON$'] = '<div id = "countryflagimg"><img height = "20"></div>'
			imageOverlayFormattingDictionary['$LEVELICON$'] = '<div id = "rankimg"><img height = "45"></div>'
			levelIcon = "OverlayImages\\Ranks\\no_rank_yet.png"
			fileExists = os.path.isfile(levelIcon)
			if fileExists:
				imageOverlayFormattingDictionary['$LEVELICON$'] =  '<div id = "rankimg"><img src="{0}" height = "45"></div>'.format(levelIcon)


			if player.stats.country:
				countryIcon = "OverlayImages\\Flagssmall\\" + str(player.stats.country).lower() + ".png"
				fileExists = os.path.isfile(countryIcon)
				if fileExists:
					imageOverlayFormattingDictionary['$FLAGICON$'] = '<div id = "countryflagimg"><img src="{0}" height = "20"></div>'.format(countryIcon)
				else:
					imageOverlayFormattingDictionary['$FLAGICON$'] = '<div id = "countryflagimg"><img height = "20"></div>'

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
							imageOverlayFormattingDictionary['$LEVELICON$'] =  '<div id = "rankimg"><img src="{0}" height = "45"></div>'.format(levelIcon)
							logging.info(imageOverlayFormattingDictionary.get('$LEVELICON$'))
						else:
							imageOverlayFormattingDictionary['$LEVELICON$'] = '<div id = "rankimg"><img height = "45"></div>'
		else:
			#default no image
			imageOverlayFormattingDictionary['$FLAGICON$'] = '<div id = "countryflagimg"><img height = "20"></div>'
			imageOverlayFormattingDictionary['$LEVELICON$'] = '<div id = "rankimg"><img height = "45"></div>'


		return imageOverlayFormattingDictionary

	def formatPreFormattedString(self, theString, stringFormattingDictionary, overlay = False):

		if overlay:
			prefixDiv = '<div id = "nonVariableText">'
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


class playerStat:

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
							self.leaderboardData[0] = factionResult(faction = Faction.US, matchType = MatchType.BASIC, name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 1:
							self.leaderboardData[1] = factionResult(faction = Faction.WM, matchType = MatchType.BASIC, name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 2:
							self.leaderboardData[2] = factionResult(faction = Faction.CW, matchType = MatchType.BASIC, name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 3:
							self.leaderboardData[3] = factionResult(faction = Faction.PE, matchType = MatchType.BASIC, name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 4:
							self.leaderboardData[4] = factionResult(faction = Faction.US, matchType = MatchType.ONES, name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 5:
							self.leaderboardData[5] = factionResult(faction = Faction.WM, matchType = MatchType.ONES, name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 6:
							self.leaderboardData[6] = factionResult(faction = Faction.CW, matchType = MatchType.ONES, name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 7:
							self.leaderboardData[7] = factionResult(faction = Faction.PE, matchType = MatchType.ONES, name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 8:
							self.leaderboardData[8] = factionResult(faction = Faction.US, matchType = MatchType.TWOS, name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 9:
							self.leaderboardData[9] = factionResult(faction = Faction.WM, matchType = MatchType.TWOS, name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 10:
							self.leaderboardData[10] = factionResult(faction = Faction.CW, matchType = MatchType.TWOS, name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 11:
							self.leaderboardData[11] = factionResult(faction = Faction.PE, matchType = MatchType.TWOS, name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 12:
							self.leaderboardData[12] = factionResult(faction = Faction.US, matchType = MatchType.THREES, name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 13:
							self.leaderboardData[13] = factionResult(faction = Faction.WM, matchType = MatchType.THREES, name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 14:
							self.leaderboardData[14] = factionResult(faction = Faction.CW, matchType = MatchType.THREES, name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
						if item.get('leaderboard_id') == 15:
							self.leaderboardData[15] = factionResult(faction = Faction.PE, matchType = MatchType.THREES, name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
		

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
		self.matchType = str(matchType).replace("-1", "None")
		self.name = name
		self.nameShort = nameShort
		self.id = leaderboard_id
		self.wins = str(wins).replace("-1", "None")
		self.losses = str(losses).replace("-1", "None")
		self.streak = str(streak).replace("-1", "None")
		self.disputes = str(disputes).replace("-1", "None")
		self.drops = str(drops).replace("-1", "None")
		self.rank = str(rank).replace("-1", "None")
		self.rankLevel = str(rankLevel).replace("-1", "None")
		self.lastMatch = str(lastMatch).replace("-1", "None")
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
		output = "name : " + str(self.name) + "\n"
		output += "factionString : " + str(self.factionString) + "\n"
		output += "faction : " + str(self.faction) + "\n"
		output += "stats : \n " + str(self.stats) + "\n"
		return output

	def __repr__(self):
		return str(self)


class ApplicationMemoryReader():
	def __init__(self):
		pass
	def getFactions(self):
		# look for COH__REC inside application memory
		buff = bytes(b"COH__REC")
		pid = Process.get_pid_by_name('RelicCOH.exe')
		logging.info("searchCString : " + str(buff))
		logging.info("pid of RelicCOH.exe: " + str(pid))
		playerList = []
		if (pid):
			with Process.open_process(pid) as p:
				addrs = p.search_all_memory(buff)
				try:
					assert(len(addrs) == 1)
					#asset that an address exists or throw an exception
					logging.info("Address : " + str(addrs) + "\n")
					logging.info("Address : " + str(hex(addrs[0])) + "\n")

					#read an abitrary number of bytes from the COH__REC memory location 4000 should do this will cover the replay header and extras
					data_dump = p.read_memory(addrs[0], (ctypes.c_byte * 4000)())
					data_dump = bytearray(data_dump)
					#do a regular expression match to find all occurances of DATAINFO in the data_dump
					matchobject = re.finditer(b'DATAINFO', data_dump)
					for item in matchobject:
						#for each start index found read the username and faction and put them in a list
						indexOfDATAINFO = int(item.start())
						logging.info(data_dump.find(b'DATAINFO'))
						usernamelength = p.read_memory(addrs[0] + indexOfDATAINFO + 28, (ctypes.c_byte * 4)())
						logging.info(int.from_bytes(usernamelength, byteorder='little', signed=False))
						usernamelength = int.from_bytes(usernamelength, byteorder='little', signed=False)
						username = p.read_memory(addrs[0] + indexOfDATAINFO + 28 + 4, (ctypes.c_byte * (usernamelength*2))())
						logging.info(bytearray(username).decode('utf-16le'))
						lengthOfFactionString = p.read_memory(addrs[0] + indexOfDATAINFO + 32 + 8 + (usernamelength*2), (ctypes.c_byte * 4)())
						lengthOfFactionString = int.from_bytes(lengthOfFactionString, byteorder='little', signed=False)
						logging.info (lengthOfFactionString)
						factionString = p.read_memory(addrs[0] + indexOfDATAINFO + 32 + 8 + (usernamelength*2) + 4, (ctypes.c_byte * (lengthOfFactionString))())
						logging.info(bytearray(factionString).decode('ascii'))
						playerList.append(Player(name=bytearray(username).decode('utf-16le'),factionString=bytearray(factionString).decode('ascii')))
							
				except Exception as e:
					logging.error("Problem finding memory : " + str(e))
		return playerList


# to use this file without the GUI be sure to have the parameters file in the same directory and uncomment below
#myIRC = IRCClient()

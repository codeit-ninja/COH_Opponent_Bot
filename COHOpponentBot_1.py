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
from IRCBetBot_Parameters import parameters
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

		self.parameters = parameters()

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
			print("A problem occurred trying to connect")
			logging.exception("In IRCClient")
			print(str(e))
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
					print (str(line).encode('utf8'))
					if (self.displayConsoleOut):
						try:
							self.output.insert(END, "".join(line) + "\n")
						except Exception as e:
							logging.exception("In run")
							print(str(e))

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
		print("in close in thread")
		try:
			# send closing message immediately
			self.irc.send(("PRIVMSG " + self.channel + " :" + str("closing opponent bot") + "\r\n").encode('utf8'))
		except Exception as e:
			logging.exception("In close")
			print(str(e))
			
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
				print("IRC send error:")
				logging.exception("In IRCSendCalledEveryTwoSeconds")
				print(str(e))
	#above is called by the timer every three seconds and checks for items in buffer to be sent, if there is one it'll send it



class IRC_Channel(threading.Thread):
	def __init__(self, parent, irc, queue, channel):
		Thread.__init__(self)
		self.parent = parent
		self.running = True
		self.irc = irc
		self.queue = queue
		self.channel = channel
		self.parameters = parameters()
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
			if (line[0] == "IWON"):
				self.parent.SendPrivateMessageToIRC(str(self.parameters.data.get('channel')) +" won")
			if (line[0] == "ILOST"):
				self.parent.SendPrivateMessageToIRC(str(self.parameters.data.get('channel')) +" lost")
			if (line[0] == "CLEAROVERLAY"):
				HandleCOHlogFile().clearOverlayHTML()
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
		print (str(messageString).encode('utf8'))

		#Check for UserCommands
		self.CheckForUserCommand(msgUserName, msgMessage)
		
	
		if (msgMessage == "exit") and (msgUserName == self.parent.adminUserName):
			self.parent.SendPrivateMessageToIRC("Exiting")
			self.close()


	def CheckForUserCommand(self, userName, message):
		if (bool(re.match("^(!)?opponent(\?)?$", message.lower())) or bool(re.match("^(!)?place your bets$" , message.lower())) or bool(re.match("^(!)?opp(\?)?$", message.lower()))):
			self.myHandleCOHlogFile = HandleCOHlogFile()
			returnedList =  self.myHandleCOHlogFile.loadLog()
			if returnedList:
				for item in returnedList:
					self.parent.SendPrivateMessageToIRC(str(item))
		if (message.lower() == "test") and ((str(userName).lower() == str(self.parameters.privatedata.get('adminUserName')).lower()) or (str(userName) == str(self.parameters.data.get('channel')).lower())):
			self.parent.SendPrivateMessageToIRC("I'm here! Pls give me mod to prevent twitch from autobanning me for spam if I have to send a few messages quickly.")
			self.parent.output.insert(END, "Oh hi again, I heard you in the " +self.channel[1:] + " channel.\n")

	def close(self):
		self.running = False
		print("Closing Channel " + str(self.channel) + " thread.")




class StatsRequest:
	def __init__(self, parameters):
		self.parameters = parameters		
		
	def returnStats(self, statnumber):
		print ("got statnumber : " + str(statnumber))
		#statString = "/steam/" + str(statnumber)
		if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
			ssl._create_default_https_context = ssl._create_unverified_context
		response = urllib.request.urlopen(self.parameters.privatedata['relicServerProxy']+str(statnumber)).read()
		statdata = json.loads(response.decode('utf-8'))
		#print(json.dumps(statdata, indent=4, sort_keys= True))
		if (statdata['result']['message'] == "SUCCESS"):
			print ("statdata load succeeded")
			playerStats = playerStat(statdata, statnumber)
			#print("playerStats : " + str(playerStats))

			return playerStats

class FileMonitor (threading.Thread):

	

	def __init__(self, filePath, pollInterval, opponentBot):
		Thread.__init__(self)
		try:
			self.running = True
			self.parameters = parameters()
			self.opponentBot = opponentBot
			self.fileIndex = 0
			self.pollInterval = int(pollInterval)
			#self.queue = q
			self.filePath = filePath
			self.fileIndex = 0
			self.theFile = []
			self.event = threading.Event()
			self.startingMissonEvent = threading.Event()
			with open(self.filePath, 'r') as f:
				lines = f.readlines()
			for line in lines: 
				self.theFile.append(line)
				#self.queue.put(line)
			#print(str(self.theFile))
			print("Initialzing with file length : " + str(len(self.theFile)) + "\n")
			self.fileIndex = len(self.theFile)
			self.theFile = None
		except Exception as e:
			logging.exception("In FileMonitor __init__")
			print(str(e))

	def run(self):
		try:
			print ("Started monitoring File : " + str(self.filePath) + "\n")
			while self.running:
				lines = []
				clearOverlay = False
				with open(self.filePath,'r') as f:
					lines = f.readlines()
					print("current File index = : " + str(self.fileIndex) + "\n")
					print ("file length = " + str(len(lines)) + "\n")
				for x in range(int(self.fileIndex), len(lines)):
					#Handle New Lines since load
					#self.queue.put(lines[x])
					if ("GAME -- Starting mission..." in lines[x]):
						self.startingMissonEvent.wait(timeout= 30) # allow extra seconds for computer AI info to load if the game is a human vs ai game
						if (self.opponentBot):
							#trigger the opponent command in the opponentbot thread
							self.opponentBot.queue.put("OPPONENT")
					if ("Win notification" in lines[x]):
						#Check if streamer won
						theSteamNumber = self.find_between(lines[x] ,"/steam/" , "]")
						if (str(self.parameters.data.get('steamNumber')) == str(theSteamNumber)):
							print("STREAMER WON\n")
							if (self.parameters.data.get('writeIWonLostInChat')):
								self.opponentBot.queue.put("IWON")
							if (self.parameters.data.get('clearOverlayAfterGameOver')):
								clearOverlay = True
					if ("Loss notification" in lines[x]):
						#Check if streamer lost
						theSteamNumber = self.find_between(lines[x] ,"/steam/" , "]")
						if (str(self.parameters.data.get('steamNumber')) == str(theSteamNumber)):
							print("STREAMER LOST\n")
							if (self.parameters.data.get('writeIWonLostInChat')):
								self.opponentBot.queue.put("ILOST")
							if (self.parameters.data.get('clearOverlayAfterGameOver')):
								clearOverlay = True

				if (self.parameters.data.get('clearOverlayAfterGameOver')):
					if (clearOverlay):
						self.opponentBot.queue.put("CLEAROVERLAY")
				self.fileIndex = len(lines)
				self.event = threading.Event()
				self.event.wait(timeout = self.pollInterval)
			print ("File Monitoring Ended.\n")
		except Exception as e:
			logging.exception("In FileMonitor run")
			print(str(e))
    
	def close(self):
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
	

	def __init__(self):

		self.parameters = parameters()
		self.logPath = self.parameters.data['logPath']
		self.data = []

		self.numberOfHumans = 0
		self.numberOfComputers = 0

		self.mapSize = -1


	
	def loadLog(self):
		print("In loadLog")
		with open(self.logPath, encoding='ISO-8859-1') as file:
			content = file.readlines()
		print(self.parameters.data['steamNumber'])
		playerList = []
		self.numberOfHumans = 0
		self.numberOfComputers = 0
		eazyCPUCount = 0
		normalCPUCount = 0
		hardCPUCount = 0
		expertCPUCount = 0
		self.mapSize = 0


		for item in content:
			if ("match started") in item.lower():
				print (item)
				# dictionary containing player number linked to steamnumber
				steamNumber = self.find_between(item, "steam/", "]")
				slot = self.find_between(item , "slot =  " , ", ranking")
				logFileRanking = self.find_between(item, "ranking =" , "\n")
				logFileRanking = str(logFileRanking).strip()

				# if slot does not exist in playerList then create player with new slot and steamNumber
				slotExists = False
				for i in range(len(playerList)):
					if str(playerList[i].slot) == str(slot):
						slotExists = True
						playerList[i].steamNumber = steamNumber
						playerList[i].logFileRanking = logFileRanking
						print("the slot exists and I'm assigning steamNumber to it")
				if (not slotExists):
					thePlayer = Player(slot = slot, steamNumber=steamNumber, logFileRanking=logFileRanking)
					playerList.append(thePlayer)
					print("the slot does not exist and I'm creating a new player")


			# set the number of players
			if ("Setting player" in item):
					theSlotNumber = self.find_between(item, "player (", ")")
					print ("The slot number : " + str(theSlotNumber))

					# if slot does not exist in playerList then create player with new slot number
					slotExists = False
					for i in range(len(playerList)):
						if str(playerList[i].slot) == str(theSlotNumber):
							slotExists = True

					factionString = self.find_between(item , "race to: " , "\n")
					print("factionString : " + str(factionString))

					if (slotExists):		
						for x in range (len(playerList)):
							if (str(theSlotNumber) == str(playerList[x].slot)):

								if factionString == "allies_commonwealth":
									playerList[x].faction = Faction.CW
									playerList[x].factionString = factionString
									print("Setting faction to CW")

								if factionString == "allies":
									playerList[x].faction = Faction.US
									playerList[x].factionString = factionString							
									print("Setting faction to US")

								if factionString == "axis_panzer_elite":
									playerList[x].faction = Faction.PE
									playerList[x].factionString = factionString								
									print("Setting faction to PE")

								if factionString == "axis":
									playerList[x].faction = Faction.WM
									playerList[x].factionString = factionString
									print("Setting faction to WM")
					else:
						if factionString == "allies_commonwealth":
							player = Player(slot=theSlotNumber, faction = Faction.CW, factionString=factionString)
							playerList.append(player)
							print("Setting faction to CW")

						if factionString == "allies":
							player = Player(slot=theSlotNumber, faction = Faction.US, factionString=factionString)
							playerList.append(player)									
							print("Setting faction to US")

						if factionString == "axis_panzer_elite":
							player = Player(slot=theSlotNumber, faction = Faction.PE, factionString=factionString)
							playerList.append(player)									
							print("Setting faction to PE")

						if factionString == "axis":
							player = Player(slot=theSlotNumber, faction = Faction.WM, factionString=factionString)
							playerList.append(player)
							print("Setting faction to WM")



			if ("GAME -- ***") in item:
				# need to reverse the string to get the humans bit out uniquely or other strings in the line can interfere with the parsing
				reverseString = item[::-1]
				self.numberOfHumans = self.find_between(reverseString, "snamuH " , "(")
				#print("humans  = " + str(self.numberOfHumans) + "\n")
				self.numberOfComputers = self.find_between(item, "Humans, ", " Computers")
			if ("PerformanceRecorder::StartRecording") in item:
					self.mapSize = self.find_between(item, "game size " , "\n")
			# clear the steam number list if a new game is found in the file
			if ("AutoMatchForm - Starting game") in item:
				eazyCPUCount = 0
				normalCPUCount = 0
				hardCPUCount = 0
				expertCPUCount = 0
				self.numberOfHumans = 0
				self.numberOfComputers = 0
				self.mapSize = 0
				playerList.clear()
				print("CLEARING PLAYER LIST\n")
			if ("Player CPU - Expert" in item):
				expertCPUCount += 1
			if ("Player CPU - Hard" in item):
				hardCPUCount += 1
			if ("Player CPU - Normal" in item):
				normalCPUCount += 1
			if ("Player CPU - Easy" in item):
				eazyCPUCount += 1
		
		# default backup player numbers - not used if file human and computers are legit numbers
		numberOfPlayers = len(playerList)


		try:
			numberOfPlayers = int(float(self.numberOfHumans)) + int(float(self.numberOfComputers)) # the float then int removes change of value error
		except Exception as e:
			logging.exception("In loadlog 1")
			print (str(e))
		print("humans " + str(self.numberOfHumans) +"\n")
		print("computers " + str(self.numberOfComputers) +"\n")
		print("number of players " + str(numberOfPlayers) + "\n")
		print("map size " + str(self.mapSize) + "\n")
		for item in playerList:
			print("playerList : " + str(item))

		try:
			if (int(self.numberOfComputers) > 0):
				self.data.append("Game with " + str(self.numberOfComputers) + " computer AI, ("+str(eazyCPUCount)+") Easy, ("+str(normalCPUCount)+") Normal, ("+str(hardCPUCount)+") Hard, ("+str(expertCPUCount)+") Expert.")
		except Exception as e:
			logging.exception("In loadlog 2")
			print(str(e))
		
		playerStatList = []

		if (playerList):
			for player in playerList:
				myStatRequest = StatsRequest(self.parameters)
				try:
					statNumber = int(player.steamNumber)
					if statNumber != -1:
						returnedStat = myStatRequest.returnStats(statNumber)
						playerStatList.append(returnedStat)
				except Exception as e:
					print(str(e))
	
		#
		#replayReader = ReplayReader()
		# not using replay reader anymore due to temp.rec file not being written to until the game is over.
		#

		# assign faction values to the players
		for item in playerList:
			for x in range(len(playerStatList)):
				if(str(item.steamNumber) == str(playerStatList[x].user.steamNumber)):
					playerStatList[x].user.faction = item.faction
					playerStatList[x].user.factionString = item.factionString
					playerStatList[x].user.slot = item.slot
					playerStatList[x].user.logFileRanking = item.logFileRanking


		print("FULL PLAYERSTATLIST\n")
		for item in playerStatList:
			print(item)


		# Because factions are often reported incorrectly check the logFileRanking with the faction ranking for the mapsize if different attempt to reassign to a closer one
		playerStatList = self.checkFactionsAreCorrect(playerStatList)


		print("FULL playerStatList After Correction\n")
		for item in playerStatList:
			print(item)


		axisTeam = []
		alliesTeam = []

		#not sure if they need clearing but apparently the lists are sometimes persistent?
		axisTeam.clear()
		alliesTeam.clear()

		for item in playerStatList:
			if (str(item.user.faction) == str(Faction.US)) or (str(item.user.faction)== str(Faction.CW)):
				alliesTeam.append(item)
			if (str(item.user.faction) == str(Faction.WM)) or (str(item.user.faction)== str(Faction.PE)):
				axisTeam.append(item)

		print("players in allies team : " +str(len(alliesTeam)))
		print("players in axis team : " + str(len(axisTeam)))

		# output each player to file
		if (self.parameters.data.get('useOverlayPreFormat')):
			self.saveOverlayHTML(axisTeam, alliesTeam)

		# output to chat if customoutput ticked
		if (self.parameters.data.get('useCustomPreFormat')):		
			for item in playerStatList:
				if(item.user.steamNumber == self.parameters.data.get('steamNumber')):
					if (self.parameters.data.get('showOwn')):
						self.data = self.data + self.createCustomOutput(item)
				else:
					self.data = self.data + self.createCustomOutput(item)				
				
		if self.data:
			return self.data
		else:
			return None


	def checkFactionsAreCorrect(self, playerStatList):
		# check the faction ranks are +/- 1 of their expected value if not attempt to assign to rank that is +/- 1
		matchType = MatchType.BASIC
		if (int(self.numberOfComputers) > 0):
			matchType = MatchType.BASIC
		if (0 <= int(self.mapSize) <= 2) and (int(self.numberOfComputers) == 0):
			matchType = MatchType.ONES
		if (3 <= int(self.mapSize) <= 4) and (int(self.numberOfComputers) == 0):
			matchType = MatchType.TWOS
		if (5 <= int(self.mapSize) <= 6) and (int(self.numberOfComputers) == 0):
			matchType = MatchType.THREES

		for x in range(len(playerStatList)):
			logFileRanking = -1
			try:
				logFileRanking = int(playerStatList[x].user.logFileRanking)
			except Exception as e:
				print(str(e))
			for key in playerStatList[x].leaderboardData:
				if (str(playerStatList[x].leaderboardData[key].matchType) == str(matchType)):
					if (str(playerStatList[x].leaderboardData[key].faction) == str(playerStatList[x].user.faction)):
						rank = -1
						try:
							if playerStatList[x].leaderboardData[key].rank:
								rank = int(playerStatList[x].leaderboardData[key].rank)
						except Exception as e:
							print(str(e))
						if not ((logFileRanking-1) <= rank <= (logFileRanking+1)):
							# reassign if not correct
							# reloop and check for first correct value
							# this will only happen if it wasn't correct first time
							for z in playerStatList[x].leaderboardData:
								if (str(playerStatList[x].leaderboardData[z].matchType) == str(matchType)):
									newrank = -1
									try:
										if playerStatList[x].leaderboardData[z].rank:
											newrank = int(playerStatList[x].leaderboardData[z].rank)
									except Exception as e:
										print(str(e))
									if ((logFileRanking-1) <= newrank <= (logFileRanking+1)):
										playerStatList[x].user.faction = playerStatList[x].leaderboardData[z].faction
		return playerStatList

	def createCustomOutput(self, playerStats):
		stringFormattingDictionary = self.populateStringFormattingDictionary(playerStats)
		customPreFormattedOutputString = self.parameters.data.get('customStringPreFormat')
		theString = self.formatPreFormattedString(customPreFormattedOutputString, stringFormattingDictionary)
		outputList = list(self.split_by_n(theString, 500))
		if (self.parameters.data.get('showSteamProfile')):
			outputList.append("Steam profile " + str(playerStats.user.steamProfileAddress))
		return outputList

	def populateStringFormattingDictionary(self, playerStats, overlay = False):
		prefixDiv = ""
		postfixDivClose = ""
		if overlay:
			prefixDiv = '<div id = "textVariables">'
			postfixDivClose = '</div>'
		stringFormattingDictionary = self.parameters.stringFormattingDictionary
		stringFormattingDictionary['$NAME$'] =  prefixDiv + str(playerStats.user.name) + postfixDivClose 
		if (bool(re.match("""^[/\.]""" , playerStats.user.name))):
			stringFormattingDictionary['$NAME$'] =  prefixDiv + str(playerStats.user.name.rjust(len(playerStats.user.name)+1)) + postfixDivClose 
		# add 1 extra whitespace to username if it starts with . or / using rjust to prevent . and / twitch chat commands causing problems
		if overlay:
			stringFormattingDictionary['$NAME$'] =  prefixDiv + str(html.escape(playerStats.user.name)) + postfixDivClose
		if type(playerStats.user.faction) is Faction:
			stringFormattingDictionary['$FACTION$'] =  prefixDiv + str(playerStats.user.faction.name) + postfixDivClose
		stringFormattingDictionary['$COUNTRY$'] =  prefixDiv + str(playerStats.user.country) + postfixDivClose
		stringFormattingDictionary['$TOTALWINS$'] =  prefixDiv + str(playerStats.totalWins) + postfixDivClose
		stringFormattingDictionary['$TOTALLOSSES$'] =  prefixDiv + str(playerStats.totalLosses) + postfixDivClose
		stringFormattingDictionary['$TOTALWLRATIO$'] =  prefixDiv + str(playerStats.totalWLRatio) + postfixDivClose

		matchType = MatchType.BASIC
		if (int(self.numberOfComputers) > 0):
			matchType = MatchType.BASIC
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + "Basic" + postfixDivClose
		if (0 <= int(self.mapSize) <= 2) and (int(self.numberOfComputers) == 0):
			matchType = MatchType.ONES
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + "1v1" + postfixDivClose
		if (3 <= int(self.mapSize) <= 4) and (int(self.numberOfComputers) == 0):
			matchType = MatchType.TWOS
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + "2v2" + postfixDivClose
		if (5 <= int(self.mapSize) <= 6) and (int(self.numberOfComputers) == 0):
			matchType = MatchType.THREES
			stringFormattingDictionary['$MATCHTYPE$'] =  prefixDiv + "3v3" + postfixDivClose


		for value in playerStats.leaderboardData:
			if (str(playerStats.leaderboardData[value].matchType) == str(matchType)):
				if (str(playerStats.leaderboardData[value].faction) == str(playerStats.user.faction)):
					stringFormattingDictionary['$WINS$'] =  prefixDiv + str(playerStats.leaderboardData[value].wins) + postfixDivClose
					stringFormattingDictionary['$LOSSES$'] =  prefixDiv + str(playerStats.leaderboardData[value].losses) + postfixDivClose
					stringFormattingDictionary['$DISPUTES$'] =  prefixDiv + str(playerStats.leaderboardData[value].disputes) + postfixDivClose
					stringFormattingDictionary['$STREAK$'] =  prefixDiv + str(playerStats.leaderboardData[value].streak) + postfixDivClose
					stringFormattingDictionary['$DROPS$'] =  prefixDiv + str(playerStats.leaderboardData[value].drops) + postfixDivClose
					stringFormattingDictionary['$RANK$'] =  prefixDiv + str(playerStats.leaderboardData[value].rank) + postfixDivClose
					stringFormattingDictionary['$LEVEL$'] =  prefixDiv + str(playerStats.leaderboardData[value].rankLevel) + postfixDivClose
					stringFormattingDictionary['$WLRATIO$'] =  prefixDiv + str(playerStats.leaderboardData[value].winLossRatio) + postfixDivClose
					 

		return stringFormattingDictionary

	def populateImageFormattingDictionary(self, playerStats):
		imageOverlayFormattingDictionary = self.parameters.imageOverlayFormattingDictionary
		if playerStats.user.country:
			countryIcon = "OverlayImages\\Flagssmall\\" + str(playerStats.user.country).lower() + ".png"
			fileExists = os.path.isfile(countryIcon)
			if fileExists:
				imageOverlayFormattingDictionary['$FLAGICON$'] = '<div id = "countryflagimg"><img src="{0}" height = "20"></div>'.format(countryIcon)
			else:
				imageOverlayFormattingDictionary['$FLAGICON$'] = '<div id = "countryflagimg"><img height = "20"></div>'
		if playerStats.user.faction:
			fileExists = False
			factionIcon = ""
			if type(playerStats.user.faction) is Faction:
				factionIcon = "OverlayImages\\Armies\\" + str(playerStats.user.faction.name).lower() + ".png"
				fileExists = os.path.isfile(factionIcon)
			print(factionIcon)
			if fileExists:
				imageOverlayFormattingDictionary['$FACTIONICON$'] = '<div id = "factionflagimg"><img src="{0}" height = "30"></div>'.format(factionIcon)
				print(imageOverlayFormattingDictionary.get('$FACTIONICON$'))
			else:
				imageOverlayFormattingDictionary['$FACTIONICON$'] = '<div id = "factionflagimg"><img height = "30"></div>'
		matchType = MatchType.BASIC
		if (int(self.numberOfComputers) > 0):
			matchType = MatchType.BASIC
		if (0 <= int(self.mapSize) <= 2) and (int(self.numberOfComputers) == 0):
			matchType = MatchType.ONES
		if (3 <= int(self.mapSize) <= 4) and (int(self.numberOfComputers) == 0):
			matchType = MatchType.TWOS
		if (5 <= int(self.mapSize) <= 6) and (int(self.numberOfComputers) == 0):
			matchType = MatchType.THREES
		for value in playerStats.leaderboardData:
			if (str(playerStats.leaderboardData[value].matchType) == str(matchType)):
				if (str(playerStats.leaderboardData[value].faction) == str(playerStats.user.faction)):
					iconPrefix = ""
					if str(playerStats.user.faction) == str(Faction.PE):
						iconPrefix = "panzer_"
					if str(playerStats.user.faction) == str(Faction.CW):
						iconPrefix = "brit_"
					if str(playerStats.user.faction) == str(Faction.US):
						iconPrefix = "us_"
					if str(playerStats.user.faction) == str(Faction.WM):
						iconPrefix = "heer_"												
					level = str(playerStats.leaderboardData[value].rankLevel).zfill(2)
					levelIcon = "OverlayImages\\Ranks\\" + iconPrefix + level + ".png"
					print("levelIcon : " + str(levelIcon))
					fileExists = os.path.isfile(levelIcon)
					if fileExists:
						imageOverlayFormattingDictionary['$LEVELICON$'] =  '<div id = "rankimg"><img src="{0}" height = "45"></div>'.format(levelIcon)
						print(imageOverlayFormattingDictionary.get('$LEVELICON$'))
					else:
						imageOverlayFormattingDictionary['$LEVELICON$'] = '<div id = "rankimg"><img height = "45"></div>'
		return imageOverlayFormattingDictionary

	def formatPreFormattedString(self, theString, stringFormattingDictionary, overlay = False):

		if overlay:
			prefixDiv = '<div id = "nonVariableText">'
			postfixDiv = '</div>'

			#compile a pattern for all the keys
			pattern = re.compile(r'(' + '|'.join(re.escape(key) for key in stringFormattingDictionary.keys()) + r')')

			print(pattern)
			#split the string to include the dictionary keys
			fullSplit = re.split(pattern, theString)
			
			print(fullSplit)
			
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

	def savePlayer(self, playerStats):
		try:
			playerNumber = "player" + str(playerStats.user.slot) + ".txt"
			with open(playerNumber , 'w') as outfile:
				outfile.write(str("{0}".format(str(playerStats.user.name))))
		except Exception as e:
			logging.exception("In savePlayer")
			print("Problem in save")
			print(str(e))

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
				print("axisTeamList : " + str(item.user.steamNumber))
				print("player steamNumber : " + str(self.parameters.data.get('steamNumber')))
				if (str(self.parameters.data.get('steamNumber')) == str(item.user.steamNumber)):
					print ("Player team is AXIS")
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
					stringFormattingDictionary = self.populateStringFormattingDictionary(item, overlay = True)
					#theString = self.formatPreFormattedString(preFormattedString, stringFormattingDictionary,overlay = True)
					# second substitue all the html images if used
					stringFormattingDictionary.update(self.populateImageFormattingDictionary(item))
					theString = self.formatPreFormattedString(preFormattedString, stringFormattingDictionary, overlay= True)
					team2 += str(theString) + str("<BR>") + "\n"
			else:
			
				for item in team1List:
					team1 += str(item.user.name) + str("<BR>") + "\n"
				for item in team2List:
					team2 += str(item.user.name) + str("<BR>") + "\n"
				
			htmlOutput = OverlayTemplates().overlayhtml.format(team1, team2)
			# create output overlay from template
			with open("overlay.html" , 'w', encoding="utf-8") as outfile:
				outfile.write(htmlOutput)
				print("Creating Overlay File\n")
			#check if css file exists and if not output the default template to folder
			if not (os.path.isfile("overlaystyle.css")):
				with open("overlaystyle.css" , 'w' , encoding="utf-8") as outfile:
					outfile.write(OverlayTemplates().overlaycss)
		except Exception as e:
			print(str(e))

	def clearOverlayHTML(self):
		try:
			htmlOutput = OverlayTemplates().overlayhtml.format("", "")
			# create output overlay from template
			with open("overlay.html" , 'w') as outfile:
				outfile.write(htmlOutput)
		except Exception as e:
			print(str(e))

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
		self.user = Player()
		#self.basic = { } 
		#self.ones = { }
		#self.twos = { }
		#self.threes = { }
		self.leaderboardData = {}

		self.totalWins = 0
		self.totalLosses = 0		
		self.totalWLRatio = None


		statString = "/steam/"+str(steamNumber)

		if (statdata['result']['message'] == "SUCCESS"):

			if statdata['statGroups'][0]['members'][0]['alias']:
				for item in statdata['statGroups']:
					for value in item['members']:
						if (value.get('name') == statString):
							self.user = Player(profile_id = value.get('profile_id'), name = value.get('alias'), steamString = value.get('name'), country = value.get('country'))
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
				print("problem with totalwins value : " + str(value) +" data : "+ str(self.leaderboardData[value].wins))
				pass						
			try:
				self.totalLosses += int(self.leaderboardData[value].losses)
			except Exception as e:
				print("problem with totallosses value : " + str(value) +" data : "+ str(self.leaderboardData[value].losses))
				pass

		self.totalWins = str(self.totalWins)
		self.totalLosses = str(self.totalLosses)

		try:
			if (int(self.totalLosses) > 0):
				self.totalWLRatio = str(round(int(self.totalWins)/int(self.totalLosses), 2))

		except Exception as e:
			logging.exception("In cohStat creating totalWLRatio")
			print(str(e))
	
	
	def __str__(self):
		output = str(self.user)
		for value in self.leaderboardData:
			output += str(self.leaderboardData[value])

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
			print(str(e))
		try:
			if (int(self.losses) != 0):
				self.winLossRatio = str(round(int(self.wins)/int(self.losses), 2))
			else:
				if(int(self.wins) > 0):
					self.winLossRatio = "Unbeaten"
		except Exception as e:
			logging.exception("In factionResult Creating winLossRatio")
			print(str(e))	


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

	def __init__(self, profile_id = None, name = None, steamString = None, steamNumber = None, country = None, factionString = None, slot = None, faction = None, logFileRanking = None):
		self.profile_id = profile_id
		self.name = name
		self.steamString = steamString
		self.steamNumber = steamNumber
		self.country = country
		self.steamProfileAddress = None
		self.factionString = factionString
		self.faction = faction
		self.logFileRanking = logFileRanking
		self.slot = slot

		if self.factionString == "axis":
			self.faction = Faction.WM
		if self.factionString == "allies":
			self.faction = Faction.US
		if self.factionString == "allies_commonwealth":
			self.faction = Faction.CW
		if self.factionString == "axis_panzer_elite":
			self.faction = Faction.PE

		try:
			if self.steamString:
				self.steamNumber = str(self.steamString).replace("/steam/", "")
			self.steamProfileAddress = "https://steamcommunity.com/profiles/" + str(self.steamNumber)
		except Exception as e:
			logging.exception("In Player creating steamProfileAddress")
			print(str(e))

	
	def __str__(self):
		output = "profile_id : " + str(self.profile_id) + "\n"
		output += "name : " + str(self.name) + "\n"
		output += "steamString : " + str(self.steamString) + "\n"
		output += "steamNumber : " + str(self.steamNumber) + "\n"
		output += "country : " + str(self.country) + "\n"
		output += "steamProfileAddress : " + str(self.steamProfileAddress) + "\n"
		output += "factionString : " + str(self.factionString) + "\n"
		output += "faction : " + str(self.faction) + "\n"
		output += "logFileRanking : " + str(self.logFileRanking) + "\n"
		output += "slot : " + str(self.slot) + "\n"
		return output

	def __repr__(self):
		return str(self)

#
# The replay reader class gets the faction and username from the replay file. this works but sadly the temp.rec replay isn't written until the game is over so it isn't useful for this opponent bot.
#
class ReplayReader:
	def __init__(self, replayFilePath = None):
		
		self.parameters = parameters()
		self.listOfPlayers = []
		self.filePath = ""

		if (replayFilePath):
			self.filePath = replayFilePath
		else:
			self.filePath = self.parameters.data.get('temprecReplayPath')

		if (os.path.isfile(self.filePath)):
			with open(self.filePath, "rb") as binary_file:
				data = binary_file.read()
				binary_file.seek(4)
				cohrecString = binary_file.read(8)
				print(cohrecString)
				dataarray = bytearray(binary_file.read(32))
				print(str(dataarray.decode()))
				binary_file.seek(76)
				relicChunky = binary_file.read(12)
				print(relicChunky.decode())


				self.indexOfDATAINFO = 0

				while True:
					self.indexOfDATAINFO = data.find('DATAINFO'.encode(), self.indexOfDATAINFO + 8)
					if self.indexOfDATAINFO == -1:
						break
					print(self.indexOfDATAINFO)
					#print(str(data.find('DATAINFO'.encode())))
					binary_file.seek(self.indexOfDATAINFO + 28)
					lenghtOfString  = int.from_bytes(binary_file.read(4), byteorder = 'little')
					print(lenghtOfString)
					binary_file.seek(self.indexOfDATAINFO + 32)
					userNameByteArray = binary_file.read(lenghtOfString*2)
					userName = userNameByteArray.decode(encoding="utf-16")
					print(userName)

					binary_file.seek(self.indexOfDATAINFO + 32 + lenghtOfString*2 + 8)
					lengthOfFaction = int.from_bytes(binary_file.read(4), byteorder = 'little')
					print(lengthOfFaction)
					factionName = binary_file.read(lengthOfFaction).decode()
					print(factionName)
					self.listOfPlayers.append(Player(name=userName, factionString=factionName))

				print(self.listOfPlayers)		

# to use this file without the GUI be sure to have the parameters file in the same directory and uncomment below
#myIRC = IRCClient()

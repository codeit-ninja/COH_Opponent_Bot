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
		self.parameters.load()

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
	
		# what to show in stat string constuct
		self.showOwn = self.parameters.data.get('showOwn')

		self.showBasic = self.parameters.data.get('showBasic')
		self.show1v1 = self.parameters.data.get('show1v1')
		self.show2v2 = self.parameters.data.get('show2v2')
		self.show3v3 = self.parameters.data.get('show3v3')

		self.showWins = self.parameters.data.get('showWins')
		self.showLosses = self.parameters.data.get('showLosses')
		self.showDisputes = self.parameters.data.get('showDisputes')
		self.showStreak = self.parameters.data.get('showStreak')
		self.showDrops = self.parameters.data.get('showDrops')
		self.showRank = self.parameters.data.get('showRank')
		self.showLevel = self.parameters.data.get('showLevel')
		self.showLastPlayed = self.parameters.data.get('showLastPlayed')

		self.showWLRatio = self.parameters.data.get('showWLRatio')

		self.automaticTrigger = self.parameters.data.get('automaticTrigger')

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
		
		# Start checking send buffer every 2 seconds.
		self.CheckIRCSendBufferEveryTwoSeconds() # only call this once.	
		

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
					
	def CheckIRCSendBufferEveryTwoSeconds(self):
		self.running
		if (self.running == True): 
			threading.Timer(3.0, self.CheckIRCSendBufferEveryTwoSeconds).start()
		self.IRCSendCalledEveryTwoSeconds()
	# above is the send to IRC timer loop that runs every two seconds
	
	def SendPrivateMessageToIRC(self, message):
		self.ircMessageBuffer.append(message)   # removed this to stop message being sent to IRC
		self.output.insert(END, message + "\n") # output message to text window

	def IRCSendCalledEveryTwoSeconds(self):
		if (self.ircMessageBuffer):
			try:
				self.irc.send(("PRIVMSG " + self.channel + " :" + str(self.ircMessageBuffer.popleft()) + "\r\n").encode('utf8'))
			except Exception as e:
				print("IRC send error:")
				logging.exception("In IRCSendCalledEveryTwoSeconds")
				print(str(e))
	#above is called by the timer every two seconds and checks for items in buffer to be sent, if there is one it'll send it



class IRC_Channel(threading.Thread):
	def __init__(self, parent, irc, queue, channel):
		Thread.__init__(self)
		self.parent = parent
		self.running = True
		self.irc = irc
		self.queue = queue
		self.channel = channel
		self.parameters = parameters()
		self.parameters.load()
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
		if (message.lower() == "test") and ((userName == self.parameters.privatedata.get('adminUserName')) or (userName == self.parameters.data.get('channel'))):
			self.parent.SendPrivateMessageToIRC("I'm here! Pls give me mod to prevent twitch from autobanning me for spam if I have to send a few messages quickly.")
			self.parent.output.insert(END, "Oh hi again, I heard you in the " +self.channel[1:] + " channel.\n")

	def close(self):
		self.running = False
		if self.myHandleCOHlogFile:
			self.myHandleCOHlogFile.close()
		print("Closing Channel " + str(self.channel) + " thread.")




class StatsRequest:
	def __init__(self, parameters):
		self.parameters = parameters		
		self.parameters.load()
		
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
			print("playerStats : " + str(playerStats))

			return playerStats

class FileMonitor (threading.Thread):

	running = True

	def __init__(self, filePath, pollInterval, opponentBot):
		Thread.__init__(self)
		try:
			self.opponentBot = opponentBot
			self.fileIndex = 0
			self.pollInterval = int(pollInterval)
			#self.queue = q
			self.filePath = filePath
			self.fileIndex = 0
			self.theFile = []
			self.event = threading.Event()
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
				with open(self.filePath,'r') as f:
					lines = f.readlines()
					print("current File index = : " + str(self.fileIndex) + "\n")
					print ("file length = " + str(len(lines)) + "\n")
				for x in range(int(self.fileIndex), len(lines)):
					#Handle New Lines since load
					#self.queue.put(lines[x])
					if ("GAME -- Starting mission..." in lines[x]):
						time.sleep(5) # allow an extra seconds for computer AI info to load if the game is a human vs ai game
						if (self.opponentBot):
							#trigger the opponent command in the opponentbot thread
							self.opponentBot.queue.put("OPPONENT")
				self.fileIndex = len(lines)
				self.event = threading.Event()
				self.event.wait(timeout = self.pollInterval)
			print ("File Monitoring Ended.\n")
		except Exception as e:
			logging.exception("In FileMonitor run")
			print(str(e))
    
	def close(self):
		self.running = False
		self.event.set()

class HandleCOHlogFile:
	

	def __init__(self):

		self.parameters = parameters()
		self.parameters.load()
		self.logPath = self.parameters.data['logPath']
		self.data = []

		self.numberOfHumans = 0
		self.numberOfComputers = 0

		self.mapSize = -1


		# values for closing the while loop if it is waiting
		self.running = True
		self.closeEvent = threading.Event()


	
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
				print ("steamNumber from File : " + str(steamNumber))
				thePlayer = Player( steamNumber = str(steamNumber), slot = slot)
				playerList.append(thePlayer)

			if ("GAME -- ***") in item:
				# need to reverse the string to get the humans bit out uniquely or other strings in the line can interfere with the parsing
				reverseString = item[::-1]
				self.numberOfHumans = self.find_between(reverseString, "snamuH " , "(")
				#print("humans  = " + str(self.numberOfHumans) + "\n")
				self.numberOfComputers = self.find_between(item, "Humans, ", " Computers")
			if ("PerformanceRecorder::StartRecording") in item:
					self.mapSize = self.find_between(item, "game size " , "\n")
			# clear the steam number list if a new game is found in the file
			if ("detected successful game start") in item:
				eazyCPUCount = 0
				normalCPUCount = 0
				hardCPUCount = 0
				expertCPUCount = 0
				self.numberOfHumans = 0
				self.numberOfComputers = 0
				self.mapSize = 0
				playerList.clear()
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

		#
		#replayReader.listOfPlayers

		try:
			numberOfPlayers = int(float(self.numberOfHumans)) + int(float(self.numberOfComputers)) # the float then int removes change of value error
		except Exception as e:
			logging.exception("In loadlog 1")
			print (str(e))
		print("humans " + str(self.numberOfHumans) +"\n")
		print("computers " + str(self.numberOfComputers) +"\n")
		print("number of players " + str(numberOfPlayers) + "\n")
		print("map size" + str(self.mapSize) + "\n")
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
	
		loop = 0

		while loop < 5 and self.running:
			# import faction values from replay temp.rec file
			replayReader = ReplayReader()


			# assign faction values to the players
			for item in replayReader.listOfPlayers:
				for x in range(len(playerStatList)):
					if(str(item.name) == str(playerStatList[x].user.name)):
						playerStatList[x].user.faction = item.faction
						playerStatList[x].user.factionString = item.factionString
						playerStatList[x].user.slot = item.slot

			#check that all playerStatList players.user.faction are not None if any are wait 10 seconds try getting them again, do this 5 times then if  not continue
			for player in playerStatList:
				if (str(player.user.faction) == str(None)):
					self.closeEvent.wait(timeout = 10)
					loop += 1
					break
				else:
					loop = 5
					break

		axisTeam = []
		alliesTeam = []

		for item in playerStatList:
			if (str(item.user.faction) == str(Faction.US)) or (str(item.user.faction)== str(Faction.CW)):
				alliesTeam.append(item)
			if (str(item.user.faction) == str(Faction.WM)) or (str(item.user.faction)== str(Faction.PE)):
				axisTeam.append(item)

		# output each player to file
		if (self.parameters.data.get('outputPlayerOverlayFiles')):
			self.saveOverlayHTML(axisTeam, alliesTeam)
		

		for item in playerStatList:
			if(item.user.steamNumber == self.parameters.data.get('steamNumber')):
				if (self.parameters.data.get('showOwn')):
					self.data = self.data + self.createOutputList(item)
			else:
				self.data = self.data + self.createOutputList(item)
				
		if self.data:
			return self.data
		else:
			return None

	def close(self):
		self.running = False
		self.closeEvent.set()

	def createOutputList(self, playerStats):

		output = ""
		output += "Name : " + str(playerStats.user.name)
		if(playerStats.user.faction):
			output += " Faction : " + str(playerStats.user.faction.name)
		if (self.parameters.data.get('showUserCountry')):
			output += " : (" + str(playerStats.user.country) + ")"

		if (self.parameters.data.get('showTotalWins')):
			output += " : Total Wins " + str(playerStats.totalWins)

		if (self.parameters.data.get('showTotalLosses')):
			output += " : Total Losses " + str(playerStats.totalLosses)

		if (self.parameters.data.get('showTotalWLRatio')):
			output += " : Total W/L Ratio " + str(playerStats.totalWLRatio)

		# The comparison of Enums in the next block of code has to be converted to str first or it will not compare properly, this is a bug in python and took me ages to find. turns  out without the str conversion they didn't compare correctly

		if ((self.parameters.data.get('showBasic')) or (bool(self.parameters.data.get('automaticMode')) and (int(self.numberOfComputers) > 0))):
			output += " : Basic :-"
			for value in playerStats.leaderboardData:
				if (str(playerStats.leaderboardData[value].matchType) == str(MatchType.BASIC)):
					if self.parameters.data.get('showOnlyDetectedFactionPlayed') and (playerStats.user.faction != None):
						if (str(playerStats.leaderboardData[value].faction) == str(playerStats.user.faction)):
							output += self.getFactionString(playerStats.leaderboardData[value])
							break
					else:
						output += self.getFactionString(playerStats.leaderboardData[value])

		if ((self.parameters.data.get('show1v1')) or ((bool(self.parameters.data.get('automaticMode')) and (0 <= int(self.mapSize) <= 2)) and (int(self.numberOfComputers) == 0))):
			output += " : 1v1 :-"
			for value in playerStats.leaderboardData:
				if (str(playerStats.leaderboardData[value].matchType) == str(MatchType.ONES)):
					if self.parameters.data.get('showOnlyDetectedFactionPlayed') and (playerStats.user.faction != None):
						if (str(playerStats.leaderboardData[value].faction) == str(playerStats.user.faction)):
							output += self.getFactionString(playerStats.leaderboardData[value])
							break
					else:
						output += self.getFactionString(playerStats.leaderboardData[value])				

		if ((self.parameters.data.get('show2v2')) or ((bool(self.parameters.data.get('automaticMode')) and (3 <= int(self.mapSize) <= 4)) and (int(self.numberOfComputers) == 0))):
			output += " : 2v2 :-"
			for value in playerStats.leaderboardData:	
				if (str(playerStats.leaderboardData[value].matchType) == str(MatchType.TWOS)):
					if self.parameters.data.get('showOnlyDetectedFactionPlayed') and (playerStats.user.faction != None):
						if (str(playerStats.leaderboardData[value].faction) == str(playerStats.user.faction)):
							output += self.getFactionString(playerStats.leaderboardData[value])
							break
					else:
						output += self.getFactionString(playerStats.leaderboardData[value])

		if ((self.parameters.data.get('show3v3')) or ((bool(self.parameters.data.get('automaticMode')) and (5 <= int(self.mapSize) <= 6)) and (int(self.numberOfComputers) == 0))):
			output += " : 3v3 :-"
			for value in playerStats.leaderboardData:
				if (str(playerStats.leaderboardData[value].matchType) == str(MatchType.THREES)):
					if self.parameters.data.get('showOnlyDetectedFactionPlayed') and (playerStats.user.faction != None):
						if (str(playerStats.leaderboardData[value].faction) == str(playerStats.user.faction)):
							output += self.getFactionString(playerStats.leaderboardData[value])
							break
					else:
						output += self.getFactionString(playerStats.leaderboardData[value])


		# removed this because it was creating confusion
		#if (self.parameters.data.get('outputPlayerOverlayFiles')):
		#	self.savePlayer(playerStats)

		outputList = list(self.split_by_n(output, 500))
		if (self.parameters.data.get('showSteamProfile')):
			outputList.append("Steam profile " + str(playerStats.user.steamProfileAddress))

		print("output list " + str (outputList))

		return outputList

	def getFactionString(self, factionData):

		print("Building FactionString")
		output = ""
		
		try:
			if (factionData.nameShort):
				output += ":- " + str(factionData.nameShort)
			if (self.parameters.data.get('showWins')):
				output += " : Wins " + str(factionData.wins)
			if (self.parameters.data.get('showLosses')):
				output += " : Losses " + str(factionData.losses)
			if (self.parameters.data.get('showDisputes')):
				output += " : Disputes " + str(factionData.disputes)					
			if (self.parameters.data.get('showStreak')):
				output += " : Streak " + str(factionData.streak)
			if (self.parameters.data.get('showDrops')):
				output += " : Drops " + str(factionData.drops)
			if (self.parameters.data.get('showRank')):
				output += " : Rank " + str(factionData.rank)
			if (self.parameters.data.get('showLevel')):
				output += " : LvL " + str(factionData.rankLevel)
			if (self.parameters.data.get('showLastPlayed')):
				output += " : Last Played " + str(factionData.lastTime)
			if (self.parameters.data.get('showWLRatio')):
				output += " : W/L Ratio " + str(factionData.winLossRatio)
			output += " -"
		except Exception as e:
			logging.exception("In getFactionString")
			print(str(e))

		print("FactionString output : " + str(output))

		return output


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
			for item in axisTeamList:
				team1 += str(item.user.name) + str("<BR>") + "\n"
			for item in alliesTeamList:
				team2 += str(item.user.name) + str("<BR>") + "\n"
			
			htmlOutput = OverlayTemplates().overlayhtml.format(team1, team2)
			# create output overlay from template
			with open("overlay.html" , 'w') as outfile:
				outfile.write(htmlOutput)
			#check if css file exists and if not output the default template to folder
			if not (os.path.isfile("overlaystyle.css")):
				with open("overlaystyle.css" , 'w') as outfile:
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


		try:
			if (int(self.totalLosses) > 0):
				self.totalWLRatio = round(int(self.totalWins)/int(self.totalLosses), 2)

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

	def __init__(self, faction = '-1', matchType = '-1',name = '-1', nameShort = '-1',leaderboard_id = '-1', wins = '-1', losses = '-1', streak = '-1', disputes = '-1', drops = '-1', rank = '-1', rankLevel = '-1', lastMatch = '-1'):
		self.faction = str(faction).replace("-1", "None") 
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

	def __init__(self, profile_id = None, name = None, steamString = None, steamNumber = None, country = None, factionString = None, slot = None):
		self.profile_id = profile_id
		self.name = name
		self.steamString = steamString
		self.steamNumber = steamNumber
		self.country = country
		self.steamProfileAddress = None
		self.factionString = factionString
		self.faction = None
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
		output += "slot : " + str(self.slot) + "\n"
		return output

	def __repr__(self):
		return str(self)

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

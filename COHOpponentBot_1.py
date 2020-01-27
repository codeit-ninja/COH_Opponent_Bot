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
		if (message.lower() == "opponent") or (message.lower() == "place your bets") or (message.lower() == "!opponent") or (message.lower() == "!opp") or (message.lower() == "opp"):
			myHandleCOHlogFile = HandleCOHlogFile(self.parent.parameters)
			returnedList =  myHandleCOHlogFile.loadLog()
			if returnedList:
				for item in returnedList:
					self.parent.SendPrivateMessageToIRC(str(item))
		if (message.lower() == "test"):
			self.parent.SendPrivateMessageToIRC("I'm here! Pls give me mod to prevent twitch from autobanning me for spam if I have to send a few messages quickly.")
			self.parent.output.insert(END, "Oh hi again, I heard you in the " +self.channel[1:] + " channel.\n")

	def close(self):
		self.running = False
		print("Closing Channel " + str(self.channel) + " thread.")




class StatsRequest:
	def __init__(self, parameters, numberOfHumans, numberOfComputers, mapSize):
		self.parameters = parameters
		try:
			self.numberOfHumans = int(numberOfHumans)
			self.numberOfComputers = int(numberOfComputers)
			self.mapSize = mapSize
		except Exception as e:
			print(str(e))		
		self.numberOfPlayers = 1 # default value
		try:
			self.numberOfPlayers = int(numberOfHumans) + int(numberOfComputers)
		except Exception as e:
			print(str(e))
		self.parameters.load()
	
	def find_between(self, s, first, last ):
		try:
			start = s.index( first ) + len( first )
			end = s.index( last, start )
			return s[start:end]
		except ValueError:
			return ""

	def split_by_n(self, seq, n):
		'''A generator to divide a sequence into chunks of n units.'''
		while seq:
			yield seq[:n]
			seq = seq[n:]
	
	
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
			stats = cohStat(statdata, statnumber)
			print("coh Stats : " + str(stats))

			output = ""
			output += "Name : " + str(stats.user.name)
			if (self.parameters.data.get('showUserCountry')):
				output += " : (" + str(stats.user.country) + ")"

			if ((self.parameters.data.get('showBasic')) or (bool(self.parameters.data.get('automaticMode')) and (int(self.numberOfComputers) > 0))):
				output += " : Basic :-"
				for item in Faction:
					if (stats.ones.get(item).nameShort):
						output += ":- " + str(stats.ones.get(item).nameShort)
					if (self.parameters.data.get('showWins')):
						output += " : Wins " + str(stats.ones.get(item).wins)
					if (self.parameters.data.get('showLosses')):
						output += " : Losses " + str(stats.ones.get(item).losses)
					if (self.parameters.data.get('showDisputes')):
						output += " : Disputes " + str(stats.ones.get(item).disputes)					
					if (self.parameters.data.get('showStreak')):
						output += " : Streak " + str(stats.ones.get(item).streak)
					if (self.parameters.data.get('showDrops')):
						output += " : Drops " + str(stats.ones.get(item).drops)
					if (self.parameters.data.get('showRank')):
						output += " : Rank " + str(stats.ones.get(item).rank)
					if (self.parameters.data.get('showLevel')):
						output += " : LvL " + str(stats.ones.get(item).rankLevel)
					if (self.parameters.data.get('showLastPlayed')):
						output += " : Last Played " + str(stats.ones.get(item).lastTime)
					if (self.parameters.data.get('showWLRatio')):
						output += " : W/L Ratio " + str(stats.ones.get(item).winLossRatio)
					output += " -"

			if ((self.parameters.data.get('show1v1')) or ((bool(self.parameters.data.get('automaticMode')) and (0 <= int(self.mapSize) <= 2)) and (int(self.numberOfComputers) == 0))):
				output += " : 1v1 :-"
				for item in Faction:
					if (stats.ones.get(item).nameShort):
						output += ":- " + str(stats.ones.get(item).nameShort)
					if (self.parameters.data.get('showWins')):
						output += " : Wins " + str(stats.ones.get(item).wins)
					if (self.parameters.data.get('showLosses')):
						output += " : Losses " + str(stats.ones.get(item).losses)
					if (self.parameters.data.get('showDisputes')):
						output += " : Disputes " + str(stats.ones.get(item).disputes)					
					if (self.parameters.data.get('showStreak')):
						output += " : Streak " + str(stats.ones.get(item).streak)
					if (self.parameters.data.get('showDrops')):
						output += " : Drops " + str(stats.ones.get(item).drops)
					if (self.parameters.data.get('showRank')):
						output += " : Rank " + str(stats.ones.get(item).rank)
					if (self.parameters.data.get('showLevel')):
						output += " : LvL " + str(stats.ones.get(item).rankLevel)
					if (self.parameters.data.get('showLastPlayed')):
						output += " : Last Played " + str(stats.ones.get(item).lastTime)
					if (self.parameters.data.get('showWLRatio')):
						output += " : W/L Ratio " + str(stats.ones.get(item).winLossRatio)
					output += " -"

			if ((self.parameters.data.get('show2v2')) or ((bool(self.parameters.data.get('automaticMode')) and (3 <= int(self.mapSize) <= 4)) and (int(self.numberOfComputers) == 0))):
				output += " : 2v2 :-"
				for item in Faction:
					if (stats.ones.get(item).nameShort):
						output += ":- " + str(stats.ones.get(item).nameShort)
					if (self.parameters.data.get('showWins')):
						output += " : Wins " + str(stats.ones.get(item).wins)
					if (self.parameters.data.get('showLosses')):
						output += " : Losses " + str(stats.ones.get(item).losses)
					if (self.parameters.data.get('showDisputes')):
						output += " : Disputes " + str(stats.ones.get(item).disputes)					
					if (self.parameters.data.get('showStreak')):
						output += " : Streak " + str(stats.ones.get(item).streak)
					if (self.parameters.data.get('showDrops')):
						output += " : Drops " + str(stats.ones.get(item).drops)
					if (self.parameters.data.get('showRank')):
						output += " : Rank " + str(stats.ones.get(item).rank)
					if (self.parameters.data.get('showLevel')):
						output += " : LvL " + str(stats.ones.get(item).rankLevel)
					if (self.parameters.data.get('showLastPlayed')):
						output += " : Last Played " + str(stats.ones.get(item).lastTime)
					if (self.parameters.data.get('showWLRatio')):
						output += " : W/L Ratio " + str(stats.ones.get(item).winLossRatio)
				output += " -"

			if ((self.parameters.data.get('show3v3')) or ((bool(self.parameters.data.get('automaticMode')) and (5 <= int(self.mapSize) <= 6)) and (int(self.numberOfComputers) == 0))):
				output += " : 3v3 :-"
				for item in Faction:
					if (stats.ones.get(item).nameShort):
						output += ":- " + str(stats.ones.get(item).nameShort)
					if (self.parameters.data.get('showWins')):
						output += " : Wins " + str(stats.ones.get(item).wins)
					if (self.parameters.data.get('showLosses')):
						output += " : Losses " + str(stats.ones.get(item).losses)
					if (self.parameters.data.get('showDisputes')):
						output += " : Disputes " + str(stats.ones.get(item).disputes)					
					if (self.parameters.data.get('showStreak')):
						output += " : Streak " + str(stats.ones.get(item).streak)
					if (self.parameters.data.get('showDrops')):
						output += " : Drops " + str(stats.ones.get(item).drops)
					if (self.parameters.data.get('showRank')):
						output += " : Rank " + str(stats.ones.get(item).rank)
					if (self.parameters.data.get('showLevel')):
						output += " : LvL " + str(stats.ones.get(item).rankLevel)
					if (self.parameters.data.get('showLastPlayed')):
						output += " : Last Played " + str(stats.ones.get(item).lastTime)
					if (self.parameters.data.get('showWLRatio')):
						output += " : W/L Ratio " + str(stats.ones.get(item).winLossRatio)
				output += " -"

			outputList = list(self.split_by_n(output, 500))
			if (self.parameters.data.get('showSteamProfile')):
				outputList.append("Steam profile " + str(stats.user.steamProfileAddress))

			print("output list " + str (outputList))

			return outputList

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
						time.sleep(1) # allow an extra second for computer AI info to load if the game is a human vs ai game
						if (self.opponentBot):
							#trigger the opponent command in the opponentbot thread
							self.opponentBot.queue.put("OPPONENT")
				self.fileIndex = len(lines)
				self.event = threading.Event()
				self.event.wait(timeout = self.pollInterval)
			print ("File Monitoring Ended.\n")
		except Exception as e:
			print(str(e))
    
	def close(self):
		self.running = False
		self.event.set()

class HandleCOHlogFile:
	

	def __init__(self, parameters):
		self.parameters = parameters
		self.logPath = self.parameters.data['logPath']
		self.data = []
	
	def loadLog(self):
		print("In loadLog")
		with open(self.logPath, encoding='ISO-8859-1') as file:
			content = file.readlines()
		print(self.parameters.data['steamNumber'])
		steamNumberList = []
		humans = 0
		computers = 0
		eazyCPUCount = 0
		normalCPUCount = 0
		hardCPUCount = 0
		expertCPUCount = 0
		mapSize = 0
		for item in content:
			if ("match started") in item.lower():
				print (item)
				steamNumber = self.find_between(item, "steam/", "]")
				ranking = self.find_between(item, "ranking =","\n")
				if (str(steamNumber) == str(self.parameters.data['steamNumber'])):
					if(self.parameters.data.get('showOwn')):
						steamNumberList.append(steamNumber)
				else:
					steamNumberList.append(steamNumber)
			# set the number of players
			if ("GAME -- ***") in item:
				# need to reverse the string to get the humans bit out uniquely or other strings in the line can interfere with the parsing
				reverseString = item[::-1]
				humans = self.find_between(reverseString, "snamuH " , "(")
				print("humans  = " + str(humans) + "\n")
				computers = self.find_between(item, "Humans, ", " Computers")
			if ("PerformanceRecorder::StartRecording") in item:
					mapSize = self.find_between(item, "game size " , "\n")
			# clear the steam number list if a new game is found in the file
			if ("successful game start") in item:
				eazyCPUCount = 0
				normalCPUCount = 0
				hardCPUCount = 0
				expertCPUCount = 0
				humans = 0
				computers = 0
				mapSize = 0
				steamNumberList.clear()
			if ("Player CPU - Expert" in item):
				expertCPUCount += 1
			if ("Player CPU - Hard" in item):
				hardCPUCount += 1
			if ("Player CPU - Normal" in item):
				normalCPUCount += 1
			if ("Player CPU - Easy" in item):
				eazyCPUCount += 1
		
		# default backup player numbers - not used if file human and computers are legit numbers
		numberOfPlayers = len(steamNumberList)

		try:
			numberOfPlayers = int(float(humans)) + int(float(computers)) # the float then int removes change of value error
		except Exception as e:
			print (str(e))
		print("humans " + str(humans) +"\n")
		print("computers " + str(computers) +"\n")
		print("number of players " + str(numberOfPlayers) + "\n")
		print("map size" + str(mapSize) + "\n")
		try:
			if (int(computers) > 0):
				self.data.append("Game with " + str(computers) + " computer AI, ("+str(eazyCPUCount)+") Easy, ("+str(normalCPUCount)+") Normal, ("+str(hardCPUCount)+") Hard, ("+str(expertCPUCount)+") Expert.")
		except Exception as e:
			print(str(e))
		
		if (steamNumberList):
			print(steamNumberList)

			for item in steamNumberList:
				myStatRequest = StatsRequest(self.parameters, humans, computers, mapSize)
				try:
					statNumber = int(item)
					self.data = self.data + list(myStatRequest.returnStats(statNumber))
					#print("DATA OUTPUT " + str (self.data))
				except ValueError:
					print ("got a value error")						
		if self.data:
			return self.data
		else:
			return None
			
	
	def find_between(self, s, first, last ):
		try:
			start = s.index( first ) + len( first )
			end = s.index( last, start )
			return s[start:end]
		except ValueError:
			return ""

class cohStat:

	def __init__(self, statdata, steamNumber):
		self.user = cohUser()
		self.basic = { } 
		self.ones = { }
		self.twos = { }
		self.threes = { }

		statString = "/steam/"+str(steamNumber)

		if (statdata['result']['message'] == "SUCCESS"):

			if statdata['statGroups'][0]['members'][0]['alias']:
				for item in statdata['statGroups']:
					for value in item['members']:
						if (value.get('name') == statString):
							self.user = cohUser(profile_id = value.get('profile_id'), name = value.get('alias'), steamString = value.get('name'), country = value.get('country'))
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
						self.basic[Faction.US] = factionResult(name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 1:
						self.basic[Faction.WM] = factionResult(name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 2:
						self.basic[Faction.CW] = factionResult(name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 3:
						self.basic[Faction.PE] = factionResult(name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 4:
						self.ones[Faction.US] = factionResult(name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 5:
						self.ones[Faction.WM] = factionResult(name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 6:
						self.ones[Faction.CW] = factionResult(name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 7:
						self.ones[Faction.PE] = factionResult(name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 8:
						self.twos[Faction.US] = factionResult(name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 9:
						self.twos[Faction.WM] = factionResult(name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 10:
						self.twos[Faction.CW] = factionResult(name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 11:
						self.twos[Faction.PE] = factionResult(name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 12:
						self.threes[Faction.US] = factionResult(name = "Americans", nameShort = "US" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 13:
						self.threes[Faction.WM] = factionResult(name = "Wehrmacht", nameShort = "WM" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 14:
						self.threes[Faction.CW] = factionResult(name = "Commonwealth", nameShort = "CW" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
					if item.get('leaderboard_id') == 15:
						self.threes[Faction.PE] = factionResult(name = "Panzer Elite", nameShort = "PE" , leaderboard_id = item.get('leaderboard_id'), wins = item.get('wins'), losses = item.get('losses'), streak = item.get('streak'), disputes = item.get('disputes'), drops = item.get('drops'), rank = item.get('rank'), rankLevel = item.get('rankLevel'), lastMatch = item.get('lastMatchDate'))
	def __str__(self):
		output = str(self.user)
		output += "Basic\n"
		output += str(self.basic.get(Faction.US))+"\n"
		output += str(self.basic.get(Faction.WM))+"\n"
		output += str(self.basic.get(Faction.PE))+"\n"
		output += str(self.basic.get(Faction.CW))+"\n"		
		output += "1v1\n"
		output += str(self.basic.get(Faction.US))+"\n"
		output += str(self.basic.get(Faction.WM))+"\n"
		output += str(self.basic.get(Faction.PE))+"\n"
		output += str(self.basic.get(Faction.CW))+"\n"
		output += "2v2\n"
		output += str(self.basic.get(Faction.US))+"\n"
		output += str(self.basic.get(Faction.WM))+"\n"
		output += str(self.basic.get(Faction.PE))+"\n"
		output += str(self.basic.get(Faction.CW))+"\n"
		output += "3v3\n"
		output += str(self.basic.get(Faction.US))+"\n"
		output += str(self.basic.get(Faction.WM))+"\n"
		output += str(self.basic.get(Faction.PE))+"\n"
		output += str(self.basic.get(Faction.CW))+"\n"

		return output

class Faction(Enum):
		US = 0
		WM = 1
		CW = 2
		PE = 3


class factionResult:

	def __init__(self, name = '-1', nameShort = '-1',leaderboard_id = '-1', wins = '-1', losses = '-1', streak = '-1', disputes = '-1', drops = '-1', rank = '-1', rankLevel = '-1', lastMatch = '-1'):
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
			ts = int(self.lastMatch)
			self.lastTime = str(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
		except Exception as e:
			print(str(e))
		try:
			if (self.losses != 0):
				self.winLossRatio = str(round(self.wins/self.losses, 2))
			else:
				if(self.wins > 0):
					self.winLossRatio = "Unbeaten"
		except Exception as e:
			print(str(e))	


	def __str__(self):
		output = "Faction : " + str(self.name) +"\n"
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

class cohUser:

	def __init__(self, profile_id = -1, name = -1, steamString = -1, country = -1):
		self.profile_id = profile_id
		self.name = name
		self.steamString = steamString
		self.country = country
		self.steamProfileAddress = None
		try:
			self.steamProfileAddress = "https://steamcommunity.com/profiles/" + str(self.steamString).replace("/steam/", "")
		except Exception as e:
			print(str(e))

	
	def __str__(self):
		output = "Name : {0}\nSteam : {1}\nCountry : {2}\n".format(str(self.name),str(self.steamProfileAddress),str(self.country))
		return output

# to use this file without the GUI be sure to have the parameters file in the same directory and uncomment below
#myIRC = IRCClient()

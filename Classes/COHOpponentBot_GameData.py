import ctypes
import datetime
import html
from importlib.util import module_from_spec
import logging
#from multiprocessing import Process
from mem_edit import Process
import os
import re
import time

import ctypes
import ctypes.util
import functools
import logging
import platform
import struct
import sys


import pymem.exception
import pymem.memory
import pymem.process
import pymem.ressources.kernel32
import pymem.ressources.structure
import pymem.ressources.psapi
import pymem.thread
import pymem.pattern
import pymem

from pymem.ressources.structure import MODULEINFO

from pymem.process import base_module

from Classes.COHOpponentBot_Faction import Faction
from Classes.COHOpponentBot_MatchType import MatchType
from Classes.COHOpponentBot_Parameters import Parameters
from Classes.COHOpponentBot_Player import Player
from Classes.COHOpponentBot_ReplayParser import ReplayParser
from Classes.COHOpponentBot_StatsRequest import StatsRequest
from Classes.COHOpponentBot_OverlayTemplates import OverlayTemplates


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
		self.mapDescription = ""

		self.gameDescriptionString = ""
		#self.placeBetsString = ""

		self.pm = None
		self.baseAddress = None


	def getDataFromGame(self):
		try:
			
			print(str(self.getCOHMemoryAddress()))

			if not self.getCOHMemoryAddress():
				print("Returning from here")
				return False
			print("we got here")

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

			print("man power : " + str(mp))

			# access replay data in game memory
			replayData = self.pm.read_bytes(self.GetPtrAddr(self.baseAddress + cohrecReplayAddress, cohrecOffsets), 4000)

			# if the above executes without throwing an error then game is in progress.
			self.gameInProgress = True

			cohreplayparser = ReplayParser(parameters=self.parameters)
			cohreplayparser.data = bytearray(replayData)
			cohreplayparser.processData()
			#print(cohreplayparser)	

			self.gameStartedDate = cohreplayparser.localDate

			self.randomStart = cohreplayparser.randomStart

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

			self.mapDescription = cohreplayparser.mapDescription

			for item in cohreplayparser.playerList:
				username = item['name']
				factionString = item['faction']
				player = Player(name=username,factionString=factionString)
				self.playerList.append(player)

			statList = self.getStatsFromGame()

			#print(statList)

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

			try:

				channelName = self.parameters.data['channel']
				numberOfHumans = str(int(self.numberOfHumans))
				numberOfComputers = str(int(self.numberOfComputers))
				numberOfPlayers = str(int(self.numberOfPlayers))
				slots = str(int(self.slots))
				randomStart = str(int(self.randomStart))
				highResources = str(int(self.highResources))
				VPCount = str(int(self.VPCount))
				automatch = str(int(self.automatch))
				mapFullName = str(self.mapFullName)
				modName = str(self.modName)

				offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
				offset = offset / 60 / 60 * -1
				hours = offset
				hours_added = datetime.timedelta(hours = hours)
				UTC_corrected_start_time = self.gameStartedDate + hours_added

				gameStarted = str(UTC_corrected_start_time)
				message = "!start,{},{},{},{},{},{},{},{},{},{},{},{}".format(channelName,gameStarted,numberOfHumans,numberOfComputers,numberOfPlayers,slots,randomStart,highResources,VPCount,automatch,mapFullName,modName)
				for count , item in enumerate(self.playerList):
					steamNumber = ""
					if item.stats:
						steamNumber = item.stats.steamNumber
					else:
						steamNumber = item.name

					faction = ""
					if item.faction:
						faction = item.faction.name
					team = "0"
					if count >= (len(self.playerList)/2):
						team = "1"

					message += ",{},{},{}".format(str(steamNumber), str(faction), str(team))
				
				self.gameDescriptionString = message
				#self.placeBetsString = "!OppStartBets,{}".format(channelName)

			except Exception as e:
				logging.error("Problem Creating Game Description")
				logging.exception("Exception : ")
				logging.error(str(e))

			return True

		except Exception as e:
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
			#logging.info("Problem in GetPtrAddr")
			#logging.info(str(e))
			#logging.exception("Stack : ")
			#' Error routinely thrown when Pointer not found
			pass
	

	def getCOHMemoryAddress(self):
		
		try:
			self.pm = pymem.Pymem("RelicCOH.exe")
			self.baseAddress = self.pm.base_address

			
			self.cohRunning = True
			return True
		except Exception as e:
			self.cohRunning = False
			return False
			
	
	# rewrite function below to remove memory search.

	def getStatsFromGame(self):
		try:

			self.cohMemoryAddress = Process.get_pid_by_name('RelicCOH.exe')

			with Process.open_process(self.cohMemoryAddress) as p:
				steamNumberList = []
				steamNumberList.append(self.parameters.data['steamNumber']) # add default value incase it isn't found
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
			logging.exception("Exception : ")

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
		stat = None
		for steamNumber in steamNumberList:
			attempts = 0
			while attempts < 10:
				try:
					stat = statRequest.returnStats(str(steamNumber))
				except Exception as e:
					pass
				attempts += 1
				if not (stat['statGroups'][0]['members'][0]['alias'] == ""):
					statsList.append(stat)
					break
				else:
					time.sleep(5) # 5 second wait before retrying to get stats from server


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
		# removed separate message for steamProfile
		#if (self.parameters.data.get('showSteamProfile')):
		#	outputList.append("Steam profile " + str(player.stats.steamProfileAddress))
		return outputList

	def populateStringFormattingDictionary(self, player, overlay = False):
		prefixDiv = ""
		postfixDivClose = ""
		if overlay:
			prefixDiv = '<div class = "textVariables">'
			postfixDivClose = '</div>'
		stringFormattingDictionary = dict(self.parameters.stringFormattingDictionary)
		#loads default values from parameters into stringFormattingDictionary (Key: Value:None)
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
		steamprofile = ""
		cohstatslink = ""

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
			steamprofile = '<div class = "steamprofile">'
			cohstatslink = '<div class = "cohstatslink">'

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
			stringFormattingDictionary['$STEAMPROFILE$'] =  prefixDiv + steamprofile + str(player.stats.steamProfileAddress) + postfixDivClose + postfixDivClose
			stringFormattingDictionary['$COHSTATSLINK$'] =  prefixDiv + cohstatslink + str(player.stats.cohstatsLink) + postfixDivClose + postfixDivClose


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
		# set default values for flags and faction rank	
		imageOverlayFormattingDictionary['$LEVELICON$'] = '<div class = "rankimg"><img src="data:," alt></div>'
		levelIcon = "OverlayImages\\Ranks\\no_rank_yet.png"
		fileExists = os.path.isfile(levelIcon)
		if fileExists:
			imageOverlayFormattingDictionary['$LEVELICON$'] =  '<div class = "rankimg"><img src="{0}" ></div>'.format(levelIcon)

		imageOverlayFormattingDictionary['$FLAGICON$'] = '<div class = "countryflagimg"><img src="data:," alt></div>'
		defaultFlagIcon = "OverlayImages\\Flagssmall\\unknown_flag.png"
		fileExists = os.path.isfile(defaultFlagIcon)
		if fileExists:
			imageOverlayFormattingDictionary['$FLAGICON$'] = '<div class = "countryflagimg"><img src="{0}" ></div>'.format(defaultFlagIcon)

		if player.stats:
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

		return imageOverlayFormattingDictionary

	def sanatizeUserName(self, userName):
		try:
			userName = str(userName) # ensure type of string
			assert(len(userName) > 2) # ensure more than 2 characters
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
			logging.info("In sanitizeUserName username less than 2 chars")
			logging.exception("Exception : ")

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
						#logging.info ("Player team is AXIS")
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
			
			cssFilePath = self.parameters.data.get('overlayStyleCSSFilePath')
			#check if css file exists and if not output the default template to folder
			if not (os.path.isfile(cssFilePath)):
				with open(cssFilePath , 'w' , encoding="utf-8") as outfile:
					outfile.write(OverlayTemplates().overlaycss)

			htmlOutput = OverlayTemplates().overlayhtml.format(cssFilePath, team1, team2)
			# create output overlay from template
			with open("overlay.html" , 'w', encoding="utf-8") as outfile:
				outfile.write(htmlOutput)
				#logging.info("Creating Overlay File\n")

		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")

	@staticmethod
	def clearOverlayHTML():
		try:

			htmlOutput = OverlayTemplates().overlayhtml.format("","", "")
			# create output overlay from template
			with open("overlay.html" , 'w') as outfile:
				outfile.write(htmlOutput)
		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")

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

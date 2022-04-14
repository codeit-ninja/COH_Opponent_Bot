import json
import logging
import os
import ssl
import urllib
from Classes.COHOpponentBot_Parameters import Parameters
from Classes.COHOpponentBot_PlayerStat import PlayerStat


class StatsRequest:
	def __init__(self, parameters = None):
		if parameters:
			self.parameters = parameters
		else:
			self.parameters = Parameters()
		
		# Declare instance variables for storing data returned from server (nested List/Dictionary)
		self.userStatCache = None
		self.userMatchHistoryCache = None
		
	def returnStats(self, steam64ID):
		try:
			self.getUserStatFromServer(steam64ID)
			# Determine server response succeeded and use it to create PlayerStat object
			if (self.userStatCache['result']['message'] == "SUCCESS"):
				playerStat = PlayerStat(self.userStatCache, steam64ID)
				return playerStat
		except Exception as e:
			logging.error("Problem in returnStats")
			logging.error(str(e))
			logging.exception("Exception : ")

	def getUserStatFromServer(self, steam64ID):
		try:
			#check stat number is 17 digit and can be converted to int if not int
			steam64ID = str(steam64ID)
			stringLength = len(steam64ID)
			assert(stringLength == 17)
			assert(int(steam64ID))

			if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
				ssl._create_default_https_context = ssl._create_unverified_context

			response = urllib.request.urlopen(self.parameters.privatedata['relicServerProxyStatRequest']+str(steam64ID)).read()
			# Decode server response as a json into a nested list/directory and store as instance variable
			self.userStatCache = json.loads(response.decode('utf-8'))

		except Exception as e:
			logging.error("Problem in returnStats")
			logging.error(str(e))
			logging.exception("Exception : ")

	def getMatchHistoryFromServer(self, steam64ID):
		try:
			#check stat number is 17 digit and can be converted to int if not int
			steam64ID = str(steam64ID)
			stringLength = len(steam64ID)
			assert(stringLength == 17)
			assert(int(steam64ID))

			if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
				ssl._create_default_https_context = ssl._create_unverified_context

			response = urllib.request.urlopen(self.parameters.privatedata['relicServerProxyMatchHistoryRequest']+str(steam64ID)).read()
			# Decode server response as a json into a nested list/directory and store as instance variable
			self.userMatchHistoryCache = json.loads(response.decode('utf-8'))
			# Determine server response succeeded and use it to create PlayerStat object
			if (self.userMatchHistoryCache['result']['message'] == "SUCCESS"):
				# implement custom match history class and instatiate object here
				pass

		except Exception as e:
			logging.error("Problem in getMatchHistory")
			logging.error(str(e))
			logging.exception("Exception : ")

	def getPlayerWinLoseLastMatch(self, userSteam64Number):
		try:
			if self.userMatchHistoryCache:
				if userSteam64Number == None:
					userSteam64Number = self.parameters.data.get('steamNumber')
				if userSteam64Number:
					playersProfileID = self.getProfileIDFromProfilesBySteamNumber(userSteam64Number)
					print("userSteam64Number : "+ str(userSteam64Number))
					print("playersProfileID : "+ str(playersProfileID))
					mostRecentMatch = self.getMostRecentMatch()
					if mostRecentMatch:
						for item in mostRecentMatch['matchhistoryreportresults']:
							if str(playersProfileID) == str(item['profile_id']):
								if str(item.get('resulttype')) == '1':
									return True
								else:
									return False

		except Exception as e:
			logging.error("Problem in getMostRecentMatch")
			logging.error(str(e))
			logging.exception("Exception : ")
			return None

	def getMostRecentMatch(self):
		if (self.userMatchHistoryCache):
			matchHistoryStatsList = list()
			try:
				for item in self.userMatchHistoryCache.get('matchHistoryStats'):
					matchHistoryStatsList.append(item)
				matchHistoryStatsList = sorted(matchHistoryStatsList, key=lambda d: d['completiontime'], reverse=True)
				if matchHistoryStatsList:
					return matchHistoryStatsList[0]
			except Exception as e:
				logging.error("Problem in getMostRecentMatch")
				logging.error(str(e))
				logging.exception("Exception : ")

	def getSteamNumberFromProfilesByProfileID(self, profileID):
		try:
			if self.userMatchHistoryCache:
				if (self.userMatchHistoryCache['result']['message'] == "SUCCESS"):
					for item in self.userMatchHistoryCache['profiles']:
						if (str(profileID) == item['profile_id']):
							# name should look like this string "/steam/76561198416060362"
							return str(item['name']).replace("/steam/", "")
		except Exception as e:
			logging.error("Problem in getSteamNumberFromProfilesByProfileID")
			logging.error(str(e))
			logging.exception("Exception : ")

	def getProfileIDFromProfilesBySteamNumber(self, steam64ID):
		try:
			if self.userMatchHistoryCache:
				if (self.userMatchHistoryCache['result']['message'] == "SUCCESS"):
					for item in self.userMatchHistoryCache['profiles']:
						# name should look like this string "/steam/76561198416060362"
						if (str(steam64ID) == str(item['name']).replace("/steam/", "")):
							return item['profile_id']
		except Exception as e:
			logging.error("Problem in getProfileIDFromProfilesBySteamNumber")
			logging.error(str(e))
			logging.exception("Exception : ")			

	def __str__(self) -> str:
		output = ""
		output += "User Stat Cache : \n"
		output += json.dumps(self.userStatCache, indent=4, sort_keys=True)
		output += "\nUser Match History Cache :\n"
		output += json.dumps(self.userMatchHistoryCache, indent=4, sort_keys=True)
		return output
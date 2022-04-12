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
			logging.error("Problem in returnStats")
			logging.error(str(e))
			logging.exception("Exception : ")
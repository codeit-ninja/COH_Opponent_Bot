# This file contains parameters kept separate from the main files due to their sensitive nature.
try:
	import ctypes.wintypes # for finding the windows home directory will throw error on linux
except Exception as e:
	print(str(e))
import json # for loading and saving data to a convenient json file
import os.path
import ssl # required for urllib certificates
import requests
import urllib.request # more for loadings jsons from urls
import string
import sys

class parameters:
	
	def __init__(self):

		self.data = {}
		self.privatedata = {}

		#IRC connection variables
		self.privatedata['IRCnick'] = 'COHopponentBot'									#The default username used to connect to IRC.
		self.privatedata['IRCpassword'] = "oauth:6lwp9xs2oye948hx2hpv5hilldl68g"		#The default password used to connect to IRC using the username above. # yes I know you shouldn't post oauth codes to git hub but I don't think this matter because this is a multi-user throw away account... lets see what happens.
		self.privatedata['IRCserver'] = 'irc.twitch.tv'
		self.privatedata['IRCport'] = 6667
		self.privatedata['adminUserName'] = 'xereborn'
		self.privatedata['relicServerProxy'] = 'https://xcoins.co.uk/secreturl.php?steamUserID='

		#custom display toggles
		# what to show in stat string constuct
		
		self.data['botUserName'] = ""
		self.data['botOAuthKey'] = ""

		self.data['showOwn'] = False

		self.data['showTotalWins'] = False
		self.data['showTotalLosses'] = False
		self.data['showTotalWLRatio'] = False

		self.data['automaticMode'] = True

		self.data['filePollInterval'] = 10

		self.data['showBasic'] = False
		self.data['show1v1'] = True
		self.data['show2v2'] = False
		self.data['show3v3'] = False

		self.data['showWins'] = False
		self.data['showLosses'] = False
		self.data['showDisputes'] = False
		self.data['showStreak'] = False
		self.data['showDrops'] = False
		self.data['showRank'] = True
		self.data['showLevel'] = True
		self.data['showLastPlayed'] = False

		self.data['showWLRatio'] = False

		self.data['showUserCountry'] = True
		self.data['showSteamProfile'] = True

		self.data['automaticTrigger'] = False
		

		#your personal steam number
		self.data['steamNumber'] = 'EnterYourSteamNumberHere (17 digits)'		#eg 76561197970959399 # alter this value to prevent the program from picking your steam info instead of your opponents.
		self.data['channel'] = 'EnterYourChannelNameHere'#'xereborn'

		#location of the COH log file
		CSIDL_PERSONAL = 5       # My Documents
		SHGFP_TYPE_CURRENT = 0   # Get current, not default value


		# the following is windows specific code using ctypes.win will not compile on linux
		try:
			buf= ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
			ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
			
			logPath = buf.value + "\\My Games\\Company of Heroes Relaunch\\warnings.log"
			self.data['logPath'] = logPath
			# attempt to extract users steamNumber from logfile
			if (os.path.isfile(logPath)):
				print("the logPath file was found")
				try:
					with open(self.data['logPath'], encoding='ISO-8859-1') as file:
						content = file.readlines()
					for item in content:
						if ("RLINK -- Found profile:") in item:
							steamNumber = self.find_between(item, "steam/", "\n")
							#print("Steam Number from Log : " + str(steamNumber))
							self.data['steamNumber'] = steamNumber
				except Exception as e:
					print(str(e))
		except Exception as e:
			print(str(e))
		#attempt to get userName from steamNumber
		try:
			statString = "/steam/" + str(self.data['steamNumber'])
			if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
				ssl._create_default_https_context = ssl._create_unverified_context
			response = urllib.request.urlopen(str(self.privatedata.get('relicServerProxy'))+str(self.data['steamNumber'])).read()
			statdata = json.loads(response.decode('utf-8'))
			#print(statdata)
			if (statdata['result']['message'] == "SUCCESS"):
				print ("statdata load succeeded")
				if statdata['statGroups'][0]['members'][0]['alias']:
					for item in statdata['statGroups']:
						for value in item['members']:
							if (value['name'] == statString):
								self.data['channel'] = value['alias']
		except Exception as e:
			print(str(e))
		
	
	def load(self):
		try:
			if (os.path.isfile('data.json')):
				with open('data.json') as json_file:
					data = json.load(json_file)
					success = self.checkDataIntegrity(data)
					if success:
						self.data = data
						print("data loaded sucessfully")
					else:
						print("data not loaded")
		except Exception as e:
			print("Problem in load")
			print(str(e))

	def checkDataIntegrity(self, data):
		success = True
		for key, value in data.items():
			if key not in self.data:
				success = False
		return success

		
	def save(self):
		try:
			with open('data.json' , 'w') as outfile:
				json.dump(self.data, outfile)
		except Exception as e:
			print("Problem in save")
			print(str(e))
			
	def find_between(self, s, first, last ):
		try:
			start = s.index( first ) + len( first )
			end = s.index( last, start )
			return s[start:end]
		except ValueError:
			return ""	
	


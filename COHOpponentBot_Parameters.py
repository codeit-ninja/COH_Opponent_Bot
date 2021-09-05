import logging
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
import winreg #  to get steamlocation automatically


class Parameters:
	
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

		self.data['whisperTo'] = "xcoinbetbot"

		self.data['showOwn'] = False

		self.data['logErrorsToFile'] = True

		self.data['filePollInterval'] = 10

		self.data['showSteamProfile'] = False

		self.data['automaticTrigger'] = True

		self.data['writeIWonLostInChat'] = True

		self.data['writePlaceYourBetsInChat'] = False

		self.data['clearOverlayAfterGameOver'] = True

		self.data['logPath'] = ""
		self.data['temprecReplayPath'] = ""

		self.data['steamFolder'] = ""
		self.data['cohPath'] = ""
		self.data['cohUCSPath'] = ""

		self.data['useOverlayPreFormat'] = True
		self.data['overlayStringPreFormatLeft'] = "$NAME$ ($FLAGICON$) $LEVELICON$ $RANK$ $FACTIONICON$"
		self.data['mirrorLeftToRightOverlay'] = True
		self.data['overlayStringPreFormatRight'] = "$FACTIONICON$ $RANK$ $LEVELICON$ ($FLAGICON$) $NAME$"
		self.data['overlayStyleCSSFilePath'] = "overlaystyle.css"

		self.data['useCustomPreFormat'] = True
		self.data['customStringPreFormat'] = "$NAME$ : $COUNTRY$ : $FACTION$ : $MATCHTYPE$ Rank $RANK$ : lvl $LEVEL$ : $STEAMPROFILE$"
		

		#your personal steam number
		self.data['steamNumber'] = 'EnterYourSteamNumberHere (17 digits)'		#eg 76561197970959399 # alter this value to prevent the program from picking your steam info instead of your opponents.
		self.data['steamAlias'] = 'EnterYourSteamAliasHere'# eg 'xereborn'
		self.data['channel'] = 'EnterYourChannelNameHere'# eg 'xereborn'

		#location of the COH log file
		CSIDL_PERSONAL = 5       # My Documents
		SHGFP_TYPE_CURRENT = 0   # Get current, not default value


		# the following is windows specific code using ctypes.win will not compile on linux
		try:
			buf= ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
			ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
			
			logPath = buf.value + "\\My Games\\Company of Heroes Relaunch\\warnings.log" #
			self.data['logPath'] = logPath
			# attempt to extract users steamNumber from logfile
			if (os.path.isfile(logPath)):
				logging.info("the logPath file was found")
				try:
					with open(self.data['logPath'], encoding='ISO-8859-1') as file:
						content = file.readlines()
					for item in content:
						if ("RLINK -- Found profile:") in item:
							steamNumber = self.find_between(item, "steam/", "\n")
							self.data['steamNumber'] = steamNumber
				except Exception as e:
					logging.error(str(e))
					logging.exception("Exception : ")
		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")


		try:
			if self.data['cohPath'] == "":
				#connecting to key in registry
				try:
					#64 bit windows
					access_registry = winreg.ConnectRegistry(None,winreg.HKEY_LOCAL_MACHINE)
					access_key = winreg.OpenKey(access_registry,r"SOFTWARE\WOW6432Node\Valve\Steam")
					steam_path = winreg.QueryValueEx(access_key, "InstallPath")
					if steam_path:
						self.data['steamFolder'] = steam_path[0]
				except:
					pass

				try:
					#32 bit windows
					access_registry = winreg.ConnectRegistry(None,winreg.HKEY_LOCAL_MACHINE)
					access_key = winreg.OpenKey(access_registry,r"SOFTWARE\Valve\Steam")
					steam_path = winreg.QueryValueEx(access_key, "InstallPath")
					if steam_path:
						self.data['steamFolder'] = steam_path[0]
				except:
					pass

		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")

		#get cohLocation
		#print(self.data['steamFolder'])

		filePath = self.data['steamFolder'] + "\\steamapps\\libraryfolders.vdf"
		steamlibraryBases = []

		if self.data['steamFolder']:
			steamlibraryBases.append(self.data['steamFolder'])

		try:
			if (os.path.isfile(filePath)):
				with open(filePath) as f:
					for line in f:
						words = line.split()
						#print(words)
						try:
							number = words[0].replace('"',"")
							location = " ".join(words[1:]).replace('"',"")
							#print(number.strip())
							number = int(number.strip())
							if type(number) is int:
								#print(location)
								steamlibraryBases.append(location)
						except Exception as e:
							pass

			print(steamlibraryBases)

			for steamBase in steamlibraryBases:
				cohPath = steamBase + "\\steamapps\\common\\Company of Heroes Relaunch\\RelicCOH.exe"
				if (os.path.isfile(cohPath)):
					self.data['cohPath'] = cohPath
					ucsPath = steamBase + "\\steamapps\\common\\Company of Heroes Relaunch\\CoH\\Engine\\Locale\\English\\RelicCOH.English.ucs"
					if (os.path.isfile(ucsPath)):
						self.data['cohUCSPath'] = ucsPath

		except Exception as e:
			logging.error("Problem in load")
			logging.error(str(e))
			logging.exception("Exception : ")



		try:
			self.data['temprecReplayPath'] = self.data.get('logPath').replace("warnings.log" , "playback\\temp.rec")
		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")
		
		
		#attempt to get userName from steamNumber
		try:
			statString = "/steam/" + str(self.data['steamNumber'])
			if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
				ssl._create_default_https_context = ssl._create_unverified_context
			response = urllib.request.urlopen(str(self.privatedata.get('relicServerProxy'))+str(self.data['steamNumber'])).read()
			statdata = json.loads(response.decode('utf-8'))
			#print(statdata)
			if (statdata['result']['message'] == "SUCCESS"):
				logging.info ("statdata load succeeded")
				if statdata['statGroups'][0]['members'][0]['alias']:
					for item in statdata['statGroups']:
						for value in item['members']:
							if (value['name'] == statString):
								self.data['channel'] = value['alias']
								self.data['steamAlias'] = value['alias']
		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")

		self.stringFormattingDictionary = {}
		self.stringFormattingDictionary['$NAME$'] = None
		self.stringFormattingDictionary['$FACTION$'] = None
		self.stringFormattingDictionary['$COUNTRY$'] = None
		self.stringFormattingDictionary['$TOTALWINS$'] = None
		self.stringFormattingDictionary['$TOTALLOSSES$'] = None
		self.stringFormattingDictionary['$TOTALWLRATIO$'] = None

		self.stringFormattingDictionary['$WINS$'] = None
		self.stringFormattingDictionary['$LOSSES$'] = None
		self.stringFormattingDictionary['$DISPUTES$'] = None
		self.stringFormattingDictionary['$STREAK$'] = None
		self.stringFormattingDictionary['$DROPS$'] = None
		self.stringFormattingDictionary['$RANK$'] = None
		self.stringFormattingDictionary['$LEVEL$'] = None
		self.stringFormattingDictionary['$WLRATIO$'] = None

		self.stringFormattingDictionary['$MATCHTYPE$'] = None
		self.stringFormattingDictionary['$STEAMPROFILE$'] = None

		self.imageOverlayFormattingDictionary = {}
		self.imageOverlayFormattingDictionary['$FLAGICON$'] = None
		self.imageOverlayFormattingDictionary['$FACTIONICON$'] = None
		self.imageOverlayFormattingDictionary['$LEVELICON$'] = None

		#finally call load at end of Initialization
		self.load()
 
		
	
	def load(self, filePath = "data.json"):
		try:
			if (os.path.isfile(filePath)):
				with open(filePath) as json_file:
					data = json.load(json_file)
					success = self.checkDataIntegrity(data)
					if success:
						self.data = data
						logging.info("data loaded sucessfully")
					else:
						logging.info("data not loaded")
		except Exception as e:
			logging.error("Problem in load")
			logging.error(str(e))
			logging.exception("Exception : ")

	def checkDataIntegrity(self, data):
		success = True
		for key, value in data.items():
			if self.data.get(key) == None:
				success = False
				break
		return success

		
	def save(self, filePath = "data.json"):
		try:
			with open(filePath , 'w') as outfile:
				json.dump(self.data, outfile)
		except Exception as e:
			logging.error("Problem in save")
			logging.error(str(e))
			logging.exception("Exception : ")
			
	def find_between(self, s, first, last ):
		try:
			start = s.index( first ) + len( first )
			end = s.index( last, start )
			return s[start:end]
		except ValueError:
			return ""	
	


VersionNumber = "2.0"
BuildDate = "17-Apr-2021"

import COHOpponentBot_Parameters
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import re
import os.path
import COHOpponentBot_Bot
import threading
from queue import Queue # to talk to the threads
from tkinter import *
from tkinter.ttk import *
from tkinter import ttk
import base64
import os
from icon import Icon

import logging # For logging information and warnings about opperation errors


class COHBotGUI:

	def __init__(self):

		self.ircClient = None #reference to the opponentbot

		self.parameters = COHOpponentBot_Parameters.Parameters()

		self.master = tk.Tk()

		self.optionsMenu = None

		self.style = Style()
		self.master.title("COH Opponent Bot")

		#checkbox string construction option bools

		self.showOwn = IntVar(value = int(bool(self.parameters.data.get('showOwn'))))
		self.showSteamProfile = IntVar(value = int(bool(self.parameters.data.get('showSteamProfile'))))
		self.automaticTrigger = IntVar(value = int(bool(self.parameters.data.get('automaticTrigger'))))
		self.writeIWonLostInChat = IntVar(value = int(bool(self.parameters.data.get('writeIWonLostInChat'))))
		self.writePlaceYourBetsInChat = IntVar(value = int(bool(self.parameters.data.get('writePlaceYourBetsInChat'))))
		self.clearOverlayAfterGameOver = IntVar(value = int(bool(self.parameters.data.get('clearOverlayAfterGameOver'))))
		self.useOverlayPreFormat = IntVar(value = int(bool(self.parameters.data.get('useOverlayPreFormat'))))
		self.mirrorLeftToRightOverlay = IntVar(value = int(bool(self.parameters.data.get('mirrorLeftToRightOverlay'))))
		self.customOverlayPreFormatStringLeft = StringVar()
		self.customOverlayPreFormatStringRight = StringVar()
		self.useCustomPreFormat = IntVar(value = int(bool(self.parameters.data.get('useCustomPreFormat'))))
		self.customChatOutputPreFormatString = StringVar()
		self.logErrorsToFile = IntVar(value = int(bool(self.parameters.data.get('logErrorsToFile'))))
		#self.steamName = 

		#Start or stop logging based on the self.logErrorsToFile variable
		self.toggleLogErrorsToFile()
		

		self.customOverlayEntry = None
		self.customChatOutputEntry = None


		tk.Label(self.master, text="Twitch Channel").grid(row=0, sticky=tk.W)
		tk.Label(self.master, text="Steam Name").grid(row=1, sticky=tk.W)
		tk.Label(self.master, text="Steam64ID Number").grid(row=2, sticky=tk.W)
		tk.Label(self.master, text="warning.log path").grid(row=3, sticky=tk.W)
		tk.Label(self.master, text="RelicCOH.exe path").grid(row=4, sticky=tk.W)

		self.entryTwitchChannel = tk.Entry(self.master, width = 70)
		self.entrySteamName = tk.Entry(self.master, width = 70)
		self.entrySteam64IDNumber = tk.Entry(self.master, width = 70)
		self.entryWarningLogPath = tk.Entry(self.master, width = 70)
		self.entryRelicCOHPath = tk.Entry(self.master, width = 70)

		self.entryTwitchChannel.grid(row=0, column=1)
		self.entrySteamName.grid(row=1, column=1)
		self.entrySteam64IDNumber.grid(row=2, column=1)
		self.entryWarningLogPath.grid(row=3, column=1)
		self.entryRelicCOHPath.grid(row=4, column=1)

		steamName = self.parameters.data.get('steamAlias')

		if (steamName):
			self.entrySteamName.insert(0, str(steamName))

		logPath = self.parameters.data.get('logPath')

		if (logPath):
			self.entryWarningLogPath.insert(0, str(logPath))

		cohPath = self.parameters.data.get('cohPath')

		if (cohPath):
			self.entryRelicCOHPath.insert(0, str(cohPath))
		

		steamNumber = "enter your steam number"

		if self.parameters.data.get('steamNumber'):
			steamNumber = self.parameters.data.get('steamNumber')

		self.entrySteam64IDNumber.insert(0, steamNumber)

		twitchName = "enter your twitch channel name"

		if self.parameters.data.get('channel'):
			twitchName = self.parameters.data.get('channel')

		self.entryTwitchChannel.insert(0, twitchName)

		self.entryTwitchChannel.config(state = "disabled")
		self.entrySteamName.config(state= "disabled")
		self.entrySteam64IDNumber.config(state = "disabled")
		self.entryWarningLogPath.config(state = "disabled")
		self.entryRelicCOHPath.config(state = "disabled")

		self.buttonTwitchChannel = tk.Button(self.master, text = "edit", command = lambda: self.editTwitchName())
		self.buttonTwitchChannel.config(width = 10)
		self.buttonTwitchChannel.grid(row=0, column =2)
		self.buttonSteamName = tk.Button(self.master, text = "edit", command = lambda: self.editSteamName())
		self.buttonSteamName.config(width = 10)
		self.buttonSteamName.grid(row=1, column =2)
		self.buttonSteam64IDNumber = tk.Button(self.master, text = "edit", command = lambda: self.editSteamNumber())
		self.buttonSteam64IDNumber.config(width = 10)
		self.buttonSteam64IDNumber.grid(row=2, column=2)        
		self.buttonLocateWarningLog = tk.Button(self.master, text = "browse", command = lambda : self.locateWarningLog() )
		self.buttonLocateWarningLog.config(width = 10)
		self.buttonLocateWarningLog.grid(row=3, column=2)
		self.cohBrowseButton = tk.Button(self.master, text = "browse", command = lambda : self.locateCOH() )
		self.cohBrowseButton.config(width = 10)
		self.cohBrowseButton.grid(row=4, column=2)
		self.buttonOptions = tk.Button(self.master, text = "options", command = self.createOptionsMenu )
		self.buttonOptions.config(width = 10)
		self.buttonOptions.grid(row=5, column=2)

		self.ircClient = None
		self.automaticFileMonitor = None
		self.automaticMemoryMonitor = None

		self.style.configure('W.TButton', font = 'calibri', size = 10, foreground = 'red')
		self.connectButton = ttk.Button(self.master, text = "Connect",style ='W.TButton', command = lambda : self.connectIRC(self.ircClient))

		self.connectButton.grid(row=6, columnspan = 3, sticky = tk.W+tk.E+tk.N+tk.S, padx=30,pady=30)

		self.consoleDisplayBool = IntVar()

		self.testButton = tk.Button(self.master, text = "Test Output", command = self.testStats )
		self.testButton.config(width = 10)
		self.testButton.grid(row =8, column=2 ,sticky=tk.E)
		self.testButton.config(state = DISABLED)

		self.clearOverlayButton = tk.Button(self.master, text = "Clear Overlay", command = COHOpponentBot_Bot.GameData.clearOverlayHTML)
		self.clearOverlayButton.config(width = 10)
		self.clearOverlayButton.grid(row = 9, column=2, sticky=tk.E)



		tk.Label(self.master, text="Console Output:").grid(row=10, sticky=tk.W)
		# create a Text widget
		self.txt = tk.Text(self.master)
		self.txt.grid(row=11, columnspan=3, sticky="nsew", padx=2, pady=2)

		# create a Scrollbar and associate it with txt
		scrollb = ttk.Scrollbar(self.master, command=self.txt.yview)
		scrollb.grid(row=11, column=4, sticky='nsew')
		self.txt['yscrollcommand'] = scrollb.set

		# import icon base64 data from separate icon.py file
		icon = Icon.icon

		icondata = base64.b64decode(icon)
		## The temp file is icon.ico
		tempFile= "icon.ico"
		iconfile= open(tempFile,"wb")
		## Extract the icon
		iconfile.write(icondata)
		iconfile.close()
		self.master.wm_iconbitmap(tempFile)
		## Delete the tempfile
		os.remove(tempFile)

		#Add File and Help menubar
		self.menubar = Menu(self.master)
		self.fileMenu = Menu(self.menubar, tearoff=0)
		self.fileMenu.add_command(label="Load Preferences", command=self.loadPreferences)
		self.fileMenu.add_command(label="Save Preferences", command=self.savePreferences)
		self.fileMenu.add_separator()
		self.fileMenu.add_command(label="Exit", command=self.master.quit)
		self.menubar.add_cascade(label="File", menu=self.fileMenu)

		self.helpmenu = Menu(self.menubar, tearoff=0)
		self.helpmenu.add_command(label="About...", command=self.showAboutDialogue)
		self.menubar.add_cascade(label="Help", menu=self.helpmenu)

		self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

		self.master.config(menu=self.menubar)

		self.master.mainloop()


	def savePreferences(self):
		files = [('Json', '*.json'),('All Files', '*.*')] 
		workingDirectory = os.getcwd()
		print("workingDirectory : {}".format(workingDirectory))
		self.master.filename =  tk.filedialog.asksaveasfilename(initialdir = workingDirectory , initialfile =  "data.json" ,title = "Save Preferences File",filetypes = files)
		logging.info("File Path : " + str(self.master.filename))
		print("File Path : " + str(self.master.filename))
		if(self.master.filename):
			pattern = re.compile(r"\u20A9|\uFFE6|\u00A5|\uFFE5") # replaces both Won sign varients for korean language and Yen symbol for Japanese language paths
			theFilename = re.sub(pattern, "/", self.master.filename)
			self.parameters.save(theFilename)

	def loadPreferences(self):
		files = [('Json', '*.json'),('All Files', '*.*')] 
		workingDirectory = os.getcwd()
		print("workingDirectory : {}".format(workingDirectory))
		self.master.filename =  tk.filedialog.askopenfilename(initialdir = workingDirectory , initialfile =  "data.json" ,title = "Load Preferences File",filetypes = files)
		logging.info("File Path : " + str(self.master.filename))
		print("File Path : " + str(self.master.filename))
		if(self.master.filename):
			pattern = re.compile(r"\u20A9|\uFFE6|\u00A5|\uFFE5") # replaces both Won sign varients for korean language and Yen symbol for Japanese language paths
			theFilename = re.sub(pattern, "/", self.master.filename)
			self.parameters.load(theFilename)
			self.refreshParameters()

	def refreshParameters(self):
		self.parameters = COHOpponentBot_Parameters.Parameters()

	def showAboutDialogue(self):
		InformationString = "Version : {}\n\nBuild Date : {}\n\nCreated by : XcomReborn\n\n Special thanks : AveatorReborn".format(VersionNumber, BuildDate)
		tk.messagebox.showinfo("Information", InformationString)

	def doNothing(self):
		pass

	def createOptionsMenu(self):
		if not self.optionsMenu:
			self.optionsMenu = tk.Toplevel(self.master)
			self.optionsMenu.protocol("WM_DELETE_WINDOW", self.on_close_options)
			self.optionsMenu.title("Chat Display Options")

			self.frameReportOptions = tk.LabelFrame(self.optionsMenu, padx =5, pady=5)
			self.frameReportOptions.grid()
			self.framePlayerInfo = tk.LabelFrame(self.optionsMenu, text = "Player Info", padx =5, pady=5)
			self.framePlayerInfo.grid(sticky=tk.N+W+E+S)

			self.frameAutoTrigger = tk.LabelFrame(self.optionsMenu, text = "Auto Trigger", padx =5, pady=5)
			self.frameAutoTrigger.grid(sticky=tk.N+W+E)

			self.frameCustomFormat = tk.LabelFrame(self.optionsMenu, text = "Custom Format", padx =5, pady=5)
			self.frameCustomFormat.grid( sticky=tk.N+W+E+S) 

			self.frameCSSFilePath = tk.LabelFrame(self.optionsMenu, text="CSS Format File", padx=5, pady=5)
			self.frameCSSFilePath.grid(sticky=tk.N+W+E+S)  

			self.frameOptionalBotCredentials = tk.LabelFrame(self.optionsMenu, text= "Optional Bot Credentials", padx= 5, pady=5)
			self.frameOptionalBotCredentials.grid(sticky=tk.N+W+E+S)

			self.frameMisc = tk.LabelFrame(self.optionsMenu, text = "Misc", padx =5, pady=5)
			self.frameMisc.grid( sticky = tk.N+W+E+S)   



			tk.Label(self.frameReportOptions, text="Report Options").grid()


			self.checkUseCustomChatOutput = tk.Checkbutton(self.frameCustomFormat, text="Use Custom Chat Output Pre-Format", variable=self.useCustomPreFormat, command = self.toggleUseCustomPreFormat)
			self.checkUseCustomChatOutput.grid(sticky=tk.W)

			self.customChatOutputEntry = tk.Entry(self.frameCustomFormat, width = 70, textvariable = self.customChatOutputPreFormatString, validate="focusout", validatecommand=self.saveCustomChatPreFormat)
			self.customChatOutputEntry.grid(sticky = tk.W)
			if self.parameters.data.get('customStringPreFormat'):
				self.customChatOutputPreFormatString.set(self.parameters.data.get('customStringPreFormat'))
			#self.toggleUseCustomPreFormat()

			self.frameCustomChatVariables = tk.LabelFrame(self.frameCustomFormat, text = "Custom Chat/Overlay Text Variables", padx= 5, pady=5)
			self.frameCustomChatVariables.grid(sticky=tk.N+W+E)

			self.stringFormatLabels = []
			self.myLabelFrames = []
			#create all custom variables from dictionary keys
			columnNumber = 0
			rowNumber = 0
			for key, value in self.parameters.stringFormattingDictionary.items():

				myLabelFrame = tk.LabelFrame(self.frameCustomChatVariables, padx =5, pady=5)
				self.frameCustomChatVariables.columnconfigure(columnNumber, minsize = 100)
				self.myLabelFrames.append(myLabelFrame)
				myLabel = tk.Label(myLabelFrame, text=str(key))
				myLabel.grid()
				
				myLabelFrame.grid(row = rowNumber,column = columnNumber, sticky = tk.N + W + E)
				columnNumber += 1
				if columnNumber > 3:
					rowNumber += 1
					columnNumber = 0
				self.stringFormatLabels.append(myLabel)

			self.frameOverlayImageIcons = tk.LabelFrame(self.frameCustomFormat, text = "HTML Overlay Only Image Icons", padx= 5, pady=5)
			self.frameOverlayImageIcons.grid(sticky=tk.N+W+E)

			#create all custom icon variables from dictionary keys
			columnNumber = 0
			rowNumber = 0
			for key, value in self.parameters.imageOverlayFormattingDictionary.items():

				myLabelFrame = tk.LabelFrame(self.frameOverlayImageIcons, padx =5, pady=5)
				self.frameOverlayImageIcons.columnconfigure(columnNumber, minsize = 100)
				self.myLabelFrames.append(myLabelFrame)
				myLabel = tk.Label(myLabelFrame, text=str(key))
				myLabel.grid()
				
				myLabelFrame.grid(row = rowNumber,column = columnNumber, sticky = tk.N + W + E)
				columnNumber += 1
				if columnNumber > 3:
					rowNumber += 1
					columnNumber = 0
				self.stringFormatLabels.append(myLabel)

			self.checkUseCustomOverlayString = tk.Checkbutton(self.frameCustomFormat, text="Use Custom HTML Overlay Pre-Format", variable=self.useOverlayPreFormat, command = self.toggleUseOverlayPreFormat)
			self.checkUseCustomOverlayString.grid(sticky=tk.W)

			
			

			
			self.customOverlayEntryLeft = tk.Entry(self.frameCustomFormat, width = 70, textvariable = self.customOverlayPreFormatStringLeft, validate="focusout", validatecommand=self.saveCustomOverlayPreFormatLeft)
			
			if self.parameters.data.get('overlayStringPreFormatLeft'):
				self.customOverlayPreFormatStringLeft.set(self.parameters.data.get('overlayStringPreFormatLeft'))
			
			self.customOverlayEntryRight = tk.Entry(self.frameCustomFormat, width = 70, textvariable = self.customOverlayPreFormatStringRight, validate="focusout", validatecommand=self.saveCustomOverlayPreFormatRight)
			if self.parameters.data.get('overlayStringPreFormatRight'):
				self.customOverlayPreFormatStringRight.set(self.parameters.data.get('overlayStringPreFormatRight'))

			self.checkUseMirrorOverlay = tk.Checkbutton(self.frameCustomFormat, text="Mirror Left/Right HTML Overlay", variable=self.mirrorLeftToRightOverlay, command = self.toggleMirrorLeftRightOverlay)
			
			tk.Label(self.frameCustomFormat, text="Left").grid(sticky=tk.W)
			self.customOverlayEntryLeft.grid(sticky = tk.W)

			self.checkUseMirrorOverlay.grid(sticky =tk.W)

			tk.Label(self.frameCustomFormat, text="Right").grid(sticky=tk.W)
			self.customOverlayEntryRight.grid(sticky = tk.W)
			
			self.toggleUseOverlayPreFormat()    

			self.checkOwn = tk.Checkbutton(self.framePlayerInfo, text="Show Own Stats", variable=self.showOwn, command = self.saveToggles)
			self.checkOwn.grid( sticky=tk.W)
			self.checkWLRatio = tk.Checkbutton(self.framePlayerInfo, text="Steam Profile", variable=self.showSteamProfile, command = self.saveToggles)
			self.checkWLRatio.grid( sticky=tk.W) 

			self.checkAutomaticTrigger = tk.Checkbutton(self.frameAutoTrigger, text="Automatic Trigger", variable=self.automaticTrigger, command = self.automaticTriggerToggle)
			self.checkAutomaticTrigger.grid( sticky=tk.W)
			self.checkWriteIWonLostInChat = tk.Checkbutton(self.frameAutoTrigger, text="Win/Lose message in Chat", variable=self.writeIWonLostInChat, command = self.saveToggles)
			self.checkWriteIWonLostInChat.grid( sticky=tk.W)
			self.checkWritePlaceYourBetsInChat = tk.Checkbutton(self.frameAutoTrigger, text="Write '!Place Your Bets' in Chat at game start", variable=self.writePlaceYourBetsInChat, command = self.saveToggles)
			self.checkWritePlaceYourBetsInChat.grid(sticky=tk.W)
			self.checkClearOverlayAfterGame = tk.Checkbutton(self.frameAutoTrigger, text="Clear overlay after game over", variable=self.clearOverlayAfterGameOver, command = self.saveToggles)
			self.checkClearOverlayAfterGame.grid( sticky=tk.W)            

			self.automaticTriggerToggle() 
			self.toggleUseCustomPreFormat() # setdisabled if custom format on first run
			self.toggleUseOverlayPreFormat()
			#self.automode() # setdisabled if auto on first run

			#CSS File Location
			tk.Label(self.frameCSSFilePath, text="CSS Path").grid(row =0,sticky=tk.W)
			self.entryCSSFilePath = tk.Entry(self.frameCSSFilePath, width= 49)
			self.entryCSSFilePath.grid(row=0,column=1)

			if(self.parameters.data.get('overlayStyleCSSFilePath')):
				self.entryCSSFilePath.insert(0, str(self.parameters.data.get('overlayStyleCSSFilePath')))

			self.entryCSSFilePath.config(state=DISABLED)

			self.buttonCSSFilePath = tk.Button(self.frameCSSFilePath, text="Browse", command = lambda: self.browseCSSFilePathButton())
			self.buttonCSSFilePath.config(width=10)
			self.buttonCSSFilePath.grid(row=0, column=2, sticky=tk.W)

			#CustomBotCredientials
			tk.Label(self.frameOptionalBotCredentials, text="Bot Account Name").grid(row=0,sticky=tk.W)
			tk.Label(self.frameOptionalBotCredentials, text="Bot oAuth Key").grid(row=1,sticky=tk.W)

			self.entryBotAccountName = tk.Entry(self.frameOptionalBotCredentials, width = 40)
			self.entryBotoAuthKey = tk.Entry(self.frameOptionalBotCredentials, width = 40)

			self.entryBotAccountName.grid(row=0,column=1)
			self.entryBotoAuthKey.grid(row=1,column=1)

			if (self.parameters.data.get('botUserName')):
				self.entryBotAccountName.insert(0, str(self.parameters.data.get('botUserName')))

			if (self.parameters.data.get('botOAuthKey')):
				self.entryBotoAuthKey.insert(0, str(self.parameters.data.get('botOAuthKey')))
				
			self.entryBotoAuthKey.config(show="*")

			self.entryBotAccountName.config(state = "disabled")
			self.entryBotoAuthKey.config(state = "disabled")

			self.buttonBotAccountName = tk.Button(self.frameOptionalBotCredentials, text = "edit", command = lambda: self.editBotName())
			self.buttonBotAccountName.config(width = 10)
			self.buttonBotAccountName.grid(row=0,column=2)
			self.buttonBotOAuthKey = tk.Button(self.frameOptionalBotCredentials, text = "edit", command = lambda: self.editOAuthKey())
			self.buttonBotOAuthKey.config(width = 10)
			self.buttonBotOAuthKey.grid(row=1,column=2)


			#Misc tickbox
			self.checkLogErrorToFile = tk.Checkbutton(self.frameMisc, text="Log Errors To File", variable=self.logErrorsToFile, command = self.toggleLogErrorsToFile)
			self.checkLogErrorToFile.grid(sticky=tk.W)

		try:
			self.optionsMenu.focus()
		except Exception as e:
			logging.error('Exception : ' + str(e))

	def toggleLogErrorsToFile(self):
		# work in progress
		if (bool(self.logErrorsToFile.get())):
			logging.getLogger().disabled = False
			logging.info("Logging Started")
			logging.info(VersionNumber)
		else:
			logging.info("Stop Logging")
			logging.getLogger().disabled = True

		self.saveToggles()

	def toggleMirrorLeftRightOverlay(self):
		if (bool(self.mirrorLeftToRightOverlay.get())):
			self.customOverlayEntryRight.config(state = DISABLED)
			#write in the left version mirror
			leftString = self.customOverlayPreFormatStringLeft.get()
			leftList = leftString.split()
			leftList.reverse()
			rightString = " ".join(leftList)
			self.customOverlayPreFormatStringRight.set(rightString)
			self.saveCustomOverlayPreFormatRight()
		else:
			if(bool(self.useOverlayPreFormat.get())):
				self.customOverlayEntryRight.config(state = NORMAL)
		self.saveToggles()


	def saveCustomChatPreFormat(self):
		if self.customChatOutputEntry:
			self.parameters.data['customStringPreFormat'] = self.customChatOutputPreFormatString.get()
		self.parameters.save()
		return True # must return true to a validate entry method        


	def saveCustomOverlayPreFormatLeft(self):
		if self.customOverlayEntryLeft:
			self.parameters.data['overlayStringPreFormatLeft'] = self.customOverlayPreFormatStringLeft.get()
		self.parameters.save()
		return True # must return true to a validate entry method

	def saveCustomOverlayPreFormatRight(self):
		if self.customOverlayEntryRight:
			self.parameters.data['overlayStringPreFormatRight'] = self.customOverlayPreFormatStringRight.get()
		self.parameters.save()
		return True # must return true to a validate entry method

	def toggleUseOverlayPreFormat(self):
		if (bool(self.useOverlayPreFormat.get())):
			self.customOverlayEntryLeft.config(state = NORMAL)
			if (self.mirrorLeftToRightOverlay.get()):
				self.customOverlayEntryRight.config(state = DISABLED)
			else:
				self.customOverlayEntryRight.config(state = NORMAL)
		else:
			self.customOverlayEntryLeft.config(state = DISABLED)
			self.customOverlayEntryRight.config(state = DISABLED)
		self.saveToggles()

	
	def toggleUseCustomPreFormat(self):
		if (bool(self.useCustomPreFormat.get())):
			self.customChatOutputEntry.config(state = NORMAL)
		else:
			self.customChatOutputEntry.config(state = DISABLED)            
		self.saveToggles()



	def testStats(self):
		logging.info("Testing Stats")
		if (self.ircClient):
			self.ircClient.queue.put('TEST')


	def automaticTriggerToggle(self):
		if(bool(self.automaticTrigger.get())):
			self.checkWriteIWonLostInChat.config(state = NORMAL)
			self.checkWritePlaceYourBetsInChat.config(state = NORMAL)
			self.checkClearOverlayAfterGame.config(state = NORMAL)            
			if (self.ircClient):
				logging.info("in automatic trigger toggle")
				self.startMonitors()
		else:
			self.closeMonitors()
			self.checkWriteIWonLostInChat.config(state = DISABLED)
			self.checkWritePlaceYourBetsInChat.config(state = DISABLED)
			self.checkClearOverlayAfterGame.config(state = DISABLED)
		self.saveToggles()        

	def saveToggles(self):
		self.parameters.data['showOwn'] = bool(self.showOwn.get())

		self.parameters.data['showSteamProfile'] = bool(self.showSteamProfile.get())

		self.parameters.data['automaticTrigger'] = bool(self.automaticTrigger.get())

		self.parameters.data['writeIWonLostInChat'] = bool(self.writeIWonLostInChat.get())

		self.parameters.data['writePlaceYourBetsInChat'] = bool(self.writePlaceYourBetsInChat.get())

		self.parameters.data['clearOverlayAfterGameOver'] = bool(self.clearOverlayAfterGameOver.get())

		self.parameters.data['useOverlayPreFormat'] = bool(self.useOverlayPreFormat.get())

		self.parameters.data['mirrorLeftToRightOverlay'] = bool(self.mirrorLeftToRightOverlay.get())

		self.parameters.data['useCustomPreFormat'] = bool(self.useCustomPreFormat.get())

		self.parameters.data['logErrorsToFile'] = bool(self.logErrorsToFile.get())


		self.parameters.save()
		try:
			if self.ircClient:
				self.ircClient.parameters = self.parameters
		except Exception as e:
			logging.error(str(e))
			logging.exception('Exception : ')

	
	def on_close_options(self):
		self.optionsMenu.destroy()
		self.optionsMenu = None


	def disableEverything(self):
		self.buttonTwitchChannel.config(state = DISABLED)
		self.buttonSteamName.config(state= DISABLED)
		self.buttonSteam64IDNumber.config(state = DISABLED)
		self.buttonLocateWarningLog.config(state = DISABLED)
		self.buttonOptions.config(state = DISABLED)
		self.cohBrowseButton.config(state = DISABLED)
		self.entryTwitchChannel.config(state = DISABLED)

		self.entrySteam64IDNumber.config(state = DISABLED)
		self.entryWarningLogPath.config(state = DISABLED)
		self.entryRelicCOHPath.config(state = DISABLED)
		self.connectButton.config(state = DISABLED)
		self.testButton.config(state = DISABLED)

		#disabled if options displayed
		if self.optionsMenu:
			if self.entryBotAccountName:
				self.entryBotAccountName.config(state = DISABLED)
			if self.entryBotoAuthKey:
				self.entryBotoAuthKey.config(state = DISABLED)
			if self.buttonBotAccountName:
				self.buttonBotAccountName.config(state = DISABLED)
			if self.buttonBotOAuthKey:
				self.buttonBotOAuthKey.config(state = DISABLED)
			if self.buttonCSSFilePath:
				self.buttonCSSFilePath.config(state=DISABLED)

	def enableButtons(self):
		self.buttonTwitchChannel.config(state = NORMAL)
		self.buttonSteamName.config(state = NORMAL)
		self.buttonSteam64IDNumber.config(state = NORMAL)
		self.buttonLocateWarningLog.config(state = NORMAL)
		self.buttonOptions.config(state = NORMAL)
		self.cohBrowseButton.config(state = NORMAL)
		self.connectButton.config(state = NORMAL)

		#enable if option frame is showing
		if self.optionsMenu:
			if self.buttonBotAccountName:
				self.buttonBotAccountName.config(state = NORMAL)
			if self.buttonBotOAuthKey:
				self.buttonBotOAuthKey.config(state = NORMAL)
			if self.buttonCSSFilePath:
				self.buttonCSSFilePath.config(state=NORMAL)
		


	def editSteamNumber(self):  
		theState = self.entrySteam64IDNumber.cget('state')
		if(theState == "disabled"):
			self.disableEverything()
			self.buttonSteam64IDNumber.config(state = NORMAL)
			self.entrySteam64IDNumber.config(state = NORMAL)

		if(theState == "normal"):
			if self.checkSteamNumber(self.entrySteam64IDNumber.get()):
				self.entrySteam64IDNumber.config(state = DISABLED)
				self.enableButtons()
				self.parameters.data['steamNumber'] = self.entrySteam64IDNumber.get()
				self.parameters.save()
			else:
				messagebox.showerror("Invaid Steam Number", "Please enter your steam number\nIt Should be an integer 17 characters long")
			
			# implement check value safe

	def editTwitchName(self):
		theState = self.entryTwitchChannel.cget('state')
		if(theState == DISABLED):
			self.disableEverything()
			self.entryTwitchChannel.config(state = NORMAL)
			self.buttonTwitchChannel.config(state = NORMAL)

		if(theState == NORMAL):
			if(self.special_match(self.entryTwitchChannel.get())):
				self.entryTwitchChannel.config(state = DISABLED)
				self.enableButtons()
				self.parameters.data['channel'] = self.entryTwitchChannel.get()
				self.parameters.save()
			else:
				messagebox.showerror("Invalid Twitch channel", "That doesn't look like a valid channel name\nTwitch user names should be 4-24 characters long\nand only contain letters numbers and underscores.")

	def editSteamName(self):
		theState = self.entrySteamName.cget('state')
		if(theState == DISABLED):
			self.disableEverything()
			self.entrySteamName.config(state = NORMAL)
			self.buttonSteamName.config(state = NORMAL)

		if(theState == NORMAL):
			self.entrySteamName.config(state = DISABLED)
			self.enableButtons()
			self.parameters.data['steamAlias'] = self.entrySteamName.get()
			self.parameters.save()


	def editBotName(self):
		theState = self.entryBotAccountName.cget('state')
		if(theState == "disabled"):
			self.disableEverything()
			self.buttonBotAccountName.config(state = NORMAL)
			self.entryBotAccountName.config(state = NORMAL)

		if(theState == "normal"):
			if(self.special_match(self.entryBotAccountName.get())):
				self.entryBotAccountName.config(state = "disabled")
				self.enableButtons()
				self.parameters.data['botUserName'] = self.entryBotAccountName.get()
				self.parameters.save()
			else:
				messagebox.showerror("Invalid Twitch channel", "That doesn't look like a valid Twitch user name\nTwitch user names should be 4-24 characters long\nand only contain letters numbers and underscores.")

	def editOAuthKey(self):  
		theState = self.entryBotoAuthKey.cget('state')
		if(theState == "disabled"):
			self.disableEverything()
			self.buttonBotOAuthKey.config(state = NORMAL)
			self.entryBotoAuthKey.config(state = NORMAL)

		if(theState == "normal"):
			if self.checkOAuthKey(self.entryBotoAuthKey.get()):
				self.entryBotoAuthKey.config(state = "disabled")
				self.enableButtons()
				self.parameters.data['botOAuthKey'] = self.entryBotoAuthKey.get()
				self.parameters.save()
			else:
				messagebox.showerror("Invaid OAuth Key", "Please enter your bots OAuth Key\nIt Should be an 36 characters long and start with oauth:\n You can find it here https://twitchapps.com/tmi/")



	def special_match(self, strg, search=re.compile(r'^[a-zA-Z0-9][\w]{3,24}$').search):
		if strg == "":
			return True #empty returns True
		return bool(search(strg)) #Allowed twitch username returns True, if None, it returns Falsenn

	def checkOAuthKey(self, oauthkey):
		try:
			if (oauthkey[:6] == "oauth:") or (oauthkey == ""):
				return True
			return False
		except Exception as e:
			logging.error('Exception : ' + str(e))
			return False

	def checkSteamNumber(self, number):
		try:
			number = int(number)
			if isinstance(number, int):
				if (len(str(number)) == 17):
					return True
			return False
		except Exception as e:
			logging.error('Exception : ' + str(e))

	def locateWarningLog(self):
		self.disableEverything()
		self.master.filename =  tk.filedialog.askopenfilename(initialdir = "/",title = "Select warning.log file",filetypes = (("log file","*.log"),("all files","*.*")))
		logging.info("File Path : " + str(self.master.filename))
		print("File Path : " + str(self.master.filename))
		if(self.master.filename != ""):
			pattern = re.compile(r"\u20A9|\uFFE6|\u00A5|\uFFE5") # replaces both Won sign varients for korean language and Yen symbol for Japanese language paths
			theFilename = re.sub(pattern, "/", self.master.filename)
			self.parameters.data['logPath'] = theFilename.replace("/",'\\')
			self.entryWarningLogPath.config(state = NORMAL)
			self.entryWarningLogPath.delete(0, tk.END)
			logpath = self.parameters.data.get('logPath')
			if logpath:
				self.entryWarningLogPath.insert(0, str(logpath))
			self.entryWarningLogPath.config(state = DISABLED)
			self.parameters.save()
		self.enableButtons()

	def locateCOH(self):
		self.disableEverything()
		self.master.filename =  tk.filedialog.askopenfilename(initialdir = "/",title = "Select location of RelicCOH.exe file",filetypes = (("RelicCOH","*.exe"),("all files","*.*")))
		logging.info("File Path : " + str(self.master.filename))
		print("File Path : " + str(self.master.filename))
		if(self.master.filename != ""):
			pattern = re.compile(r"\u20A9|\uFFE6|\u00A5|\uFFE5") # replaces both Won sign varients for korean language and Yen symbol for Japanese language paths
			theFilename = re.sub(pattern, "/", self.master.filename)
			self.parameters.data['logPath'] = theFilename.replace("/",'\\')
			self.entryRelicCOHPath.config(state = NORMAL)
			self.entryRelicCOHPath.delete(0, tk.END)
			logpath = self.parameters.data.get('cohPath')
			if logpath:
				self.entryRelicCOHPath.insert(0, str(logpath))
			self.entryRelicCOHPath.config(state = DISABLED)
			self.parameters.save()
		self.enableButtons()

	def browseCSSFilePathButton(self):
		self.disableEverything()
		cwd = os.getcwd()
		self.master.filename =  tk.filedialog.askopenfilename(initialdir = cwd,title = "Select location of CSS file",filetypes = (("css file","*.css"),("all files","*.*")))
		logging.info("File Path : " + str(self.master.filename))
		print("File Path : " + str(self.master.filename))
		if(self.master.filename != ""):
			pattern = re.compile(r"\u20A9|\uFFE6|\u00A5|\uFFE5") # replaces both Won sign varients for korean language and Yen symbol for Japanese language paths
			theFilename = re.sub(pattern, "/", self.master.filename)
			self.parameters.data['overlayStyleCSSFilePath'] = theFilename.replace("/",'\\')
			self.entryCSSFilePath.config(state = NORMAL)
			self.entryCSSFilePath.delete(0, tk.END)
			cssPath = self.parameters.data.get('overlayStyleCSSFilePath')
			if cssPath:
				self.entryCSSFilePath.insert(0, str(cssPath))
			self.entryCSSFilePath.config(state = DISABLED)
			self.parameters.save()
		self.enableButtons()



	def connectIRC(self, thread):
		if((self.checkSteamNumber(self.parameters.data.get('steamNumber'))) and (self.special_match(self.parameters.data.get('channel'))) and (os.path.isfile(self.parameters.data.get('logPath')))):
			# connect if there is no thread running, disconnect if thread is running
			if self.ircClient:
				#close thread
				try:
					if(self.ircClient):
						self.ircClient.close()
					self.closeMonitors()

				except Exception as e:
					logging.error('Exception : ' + str(e))
				while (threading.active_count() > 1):
					pass
				self.testButton.config(state = DISABLED)
				self.enableButtons()
				self.connectButton.config(text = "Connect")
				self.ircClient = None
				
			else:
				#start thread
				self.disableEverything()
				self.connectButton.config(text = "Disconnect")
				self.testButton.config(state = NORMAL)
				self.ircClient = COHOpponentBot_Bot.IRCClient(self.txt, bool(self.consoleDisplayBool.get()), parameters=self.parameters)
				self.ircClient.start()
				if (bool(self.parameters.data.get('automaticTrigger'))):
					self.startMonitors()
				self.connectButton.config(state = NORMAL)
		else:
			messagebox.showerror("Invalid details", "Please check that your twitch username, Steam Number and warning.log file path are valid.")

	def startMonitors(self):
		#Ensure they are off if running
		self.closeMonitors()
		#Create Monitor Threads and start them.
		if self.ircClient:
			self.automaticFileMonitor = COHOpponentBot_Bot.FileMonitor(self.parameters.data.get('logPath'), self.parameters.data.get('filePollInterval'), self.ircClient, parameters=self.parameters)
			self.automaticFileMonitor.start()
			self.automaticMemoryMonitor = COHOpponentBot_Bot.MemoryMonitor(pollInterval = self.parameters.data.get('filePollInterval'), ircClient= self.ircClient, parameters=self.parameters)
			self.automaticMemoryMonitor.start()

	def closeMonitors(self):
		if self.automaticFileMonitor:
			self.automaticFileMonitor.close()
		if self.automaticMemoryMonitor:
			self.automaticMemoryMonitor.close()

	def on_closing(self):
		logging.info("In on_closing program (Closing)")
		try:
			if(self.ircClient):
				self.ircClient.close()
			self.closeMonitors()
		except Exception as e:
			logging.exception('Exception : ' + str(e))
		while (threading.active_count() > 1):
			pass
		logging.info("Exiting main thread")
		sys.exit()



# Program Entry Starts here
# Default error logging log file location:
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(format='%(asctime)s (%(threadName)-10s) [%(levelname)s] %(message)s', filename= 'COH_Opponent_Bot.log',filemode = "w", level=logging.INFO)

COHOpponentBot_Bot.GameData.clearOverlayHTML()

main = COHBotGUI()
VersionNumber = "Version 1.0"

import IRCBetBot_Parameters
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import re
import os.path
import COHOpponentBot_1
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

        self.thread = None #reference to the opponentbot

        self.parameters = IRCBetBot_Parameters.parameters()
        self.parameters.load()

        self.master = tk.Tk()

        self.optionsMenu = None

        self.style = Style()
        self.master.title("COH Opponent Bot")

        #checkbox string construction option bools

        self.showOwn = IntVar(value = int(bool(self.parameters.data.get('showOwn'))))

        self.automaticMode = IntVar(value = int(bool(self.parameters.data.get('automaticMode'))))

        self.showTotalWins = IntVar(value = int(bool(self.parameters.data.get('showTotalWins'))))
        self.showTotalLosses = IntVar(value = int(bool(self.parameters.data.get('showTotalLosses'))))
        self.showTotalWLRatio = IntVar(value = int(bool(self.parameters.data.get('showTotalWLRatio'))))
        
        self.showBasic = IntVar(value = int(bool(self.parameters.data.get('showBasic'))))
        self.show1v1 = IntVar(value = int(bool(self.parameters.data.get('show1v1'))))
        self.show2v2 = IntVar(value = int(bool(self.parameters.data.get('show2v2'))))
        self.show3v3 = IntVar(value = int(bool(self.parameters.data.get('show3v3'))))
        
        self.showWins = IntVar(value = int(bool(self.parameters.data.get('showWins'))))
        self.showLosses = IntVar(value = int(bool(self.parameters.data.get('showLosses'))))
        self.showDisputes = IntVar(value = int(bool(self.parameters.data.get('showDisputes'))))
        self.showStreak = IntVar(value = int(bool(self.parameters.data.get('showStreak'))))
        self.showDrops = IntVar(value = int(bool(self.parameters.data.get('showDrops'))))
        self.showRank = IntVar(value = int(bool(self.parameters.data.get('showRank'))))
        self.showLevel = IntVar(value = int(bool(self.parameters.data.get('showLevel'))))
        self.showLastPlayed = IntVar(value = int(bool(self.parameters.data.get('showLastPlayed'))))
        
        self.showWLRatio = IntVar(value = int(bool(self.parameters.data.get('showWLRatio'))))

        self.showSteamProfile = IntVar(value = int(bool(self.parameters.data.get('showSteamProfile'))))
        self.showUserCountry = IntVar(value = int(bool(self.parameters.data.get('showUserCountry'))))

        self.automaticTrigger = IntVar(value = int(bool(self.parameters.data.get('automaticTrigger'))))

        tk.Label(self.master, text="Twitch Channel").grid(row=0, sticky=tk.W)
        tk.Label(self.master, text="Bot Account Name").grid(row=1, sticky=tk.W)
        tk.Label(self.master, text="Bot oAuth Key").grid(row=2, sticky=tk.W)
        tk.Label(self.master, text="Steam64ID Number").grid(row=3, sticky=tk.W)
        tk.Label(self.master, text="warning.log path").grid(row=4, sticky=tk.W)

        self.e1 = tk.Entry(self.master, width = 70)
        self.e2 = tk.Entry(self.master, width = 70)
        self.e3 = tk.Entry(self.master, width = 70)
        self.e4 = tk.Entry(self.master, width = 70)
        self.e5 = tk.Entry(self.master, width = 70)

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.e3.grid(row=2, column=1)
        self.e4.grid(row=3, column=1)
        self.e5.grid(row=4, column=1)

        logPath = self.parameters.data.get('logPath')
        if (logPath):
            self.e5.insert(0, str(logPath))

        steamNumber = "enter your steam number"
        if self.parameters.data.get('steamNumber'):
            steamNumber = self.parameters.data.get('steamNumber')

        self.e4.insert(0, steamNumber)

        twitchName = "enter your twitch channel name"
        if self.parameters.data.get('channel'):
            twitchName = self.parameters.data.get('channel')

        self.e1.insert(0, twitchName)
        if (self.parameters.data.get('botUserName')):
            self.e2.insert(0, str(self.parameters.data.get('botUserName')))

        if (self.parameters.data.get('botOAuthKey')):
            self.e3.insert(0, str(self.parameters.data.get('botOAuthKey')))

        self.e1.config(state = "disabled")
        self.e2.config(state = "disabled")
        self.e3.config(state = "disabled")
        self.e4.config(state = "disabled")
        self.e5.config(state = "disabled")

        self.b1 = tk.Button(self.master, text = "edit", command = lambda: self.editTwitchName())
        self.b1.config(width = 10)
        self.b1.grid(row=0, column =2)
        self.b2 = tk.Button(self.master, text = "edit", command = lambda: self.editBotName())
        self.b2.config(width = 10)
        self.b2.grid(row=1, column=2)
        self.b3 = tk.Button(self.master, text = "edit", command = lambda: self.editOAuthKey())
        self.b3.config(width = 10)
        self.b3.grid(row=2, column=2)
        self.b4 = tk.Button(self.master, text = "edit", command = lambda: self.editSteamNumber())
        self.b4.config(width = 10)
        self.b4.grid(row=3, column=2)        
        self.b5 = tk.Button(self.master, text = "browse", command = lambda : self.locateWarningLog() )
        self.b5.config(width = 10)
        self.b5.grid(row=4, column=2)
        self.b6 = tk.Button(self.master, text = "options", command = self.createOptionsMenu )
        self.b6.config(width = 10)
        self.b6.grid(row=5, column=2)



        self.thread = None
        self.automaticFileMonitor = None

        self.style.configure('W.TButton', font = 'calibri', size = 10, foreground = 'red')
        self.connectButton = ttk.Button(self.master, text = "Connect",style ='W.TButton', command = lambda : self.connectIRC(self.thread))
        #self.connectButton.config(width = 10, height = 5)
        self.connectButton.grid(row=6, columnspan = 3, sticky = tk.W+tk.E+tk.N+tk.S, padx=30,pady=30)

        #self.master.iconbitmap('coh.ico')
        self.consoleDisplayBool = IntVar()
        checkButton1 = tk.Checkbutton(self.master, text="Display IRC raw chat output", variable=self.consoleDisplayBool, command = self.displayConsoleToggled)
        checkButton1.grid(row=8, sticky=tk.W)

        self.testButton = tk.Button(self.master, text = "Test Output", command = self.testStats )
        self.testButton.config(width = 10)
        self.testButton.grid(row =8, column=2 ,sticky=tk.E)
        self.testButton.config(state = DISABLED)


        tk.Label(self.master, text="Console Output:").grid(row=9, sticky=tk.W)
        # create a Text widget
        self.txt = tk.Text(self.master)
        self.txt.grid(row=10, columnspan=3, sticky="nsew", padx=2, pady=2)

        # create a Scrollbar and associate it with txt
        scrollb = ttk.Scrollbar(self.master, command=self.txt.yview)
        scrollb.grid(row=8, column=4, sticky='nsew')
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


        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.master.mainloop()

    def createOptionsMenu(self):
        if not self.optionsMenu:
            self.optionsMenu = tk.Toplevel(self.master)
            self.optionsMenu.protocol("WM_DELETE_WINDOW", self.on_close_options)
            self.optionsMenu.title("Chat Display Options")

            self.f1 = tk.LabelFrame(self.optionsMenu, padx =5, pady=5)
            self.f1.grid()
            self.f2 = tk.LabelFrame(self.optionsMenu, text = "Player Info", padx =5, pady=5)
            self.f2.grid()
            self.f3 = tk.LabelFrame(self.optionsMenu, text = "Match Types", padx =5, pady=5)
            self.f3.grid()
            self.f4 = tk.LabelFrame(self.optionsMenu, text = "Faction Stats", padx =5, pady=5)
            self.f4.grid()
            self.f5 = tk.LabelFrame(self.optionsMenu, text = "Auto Trigger", padx =5, pady=5)
            self.f5.grid()            



            tk.Label(self.f1, text="Report Options").grid(sticky=tk.W)

            

            self.checkOwn = tk.Checkbutton(self.f2, text="Show Own Stats", variable=self.showOwn, command = self.saveToggles)
            self.checkOwn.grid( sticky=tk.W)
            self.checkWLRatio = tk.Checkbutton(self.f2, text="Country", variable=self.showUserCountry, command = self.saveToggles)
            self.checkWLRatio.grid( sticky=tk.W)
            self.checkWLRatio = tk.Checkbutton(self.f2, text="Steam Profile", variable=self.showSteamProfile, command = self.saveToggles)
            self.checkWLRatio.grid( sticky=tk.W) 
            self.checkTotalWins = tk.Checkbutton(self.f2, text="Total Wins", variable=self.showTotalWins, command = self.saveToggles)
            self.checkTotalWins.grid( sticky=tk.W)             
            self.checkTotalLosses = tk.Checkbutton(self.f2, text="Total Losses", variable=self.showTotalLosses, command = self.saveToggles)
            self.checkTotalLosses.grid( sticky=tk.W) 
            self.checkTotalWLRatio = tk.Checkbutton(self.f2, text="Total W/L Ratio", variable=self.showTotalWLRatio, command = self.saveToggles)
            self.checkTotalWLRatio.grid( sticky=tk.W) 


            #s1 = ttk.Separator(OptionMenu, orient=HORIZONTAL)
            #s1.grid()
            self.checkAutomaticMode = tk.Checkbutton(self.f3, text="AUTOMATIC MODE", variable=self.automaticMode, command = self.automode)
            self.checkAutomaticMode.grid( sticky=tk.W)

            self.checkBasic = tk.Checkbutton(self.f3, text="Basic Matches", variable=self.showBasic, command = self.saveToggles)
            self.checkBasic.grid( sticky=tk.W)
            self.check1v1 = tk.Checkbutton(self.f3, text="1v1 Matches", variable=self.show1v1, command = self.saveToggles)
            self.check1v1.grid( sticky=tk.W)
            self.check2v2 = tk.Checkbutton(self.f3, text="2v2 Matches", variable=self.show2v2, command = self.saveToggles)
            self.check2v2.grid( sticky=tk.W)
            self.check3v3 = tk.Checkbutton(self.f3, text="3v3 Matches", variable=self.show3v3, command = self.saveToggles)
            self.check3v3.grid( sticky=tk.W)
            #s2 = ttk.Separator(OptionMenu, orient=HORIZONTAL)
            #s2.grid()
            #self.frame1 = tk.Frame(self.master, text = "faction stats")
            #self.frame1.grid()
            self.checkWins = tk.Checkbutton(self.f4, text="Wins", variable=self.showWins, command = self.saveToggles)
            self.checkWins.grid( sticky=tk.W)
            self.checkLosses = tk.Checkbutton(self.f4, text="Losses", variable=self.showLosses, command = self.saveToggles)
            self.checkLosses.grid( sticky=tk.W)
            self.checkDisputes = tk.Checkbutton(self.f4, text="Disputes", variable=self.showDisputes, command = self.saveToggles)
            self.checkDisputes.grid( sticky=tk.W)
            self.checkStreak = tk.Checkbutton(self.f4, text="Streak", variable=self.showStreak, command = self.saveToggles)
            self.checkStreak.grid( sticky=tk.W)
            self.checkDrops = tk.Checkbutton(self.f4, text="Drops", variable=self.showDrops, command = self.saveToggles)
            self.checkDrops.grid( sticky=tk.W)
            self.checkRank = tk.Checkbutton(self.f4, text="Rank", variable=self.showRank, command = self.saveToggles)
            self.checkRank.grid( sticky=tk.W)
            self.checkLevel = tk.Checkbutton(self.f4, text="Level", variable=self.showLevel, command = self.saveToggles)
            self.checkLevel.grid( sticky=tk.W)
            self.checkLastPlayed = tk.Checkbutton(self.f4, text="Last Played", variable=self.showLastPlayed, command = self.saveToggles)
            self.checkLastPlayed.grid( sticky=tk.W)
            self.checkWLRatio = tk.Checkbutton(self.f4, text="W/L Ratio", variable=self.showWLRatio, command = self.saveToggles)
            self.checkWLRatio.grid( sticky=tk.W)

            self.checkAutomaticTrigger = tk.Checkbutton(self.f5, text="Automatic Trigger", variable=self.automaticTrigger, command = self.automaticTriggerToggle)
            self.checkAutomaticTrigger.grid( sticky=tk.W)


            self.automode() # setdisabled if auto on first run
        try:
            self.optionsMenu.focus()
        except Exception as e:
            logging.exception('Exception : ')

    def testStats(self):
        print("Testing Stats")
        if (self.thread):
            self.thread.queue.put('OPPONENT')


    def automaticTriggerToggle(self):
        if(bool(self.automaticTrigger.get())):
            if (self.thread):
                print("in automatic trigger toggle")
                self.automaticFileMonitor = COHOpponentBot_1.FileMonitor(self.parameters.data.get('logPath'),self.parameters.data.get('filePollInterval'), self.thread)
                self.automaticFileMonitor.start()
        else:
            if (self.automaticFileMonitor):
                print("trying to close automatic file monitor")
                self.automaticFileMonitor.close()
        self.saveToggles()        

    def automode(self):
        if (bool(self.automaticMode.get())):
            self.checkBasic.deselect()
            self.checkBasic.config(state = DISABLED)
            self.check1v1.deselect()
            self.check1v1.config(state = DISABLED)
            self.check2v2.deselect()
            self.check2v2.config(state = DISABLED)
            self.check3v3.deselect()
            self.check3v3.config(state = DISABLED)
        else:
            self.checkBasic.config(state = NORMAL)
            self.check1v1.config(state = NORMAL)
            self.check2v2.config(state = NORMAL)
            self.check3v3.config(state = NORMAL)
        self.saveToggles()

    def saveToggles(self):
        self.parameters.data['showOwn'] = bool(self.showOwn.get())

        self.parameters.data['automaticMode'] = bool(self.automaticMode.get())
        self.parameters.data['showTotalWins'] = bool(self.showTotalWins.get())
        self.parameters.data['showTotalLosses'] = bool(self.showTotalLosses.get())
        self.parameters.data['showTotalWLRatio'] = bool(self.showTotalWLRatio.get())

        self.parameters.data['showBasic'] = bool(self.showBasic.get())
        self.parameters.data['show1v1'] = bool(self.show1v1.get())
        self.parameters.data['show2v2'] = bool(self.show2v2.get())
        self.parameters.data['show3v3'] = bool(self.show3v3.get())
        
        self.parameters.data['showWins'] = bool(self.showWins.get())
        self.parameters.data['showLosses'] = bool(self.showLosses.get())
        self.parameters.data['showDisputes'] = bool(self.showDisputes.get())
        self.parameters.data['showStreak'] = bool(self.showStreak.get())
        self.parameters.data['showDrops'] = bool(self.showDrops.get())
        self.parameters.data['showRank'] = bool(self.showRank.get())
        self.parameters.data['showLevel'] = bool(self.showLevel.get())
        self.parameters.data['showLastPlayed'] = bool(self.showLastPlayed.get())
        
        self.parameters.data['showWLRatio'] = bool(self.showWLRatio.get())

        self.parameters.data['showSteamProfile'] = bool(self.showSteamProfile.get())
        self.parameters.data['showUserCountry'] = bool(self.showUserCountry.get())

        self.parameters.data['automaticTrigger'] = bool(self.automaticTrigger.get())

        self.parameters.save()
        try:
            if self.thread:
                self.thread.parameters = self.parameters
        except Exception as e:
            logging.exception('Exception : ')

    
    def on_close_options(self):
        self.optionsMenu.destroy()
        self.optionsMenu = None

    def displayConsoleToggled(self):
        try:
            print(bool(self.consoleDisplayBool.get()))
            self.thread.displayConsoleOut = bool(self.consoleDisplayBool.get())
        except Exception as e:
            logging.exception('Exception : ')

    def disableEverything(self):
        self.b1.config(state = DISABLED)
        self.b2.config(state = DISABLED)
        self.b3.config(state = DISABLED)
        self.b4.config(state = DISABLED)
        self.b5.config(state = DISABLED)
        self.e1.config(state = DISABLED)
        self.e2.config(state = DISABLED)
        self.e3.config(state = DISABLED)
        self.e4.config(state = DISABLED)
        self.e5.config(state = DISABLED)
        self.connectButton.config(state = DISABLED)
        self.b6.config(state = DISABLED)
        self.testButton.config(state = DISABLED)

    def enableButtons(self):
        self.b1.config(state = NORMAL)
        self.b2.config(state = NORMAL)
        self.b3.config(state = NORMAL)
        self.b4.config(state = NORMAL)
        self.b5.config(state = NORMAL)
        self.connectButton.config(state = NORMAL)
        self.b6.config(state = NORMAL)
        #self.testButton.config(state = NORMAL)
        


    def editSteamNumber(self):  
        theState = self.e4.cget('state')
        if(theState == "disabled"):
            self.disableEverything()
            self.b4.config(state = NORMAL)
            self.e4.config(state = NORMAL)

        if(theState == "normal"):
            if self.checkSteamNumber(self.e4.get()):
                self.e4.config(state = DISABLED)
                self.enableButtons()
                self.parameters.data['steamNumber'] = self.e4.get()
                self.parameters.save()
            else:
                messagebox.showerror("Invaid Steam Number", "Please enter your steam number\nIt Should be an integer 17 characters long")
            
            # implement check value safe

    def editTwitchName(self):
        theState = self.e1.cget('state')
        if(theState == DISABLED):
            self.disableEverything()
            self.e1.config(state = NORMAL)
            self.b1.config(state = NORMAL)

        if(theState == NORMAL):
            if(self.special_match(self.e1.get())):
                self.e1.config(state = DISABLED)
                self.enableButtons()
                self.parameters.data['channel'] = self.e1.get()
                self.parameters.save()
            else:
                messagebox.showerror("Invalid Twitch channel", "That doesn't look like a valid channel name\nTwitch user names should be 4-24 characters long\nand only contain letters numbers and underscores.")

    def editBotName(self):
        theState = self.e2.cget('state')
        if(theState == "disabled"):
            self.disableEverything()
            self.b2.config(state = NORMAL)
            self.e2.config(state = NORMAL)

        if(theState == "normal"):
            if(self.special_match(self.e2.get())):
                self.e2.config(state = "disabled")
                self.enableButtons()
                self.parameters.data['botUserName'] = self.e2.get()
                self.parameters.save()
            else:
                messagebox.showerror("Invalid Twitch channel", "That doesn't look like a valid Twitch user name\nTwitch user names should be 4-24 characters long\nand only contain letters numbers and underscores.")

    def editOAuthKey(self):  
        theState = self.e3.cget('state')
        if(theState == "disabled"):
            self.disableEverything()
            self.b3.config(state = NORMAL)
            self.e3.config(state = NORMAL)

        if(theState == "normal"):
            if self.checkOAuthKey(self.e3.get()):
                self.e3.config(state = "disabled")
                self.enableButtons()
                self.parameters.data['botOAuthKey'] = self.e3.get()
                self.parameters.save()
            else:
                messagebox.showerror("Invaid OAuth Key", "Please enter your bots OAuth Key\nIt Should be an 36 characters long and start with oauth:\n You can find it here https://twitchapps.com/tmi/")



    def special_match(self, strg, search=re.compile(r'^[a-zA-Z0-9][\w]{3,24}$').search):
        if strg == "":
            return True
        return bool(search(strg))

    def checkOAuthKey(self, oauthkey):
        try:
            if (oauthkey[:6] == "oauth:") or (oauthkey == ""):
                return True
            return False
        except Exception as e:
            logging.exception('Exception : ')
            return False

    def checkSteamNumber(self, number):
        try:
            number = int(number)
            if isinstance(number, int):
                if (len(str(number)) == 17):
                    return True
            return False
        except Exception as e:
            logging.exception('Exception : ')

    def locateWarningLog(self):
        self.disableEverything()
        self.master.filename =  tk.filedialog.askopenfilename(initialdir = "/",title = "Select warning.log file",filetypes = (("log file","*.log"),("all files","*.*")))
        print(self.master.filename)
        if(self.master.filename != ""):
            self.parameters.data['logPath'] = self.master.filename.replace("/",'\\')
            self.e5.config(state = NORMAL)
            self.e5.delete(0, tk.END)
            logpath = self.parameters.data.get('logPath')
            if logpath:
                self.e5.insert(0, str(logpath))
            self.e5.config(state = DISABLED)
            self.parameters.save()
        self.enableButtons()



    def connectIRC(self, thread):
        if((self.checkSteamNumber(self.parameters.data.get('steamNumber'))) and (self.special_match(self.parameters.data.get('channel'))) and (os.path.isfile(self.parameters.data.get('logPath')))):
            self.disableEverything()
            self.b6.config(state = NORMAL)
            self.testButton.config(state = NORMAL)
            self.thread = COHOpponentBot_1.IRCClient(self.txt, bool(self.consoleDisplayBool.get()))
            self.thread.start()
            if (bool(self.parameters.data.get('automaticTrigger'))):
                self.automaticFileMonitor = COHOpponentBot_1.FileMonitor(self.parameters.data.get('logPath'),self.parameters.data.get('filePollInterval'), self.thread)
                self.automaticFileMonitor.start()
        else:
            messagebox.showerror("Invalid details", "Please check that your twitch username, Steam Number and warning.log file path are valid.")


    def on_closing(self):
        print("closing")
        try:
            if(self.thread):
                self.thread.close()
            if(self.automaticFileMonitor):
                self.automaticFileMonitor.close()
                self.automaticFileMonitor.event.set()
        except Exception as e:
            logging.exception('Exception : ')
        while (threading.active_count() > 1):
            pass
        print("exiting main thread")
        sys.exit()


# Program Entry Starts here
# Default error logging log file location:
logging.basicConfig(format='%(asctime)s (%(threadName)-10s) [%(levelname)s] %(message)s', filename= 'IRCOpponent_Temp_ERROR.log',filemode = "w", level=logging.DEBUG)
logging.info("Logging Started")
logging.info(VersionNumber)


COHOpponentBot_1.HandleCOHlogFile().clearOverlayHTML()

main = COHBotGUI()
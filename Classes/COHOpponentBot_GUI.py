import sys
import re
import os.path
import base64
import os
import logging
import threading

from tkinter import (
    DISABLED, N, E, NORMAL, S, W, IntVar, Menu, StringVar, messagebox
    )
from os.path import relpath

import tkinter as tkinter
from tkinter import ttk
import tkinter.filedialog
from tkinter.ttk import Style

from Classes.COHOpponentBot_Icon import Icon
from Classes.COHOpponentBot_GameData import GameData
from Classes.COHOpponentBot_MemoryMonitor import MemoryMonitor

import Classes.COHOpponentBot_IRC_Client as COHOpponentBot_IRC_Client
import Classes.COHOpponentBot_Settings as COHOpponentBot_Settings


class GUI:
    """Graphical User Interface for the COH Opponent Bot."""

    def __init__(self):

        # Enter Build Variables for marking About Box
        self.VersionNumber = "3.0.5"
        self.BuildDate = "04-May-2022"

        self.ircClient = None  # reference to the opponentbot

        self.settings = COHOpponentBot_Settings.Settings()

        self.master = tkinter.Tk()

        self.optionsMenu = None

        self.style = Style()
        self.master.title("COH Opponent Bot")

        # Checkbox string construction option bools

        v = int(bool(self.settings.data.get('showOwn')))
        self.showOwn = IntVar(value=v)
        v = int(bool(self.settings.data.get('automaticTrigger')))
        self.automaticTrigger = IntVar(value=v)
        v = int(bool(self.settings.data.get('writeIWonLostInChat')))
        self.writeIWonLostInChat = IntVar(value=v)
        v = int(bool(self.settings.data.get('automaticSetBettingOdds')))
        self.automaticSetBettingOdds = IntVar(value=v)
        v = int(bool(self.settings.data.get('writePlaceYourBetsInChat')))
        self.writePlaceYourBetsInChat = IntVar(value=v)
        v = int(bool(self.settings.data.get('clearOverlayAfterGameOver')))
        self.clearOverlayAfterGameOver = IntVar(value=v)
        v = int(bool(self.settings.data.get('useOverlayPreFormat')))
        self.useOverlayPreFormat = IntVar(value=v)
        v = int(bool(self.settings.data.get('mirrorLeftToRightOverlay')))
        self.mirrorLeftToRightOverlay = IntVar(value=v)
        v = int(bool(self.settings.data.get('useCustomPreFormat')))
        self.useCustomPreFormat = IntVar(value=v)
        v = int(bool(self.settings.data.get('logErrorsToFile')))
        self.logErrorsToFile = IntVar(value=v)

        self.customOverlayPreFormatStringLeft = StringVar()
        self.customOverlayPreFormatStringRight = StringVar()
        self.customChatOutputPreFormatString = StringVar()

        # Start or stop logging based on the self.logErrorsToFile variable
        self.toggle_log_errors_to_file()

        self.customOverlayEntry = None
        self.customChatOutputEntry = None

        tkinter.Label(
            self.master,
            text="Twitch Channel"
            ).grid(row=0, sticky=W)
        tkinter.Label(
            self.master,
            text="Steam Name"
            ).grid(row=1, sticky=W)
        tkinter.Label(
            self.master,
            text="Steam64ID Number"
            ).grid(row=2, sticky=W)
        tkinter.Label(
            self.master,
            text="warning.log path"
            ).grid(row=3, sticky=W)
        tkinter.Label(
            self.master,
            text="RelicCOH.exe path"
            ).grid(row=4, sticky=W)

        self.entryTwitchChannel = tkinter.Entry(self.master, width=70)
        self.entrySteamName = tkinter.Entry(self.master, width=70)
        self.entrySteam64IDNumber = tkinter.Entry(self.master, width=70)
        self.entryWarningLogPath = tkinter.Entry(self.master, width=70)
        self.entryRelicCOHPath = tkinter.Entry(self.master, width=70)

        self.entryTwitchChannel.grid(row=0, column=1)
        self.entrySteamName.grid(row=1, column=1)
        self.entrySteam64IDNumber.grid(row=2, column=1)
        self.entryWarningLogPath.grid(row=3, column=1)
        self.entryRelicCOHPath.grid(row=4, column=1)

        steamName = "Enter Your Steam Name Here"
        if self.settings.data.get('steamAlias'):
            steamName = self.settings.data.get('steamAlias')
        self.entrySteamName.insert(0, str(steamName))

        logPath = self.settings.data.get('logPath')
        if (logPath):
            self.entryWarningLogPath.insert(0, str(logPath))

        cohPath = self.settings.data.get('cohPath')
        if (cohPath):
            self.entryRelicCOHPath.insert(0, str(cohPath))

        steamNumber = "Enter Your Steam Number Here (17 digits)"
        if self.settings.data.get('steamNumber'):
            steamNumber = self.settings.data.get('steamNumber')
        self.entrySteam64IDNumber.insert(0, steamNumber)

        twitchName = "Enter Your Twitch Channel Name Here"
        if self.settings.data.get('channel'):
            twitchName = self.settings.data.get('channel')
        self.entryTwitchChannel.insert(0, twitchName)

        self.entryTwitchChannel.config(state="disabled")
        self.entrySteamName.config(state="disabled")
        self.entrySteam64IDNumber.config(state="disabled")
        self.entryWarningLogPath.config(state="disabled")
        self.entryRelicCOHPath.config(state="disabled")

        self.buttonTwitchChannel = tkinter.Button(
            self.master, text="edit", command=lambda: self.edit_twitch_name()
            )
        self.buttonTwitchChannel.config(width=10)
        self.buttonTwitchChannel.grid(row=0, column=2)
        self.buttonSteamName = tkinter.Button(
            self.master, text="edit", command=lambda: self.edit_steam_name())
        self.buttonSteamName.config(width=10)
        self.buttonSteamName.grid(row=1, column=2)
        self.buttonSteam64IDNumber = tkinter.Button(
            self.master, text="edit", command=lambda: self.edit_steam_number())
        self.buttonSteam64IDNumber.config(width=10)
        self.buttonSteam64IDNumber.grid(row=2, column=2)
        self.buttonLocateWarningLog = tkinter.Button(
            self.master,
            text="browse",
            command=lambda: self.locate_warning_log()
            )
        self.buttonLocateWarningLog.config(width=10)
        self.buttonLocateWarningLog.grid(row=3, column=2)
        self.cohBrowseButton = tkinter.Button(
            self.master, text="browse", command=lambda: self.locate_COH())
        self.cohBrowseButton.config(width=10)
        self.cohBrowseButton.grid(row=4, column=2)
        self.buttonOptions = tkinter.Button(
            self.master, text="options", command=self.create_options_menu)
        self.buttonOptions.config(width=10)
        self.buttonOptions.grid(row=5, column=2)

        self.ircClient = None
        self.automaticMemoryMonitor = None

        self.style.configure(
            'W.TButton', font='calibri', size=10, foreground='red')
        self.connectButton = ttk.Button(
            self.master, text="Connect", style='W.TButton',
            command=lambda: self.connect_IRC(self.ircClient)
            )

        self.connectButton.grid(
            row=6, columnspan=3, sticky=W+E+N+S, padx=30, pady=30)

        self.consoleDisplayBool = IntVar()

        self.testButton = tkinter.Button(
            self.master, text="Test Output", command=self.test_stats)
        self.testButton.config(width=10)
        self.testButton.grid(row=8, column=2, sticky=E)
        self.testButton.config(state=DISABLED)

        self.clearOverlayButton = tkinter.Button(
            self.master, text="Clear Overlay",
            command=GameData.clear_overlay_HTML)
        self.clearOverlayButton.config(width=10)
        self.clearOverlayButton.grid(row=9, column=2, sticky=E)

        tkinter.Label(
            self.master,
            text="Console Output:"
        ).grid(row=10, sticky=W)
        # create a Text widget
        self.txt = tkinter.Text(self.master)
        self.txt.grid(row=11, columnspan=3, sticky="nsew", padx=2, pady=2)

        # create a Scrollbar and associate it with txt
        scrollb = ttk.Scrollbar(self.master, command=self.txt.yview)
        scrollb.grid(row=11, column=4, sticky='nsew')
        self.txt['yscrollcommand'] = scrollb.set

        # import icon base64 data from separate icon.py file
        icon = Icon.icon

        icondata = base64.b64decode(icon)
        # The temp file is icon.ico
        tempFile = "Icon.ico"
        iconfileHandle = open(tempFile, "wb")
        # Extract the icon
        iconfileHandle.write(icondata)
        iconfileHandle.close()
        self.master.wm_iconbitmap(tempFile)
        # Delete the tempfile
        os.remove(tempFile)

        # Add File and Help menubar
        self.menubar = Menu(self.master)
        self.fileMenu = Menu(self.menubar, tearoff=0)
        self.fileMenu.add_command(
            label="Load Preferences",
            command=self.load_preferences)
        self.fileMenu.add_command(
            label="Save Preferences",
            command=self.save_preferences)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Exit", command=self.master.quit)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)

        self.helpmenu = Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(
            label="About...",
            command=self.show_about_dialogue)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.master.config(menu=self.menubar)

        self.master.mainloop()

    def save_preferences(self):
        """Save preferences drop down."""

        files = [('Json', '*.json'), ('All Files', '*.*')]
        workingDirectory = os.getcwd()
        print("workingDirectory : {}".format(workingDirectory))
        self.master.filename = tkinter.filedialog.asksaveasfilename(
            initialdir=workingDirectory,
            initialfile="data.json",
            title="Save Preferences File",
            filetypes=files)
        logging.info("File Path : " + str(self.master.filename))
        print("File Path : " + str(self.master.filename))
        if(self.master.filename):
            pattern = re.compile(r"\u20A9|\uFFE6|\u00A5|\uFFE5")
            # replaces both Won sign varients for korean language
            # and Yen symbol for Japanese language paths
            theFilename = re.sub(pattern, "/", self.master.filename)
            self.settings.save(theFilename)

    def load_preferences(self):
        """load preferences drop down."""

        files = [('Json', '*.json'), ('All Files', '*.*')]
        workingDirectory = os.getcwd()
        print("workingDirectory : {}".format(workingDirectory))
        self.master.filename = tkinter.filedialog.askopenfilename(
            initialdir=workingDirectory,
            initialfile="data.json",
            title="Load Preferences File",
            filetypes=files)
        logging.info("File Path : " + str(self.master.filename))
        print("File Path : " + str(self.master.filename))
        if(self.master.filename):
            pattern = re.compile(r"\u20A9|\uFFE6|\u00A5|\uFFE5")
            # replaces both Won sign varients for korean language
            # and Yen symbol for Japanese language paths
            theFilename = re.sub(pattern, "/", self.master.filename)
            self.settings.load(theFilename)
            self.refresh_settings()

    def refresh_settings(self):
        self.settings = COHOpponentBot_Settings.Settings()

    def show_about_dialogue(self):
        InformationString = (
            f"Version : {self.VersionNumber}\n\n"
            f"Build Date : {self.BuildDate}\n\n"
            "Created by : XcomReborn\n\n"
            "Special thanks : AveatorReborn"
        )
        tkinter.messagebox.showinfo("Information", InformationString)

    def create_options_menu(self):
        if not self.optionsMenu:
            self.optionsMenu = tkinter.Toplevel(self.master)
            self.optionsMenu.protocol(
                "WM_DELETE_WINDOW",
                self.on_close_options)
            self.optionsMenu.title("Chat Display Options")

            self.frameReportOptions = tkinter.LabelFrame(
                self.optionsMenu,
                padx=5,
                pady=5)
            self.frameReportOptions.grid()
            self.framePlayerInfo = tkinter.LabelFrame(
                self.optionsMenu,
                text="Player Info",
                padx=5,
                pady=5)
            self.framePlayerInfo.grid(sticky=N+W+E+S)

            self.frameAutoTrigger = tkinter.LabelFrame(
                self.optionsMenu,
                text="Auto Trigger",
                padx=5,
                pady=5)
            self.frameAutoTrigger.grid(sticky=N+W+E)

            self.frameCustomFormat = tkinter.LabelFrame(
                self.optionsMenu,
                text="Custom Format",
                padx=5,
                pady=5)
            self.frameCustomFormat.grid(sticky=N+W+E+S)

            self.frameCSSFilePath = tkinter.LabelFrame(
                self.optionsMenu,
                text="CSS Format File",
                padx=5,
                pady=5)
            self.frameCSSFilePath.grid(sticky=N+W+E+S)

            self.frameOptionalBotCredentials = tkinter.LabelFrame(
                self.optionsMenu,
                text="Optional Bot Credentials",
                padx=5,
                pady=5)
            self.frameOptionalBotCredentials.grid(sticky=N+W+E+S)

            self.frameMisc = tkinter.LabelFrame(
                self.optionsMenu,
                text="Misc",
                padx=5,
                pady=5)
            self.frameMisc.grid(sticky=N+W+E+S)

            tkinter.Label(
                self.frameReportOptions,
                text="Report Options"
            ).grid()

            self.checkUseCustomChatOutput = tkinter.Checkbutton(
                self.frameCustomFormat,
                text="Use Custom Chat Output Pre-Format",
                variable=self.useCustomPreFormat,
                command=self.toggle_use_custom_preformat)
            self.checkUseCustomChatOutput.grid(sticky=W)

            self.customChatOutputEntry = tkinter.Entry(
                self.frameCustomFormat,
                width=70,
                textvariable=self.customChatOutputPreFormatString,
                validate="focusout",
                validatecommand=self.save_custom_chat_preformat)
            self.customChatOutputEntry.grid(sticky=W)
            if self.settings.data.get('customStringPreFormat'):
                self.customChatOutputPreFormatString.set(
                    self.settings.data.get('customStringPreFormat'))

            self.frameCustomChatVariables = tkinter.LabelFrame(
                self.frameCustomFormat,
                text="Custom Chat/Overlay Text Variables",
                padx=5,
                pady=5)
            self.frameCustomChatVariables.grid(sticky=N+W+E)

            self.stringFormatLabels = []
            self.myLabelFrames = []
            # create all custom variables from dictionary keys
            columnNumber = 0
            rowNumber = 0

            sfd = self.settings.stringFormattingDictionary
            for key, value in sfd.items():

                myLabelFrame = tkinter.LabelFrame(
                    self.frameCustomChatVariables,
                    padx=5,
                    pady=5)
                self.frameCustomChatVariables.columnconfigure(
                    columnNumber,
                    minsize=100)
                self.myLabelFrames.append(myLabelFrame)
                myLabel = tkinter.Label(myLabelFrame, text=str(key))
                myLabel.grid()

                myLabelFrame.grid(
                    row=rowNumber,
                    column=columnNumber,
                    sticky=N + W + E)
                columnNumber += 1
                if columnNumber > 3:
                    rowNumber += 1
                    columnNumber = 0
                self.stringFormatLabels.append(myLabel)

            self.frameOverlayImageIcons = tkinter.LabelFrame(
                self.frameCustomFormat,
                text="HTML Overlay Only Image Icons",
                padx=5,
                pady=5)
            self.frameOverlayImageIcons.grid(sticky=N+W+E)

            # create all custom icon variables from dictionary keys
            columnNumber = 0
            rowNumber = 0
            iofd = self.settings.imageOverlayFormattingDictionary.items()
            for key, value in iofd:

                myLabelFrame = tkinter.LabelFrame(
                    self.frameOverlayImageIcons,
                    padx=5,
                    pady=5)
                self.frameOverlayImageIcons.columnconfigure(
                    columnNumber, minsize=100)
                self.myLabelFrames.append(myLabelFrame)
                myLabel = tkinter.Label(myLabelFrame, text=str(key))
                myLabel.grid()

                myLabelFrame.grid(
                    row=rowNumber,
                    column=columnNumber,
                    sticky=N + W + E)
                columnNumber += 1
                if columnNumber > 3:
                    rowNumber += 1
                    columnNumber = 0
                self.stringFormatLabels.append(myLabel)

            self.checkUseCustomOverlayString = tkinter.Checkbutton(
                self.frameCustomFormat,
                text="Use Custom HTML Overlay Pre-Format",
                variable=self.useOverlayPreFormat,
                command=self.toggle_use_overlay_preformat)
            self.checkUseCustomOverlayString.grid(sticky=W)

            self.customOverlayEntryLeft = tkinter.Entry(
                self.frameCustomFormat,
                width=70,
                textvariable=self.customOverlayPreFormatStringLeft,
                validate="focusout",
                validatecommand=self.save_custom_overlay_preformat_left)

            if self.settings.data.get('overlayStringPreFormatLeft'):
                self.customOverlayPreFormatStringLeft.set(
                    self.settings.data.get('overlayStringPreFormatLeft'))

            self.customOverlayEntryRight = tkinter.Entry(
                self.frameCustomFormat,
                width=70,
                textvariable=self.customOverlayPreFormatStringRight,
                validate="focusout",
                validatecommand=self.save_custom_overlay_preformat_right)

            if self.settings.data.get('overlayStringPreFormatRight'):
                self.customOverlayPreFormatStringRight.set(
                    self.settings.data.get('overlayStringPreFormatRight'))

            self.checkUseMirrorOverlay = tkinter.Checkbutton(
                self.frameCustomFormat,
                text="Mirror Left/Right HTML Overlay",
                variable=self.mirrorLeftToRightOverlay,
                command=self.toggle_mirror_left_right_overlay)

            tkinter.Label(self.frameCustomFormat, text="Left").grid(sticky=W)
            self.customOverlayEntryLeft.grid(sticky=W)

            self.checkUseMirrorOverlay.grid(sticky=W)

            tkinter.Label(self.frameCustomFormat, text="Right").grid(sticky=W)
            self.customOverlayEntryRight.grid(sticky=W)

            self.toggle_use_overlay_preformat()

            self.checkOwn = tkinter.Checkbutton(
                self.framePlayerInfo,
                text="Show Own Stats",
                variable=self.showOwn,
                command=self.save_toggles)

            self.checkOwn.grid(sticky=W)

            self.checkAutomaticTrigger = tkinter.Checkbutton(
                self.frameAutoTrigger,
                text="Automatic Trigger",
                variable=self.automaticTrigger,
                command=self.automatic_trigger_toggle)
            self.checkAutomaticTrigger.grid(sticky=W)

            self.checkWritePlaceYourBetsInChat = tkinter.Checkbutton(
                self.frameAutoTrigger,
                text="Write '!Place Your Bets' in Chat at game start",
                variable=self.writePlaceYourBetsInChat,
                command=self.save_toggles)
            self.checkWritePlaceYourBetsInChat.grid(sticky=W)

            self.checkAutomaticSetBettingOdds = tkinter.Checkbutton(
                self.frameAutoTrigger,
                text="Auto Set Betting Odds in Chat",
                variable=self.automaticSetBettingOdds,
                command=self.save_toggles)
            self.checkAutomaticSetBettingOdds.grid(sticky=W)

            # self.checkWriteIWonLostInChat = tkinter.Checkbutton(
            #    self.frameAutoTrigger,
            #    text="Win/Lose message in Chat",
            #    variable=self.writeIWonLostInChat,
            #    command=self.save_toggles)

            # self.checkWriteIWonLostInChat.grid(sticky=W)

            self.checkClearOverlayAfterGame = tkinter.Checkbutton(
                self.frameAutoTrigger,
                text="Clear overlay after game over",
                variable=self.clearOverlayAfterGameOver,
                command=self.save_toggles)
            self.checkClearOverlayAfterGame.grid(sticky=W)

            self.automatic_trigger_toggle()
            self.toggle_use_custom_preformat()
            # setdisabled if custom format on first run
            self.toggle_use_overlay_preformat()
            # self.automode() # setdisabled if auto on first run

            # CSS File Location
            tkinter.Label(
                self.frameCSSFilePath,
                text="CSS Path"
            ).grid(row=0, sticky=W)
            self.entryCSSFilePath = tkinter.Entry(
                self.frameCSSFilePath,
                width=49
            )
            self.entryCSSFilePath.grid(row=0, column=1)

            if(self.settings.data.get('overlayStyleCSSFilePath')):
                self.entryCSSFilePath.insert(
                    0,
                    str(self.settings.data.get('overlayStyleCSSFilePath')))

            self.entryCSSFilePath.config(state=DISABLED)

            self.buttonCSSFilePath = tkinter.Button(
                self.frameCSSFilePath,
                text="Browse",
                command=lambda: self.browse_CSS_file_path_button())
            self.buttonCSSFilePath.config(width=10)
            self.buttonCSSFilePath.grid(row=0, column=2, sticky=W)

            # CustomBotCredientials
            tkinter.Label(
                self.frameOptionalBotCredentials,
                text="Bot Account Name").grid(row=0, sticky=W)
            tkinter.Label(
                self.frameOptionalBotCredentials,
                text="Bot oAuth Key").grid(row=1, sticky=W)

            self.entryBotAccountName = tkinter.Entry(
                self.frameOptionalBotCredentials,
                width=40)
            self.entryBotoAuthKey = tkinter.Entry(
                self.frameOptionalBotCredentials,
                width=40)

            self.entryBotAccountName.grid(row=0, column=1)
            self.entryBotoAuthKey.grid(row=1, column=1)

            if (self.settings.data.get('botUserName')):
                self.entryBotAccountName.insert(
                    0,
                    str(self.settings.data.get('botUserName')))

            if (self.settings.data.get('botOAuthKey')):
                self.entryBotoAuthKey.insert(
                    0,
                    str(self.settings.data.get('botOAuthKey')))

            self.entryBotoAuthKey.config(show="*")

            self.entryBotAccountName.config(state="disabled")
            self.entryBotoAuthKey.config(state="disabled")

            self.buttonBotAccountName = tkinter.Button(
                self.frameOptionalBotCredentials,
                text="edit",
                command=lambda: self.edit_bot_name())
            self.buttonBotAccountName.config(width=10)
            self.buttonBotAccountName.grid(row=0, column=2)
            self.buttonBotOAuthKey = tkinter.Button(
                self.frameOptionalBotCredentials,
                text="edit",
                command=lambda: self.edit_oauth_key())
            self.buttonBotOAuthKey.config(width=10)
            self.buttonBotOAuthKey.grid(row=1, column=2)

            # Misc tickbox
            self.checkLogErrorToFile = tkinter.Checkbutton(
                self.frameMisc,
                text="Log Errors To File",
                variable=self.logErrorsToFile,
                command=self.toggle_log_errors_to_file
            )
            self.checkLogErrorToFile.grid(sticky=W)

        try:
            self.optionsMenu.focus()
        except Exception as e:
            logging.error('Exception : ' + str(e))

    def toggle_log_errors_to_file(self):
        """Change preference for logging errors to file."""

        if (bool(self.logErrorsToFile.get())):
            logging.getLogger().disabled = False
            logging.info("Logging Started")
            logging.info(self.VersionNumber)
        else:
            logging.info("Stop Logging")
            logging.getLogger().disabled = True

        self.save_toggles()

    def toggle_mirror_left_right_overlay(self):
        if (bool(self.mirrorLeftToRightOverlay.get())):
            self.customOverlayEntryRight.config(state=DISABLED)
            # write in the left version mirror
            leftString = self.customOverlayPreFormatStringLeft.get()
            leftList = leftString.split()
            leftList.reverse()
            rightString = " ".join(leftList)
            self.customOverlayPreFormatStringRight.set(rightString)
            self.save_custom_overlay_preformat_right()
        else:
            if(bool(self.useOverlayPreFormat.get())):
                self.customOverlayEntryRight.config(state=NORMAL)
        self.save_toggles()

    def save_custom_chat_preformat(self):
        if self.customChatOutputEntry:
            cco = self.customChatOutputPreFormatString.get()
            self.settings.data['customStringPreFormat'] = cco
        self.settings.save()
        return True  # must return true to a validate entry method

    def save_custom_overlay_preformat_left(self):
        if self.customOverlayEntryLeft:
            ospf = self.customOverlayPreFormatStringLeft.get()
            self.settings.data['overlayStringPreFormatLeft'] = ospf
        self.settings.save()
        return True  # must return true to a validate entry method

    def save_custom_overlay_preformat_right(self):
        if self.customOverlayEntryRight:
            ospf = self.customOverlayPreFormatStringRight.get()
            self.settings.data['overlayStringPreFormatRight'] = ospf
        self.settings.save()
        return True  # must return true to a validate entry method

    def toggle_use_overlay_preformat(self):
        if (bool(self.useOverlayPreFormat.get())):
            self.customOverlayEntryLeft.config(state=NORMAL)
            if (self.mirrorLeftToRightOverlay.get()):
                self.customOverlayEntryRight.config(state=DISABLED)
            else:
                self.customOverlayEntryRight.config(state=NORMAL)
        else:
            self.customOverlayEntryLeft.config(state=DISABLED)
            self.customOverlayEntryRight.config(state=DISABLED)
        self.save_toggles()

    def toggle_use_custom_preformat(self):
        if (bool(self.useCustomPreFormat.get())):
            self.customChatOutputEntry.config(state=NORMAL)
        else:
            self.customChatOutputEntry.config(state=DISABLED)
        self.save_toggles()

    def test_stats(self):
        logging.info("Testing Stats")
        if (self.ircClient):
            self.ircClient.queue.put('TEST')

    def automatic_trigger_toggle(self):
        if(bool(self.automaticTrigger.get())):
            # self.checkWriteIWonLostInChat.config(state=NORMAL)
            self.checkWritePlaceYourBetsInChat.config(state=NORMAL)
            self.checkClearOverlayAfterGame.config(state=NORMAL)
            self.checkAutomaticSetBettingOdds.config(state=NORMAL)
            if (self.ircClient):
                logging.info("in automatic trigger toggle")
                self.start_monitors()
        else:
            self.close_monitors()
            # self.checkWriteIWonLostInChat.config(state=DISABLED)
            self.checkWritePlaceYourBetsInChat.config(state=DISABLED)
            self.checkClearOverlayAfterGame.config(state=DISABLED)
            self.checkAutomaticSetBettingOdds.config(state=DISABLED)
        self.save_toggles()

    def save_toggles(self):
        self.settings.data['showOwn'] = bool(self.showOwn.get())

        self.settings.data['automaticTrigger'] = (
            bool(self.automaticTrigger.get()))

        self.settings.data['automaticSetBettingOdds'] = (
            bool(self.automaticSetBettingOdds.get()))

        self.settings.data['writeIWonLostInChat'] = (
            bool(self.writeIWonLostInChat.get()))

        self.settings.data['writePlaceYourBetsInChat'] = (
            bool(self.writePlaceYourBetsInChat.get()))

        self.settings.data['clearOverlayAfterGameOver'] = (
            bool(self.clearOverlayAfterGameOver.get()))

        self.settings.data['useOverlayPreFormat'] = (
            bool(self.useOverlayPreFormat.get()))

        self.settings.data['mirrorLeftToRightOverlay'] = (
            bool(self.mirrorLeftToRightOverlay.get()))

        self.settings.data['useCustomPreFormat'] = (
            bool(self.useCustomPreFormat.get()))

        self.settings.data['logErrorsToFile'] = (
            bool(self.logErrorsToFile.get()))

        self.settings.save()
        try:
            if self.ircClient:
                self.ircClient.settings = self.settings
        except Exception as e:
            logging.error(str(e))
            logging.exception('Exception : ')

    def on_close_options(self):
        self.optionsMenu.destroy()
        self.optionsMenu = None

    def disable_everything(self):
        self.buttonTwitchChannel.config(state=DISABLED)
        self.buttonSteamName.config(state=DISABLED)
        self.buttonSteam64IDNumber.config(state=DISABLED)
        self.buttonLocateWarningLog.config(state=DISABLED)
        self.buttonOptions.config(state=DISABLED)
        self.cohBrowseButton.config(state=DISABLED)
        self.entryTwitchChannel.config(state=DISABLED)

        self.entrySteam64IDNumber.config(state=DISABLED)
        self.entryWarningLogPath.config(state=DISABLED)
        self.entryRelicCOHPath.config(state=DISABLED)
        self.connectButton.config(state=DISABLED)
        self.testButton.config(state=DISABLED)

        # disabled if options displayed
        if self.optionsMenu:
            if self.entryBotAccountName:
                self.entryBotAccountName.config(state=DISABLED)
            if self.entryBotoAuthKey:
                self.entryBotoAuthKey.config(state=DISABLED)
            if self.buttonBotAccountName:
                self.buttonBotAccountName.config(state=DISABLED)
            if self.buttonBotOAuthKey:
                self.buttonBotOAuthKey.config(state=DISABLED)
            if self.buttonCSSFilePath:
                self.buttonCSSFilePath.config(state=DISABLED)

    def enable_buttons(self):
        self.buttonTwitchChannel.config(state=NORMAL)
        self.buttonSteamName.config(state=NORMAL)
        self.buttonSteam64IDNumber.config(state=NORMAL)
        self.buttonLocateWarningLog.config(state=NORMAL)
        self.buttonOptions.config(state=NORMAL)
        self.cohBrowseButton.config(state=NORMAL)
        self.connectButton.config(state=NORMAL)

        # enable if option frame is showing
        if self.optionsMenu:
            if self.buttonBotAccountName:
                self.buttonBotAccountName.config(state=NORMAL)
            if self.buttonBotOAuthKey:
                self.buttonBotOAuthKey.config(state=NORMAL)
            if self.buttonCSSFilePath:
                self.buttonCSSFilePath.config(state=NORMAL)

    def edit_steam_number(self):
        theState = self.entrySteam64IDNumber.cget('state')
        if(theState == "disabled"):
            self.disable_everything()
            self.buttonSteam64IDNumber.config(state=NORMAL)
            self.entrySteam64IDNumber.config(state=NORMAL)

        if(theState == "normal"):
            if self.check_steam_number(self.entrySteam64IDNumber.get()):
                self.entrySteam64IDNumber.config(state=DISABLED)
                self.enable_buttons()
                steam64ID = self.entrySteam64IDNumber.get()
                self.settings.data['steamNumber'] = steam64ID
                self.settings.save()
            else:
                messagebox.showerror(
                    "Invaid Steam Number", "Please enter your steam number\n"
                    "It Should be an integer 17 characters long")

    def edit_twitch_name(self):
        theState = self.entryTwitchChannel.cget('state')
        if(theState == DISABLED):
            self.disable_everything()
            self.entryTwitchChannel.config(state=NORMAL)
            self.buttonTwitchChannel.config(state=NORMAL)

        if(theState == NORMAL):
            if(self.special_match(self.entryTwitchChannel.get())):
                self.entryTwitchChannel.config(state=DISABLED)
                self.enable_buttons()
                self.settings.data['channel'] = self.entryTwitchChannel.get()
                self.settings.save()
            else:
                messagebox.showerror(
                    "Invalid Twitch channel",
                    "That doesn't look like a valid channel name\n"
                    "Twitch user names should be 4-24 characters long\n"
                    "and only contain letters numbers and underscores.")

    def edit_steam_name(self):
        theState = self.entrySteamName.cget('state')
        if(theState == DISABLED):
            self.disable_everything()
            self.entrySteamName.config(state=NORMAL)
            self.buttonSteamName.config(state=NORMAL)

        if(theState == NORMAL):
            self.entrySteamName.config(state=DISABLED)
            self.enable_buttons()
            self.settings.data['steamAlias'] = self.entrySteamName.get()
            self.settings.save()

    def edit_bot_name(self):
        theState = self.entryBotAccountName.cget('state')
        if(theState == "disabled"):
            self.disable_everything()
            self.buttonBotAccountName.config(state=NORMAL)
            self.entryBotAccountName.config(state=NORMAL)

        if(theState == "normal"):
            if(self.special_match(self.entryBotAccountName.get())):
                self.entryBotAccountName.config(state="disabled")
                self.enable_buttons()
                botacc = self.entryBotAccountName.get()
                self.settings.data['botUserName'] = botacc
                self.settings.save()
            else:
                messagebox.showerror(
                    "Invalid Twitch channel",
                    "That doesn't look like a valid Twitch user name\n"
                    "Twitch user names should be 4-24 characters long\n"
                    "and only contain letters numbers and underscores.")

    def edit_oauth_key(self):
        theState = self.entryBotoAuthKey.cget('state')
        if(theState == "disabled"):
            self.disable_everything()
            self.buttonBotOAuthKey.config(state=NORMAL)
            self.entryBotoAuthKey.config(state=NORMAL)

        if(theState == "normal"):
            if self.check_oauth_key(self.entryBotoAuthKey.get()):
                self.entryBotoAuthKey.config(state="disabled")
                self.enable_buttons()
                oAuth = self.entryBotoAuthKey.get()
                self.settings.data['botOAuthKey'] = oAuth
                self.settings.save()
            else:
                messagebox.showerror(
                    "Invaid OAuth Key",
                    "Please enter your bots OAuth Key\n"
                    "It Should be an 36 characters long and "
                    "start with oauth:\n"
                    "You can find it here https://twitchapps.com/tmi/")

    def special_match(
            self,
            strg,
            search=re.compile(r'^[a-zA-Z0-9][\w]{3,24}$').search
            ):
        if strg == "":
            return True  # empty returns True
        return bool(search(strg))
        # Allowed twitch username returns True,
        # if None, it returns False

    def check_oauth_key(self, oauthkey):
        try:
            if (oauthkey[:6] == "oauth:") or (oauthkey == ""):
                return True
            return False
        except Exception as e:
            logging.error(str(e))
            logging.exception("Exception : ")
            return False

    def check_steam_number(self, number):
        try:
            number = int(number)
            if isinstance(number, int):
                if (len(str(number)) == 17):
                    return True
            return False
        except Exception as e:
            logging.error(str(e))
            logging.exception("Exception : ")

    def locate_warning_log(self):
        self.disable_everything()
        self.master.filename = tkinter.filedialog.askopenfilename(
                initialdir="/",
                title="Select warning.log file",
                filetypes=(("log file", "*.log"), ("all files", "*.*")))
        logging.info("File Path : " + str(self.master.filename))
        print("File Path : " + str(self.master.filename))
        if(self.master.filename != ""):
            pattern = re.compile(r"\u20A9|\uFFE6|\u00A5|\uFFE5")
            # replaces both Won sign varients for korean language
            # and Yen symbol for Japanese language paths
            theFilename = re.sub(pattern, "/", self.master.filename)
            self.settings.data['logPath'] = theFilename.replace("/", '\\')
            self.entryWarningLogPath.config(state=NORMAL)
            self.entryWarningLogPath.delete(0, tkinter.END)
            logpath = self.settings.data.get('logPath')
            if logpath:
                self.entryWarningLogPath.insert(0, str(logpath))
            self.entryWarningLogPath.config(state=DISABLED)
            self.settings.save()
        self.enable_buttons()

    def locate_COH(self):
        self.disable_everything()
        self.master.filename = tkinter.filedialog.askopenfilename(
            initialdir="/",
            title="Select location of RelicCOH.exe file",
            filetypes=(("RelicCOH", "*.exe"), ("all files", "*.*")))
        logging.info("File Path : " + str(self.master.filename))
        print("File Path : " + str(self.master.filename))
        if(self.master.filename != ""):
            # set cohPath
            if (os.path.isfile(self.master.filename)):
                self.settings.data['cohPath'] = self.master.filename
            # set ucsPath
            d = os.path.dirname(self.master.filename)
            ucsPath = d + (
                "\\CoH\\Engine\\Locale\\English"
                "\\RelicCOH.English.ucs")
            if (os.path.isfile(ucsPath)):
                self.settings.data['cohUCSPath'] = ucsPath
            self.entryRelicCOHPath.config(state=NORMAL)
            self.entryRelicCOHPath.delete(0, tkinter.END)
            cohpath = self.settings.data.get('cohPath')
            if cohpath:
                self.entryRelicCOHPath.insert(0, str(cohpath))
            self.entryRelicCOHPath.config(state=DISABLED)
            self.settings.save()
        self.enable_buttons()

    def browse_CSS_file_path_button(self):
        self.disable_everything()
        cwd = os.getcwd()
        self.master.filename = tkinter.filedialog.askopenfilename(
            initialdir=cwd,
            title="Select location of CSS file",
            filetypes=(("css file", "*.css"), ("all files", "*.*")))
        if os.path.isfile(self.master.filename):
            self.master.filename = relpath(self.master.filename, cwd)
            logging.info("File Path : " + str(self.master.filename))
            print("File Path : " + str(self.master.filename))
        if(self.master.filename != ""):
            pattern = re.compile(r"\u20A9|\uFFE6|\u00A5|\uFFE5")
            # replaces both Won sign varients for korean language
            # and Yen symbol for Japanese language paths
            theFilename = re.sub(pattern, "/", self.master.filename)
            theFilename = theFilename.replace("/", '\\')
            self.settings.data['overlayStyleCSSFilePath'] = theFilename
            self.entryCSSFilePath.config(state=NORMAL)
            self.entryCSSFilePath.delete(0, tkinter.END)
            cssPath = self.settings.data.get('overlayStyleCSSFilePath')
            if cssPath:
                self.entryCSSFilePath.insert(0, str(cssPath))
            self.entryCSSFilePath.config(state=DISABLED)
            self.settings.save()
        self.enable_buttons()

    def connect_IRC(self, thread):
        if (
            self.check_steam_number(self.settings.data.get('steamNumber'))
            and self.special_match(self.settings.data.get('channel'))
            and os.path.isfile(self.settings.data.get('logPath'))
        ):
            # connect if there is no thread running
            # disconnect if thread is running
            if self.ircClient:
                # close thread
                try:
                    if(self.ircClient):
                        self.ircClient.close()
                    self.close_monitors()

                except Exception as e:
                    logging.error(str(e))
                    logging.exception("Exception : ")

                self.testButton.config(state=DISABLED)
                self.enable_buttons()
                self.connectButton.config(text="Connect")
                self.ircClient = None

            else:
                # start thread
                self.disable_everything()
                self.connectButton.config(text="Disconnect")
                self.testButton.config(state=NORMAL)
                self.ircClient = COHOpponentBot_IRC_Client.IRC_Client(
                    self.txt,
                    bool(self.consoleDisplayBool.get()),
                    settings=self.settings
                )
                self.ircClient.start()
                if (bool(self.settings.data.get('automaticTrigger'))):
                    self.start_monitors()
                self.connectButton.config(state=NORMAL)
        else:
            messagebox.showerror(
                "Invalid details",
                "Please check that your twitch username, Steam Number"
                " and warning.log file path are valid.")

    def start_monitors(self):
        # Ensure they are off if running
        self.close_monitors()
        # Create Monitor Threads and start them.
        if self.ircClient:
            self.automaticMemoryMonitor = MemoryMonitor(
                pollInterval=self.settings.data.get('filePollInterval'),
                ircClient=self.ircClient,
                settings=self.settings)
            self.automaticMemoryMonitor.start()

    def close_monitors(self):
        if self.automaticMemoryMonitor:
            self.automaticMemoryMonitor.close()

    def on_closing(self):
        logging.info("In on_closing program (Closing)")
        try:
            if(self.ircClient):
                self.ircClient.close()
            self.close_monitors()
        except Exception as e:
            logging.error(str(e))
            logging.exception("Exception : ")
        while (threading.active_count() > 1):
            pass
        logging.info("Exiting main thread")
        sys.exit()

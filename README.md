# COH_Opponent_Bot
Company of Heroes Opponent Chat Bot (IRC protocol) simple python socket implementation for twitch.tv


This program is for use in twitch chat for displaying COH 1v1 opponents to your viewers:

To execute it from source code:
Extract files to the same directory including the .ico file.
Make sure you have python (3) installed.
From the command line use. "python COHOpponentBot.py" (windows) "python3 COHOpponentBot.py" (Linux)

Python Dependencies :
requests
pyinstaller

These can be installed using pip or pip3 using pip install pyinstaller

On Windows you can compile a single executable using pyinstaller, the commands can be executed in the build.bat batch file.

# A precompiled windows 10 compatable executable can be downloaded :

HERE : https://xcoins.co.uk/Misc/COHOpponentBot.rar

To use the executable:

1. Execute the main file (COHOpponentBotGUI.exe) by double clicking on the icon. (Windows 10)
2. Check the information is correct, if not edit the fields using the buttons with your twitch user name, your Steam64ID*, and your company of heroes warning.log file location#
3. Click Connect and Start Streaming on twitch the usual way.
4. Any user typing "opponent" or "!opponent" or "!opp" or "opp" in chat will trigger the bot to find you opponents name, steam profile and coh1 1v1 stats.

if you also add a twitch username to the bot user name field you'll also need to add an OAuth key to the bot OAuth key field.
Doing so will connect using this user name as your bot. It is ok to use the same user account as your channel user or a different one.

Get your OAuth Key from twitch at this address  : https://twitchapps.com/tmi/

Your warning.log location should be found automatically... unless you have a non standard install or are running coh on mac or linux or some weird shit.
Your STEAM64 ID should be found automatically if you have previously run coh and set the warning.log correctly.

IF NOT:

* Your Steam64 ID can be found by:

  1.  Open up your Steam client and choose View, then click Settings
  2.  Choose Interface and check the box that reads, "Display Steam URL address when available"
  3.  Click OK
  4.  Now click on your Steam Profile Name and select View Profile

visit https://steamid.co/ and enter your steam account name if your ID number doesn't show up in the steam client URL

Your warning.log file location is typically found at (windows 10):

C:\Users\*YOURCOMPUTERACCOUNTNAME*\Documents\my games\Company of Heroes Relaunch\warning.log

NOTE:

AUTOMATIC MODE shows only the stats for the game you are currently in; eg basic (with computers), 1v1, 2v2, 3v3.

Automatic Trigger checks the game every 10 seconds and will trigger the opponent command automatically if it detects a new game.


Enjoy, 

XeReborn aka Xcom.

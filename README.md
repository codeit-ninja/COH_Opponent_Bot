# COH_Opponent_Bot


This COH_Opponent_Bot is a Company of Heroes (COH) Opponent Chat Bot that uses a simple python socket partial implementation of the IRC protocol for twitch.tv

For use with COH 1 only.

This program is for people who stream/broadcast COH1 games on twitch.tv to provide COH opponents information to their viewers:

It parses opponent data from the COH warning.log file and fetches opponent leaderboard statistic information from the Relic Server via a proxy web address.

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

HERE : https://github.com/XcomReborn/COH_Opponent_Bot/blob/master/dist/COHOpponentBot.rar

To use the executable:

1. Download the rar file and unrar (unzip) it into a new folder.
1. Execute the main file (COHOpponentBotGUI.exe) by double clicking on the icon.
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

# Twitch TV Chat Bot Commands

typing:

'opponent' or 
'!opponent' or
'!opp' or
'opp'

Will result in the bot displaying the selected statistic data in the twitch.tv chat.


# To use the overlay in OBS:

Prerequisite : https://obsproject.com/ (download from here, requires the browser plugin - default in the windows version)

1. Create a new source of type browser.
2. Set the size of the browser to the size of your stream output (eg: 1920 width x 1080 height)
3. Tick the box for using local file.
4. Setting the use custom frame rate tick box to true (on) and entering a frame rate of 2 in the FPS field will prevent the overlay from flickering.
5. Use the file browse button to point the browser at local file overlay.html in the programs base directory. (if overlay.html doesn't exist, run the program once and press test, this will create one)
6. If the created source doesn't fill the preview screen (it should if you set the resolution correctly) expand the source to overlay/cover the entire preview screen.
7. Done.

- The next time you get an opponent or type opp in chat or press the test button the overlay will show the opponents.
- The overlay custom output preformat string can be set in the options by pressing the options button.
- The overlay can be further customised if you alter the overlaystyle.css file manually file that will be created in the same directory as the overlay.html.



Enjoy, 

XeReborn aka Xcom.

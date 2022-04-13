import socket
import sys
import collections # for deque
from decimal import *
from random import choice
import os # to allow directory exists checking etc.
import os.path
from pymem.process import module_from_name # required for urllib certificates
from tkinter import *
import threading
from threading import Thread
from queue import Queue # to talk to the threads
import logging

#import all secret parameters from parameters file
from Classes.COHOpponentBot_Parameters import Parameters
from Classes.COHOpponentBot_IRC_Channel import IRC_Channel

#Here are the message lines held until sent
messageDeque = collections.deque()
toSend = False

class IRC_Client(threading.Thread):
	
	def __init__(self, output, consoleDisplayBool, parameters = None):

		Thread.__init__(self)

		self.output = output

		self.displayConsoleOut = consoleDisplayBool

		if parameters:
			self.parameters = parameters
		else:
			self.parameters = Parameters()	

		self.adminUserName = self.parameters.privatedata.get('adminUserName')	# This username will be able to use admin commands, exit the program and bypass some limits.

		#use botusername or get default if not set
		if (self.parameters.data.get('botUserName') == ""):
			self.nick = self.parameters.privatedata.get('IRCnick')				#This value is the username used to connect to IRC eg: "xcomreborn".
		else:
			self.nick = self.parameters.data.get('botUserName')
		
		self.channel = "#" + self.parameters.data.get('channel').lower() 		#The channel name for your channel eg: "#xcomreborn".
		
		#use botoauthkey or get default if not set
		if (self.parameters.data.get('botOAuthKey') == ""):
			self.password = self.parameters.privatedata.get('IRCpassword')			
		else:
			self.password = self.parameters.data.get('botOAuthKey')
		
		self.server = self.parameters.privatedata.get('IRCserver')
		self.port = self.parameters.privatedata.get('IRCport')
		self.relicServerProxy = self.parameters.privatedata.get('relicServerProxy')
	
		#create IRC socket
		try:
			self.irc = socket.socket()
		except Exception as e:
			logging.error("A problem occurred trying to connect")
			logging.error("In IRCClient")
			logging.error(str(e))
			logging.exception("Exception : ")			
			self.irc.close()
			sys.exit(0)
		
		#irc send message buffer
		self.ircMessageBuffer = collections.deque()

		self.running = True
		
		# Start checking send buffer every 3 seconds.

		self.CheckIRCSendBufferEveryThreeSeconds() # only call this once.	
		
		try:
			self.irc.connect((self.server, self.port))
		except Exception as e:
			logging.error("A problem occurred trying to connect")
			logging.error("In IRCClient")
			logging.error(str(e))
			logging.exception("Exception : ")
			self.irc.close()
			sys.exit(0)			

		#sends variables for connection to twitch chat
		self.irc.send(('PASS ' + self.password + '\r\n').encode("utf8"))
		self.irc.send(('USER ' + self.nick + '\r\n').encode("utf8"))
		self.irc.send(('NICK ' + self.nick + '\r\n').encode("utf8"))
		self.irc.send(('CAP REQ :twitch.tv/membership' + '\r\n').encode("utf8")) # sends a twitch specific request necessary to recieve mode messages
		self.irc.send(('CAP REQ :twitch.tv/tags'+ '\r\n').encode("utf8")) # sends a twitch specific request for extra data contained in the PRIVMSG changes the way it is parsed
		self.irc.send(('CAP REQ :twitch.tv/commands' + '\r\n').encode("utf8")) # supposidly adds whispers
		
		#start sub thread that uses shared Queue to communicate 
		# pass it irc for messaging, channel to join and queue
		self.queue = Queue()
		self.channelThread = IRC_Channel(self, self.irc, self.queue, self.channel, parameters=self.parameters)
		self.channelThread.start()

		#
		# Array to hold all the new threads	only neccessary if adding more channels
		#
		#threads = {}
		#threads[self.channel] = self.channelThread
		
	def run(self):
		self.running = True
		timeoutTimer = threading.Timer(5, self.connectionTimedOut)
		timeoutTimer.start()
		#create readbuffer to hold strings from IRC
		readbuffer = ""	
		self.irc.setblocking(0)	
		
		# This is the main loop
		while self.running:
			try:
				#maintain non blocking recieve buffer from IRC
				readbuffer= readbuffer+self.irc.recv(1024).decode("utf-8")
				temp=str.split(readbuffer, "\n")
				readbuffer=temp.pop( )
				for line in temp:
					self.queue.put(line)
					# send copy of recieved line to channel thread
					line=str.rstrip(line)
					line=str.split(line)
					logging.info (str(line).encode('utf8'))
					if (self.displayConsoleOut):
						try:
							message = "".join(line) + "\n"
							self.SendToOutputField(message)
						except Exception as e:
							logging.error("In run")
							logging.error(str(e))
							logging.exception("Exception : ")

					if (len(line) >= 3) and ("JOIN" == line[1]) and (":"+self.nick.lower()+"!"+self.nick.lower()+"@"+self.nick.lower()+".tmi.twitch.tv" == line[0]):
						#cancel auto closing the thread
						timeoutTimer.cancel()
						try:
							message = "Joined "+self.channel+" successfully.\n"
							self.SendToOutputField(message)
							message = "You can type 'test' in the " +self.channel[1:]+ " channel to say hello!\n"
							self.SendToOutputField(message)
						except Exception as e:
							logging.error(str(e))
							logging.exception("Exception : ")

					if(line[0]=="PING"):
						self.irc.send(("PONG %s\r\n" % line[0]).encode("utf8"))
			except Exception as e:
				pass

	def connectionTimedOut(self):
		try:
			message = "Connection to "+self.channel+" timed out, was the channel spelt correctly and is port 6667 open?\n"
			self.SendToOutputField(message)
		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")
		self.close()

	def close(self):
		self.queue.put("EXITTHREAD")
		logging.info("in close in thread")
		try:
			# send closing message immediately
			self.irc.send(("PRIVMSG " + self.channel + " :" + str("closing opponent bot") + "\r\n").encode('utf8'))
			while self.channelThread.is_alive():
				pass
			self.running = False
		except Exception as e:
			logging.error("In close")
			logging.error(str(e))
			logging.exception("Exception : ")
			
	def AssurePathExists(self, path):
		dir = os.path.dirname(path)
		if not os.path.exists(dir):
			os.makedirs(dir)
					
	def CheckIRCSendBufferEveryThreeSeconds(self):
		if (self.running == True): 
			threading.Timer(3.0, self.CheckIRCSendBufferEveryThreeSeconds).start()
		self.IRCSendCalledEveryThreeSeconds()
	# above is the send to IRC timer loop that runs every three seconds
	
	def SendPrivateMessageToIRC(self, message):
		self.SendToOutputField(message) # output message to text window
		message = ("PRIVMSG " + str(self.channel) + " :" + str(message) + "\r\n")
		self.ircMessageBuffer.append(message)   # removed this to stop message being sent to IRC		

	def SendWhisperToIRC(self, message, whisperTo):
		try:
			#whisper is currently disabled by twitch
			self.ircMessageBuffer.append("PRIVMSG " + str(self.channel) + " :/w " + str(whisperTo) + " " + str(message) + "\r\n")
		except Exception as e:
			logging.error("Error in SendWhisperToIRC")
			logging.error(str(e))
			logging.exception("Exception : ")

	def SendMessageToOpponentBotChannelIRC(self, message):
		try:
			self.ircMessageBuffer.append(("PRIVMSG " + str("#" + self.nick).lower() + " :" + str(message) + "\r\n"))
		except Exception as e:
			logging.error("Error in SendMessageToOpponentBotChannelIRC")
			logging.error(str(e))
			logging.exception("Exception : ")

	def SendToOutputField(self, message):
		try:
			#First strip characters outside of range that cannot be handled by tkinter output field
			char_list = '' 
			for x in range(len(message)): 
				if ord(message[x]) in range(65536):
					char_list += message[x]
			message = char_list
		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")
		try:
			self.output.insert(END, message + "\n")
		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")

	def IRCSendCalledEveryThreeSeconds(self):
		#print("called")
		if (self.ircMessageBuffer):
			try:
				#print("Buffered")
				stringToSend = str(self.ircMessageBuffer.popleft())
				print("string to send : " + stringToSend)
				self.irc.send((stringToSend).encode('utf8'))
			except Exception as e:
				logging.error("IRC send error:")
				logging.error("In IRCSendCalledEveryThreeSeconds")
				logging.error(str(e))
				logging.exception("Exception : ")
	#above is called by the timer every three seconds and checks for items in buffer to be sent, if there is one it'll send it

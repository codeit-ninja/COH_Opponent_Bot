







class FileMonitor (threading.Thread):

	def __init__(self, filePath, pollInterval = 30, ircClient = None, parameters = None):
		Thread.__init__(self)
		try:
			logging.info("File Monitor Started!")
			self.running = True

			if parameters:
				self.parameters = parameters
			else:
				self.parameters = Parameters()	

			self.ircClient = ircClient
			self.filePointer = 0
			self.pollInterval = int(pollInterval)
			self.filePath = filePath
			self.event = threading.Event()
			f = open(self.filePath, 'r' , encoding='ISO-8859-1')
			f.readlines()
			self.filePointer = f.tell()
			f.close()
			logging.info("Initialzing with file length : " + str(self.filePointer) + "\n")

		except Exception as e:
			logging.error("In FileMonitor __init__")
			logging.error(str(e))
			logging.exception("Exception : ")

	def run(self):
		try:
			logging.info ("Started monitoring File : " + str(self.filePath) + "\n")
			while self.running:
				lines = []
				clearOverlay = False
				f = open(self.filePath, 'r' , encoding='ISO-8859-1')
				f.seek(self.filePointer)
				lines = f.readlines()
				self.filePointer = f.tell()
				f.close()

				for line in lines:

					if ("Win notification" in line):
						#Check if streamer won
						theSteamNumber = self.find_between(line ,"/steam/" , "]")
						if (str(self.parameters.data.get('steamNumber')) == str(theSteamNumber)):
							logging.info("STREAMER WON\n")
							if (self.parameters.data.get('writeIWonLostInChat')):
								self.ircClient.queue.put("IWON")
							if (self.parameters.data.get('clearOverlayAfterGameOver')):
								clearOverlay = True
					if ("Loss notification" in line):
						#Check if streamer lost
						theSteamNumber = self.find_between(line ,"/steam/" , "]")
						if (str(self.parameters.data.get('steamNumber')) == str(theSteamNumber)):
							logging.info("STREAMER LOST\n")
							if (self.parameters.data.get('writeIWonLostInChat')):
								self.ircClient.queue.put("ILOST")
							if (self.parameters.data.get('clearOverlayAfterGameOver')):
								clearOverlay = True

				if (self.parameters.data.get('clearOverlayAfterGameOver')):
					if (clearOverlay):
						self.ircClient.queue.put("CLEAROVERLAY")
				self.event = threading.Event()
				self.event.wait(timeout = self.pollInterval)
			logging.info ("File Monitoring Ended.\n")
			#self.join()
		except Exception as e:
			logging.error("In FileMonitor run")
			logging.error(str(e))
			logging.exception("Exception : ")

	def close(self):
		logging.info("File Monitor Closing!")
		self.running = False
		# break out of loops if waiting
		if self.event:
			self.event.set()

	def find_between(self, s, first, last ):
		try:
			start = s.index( first ) + len( first )
			end = s.index( last, start )
			return s[start:end]
		except ValueError:
			return ""

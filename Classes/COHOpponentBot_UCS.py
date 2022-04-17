import logging
import os

from Classes.COHOpponentBot_Parameters import Parameters


class UCS:
	def __init__(self, ucsPath = None, parameters = None) -> None:
		
		self.parameters = parameters
		if not parameters:
			self.parameters = Parameters()

		self.ucsPath = ucsPath
		if not ucsPath:
			self.ucsPath = self.parameters.data.get('cohUCSPath')
		

	def compareUCS(self, compareString):
		try:
			if compareString:
				if (os.path.isfile(self.ucsPath)):
					with open(self.ucsPath, 'r',  encoding='utf16') as f:	
						for line in f:
							if len(line.split('\t')) > 1:
								firstString = str(line.split('\t')[0])
								if str(compareString[1:].strip()) == str(firstString):
									return " ".join(line.split()[1:])
		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")
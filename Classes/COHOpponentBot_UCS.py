from inspect import Parameter
import logging
import os


class UCS:
	def __init__(self, parameters = None) -> None:
		
		if parameters:
			self.parameters = parameters
		else:
			self.parameters = Parameter()	

		self.ucsPath = self.parameters.data.get('cohUCSPath')

	def compareUCS(self, compareString):
		try:
			if (os.path.isfile(self.ucsPath)):
				linenumber = 1
				with open(self.ucsPath, 'r',  encoding='utf16') as f:	
					for line in f:
						linenumber += 1
						firstString = str(line.split('\t')[0])
						if str(compareString[1:].strip()) == str(firstString):
							if len(line.split('\t')) > 1:
								return " ".join(line.split()[1:])
		except Exception as e:
			logging.error(str(e))
			logging.exception("Exception : ")
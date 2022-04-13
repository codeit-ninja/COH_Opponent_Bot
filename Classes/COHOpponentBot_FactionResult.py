import re
import logging
import datetime

class FactionResult():

	def __init__(self, faction = None, matchType = '-1',name = '-1', nameShort = '-1',leaderboard_id = '-1', wins = '-1', losses = '-1', streak = '-1', disputes = '-1', drops = '-1', rank = '-1', rankLevel = '-1', lastMatch = '-1'):
		self.faction = faction 
		self.matchType = re.sub(r"^-1\b", "", str(matchType))
		self.name = name
		self.nameShort = nameShort
		self.id = leaderboard_id
		self.wins = re.sub(r"^-1\b", "" ,str(wins))
		self.losses = re.sub(r"^-1\b", "" ,str(losses))
		self.streak = re.sub(r"^-1\b", "" ,str(streak))
		self.disputes = re.sub(r"^-1\b", "" ,str(disputes))
		self.drops = re.sub(r"^-1\b", "" ,str(drops))
		self.rank = re.sub(r"^-1\b", "" ,str(rank))
		self.rankLevel = re.sub(r"^-1\b", "" ,str(rankLevel))
		self.lastMatch = re.sub(r"^-1\b", "" ,str(lastMatch))
		self.lastTime = None
		self.winLossRatio = None
		try:
			if isinstance(self.lastMatch, str):
				if ((str(self.lastMatch) != "None") and (str(self.lastMatch) != "")):
					logging.info("self.lastMatch : " + str(self.lastMatch))
					ts = int(self.lastMatch)
					self.lastTime = str(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
		except Exception as e:
			logging.error("In factionResult Creating timestamp")
			logging.error(str(e))
			logging.exception("Exception : ")
		try:
			if (int(self.losses) != 0):
				self.winLossRatio = str(round(int(self.wins)/int(self.losses), 2))
			else:
				if(int(self.wins) > 0):
					self.winLossRatio = "Unbeaten"
		except Exception as e:
			logging.error("In factionResult Creating winLossRatio")
			logging.error(str(e))	
			logging.exception("Exception : ")


	def __str__(self):
		output = "Faction : " + str(self.name) + "\n"
		output += "Faction : " + str(self.faction) + "\n"
		output += "matchType : " + str(self.matchType) + "\n"
		output += "Short Name : "+ str(self.nameShort) + "\n"
		output += "Wins : " + str(self.wins) + "\n"
		output += "Losses : " + str(self.losses) + "\n"
		output += "Streak : " + str(self.streak) + "\n"
		output += "Disputes : " + str(self.disputes) + "\n"
		output += "Drops : " + str(self.drops) + "\n"
		output += "Rank : " + str(self.rank) + "\n"
		output += "Level : " + str(self.rankLevel) + "\n"
		output += "Last Time : " + str(self.lastMatch) + "\n"

		return output

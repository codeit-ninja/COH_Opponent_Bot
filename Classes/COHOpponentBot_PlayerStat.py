import logging
from Classes.COHOpponentBot_Faction import Faction
from Classes.COHOpponentBot_FactionResult import FactionResult
from Classes.COHOpponentBot_MatchType import MatchType


class PlayerStat:

    def __init__(self, statdata, steamNumber):

        # steamNumber is required in addition to statData
        # to compare the steamNumber to the internal profiles
        # that can contain other profile info
        self.leaderboardData = {}
        self.totalWins = 0
        self.totalLosses = 0
        self.totalWLRatio = None
        self.steamNumber = steamNumber
        self.profile_id = None
        self.alias = None
        self.country = None
        self.steamString = None
        self.steamProfileAddress = None
        self.cohstatsLink = None

        statString = "/steam/"+str(steamNumber)

        if statdata:
            if (statdata['result']['message'] == "SUCCESS"):

                if statdata['statGroups'][0]['members'][0]['alias']:
                    for item in statdata['statGroups']:
                        for value in item['members']:
                            if (value.get('name') == statString):
                                self.profile_id = value.get('profile_id')
                                self.alias = value.get('alias')
                                self.steamString = value.get('name')
                                self.country = value.get('country')
                if statdata.get('leaderboardStats'):
                    # print(json.dumps(statdata, indent=4, sort_keys= True))
                    # following number compare to leaderboard_id
                    # 0 is basic american
                    # 1 is basic wher
                    # 2 is basic commonWeath
                    # 3 is basic pe
                    # 4 is american 1v1
                    # 5 is wher 1v1
                    # 6 is commonWeath 1v1
                    # 7 is pe 1v1
                    # 8 is american 2v2
                    # 9 is wher 2v2
                    # 10 is commonweath 2v2
                    # 11 is pe 2v2
                    # 12 is american 3v3
                    # 13 is wher 3v3
                    # 14 is commonWeath 3v3
                    # 15 is pe 3v3
                    for item in statdata['leaderboardStats']:
                        # print(item)
                        if item.get('leaderboard_id') == 0:
                            self.leaderboardData[0] = FactionResult(
                                faction=Faction.US,
                                matchType=MatchType.BASIC,
                                name="Americans",
                                nameShort="US",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 1:
                            self.leaderboardData[1] = FactionResult(
                                faction=Faction.WM,
                                matchType=MatchType.BASIC,
                                name="Wehrmacht",
                                nameShort="WM",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 2:
                            self.leaderboardData[2] = FactionResult(
                                faction=Faction.CW,
                                matchType=MatchType.BASIC,
                                name="Commonwealth",
                                nameShort="CW",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 3:
                            self.leaderboardData[3] = FactionResult(
                                faction=Faction.PE,
                                matchType=MatchType.BASIC,
                                name="Panzer Elite",
                                nameShort="PE",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 4:
                            self.leaderboardData[4] = FactionResult(
                                faction=Faction.US,
                                matchType=MatchType.ONES,
                                name="Americans",
                                nameShort="US",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 5:
                            self.leaderboardData[5] = FactionResult(
                                faction=Faction.WM,
                                matchType=MatchType.ONES,
                                name="Wehrmacht",
                                nameShort="WM",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 6:
                            self.leaderboardData[6] = FactionResult(
                                faction=Faction.CW,
                                matchType=MatchType.ONES,
                                name="Commonwealth",
                                nameShort="CW",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 7:
                            self.leaderboardData[7] = FactionResult(
                                faction=Faction.PE,
                                matchType=MatchType.ONES,
                                name="Panzer Elite",
                                nameShort="PE",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 8:
                            self.leaderboardData[8] = FactionResult(
                                faction=Faction.US,
                                matchType=MatchType.TWOS,
                                name="Americans",
                                nameShort="US",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 9:
                            self.leaderboardData[9] = FactionResult(
                                faction=Faction.WM,
                                matchType=MatchType.TWOS,
                                name="Wehrmacht",
                                nameShort="WM",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 10:
                            self.leaderboardData[10] = FactionResult(
                                faction=Faction.CW,
                                matchType=MatchType.TWOS,
                                name="Commonwealth",
                                nameShort="CW",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 11:
                            self.leaderboardData[11] = FactionResult(
                                faction=Faction.PE,
                                matchType=MatchType.TWOS,
                                name="Panzer Elite",
                                nameShort="PE",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 12:
                            self.leaderboardData[12] = FactionResult(
                                faction=Faction.US,
                                matchType=MatchType.THREES,
                                name="Americans",
                                nameShort="US",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 13:
                            self.leaderboardData[13] = FactionResult(
                                faction=Faction.WM,
                                matchType=MatchType.THREES,
                                name="Wehrmacht",
                                nameShort="WM",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )
                        if item.get('leaderboard_id') == 14:
                            self.leaderboardData[14] = FactionResult(
                                faction=Faction.CW,
                                matchType=MatchType.THREES,
                                name="Commonwealth",
                                nameShort="CW",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                                )
                        if item.get('leaderboard_id') == 15:
                            self.leaderboardData[15] = FactionResult(
                                faction=Faction.PE,
                                matchType=MatchType.THREES,
                                name="Panzer Elite",
                                nameShort="PE",
                                leaderboard_id=item.get('leaderboard_id'),
                                wins=item.get('wins'),
                                losses=item.get('losses'),
                                streak=item.get('streak'),
                                disputes=item.get('disputes'),
                                drops=item.get('drops'),
                                rank=item.get('rank'),
                                rankLevel=item.get('ranklevel'),
                                lastMatch=item.get('lastMatchDate')
                            )

            for value in self.leaderboardData:
                try:
                    self.totalWins += int(self.leaderboardData[value].wins)
                except Exception as e:
                    logging.error(str(e))
                    logging.error(
                        f"Problem with totalwins value : {str(value)}"
                        f" data : {str(self.leaderboardData[value].wins)}"
                    )
                try:
                    self.totalLosses += int(self.leaderboardData[value].losses)
                except Exception as e:
                    logging.error(str(e))
                    logging.error(
                        f"Problem with totallosses value : {str(value)}"
                        f" data : {str(self.leaderboardData[value].losses)}"
                    )

            self.totalWins = str(self.totalWins)
            self.totalLosses = str(self.totalLosses)

            try:
                if (int(self.totalLosses) > 0):
                    self.totalWLRatio = str(round(
                        int(self.totalWins)/int(self.totalLosses), 2))

            except Exception as e:
                logging.error("In cohStat creating totalWLRatio")
                logging.error(str(e))
                logging.exception("Exception : ")

            if self.steamString:
                self.steamNumber = str(self.steamString).replace("/steam/", "")
                self.steamProfileAddress = (
                    f"steamcommunity.com/profiles/{str(self.steamNumber)}")
                self.cohstatsLink = (
                    f"playercard.cohstats.com/?steamid={str(self.steamNumber)}"
                )

    def __str__(self):

        output = ""
        for value in self.leaderboardData:
            output += str(self.leaderboardData[value])

        output += f"steamNumber : {str(self.steamNumber)}\n"
        output += f"profile_id : {str(self.profile_id)}\n"
        output += f"alias : {str(self.alias)}\n"
        output += f"country : {str(self.country)}\n"
        output += f"steamString : {str(self.steamString)}\n"
        output += f"steamProfileAddress : {str(self.steamProfileAddress)}\n"
        output += f"cohstatsLink : {str(self.cohstatsLink)}\n"
        output += "Totals\n"
        output += f"Wins : {str(self.totalWins)}\n"
        output += f"Losses : {str(self.totalLosses)}\n"
        output += f"W/L Ratio : {str(self.totalWLRatio)}\n"

        return output

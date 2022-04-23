import json
import logging
import os
import ssl
import urllib

from Classes.COHOpponentBot_Settings import Settings
from Classes.COHOpponentBot_PlayerStat import PlayerStat


class StatsRequest:
    """Contacts Relic COH1 server via proxy to get steam player data."""

    def __init__(self, settings=None):
        self.settings = settings
        if not settings:
            self.settings = Settings()

        # Declare instance variables for storing data
        # returned from server (nested List/Dictionary)
        self.userStatCache = None
        self.userMatchHistoryCache = None
        self.availableLeaderboards = None

    def return_stats(self, steam64ID) -> PlayerStat:
        try:
            self.get_user_stat_from_server(steam64ID)
            self.get_available_leaderboards_from_server()
            # Determine server response succeeded
            # and use it to create PlayerStat object
            result = self.userStatCache.get('result')
            if result:
                if (result.get('message') == "SUCCESS"):
                    result = self.availableLeaderboards.get('result')
                    if result:
                        if result.get('message') == "SUCCESS":
                            playerStat = PlayerStat(
                                self.userStatCache,
                                self.availableLeaderboards,
                                steam64ID)
                            return playerStat
        except Exception as e:
            logging.error("Problem in returnStats")
            logging.error(str(e))
            logging.exception("Exception : ")

    def get_user_stat_from_server(self, steam64ID):
        """Cache the user stats."""

        try:
            # check stat number is 17 digit
            # and can be converted to int if not int
            steam64ID = str(steam64ID)
            stringLength = len(steam64ID)
            assert(stringLength == 17)
            assert(int(steam64ID))

            if not os.environ.get('PYTHONHTTPSVERIFY', ''):
                if getattr(ssl, '_create_unverified_context', None):
                    context = ssl._create_unverified_context
                    ssl._create_default_https_context = context

            pd = self.settings.privatedata
            rs = pd.get('relicServerProxyStatRequest')
            response = urllib.request.urlopen(rs + str(steam64ID)).read()
            # Decode server response as a json into a
            # nested list/directory and store as instance variable
            self.userStatCache = json.loads(response.decode('utf-8'))

        except Exception as e:
            logging.error("Problem in returnStats")
            logging.error(str(e))
            logging.exception("Exception : ")

    def get_match_history_from_server(self, steam64ID) -> bool:
        """Cache the player match history."""

        try:
            # check stat number is 17 digit
            # and can be converted to int if not int
            steam64ID = str(steam64ID)
            stringLength = len(steam64ID)
            assert(stringLength == 17)
            assert(int(steam64ID))

            if not os.environ.get('PYTHONHTTPSVERIFY', ''):
                if getattr(ssl, '_create_unverified_context', None):
                    context = ssl._create_unverified_context
                    ssl._create_default_https_context = context

            pd = self.settings.privatedata
            mh = pd.get('relicServerProxyMatchHistoryRequest')
            response = urllib.request.urlopen(mh + str(steam64ID)).read()
            # Decode server response as a json into
            # a nested list/directory and store as instance variable
            self.userMatchHistoryCache = json.loads(response.decode('utf-8'))
            # Determine server response succeeded and use it
            # to create PlayerStat object
            if (self.userMatchHistoryCache['result']['message'] == "SUCCESS"):
                # implement custom match history class
                # and instatiate object here
                return True

        except Exception as e:
            logging.error("Problem in getMatchHistory")
            logging.error(str(e))
            logging.exception("Exception : ")

    def get_available_leaderboards_from_server(self) -> bool:
        """Cache the available leaderboards."""

        try:
            if not os.environ.get('PYTHONHTTPSVERIFY', ''):
                if getattr(ssl, '_create_unverified_context', None):
                    context = ssl._create_unverified_context
                    ssl._create_default_https_context = context

            pd = self.settings.privatedata
            rs = pd.get('relicServerProxyLeaderBoards')
            response = urllib.request.urlopen(rs).read()
            # Decode server response as a json into
            # a nested list/directory and store as instance variable
            self.availableLeaderboards = json.loads(response.decode('utf-8'))
            # Determine server response succeeded and use it
            # to create PlayerStat object
            if (self.availableLeaderboards['result']['message'] == "SUCCESS"):
                return True

        except Exception as e:
            logging.error("Problem in getMatchHistory")
            logging.error(str(e))
            logging.exception("Exception : ")

    def get_player_win_last_match(self, userSteam64Number):
        """Gets Win or Loss from match history."""

        if self.userMatchHistoryCache:
            if not userSteam64Number:
                userSteam64Number = self.settings.data.get('steamNumber')
            if userSteam64Number:
                playersProfileID = self.get_profile_ID(userSteam64Number)
                mostRecentMatch = self.get_most_recent_match()
                if mostRecentMatch:
                    matches = mostRecentMatch.get('matchhistoryreportresults')
                    for item in matches:
                        if str(playersProfileID) == str(item['profile_id']):
                            if str(item.get('resulttype')) == '1':
                                return True
                            else:
                                return False

    def get_most_recent_match(self):
        """Gets the players most recent match from match history."""

        if (self.userMatchHistoryCache):
            historyList = list()
            for item in self.userMatchHistoryCache.get('matchHistoryStats'):
                historyList.append(item)
            historyList = sorted(
                historyList,
                key=lambda d: d['completiontime'],
                reverse=True
            )
            if historyList:
                return historyList[0]

    def get_steam_number(self, profileID):
        """Gets a player steam number from match history."""

        try:
            if self.userMatchHistoryCache:
                mhr = self.userMatchHistoryCache['result']
                if (mhr['message'] == "SUCCESS"):
                    for item in self.userMatchHistoryCache['profiles']:
                        if (str(profileID) == item['profile_id']):
                            # name should look like this string
                            # "/steam/76561198416060362"
                            return str(item['name']).replace("/steam/", "")
        except Exception as e:
            logging.error("Problem in getSteamNumberFromProfilesByProfileID")
            logging.error(str(e))
            logging.exception("Exception : ")

    def get_profile_ID(self, steam64ID):
        """Gets the profile ID from match history."""

        try:
            if self.userMatchHistoryCache:
                mhr = self.userMatchHistoryCache['result']
                if (mhr['message'] == "SUCCESS"):
                    for item in self.userMatchHistoryCache['profiles']:
                        # name should look like this string
                        # "/steam/76561198416060362"
                        steamNumber = str(item['name']).replace("/steam/", "")
                        if (str(steam64ID) == steamNumber):
                            return item['profile_id']
        except Exception as e:
            logging.error("Problem in getProfileIDFromProfilesBySteamNumber")
            logging.error(str(e))
            logging.exception("Exception : ")

    def __str__(self) -> str:
        output = ""
        output += "User Stat Cache : \n"
        uc = self.userStatCache
        output += json.dumps(uc, indent=4, sort_keys=True)
        output += "\nUser Match History Cache :\n"
        mhc = self.userMatchHistoryCache
        output += json.dumps(mhc, indent=4, sort_keys=True)
        return output

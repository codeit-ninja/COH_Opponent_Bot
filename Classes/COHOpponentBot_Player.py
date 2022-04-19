from Classes.COHOpponentBot_Faction import Faction


class Player:

    def __init__(self, name=None, factionString=None, faction=None):
        self.name = name
        self.factionString = factionString
        self.faction = faction
        self.stats = None
        # This will be None for computers
        # but point to a playerStat Object for players

        if self.factionString == "axis":
            self.faction = Faction.WM
        if self.factionString == "allies":
            self.faction = Faction.US
        if self.factionString == "allies_commonwealth":
            self.faction = Faction.CW
        if self.factionString == "axis_panzer_elite":
            self.faction = Faction.PE

    def __str__(self):
        output = "name : {}\n".format(str(self.name))
        output += "factionString : {}\n".format(str(self.factionString))
        output += "faction : {}\n".format(str(self.faction))
        output += "stats : {}\n".format(str(self.stats))
        return output

    def __repr__(self):
        return str(self)

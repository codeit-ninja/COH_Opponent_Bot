from dataclasses import dataclass
import datetime
import logging
import threading

from Classes.COHOpponentBot_GameData import GameData
from Classes.COHOpponentBot_Parameters import Parameters
from Classes.COHOpponentBot_ReplayParser import ReplayParser



for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(format='%(asctime)s (%(threadName)-10s) [%(levelname)s] %(message)s', filename= 'PointerFinder.log',filemode = "w", level=logging.INFO)

started = datetime.datetime.now()


# not used but for reference
#mpPointerAddress = 0x00901EA8
#mpOffsets=[0xC,0xC,0x18,0x10,0x24,0x18,0x264]

# not used but for reference
#muniPointerAddress = 0x00901EA8
#muniOffsets=[0xC,0xC,0x18,0x10,0x24,0x18,0x26C]

# not used but for reference
#fuelPointerAddress = 0x00901EA8
#fuelOffsets = [0xC,0xC,0x18,0x10,0x24,0x18,0x268]

# check game is running by accessing player mp
#mp = self.pm.read_float(self.GetPtrAddr(int(self.baseAddress) + int(mpPointerAddress), mpOffsets))

# Pointer list:

myListOfCOHRECPointers = []

#1
#cohrecReplayAddress = 0x008F80E0
#cohrecOffsets = [0x10,0x20,0x160,0x4,0x118,0x110,0x0]
#myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

#2
#cohrecReplayAddress = 0x008F80E0
#cohrecOffsets = [0x10,0x20,0x160,0x4,0x110,0x110,0x0]
#myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

#3
#cohrecReplayAddress = 0x009017E8
#cohrecOffsets = [0x1C,0x0,0x80,0x2C,0x110,0x0]
#myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

#4
#cohrecReplayAddress = 0x009017E8
#cohrecOffsets = [0x1C,0x0,0x80,0x24,0x110,0x0]
#myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

#5
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x28,0x160,0x4,0x84,0x2C,0x110,0x0]
myListOfCOHRECPointers.append([cohrecReplayAddress,cohrecOffsets])

#6
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x28,0x160,0x4,0x84,0x24,0x110,0x0]
myListOfCOHRECPointers.append([cohrecReplayAddress,cohrecOffsets])

#7
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x4,0x160,0x4,0x118,0x110,0x0]
myListOfCOHRECPointers.append([cohrecReplayAddress,cohrecOffsets])

#8
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x4,0x160,0x4,0x110,0x110,0x0]
myListOfCOHRECPointers.append([cohrecReplayAddress,cohrecOffsets])

#9
#cohrecReplayAddress = 0x0090416C
#cohrecOffsets = [0x4,0x4,0x194,0x4,0x118,0x110,0x0]
#myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

#10
#cohrecReplayAddress = 0x0090416C
#cohrecOffsets = [0x4,0x8,0x194,0x4,0x118,0x110,0x0]
#myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

#11
#cohrecReplayAddress = 0x0090416C
#cohrecOffsets = [0x4,0x4,0x194,0x4,0x110,0x110,0x0]
#myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

#12
#cohrecReplayAddress = 0x0090416C
#cohrecOffsets = [0x4,0x8,0x194,0x4,0x110,0x110,0x0]
#myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

parameters = Parameters()

gameData = GameData()
gameData.GetCOHMemoryAddress()

loops = 0

event = threading.Event()


while gameData.GetCOHMemoryAddress():
    
    loops += 1

    logging.info(f"Loop : {loops}")
    for count, item in enumerate(myListOfCOHRECPointers):
        logging.info(f"{count} {item}")
        actualCOHRECMemoryAddress = gameData.GetPtrAddr(gameData.baseAddress + item[0], item[1])
        logging.info(f"actualCOHRECMemoryAddress {str(actualCOHRECMemoryAddress)}")
        if actualCOHRECMemoryAddress:
            try:
                startTimeReadMemory = datetime.datetime.now()
                replayByteData = gameData.pm.read_bytes(actualCOHRECMemoryAddress, 4000)
                endTimeReadMemory = datetime.datetime.now()
                logging.info(f"Time to read memory {str(endTimeReadMemory - startTimeReadMemory)}")
                if replayByteData[4:12] == bytes("COH__REC".encode('ascii')):
                    logging.info("Pointing to COH__REC")
                    startTimeProcessMemory = datetime.datetime.now()
                    replayByteData = bytearray(replayByteData)
                    replayParser = ReplayParser(parameters=parameters)
                    replayParser.data = bytearray(replayByteData)
                    success = replayParser.processData()
                    endTimeProcessMemory = datetime.datetime.now()
                    logging.info(f"Time to process replayByteDate : {str(endTimeProcessMemory - startTimeProcessMemory)}")
                    if success:
                        logging.info("Parsed successfully.")
                    else:
                        logging.info("Did not parse successfully.")
            except:
                logging.error("Not reading memory at this location properly")
                logging.exception("Exception : ")
        event.wait(10)

finished = datetime.datetime.now()


difference = (finished - started)

logging.info(f"Excution took {str(difference)}")





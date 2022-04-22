import datetime
import logging
import threading

from Classes.COHOpponentBot_GameData import GameData
from Classes.COHOpponentBot_Settings import Settings
from Classes.COHOpponentBot_ReplayParser import ReplayParser

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(
    format='%(asctime)s (%(threadName)-10s) [%(levelname)s] %(message)s',
    filename='PointerFinder.log',
    filemode="w",
    level=logging.INFO
)

started = datetime.datetime.now()

# not used but for reference
# mpPointerAddress = 0x00901EA8
# mpOffsets=[0xC,0xC,0x18,0x10,0x24,0x18,0x264]

# not used but for reference
# muniPointerAddress = 0x00901EA8
# muniOffsets=[0xC,0xC,0x18,0x10,0x24,0x18,0x26C]

# not used but for reference
# fuelPointerAddress = 0x00901EA8
# fuelOffsets = [0xC,0xC,0x18,0x10,0x24,0x18,0x268]

# Pointer list:

myListOfCOHRECPointers = []

# 1
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x28, 0x160, 0x4, 0x84, 0x2C, 0x110, 0x0]
myListOfCOHRECPointers.append([cohrecReplayAddress, cohrecOffsets])

# 2
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x28, 0x160, 0x4, 0x84, 0x24, 0x110, 0x0]
myListOfCOHRECPointers.append([cohrecReplayAddress, cohrecOffsets])

# 3
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x4, 0x160, 0x4, 0x118, 0x110, 0x0]
myListOfCOHRECPointers.append([cohrecReplayAddress, cohrecOffsets])

# 4
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x4, 0x160, 0x4, 0x110, 0x110, 0x0]
myListOfCOHRECPointers.append([cohrecReplayAddress, cohrecOffsets])

settings = Settings()

gameData = GameData()
gameData.get_COH_memory_address()

loops = 0

event = threading.Event()

timeTakenToSearchStart = datetime.datetime.now()
gameData.get_replayParser_by_search()
timeTakenToSearchEnd = datetime.datetime.now()
logging.info(
    "Time taken to get replay data by Search : "
    f"{str(timeTakenToSearchEnd-timeTakenToSearchStart)}"
)

while gameData.get_COH_memory_address():

    loops += 1

    logging.info(f"Loop : {loops}")
    for count, item in enumerate(myListOfCOHRECPointers):
        logging.info(f"{count} {item}")
        startGetPointer = datetime.datetime.now()
        actualCOHRECMemoryAddress = gameData.get_pointer_address(
            gameData.baseAddress + item[0],
            item[1]
        )
        endGetPointer = datetime.datetime.now()
        logging.info(
            f"Time to GetPtrAddr : {str(endGetPointer - startGetPointer)}"
        )
        logging.info(
            f"actualCOHRECMemoryAddress {str(actualCOHRECMemoryAddress)}"
        )
        if actualCOHRECMemoryAddress:
            try:
                startTimeReadMemory = datetime.datetime.now()
                replayByteData = gameData.pm.read_bytes(
                    actualCOHRECMemoryAddress, 4000
                )
                endTimeReadMemory = datetime.datetime.now()
                diff = endTimeReadMemory - startTimeReadMemory
                logging.info(
                    f"Time to read memory {str(diff)}"
                )
                if replayByteData[4:12] == bytes("COH__REC".encode('ascii')):
                    logging.info("Pointing to COH__REC")
                    startTimeProcessMemory = datetime.datetime.now()
                    replayByteData = bytearray(replayByteData)
                    replayParser = ReplayParser(parameters=settings)
                    replayParser.data = bytearray(replayByteData)
                    success = replayParser.process_data()
                    endTimeProcessMemory = datetime.datetime.now()
                    diff = endTimeProcessMemory - startTimeProcessMemory
                    logging.info(
                        f"Time to process replayByteDate : {str(diff)}"
                    )
                    if success:
                        logging.info("Parsed successfully.")
                    else:
                        logging.info("Did not parse successfully.")
            except Exception as e:
                logging.error(str(e))
                logging.error("Not reading memory at this location properly")
                logging.exception("Exception : ")
    event.wait(10)

finished = datetime.datetime.now()


difference = (finished - started)

logging.info(f"Excution took {str(difference)}")

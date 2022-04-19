import logging
import threading

from Classes.COHOpponentBot_GameData import GameData



for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(format='%(asctime)s (%(threadName)-10s) [%(levelname)s] %(message)s', filename= 'PointerFinder.log',filemode = "w", level=logging.INFO)

# Pointer list:

myListOfPointers = []

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
myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

#6
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x28,0x160,0x4,0x84,0x24,0x110,0x0]
myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

#7
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x4,0x160,0x4,0x118,0x110,0x0]
myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

#8
cohrecReplayAddress = 0x00902030
cohrecOffsets = [0x4,0x160,0x4,0x110,0x110,0x0]
myListOfPointers.append([cohrecReplayAddress,cohrecOffsets])

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



gameData = GameData()
gameData.GetCOHMemoryAddress()

loops = 0

event = threading.Event()

while gameData.GetCOHMemoryAddress():
    loops += 1
    logging.info(f"Loop : {loops}")
    for count, item in enumerate(myListOfPointers):
        logging.info(f"{count} {item}")
        actualCOHRECMemoryAddress = gameData.GetPtrAddr(gameData.baseAddress + item[0], item[1])
        logging.info(f"actualCOHRECMemoryAddress {str(actualCOHRECMemoryAddress)}")
        if actualCOHRECMemoryAddress:
            try:
                header = gameData.pm.read_bytes(actualCOHRECMemoryAddress, 8)
                if header[4:12] == bytes("COH__REC".encode('ascii')):
                    logging.info("Pointing to COH__REC")
            except:
                logging.error("Not reading memory at this location properly")
    event.wait(10)









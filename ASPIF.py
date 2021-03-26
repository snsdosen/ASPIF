#!/usr/bin/python3

#ASPIF python client
#snsdosen 2019-2021

import time
import serial
import sys
import array
from struct import pack
from datetime import datetime
import getopt
import os

global IDENTIFIER       #Firmware identifier

#Commands
global CMD_IDENTIFIER   #Get identifier
global CMD_VERSION      #Get version
global CMD_READ         #Read from flash
global CMD_WRITE        #Write to flash
global CMD_ERASE        #Erase flash
global CMD_INFO         #Print info of the connected chip
global CMD_PUSH         #Push data from client to buffer
global CMD_PULL         #Pull data from buffer to client

#Subcommands
global INFO_JEDEC       #Get JEDEC ID
global INFO_MAN_ID      #Get Manufacturer ID
global INFO_CAPACITY    #Get flash capacity

#Responese
global RES_OK           #Positive response
global RES_ERR          #Negative response
global RES_CONTINUE     #Continue feeding the input buffer
global RES_BUSY         #Busy keep alive

global mode             #Program working mode, erasing, reading, writing
global serialPort       #Serial port to comunicate on
global fileName         #File name to read to or write to
global fileSize         #Number of bytes to read or write
global serialObj        #Serial port object

global flashJEDEC       #JEDEC of flash chip
global flashMAN_ID      #Manufacturer ID of flash chip
global flashCapacity    #Capacity in bytes
global flashPageCount   #Number of frames found on the flash
global flashPageSize    #Size of the single frame

global appName
global appVersion
global execName         #Name of the executable/script

global currentAddress   #Active erasing/reading/writing address
global currentPacket    #Active reading or writing packet

IDENTIFIER = "ASPIF"

#Commands
CMD_IDENTIFIER =    0x58    #'X'
CMD_VERSION =       0x56    #'V'
CMD_READ =          0x52    #'R'
CMD_WRITE =         0x57    #'W'
CMD_ERASE =         0x45    #'E'
CMD_INFO =          0x49    #'I'
CMD_PUSH =          0x48    #'H'
CMD_PULL =          0x4C    #'L'

#Subcommands
INFO_JEDEC =        0x4A    #'J'
INFO_MAN_ID =       0x4D    #'M'
INFO_CAPACITY =     0x43    #'C'

#Responses
RES_OK =            'K'
RES_ERR =           'E'
RES_CONTINUE =      'C'
RES_BUSY =          'B'

appName = "ASPIF client"
appVersion = "0.2"
execName = "ASPIF.py"

#Variables
mode = ""
serialPort = ""
fileName = ""
fileSize = ""

flashJEDEC = ""
flashMAN_ID = ""
flashCapacity = ""
flashPageCount = ""
flashPageSize = 0

currentAddress = 0
currentPacket = bytearray()

#Show info about the application
def about():
    print (appName + " " + appVersion)

#Show application help
def help():
    success("Program usage:")
    print (execName + " <--h|--e|--r|--w|--i> --p (PortName) --f (FileName) --s (FileSize)")
    print ("\t--h, --help\t\tShow help screen")
    print ("\t--e, --erase\t\tFully erase flash")
    print ("\t--p, --port\t\tSpecify flasher tty port")
    print ("\t--r, --read\t\tRead data from flash to file")
    print ("\t--w, --write\t\tWrite data from file to flash")
    print ("\t--i, --info\t\tShow flash info (JEDEC ID, capacity, block size)")
    print ("\t--f, --file\t\tFile to read from or write to")
    print ("\t--s, --size\t\tSize of data (in bytes) to read or write")

#Show colored warning message
def warning(message):
    if os.name == "nt":
        print('Warning: ' + message)
    else:
        print('\x1b[1;33;40m' + 'Warning:' + '\x1b[0m ' + message)

#Show deal breaking message
def error(message):
    if os.name == "nt":
        print('Error: ' + message)
    else:
        print('\x1b[1;31;40m' + 'Error:' + '\x1b[0m ' + message)

#Show success message
def success(message):
    if os.name == "nt":
        print(message)
    else:
        print('\x1b[1;32;40m' + message + '\x1b[0m ')

#Confirm that we are talking to a correct device
def validate():
    serialObj.write(bytes([CMD_IDENTIFIER]))
    if(serialObj.readline().rstrip().decode("utf-8") != IDENTIFIER):
        error("Device not recognised")
        sys.exit()

#Command line arguments
opts, args = getopt.getopt(sys.argv[1:] , "heprwi:f:s" , [ "help" , "erase" , "port=" , "read" , "write", "info", "file=", "size="])

#about()

for opt, arg in opts:
    if opt in ("-h", "--help"):
        about()
        help()
        sys.exit()

    elif opt in ("-e", "--erase"):
        mode = "ERASE"

    elif opt in ("-p", "--port"):
        serialPort = arg

    elif opt in ("-r", "--read"):
        mode = "READ"

    elif opt in ("-w", "--write"):
        mode = "WRITE"

    elif opt in ("-i", "--info"):
        mode = "INFO"

    elif opt in ("-f", "--file"):
        fileName = arg

    elif opt in ("-s", "--size"):
        fileSize = arg

    else:
        help()
        sys.exit()

#Check if serial port was given
if serialPort == "":
    warning("no serial port specified")
    help()
    sys.exit()

#Check if file name is missing for read and write operations
if fileName == "" and (mode == "READ" or mode == "WRITE"):
    warning("no file name specified")
    help()
    sys.exit()

#Check if file size is missing for read and write operations
if fileSize == "" and (mode == "READ" or mode == "WRITE"):
    warning("no file size specified")
    help()
    sys.exit()

#Beginning of the program
try:
    serialObj = serial.Serial(port=serialPort, baudrate=115200, timeout=2)
except serial.SerialException:
    error("could not open port \"" + serialPort + "\"")
    sys.exit()

validate()

if mode == "ERASE":
    if os.name == "nt":
        print('Flash erase initiated')
    else:
        print('Flash \x1b[1;31;40m' + 'erase' + '\x1b[0m initiated')

    serialObj.write(bytes([CMD_ERASE]))

    #Poll busy status, acknowledge on end
    while serialObj.readline().rstrip().decode("utf-8") == RES_BUSY:
        sys.stdout.write(".")
        sys.stdout.flush()

    #Wait for acknowledge
    #if serialObj.readline().rstrip().decode("utf-8") != CMD_ERASE:
        #error("failed to receive erase acknowledge")
        #sys.exit()

    if os.name == "nt":
        print('\nErase complete!')
    else:
        print('\nErase \x1b[1;32;40m' + 'complete!' + '\x1b[0m')

elif mode == "READ":
    if os.name == "nt":
        print('Flash read initiated')
    else:
        print('Flash \x1b[1;32;40m' + 'read' + '\x1b[0m initiated')

    #Open file for writing
    file = open(fileName, 'wb')

    #Get number of packets to fetch based on the file size
    packetCount = int(fileSize) / 256
    currentAddress = 0

    for x in range(int(packetCount)):
        sys.stdout.write("Reading page: " + str(x + 1) + "/" + str(int(packetCount)))
        sys.stdout.flush()

        currentPacket = bytearray()

        currentAddress = x
        serialObj.write(bytes([CMD_READ, (currentAddress >> 8) & 0xFF, (currentAddress) & 0xFF]))

        #Send address MSB
        #currentPacket.append()
        #currentPacket.append((currentAddress) & 0xFF)

        #serialObj.write(currentPacket);

        #Wait for acknowledge
        if serialObj.readline().rstrip().decode("utf-8") != 'R':
            error("failed to receive read acknowledge")
            sys.exit()

        serialObj.write(bytes([CMD_PULL]));

        recvData = serialObj.read(256)
        sys.stdout.write("\r")
        sys.stdout.flush()

        file.write(recvData)

    if os.name == "nt":
        print('\nReading complete!')
    else:
        print('\nReading \x1b[1;32;40m' + 'complete!' + '\x1b[0m')

    file.close()

elif mode == "WRITE":
    if os.name == "nt":
        print('Flash write initiated')
    else:
        print('Flash \x1b[1;31;40m' + 'write' + '\x1b[0m initiated')

    #Open file for reading
    file = open(fileName, 'rb')

    #Get number of packets to write based on the file size
    packetCount = int(fileSize) / 256
    currentAddress = 0

    for x in range(int(packetCount)):
        sys.stdout.write("Writing page: " + str(x + 1) + "/" + str(int(packetCount)))
        sys.stdout.flush()

        currentPacket = bytearray()
        currentAddress = x

        #Push data to buffer on the flasher
        serialObj.write(bytes([CMD_PUSH]))

        #Some Arduinos (eg. Leonardo) crash when there is too much data in the buffer
        #so to be safe we need to upload chunks of 32 bytes at a time to not overflow the buffer
        for y in range(8):
            #Read data from file to array
            sentData = file.read(32)

            #Send it to flasher
            serialObj.write(sentData)

            #Wait for acknowledge
            if serialObj.readline().rstrip().decode("utf-8") != RES_CONTINUE:
                error("failed to receive continue acknowledge")
                sys.exit()

        serialObj.write(bytes([CMD_WRITE, (currentAddress >> 8) & 0xFF, (currentAddress) & 0xFF]))

        #Send address MSB
        #currentPacket.append()
        #currentPacket.append()

        #serialObj.write(currentPacket);

        #Wait for acknowledge
        if serialObj.readline().rstrip().decode("utf-8") != 'W':
            error("failed to receive write acknowledge")
            sys.exit()

        sys.stdout.write("\r")
        sys.stdout.flush()

    if os.name == "nt":
        print('\nWriting complete!')
    else:
        print('\nWriting \x1b[1;32;40m' + 'complete!' + '\x1b[0m')

    file.close()

elif mode == "INFO":
    if os.name == "nt":
        print('Flash info:')
    else:
        print('\x1b[1;32;40m' + 'Flash info' + '\x1b[0m:')

    serialObj.write(bytes([CMD_INFO]))
    serialObj.write(bytes([INFO_JEDEC]))
    flashJEDEC = serialObj.readline().rstrip().decode("utf-8")

    serialObj.write(bytes([CMD_INFO]))
    serialObj.write(bytes([INFO_MAN_ID]))
    flashMAN_ID = serialObj.readline().rstrip().decode("utf-8")

    serialObj.write(bytes([CMD_INFO]))
    serialObj.write(bytes([INFO_CAPACITY]))
    flashCapacity = serialObj.readline().rstrip().decode("utf-8")

    print("JEDEC: " + flashJEDEC)
    print("Manufacturer ID: " + flashMAN_ID)
    print("Capacity: " + flashCapacity + " bytes")

else:
    print (warning("no operation selected"))

serialObj.close()

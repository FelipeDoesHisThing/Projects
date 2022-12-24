import re
import time
import struct
import serial
import threading
from datetime import datetime, timedelta
from typing import List, Tuple, Union, Callable

import libs.Constants as Constants
from libs.Constants import SerialPacketIDs

PACKET_BUFFER_SIZE = 1000

# Struct Packing Documentation
# Format | Type                 | Size (bytes)
#---------------------------------------------
# c      | byte                 | 1
# b      | signed char          | 1
# B      | unsigned char        | 1
# h      | short                | 2
# H      | unsigned short       | 2
# i      | int                  | 4
# I      | unsigned int         | 4
# l      | long                 | 4  (apparently same size as int)
# L      | unsigned long        | 4
# q      | long long            | 8
# Q      | unsigned long long   | 8
# f      | float                | 4
# d      | double               | 8
# s      | char[]               | -
# p      | char[]               | -
# P      | void*                | -

# this dictionary keeps track of the serial interface objects that have been created and are still
# open, so that when ctrl+c is pressed, it can automatically terminate all the background 
# threads and close all the open ports.
# Keys are the COM ports
# Values are the objects
serialInterfaceObjectsOpen = {} # Do NOT add or remove from this

def CloseAllSerialInterfaceObjects() -> None:
    """
    THIS IS MEANT TO ONLY BE RUN WHEN KILLING THE PROGRAM.
    Closes all the serial interface objects that are still open.
    """
    keyValuePairs = list(serialInterfaceObjectsOpen.items())
    for _, interfaceObject in keyValuePairs:
        interfaceObject.DisconnectSerialPort()  


###################################################################################################
#<!--                                    Serial Port Interface                                  -->
###################################################################################################

class SerialPortInterface:
    def __init__(self, 
                 comPort: str, 
                 baudRate: int=9600, 
                 packetParsingFunc: Callable[[dict, int, bytearray], Tuple[dict, bytearray, bool]]=None,
                 packetInterruptFunc: Callable[[dict], bool]=None
                 ) -> None:
        """
        Creates a new Serial Port Interface object capable of reading both packets and strings, and writing packets.

        @param comPort (str)                   - The COM port to connect to (i.e. 'COM3')
        @param baudRate (int)                  - The Baud Rate to use on the serial port
        @param packetParsingFunc (Callable[[dict, int, bytearray], Tuple[dict, bytearray, bool]]) - A function that is used to 
                                                                                                   parse additional packets in 
                                                                                                   the background thread
        """
        self.__serPort = None               # the serial port object to read and write to
        self.__comPort = comPort            # the COM port
        self.__baudRate = baudRate          # the baud rate to use
        self.__readThread = None            # the background reading thread

        self.packetParsingFunc = packetParsingFunc     # A function that is used to parse additional packets in the background thread
        self.packetInterruptFunc = packetInterruptFunc # A function that is called whenever a packet is received. If false is returned, 
                                                       # it won't add that packet to the packet buffer. 
        
        self.serialStringInputBuffer = []   # Type: List[str] the input buffer that the reading thread appends to for serial println's
        self.serialPacketInputBuffer = []   # Type: List[dict] the input buffer that the reading thread appends to for packets

        self.serialStringInputBufferLock = threading.Lock() # The mutex lock for the string input buffer
        self.serialPacketInputBufferLock = threading.Lock() # The mutex lock for the packet input buffer

        self.ConnectSerialPort()
        

    ###################################################################################################
    #<!--                                  Connections                                              -->
    ###################################################################################################

    def ConnectSerialPort(self) -> None:
        """
        Connects the serial port to the member variable comPort in a blocking fashion.
        """
        print("Connecting Serial Port... ", end='', flush=True)

        while(self.__TryToInitSerialPort__() == False):
            time.sleep(0.5)

        # insert this object into the open serial interfaces
        serialInterfaceObjectsOpen[self.__comPort] = self

        print("Connected")


    def DisconnectSerialPort(self) -> None:
        """
        Disconnects the serial port and closes it. Also closes the reading thread if it is running.
        """
        print("Disonnecting Serial Port " + self.__comPort + "... ", end='', flush=True)
        self.StopReading()
        self.__serPort.close()
        self.__serPort = None

        # remove this object from the open serial interfaces
        serialInterfaceObjectsOpen.pop(self.__comPort, None)

        print("Disconnected")

        print("Unread Buffers after Disconnecting Serial Port ", end='')
        print("(String Buffer): ", end='')
        print(self.serialStringInputBuffer)
        print("(Packet Buffer): ", end='')
        print(self.serialPacketInputBuffer)
        


    ###################################################################################################
    #<!--                                  Write Packet                                             -->
    ###################################################################################################

    def WritePacket_PingRequest(self, sequenceNum: int=0) -> bool:
        """
        Writes a ping request packet over the serial port.

        @param sequenceNum (int)   - The sequence number to send

        @return (bool)   True: If the packet was successfully written.
                         False: If the packet was not successfully written.
        """
        packet = struct.pack('>I', sequenceNum)
        return self.__WritePacket__(SerialPacketIDs.PING_REQUEST_PACKET_ID, packet)


    def WritePacket_PingReply(self, sequenceNum: int=0) -> bool:
        """
        Writes a ping reply packet over the serial port.

        @param sequenceNum (int)   - The sequence number to send

        @return (bool)   True: If the packet was successfully written.
                         False: If the packet was not successfully written.
        """
        packet = struct.pack('>I', sequenceNum)
        return self.__WritePacket__(SerialPacketIDs.PING_REPLY_PACKET_ID, packet)


    ###################################################################################################
    #<!--                                  Read Packet                                              -->
    ###################################################################################################

    def WaitForPacket(self, packetID: int, delaySeconds: float=0.1, timeoutSeconds: float=None) -> dict:
        """
        Continuosly reads the serial buffer until the exact packet ID is matched.
        It is blocking.

        @param packetID (int)          - The packet ID to match
        @param delaySeconds (float)    - The amount of delay between checking whether there is a line available.
        @param timeoutSeconds (float)  - The amount of seconds before this method times out and returns None.
                                         If set to None, this method won't time out
            
        @return (dict)  - The packet matched or None on timeout
        """
        # Set the target time for the timeout
        timeoutTargetTime = None
        if timeoutSeconds:
            timeoutTargetTime = datetime.now() + timedelta(seconds=timeoutSeconds)

        packet = None
        match = False
        while (not match):
            packet = self.__ReadSerialPacketNonblocking__()
            if packet:
                match = (packet['packetID'] == packetID)

            # Check if we have hit the timeout
            if timeoutTargetTime and datetime.now() > timeoutTargetTime:
                return None

            time.sleep(delaySeconds)
        
        return packet


    def WaitForAnyPacketNoMatch(self, delaySeconds: float=0.1, timeoutSeconds: int=None) -> dict:
        """
        Continuosly reads the serial buffer until any packet is read
        It is blocking.

        @param delaySeconds (float)            - The amount of delay between checking whether there is a packet available.
        @param timeoutSeconds (float)          - The amount of seconds before this method times out and returns None.
                                                 If set to None, this method won't time out
            
        @return (dict)  - The packet matched or None on timeout
        """
        # Set the target time for the timeout
        timeoutTargetTime = None
        if timeoutSeconds:
            timeoutTargetTime = datetime.now() + timedelta(seconds=timeoutSeconds)

        while (True):
            if (self.PacketAvailable()):
                # read packet from serial port and check if it is a match
                packet = self.__ReadSerialPacketNonblocking__()
                if packet:
                    return packet

            # Check if we have hit the timeout
            if timeoutTargetTime and datetime.now() > timeoutTargetTime:
                return None

            time.sleep(delaySeconds)


    def WaitForAnyPacket(self, packetIDsToMatch: List[int], delaySeconds: float=0.1, timeoutSeconds: int=None) -> dict:
        """
        Continuosly reads the serial buffer until one of the packets in the array packetIDsToMatch is matched.
        It is blocking.

        @param packetIDsToMatch (List[int])    - The packet IDs to match
        @param delaySeconds (float)            - The amount of delay between checking whether there is a packet available.
        @param timeoutSeconds (float)          - The amount of seconds before this method times out and returns None.
                                                 If set to None, this method won't time out
            
        @return (dict)  - The packet matched or None on timeout
        """
        # Set the target time for the timeout
        timeoutTargetTime = None
        if timeoutSeconds:
            timeoutTargetTime = datetime.now() + timedelta(seconds=timeoutSeconds)

        packet = None
        match = False
        while (not match):
            # read packet from serial port and check if it is a match
            packet = self.__ReadSerialPacketNonblocking__()
            if packet:
                for packetID in packetIDsToMatch:
                    match = (packet['packetID'] == packetID)
                    if match:
                        break
                
            # Check if we have hit the timeout
            if timeoutTargetTime and datetime.now() > timeoutTargetTime:
                return None

            time.sleep(delaySeconds)

        return packet


    def WaitForAllPackets(self, packetIDsToMatch: List[int], delaySeconds: float=0.1, timeoutSeconds: int=None) -> List[dict]:
        """
        Continuosly reads the serial buffer until all of the packet IDs in the array
        packetIDsToMatch are matched. It doesn't matter the order in which they are matched.
        It is blocking, and only one packet ID from strsToMatch can match each packet.
        Will return None on timeout

        @param packetIDsToMatch (List[int])    - The packet IDs to match
        @param delaySeconds (float)            - The amount of delay between checking whether there is a packet available.
        @param timeoutSeconds (float)          - The amount of seconds before this method times out and returns None.
                                                 If set to None, this method won't time out.
            
        @return (List[dict])  - The packets matched or None on timeout
        """
        # Set the target time for the timeout
        timeoutTargetTime = None
        if timeoutSeconds:
            timeoutTargetTime = datetime.now() + timedelta(seconds=timeoutSeconds)

        # Create an array to keep track of which IDs are left to be matched
        packetIDsLeft = []
        for id in packetIDsToMatch:
            packetIDsLeft.append(id)

        # keep track of the patterns we already matched in an array of tuples.
        # Each tuple is (string: the string matched, int: the index in strsToMatch that it matched with)
        packetsFound = []

        # read packet from serial port until all strings have been found
        while (len(packetsFound) != len(packetIDsLeft)):
            packet = self.__ReadSerialPacketNonblocking__()
            if packet:
                for idx, packetID in enumerate(packetIDsLeft):
                    # if it hasn't been matched yet
                    if packetIDsLeft[idx] != None:
                        match = (packet['packetID'] == packetID)
                        if match:
                            packetsFound.append(packet)
                            packetIDsLeft[idx] = None
                            break
                
            # Check if we have hit the timeout
            if timeoutTargetTime and datetime.now() > timeoutTargetTime:
                return None

            time.sleep(delaySeconds)

        return packetsFound


    ###################################################################################################
    #<!--                                   Read Serial String                                      -->
    ###################################################################################################

    def WaitForSerialString(self, strToMatch: str, delaySeconds: float=0.1, timeoutSeconds: int=None) -> str:
        """
        Continuosly reads the serial buffer until the exact string is matched.
        It is blocking.

        @param strToMatch (str)        - The string to match (supports regex)
        @param delaySeconds (float)    - The amount of delay between checking whether there is a packet available.
        @param timeoutSeconds (float)  - The amount of seconds before this method times out and returns None.
                                        If set to None, this method won't time out.
            
        @return (str)  - The string matched or None on timeout
        """
        # Set the target time for the timeout
        timeoutTargetTime = None
        if timeoutSeconds:
            timeoutTargetTime = datetime.now() + timedelta(seconds=timeoutSeconds)

        # compile the string we want to match against into a pattern
        pattern = re.compile(strToMatch)

        # read line from serial port and check if it is a match
        match = False
        while (not match):
            line = self.__ReadSerialStringNonblocking__()
            if line:
                match = pattern.fullmatch(line)
                
            # Check if we have hit the timeout
            if timeoutTargetTime and datetime.now() > timeoutTargetTime:
                return None

            time.sleep(delaySeconds)

        return match.group(0)


    def WaitForAnySerialString(self, strsToMatch: List[str], delaySeconds: float=0.1, timeoutSeconds: int=None) -> Tuple[str, int]:
        """
        Continuosly reads the serial buffer until one of the strings in the array
        strsToMatch is matched.
        It is blocking.

        @param strsToMatch (List[str])     - The strings to match (supports regex)
        @param delaySeconds (float)        - The amount of delay between checking whether there is a packet available.
        @param timeoutSeconds (float)      - The amount of seconds before this method times out and returns None.
                                            If set to None, this method won't time out.
            
        @return (Tuple[str, int])
                - str         - The string matched or None on timeout
                - int         - The index of which of the strings in strsToMatch was matched or -1 on timeout
        """
        # Set the target time for the timeout
        timeoutTargetTime = None
        if timeoutSeconds:
            timeoutTargetTime = datetime.now() + timedelta(seconds=timeoutSeconds)

        # compile the strings we want to match against into a pattern
        patterns = []
        for strToMatch in strsToMatch:
            patterns.append(re.compile(strToMatch))

        # read line from serial port and check if it is a match
        idxMatched = -1
        match = False
        while (not match):
            line = self.__ReadSerialStringNonblocking__()
            if line:
                for idx, pattern in enumerate(patterns):
                    match = pattern.fullmatch(line)
                    if match:
                        idxMatched = idx
                        break

            # Check if we have hit the timeout
            if timeoutTargetTime and datetime.now() > timeoutTargetTime:
                return None, -1

            time.sleep(delaySeconds)

        return match.group(0), idxMatched


    def WaitForAnySerialString(self, delaySeconds: float=0.1, timeoutSeconds: int=None) -> Tuple[str, int]:
        """
        Continuosly reads the serial buffer until any serial string is available.
        It is blocking.

        @param delaySeconds (float)        - The amount of delay between checking whether there is a packet available.
        @param timeoutSeconds (float)      - The amount of seconds before this method times out and returns None.
                                            If set to None, this method won't time out.
            
        @return str   - The string matched or None on timeout
        """
        # Set the target time for the timeout
        timeoutTargetTime = None
        if timeoutSeconds:
            timeoutTargetTime = datetime.now() + timedelta(seconds=timeoutSeconds)

        # read line from serial port and check if it is a match
        while (True):
            if (self.SerialStringAvailable()):
                line = self.__ReadSerialStringNonblocking__()
                if line:
                    return line

            # Check if we have hit the timeout
            if timeoutTargetTime and datetime.now() > timeoutTargetTime:
                return None

            time.sleep(delaySeconds)


    def WaitForAllSerialStrings(self, strsToMatch: List[str], delaySeconds: float=0.1, timeoutSeconds: int=None) -> List[Tuple[str, int]]:
        """
        Continuosly reads the serial buffer until all of the strings in the array
        strsToMatch is matched. It doesn't matter the order in which they are matched.
        It is blocking, and only one string from strsToMatch can match each line.

        @param strsToMatch (List[str])     - The strings to match (supports regex)
        @param delaySeconds (float)        - The amount of delay between checking whether there is a packet available.
        @param timeoutSeconds (float)      - The amount of seconds before this method times out and returns None.
                                            If set to None, this method won't time out.
            
        @return (List[Tuple[str, int]])
                - str               - The string matched.
                - int               - The index of which of the strings in strsToMatch was matched.
        """
        # Set the target time for the timeout
        timeoutTargetTime = None
        if timeoutSeconds:
            timeoutTargetTime = datetime.now() + timedelta(seconds=timeoutSeconds)

        # compile the strings we want to match against into a pattern array
        patterns = []
        for strToMatch in strsToMatch:
            patterns.append(re.compile(strToMatch))

        # keep track of the patterns we already matched in an array of tuples.
        # Each tuple is (string: the string matched, int: the index in strsToMatch that it matched with)
        patternsMatched = []

        # read line from serial port until all strings have been found
        while (len(patternsMatched) != len(patterns)):
            line = self.__ReadSerialStringNonblocking__()
            if line:
                for idx, pattern in enumerate(patterns):
                    # if it hasn't been matched yet
                    if patterns[idx] != None:
                        match = pattern.fullmatch(line)
                        if match:
                            patternsMatched.append((match.group(0), idx))
                            patterns[idx] = None
                            break
                
            # Check if we have hit the timeout
            if timeoutTargetTime and datetime.now() > timeoutTargetTime:
                return None
                
            time.sleep(delaySeconds)

        return patternsMatched


    ###################################################################################################
    #<!--                                  Read Availability                                        -->
    ###################################################################################################

    def PacketAvailable(self) -> bool:
        """
        Returns true if there are packets available to read from the serial buffer

        @return (bool)  - True if at least one packet is available to read from the serial buffer
        """
        return (self.__GetPacketBufferLength__() > 0)


    def SerialStringAvailable(self) -> bool:
        """
        Returns true if there are serial strings available to read from the serial buffer

        @return (bool)    - True if at least one serial string is available to read from the serial buffer
        """
        return (self.__GetSerialStringBufferLength__() > 0)


    ###################################################################################################
    #<!--                                  Background Thread Stuff                                  -->
    ###################################################################################################

    def StartReading(self) -> None:
        """
        Starts a background reading thread, which will fill up the buffer with serial strings
        and packets as they arrive.
        """
        if self.__readThread == None:
            self.__readThread = ReadingThread(self)
            self.__readThread.setDaemon(True)
            self.__readThread.start()
        else:
            print("The reading thread was already running.")


    def StopReading(self) -> None:
        """
        Stops the background reading thread if it has been started.
        """
        if self.__readThread != None:
            self.__readThread.stop()
            self.__readThread = None

    
    ###################################################################################################
    #<!--                                  Private Methods (Don't Call)                             -->
    ###################################################################################################

    def __TryToInitSerialPort__(self) -> bool:
        """
        Attempts to connect the serial port to the member variable comPort.

        @return (bool)    - True if successfully connected to serial port
        """
        try:
            self.__serPort = serial.Serial(
                    port=self.__comPort,
                    baudrate=self.__baudRate,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    write_timeout=1)
            return True
        except Exception as e:
            print(e)
            return False


    def __WritePacket__(self, packetId: int, packet: bytearray) -> bool:
        """
        Writes the given packet bytes across the serial port with the given packet ID.
        The format of serial communication looks like this:
            `[Packet Number]+[Content]~

        @param packetId (int)      - The Packet's ID.
        @param packet (bytearray)  - The Packet's data to send.

        @return (bool)          - Whether the packet was successfully written or not
        """
        if self.__serPort.isOpen():
            try:
                self.__serPort.write("`".encode())
                self.__serPort.write((str(packetId)).encode())
                self.__serPort.write("+".encode())
                self.__serPort.write(packet)
                self.__serPort.write("~".encode())

                return True
            except serial.SerialTimeoutException:
                print("Serial Port Write Timout, Reconnecting...")
                
                # if the reading thread was running beforehand, we want to reconnect that too
                # after stopping it
                if self.__readThread != None:
                    reconnectReadThread = True
                self.StopReading()

                self.DisconnectSerialPort()
                self.ConnectSerialPort()

                # reconnect reading thread again
                if reconnectReadThread:
                    self.StartReading()

                return False
        else:
            return False


    def __ReadSerialPacketBlocking__(self, delay: float=0) -> dict:
        """
        Reads a single packet from the serial buffer that is filled from the reading thread.
        It will block until a packet is read from the buffer.
        Will return None if there are no packets to read and the thread is not running.

        @param delay (float)   - The amount of delay (seconds) between checking whether there is a packet available.

        @return (dict)  - The oldest read packet from the serial port, or None.
        """
        while not self.PacketAvailable():
            # if there are no lines available to read and the reading thread is not running,
            # we have entered an infinite loop
            if self.__readThread == None:
                print("__ReadSerialPacketBlocking__: Must call StartReading() to start the reading thread beforehand.")
                return None
            
            time.sleep(delay)

        return self.__PopPacket__()


    def __ReadSerialPacketNonblocking__(self) -> dict:
        """
        Reads a single packet from the serial buffer that is filled from the reading thread.
        It will block until a packet is read from the buffer.
        Will return None if there are no packets to read and the thread is not running.

        @return (dict)  - The oldest read packet from the serial port, or None if none are available.
        """
        if self.PacketAvailable():
            return self.__PopPacket__()

        # if there are no lines available to read, but this was called, log a warning and return None
        if self.__readThread == None:
            print("__ReadSerialPacketNonblocking__: Must call StartReading() to start the reading thread beforehand.")
        return None


    def __ReadSerialStringBlocking__(self, delay: float=0) -> str:
        """
        Reads a single line from the serial buffer that is filled from the reading thread.
        It will block until a line is read from the buffer.
        Will return None if there are no lines to read and the thread is not running.

        @param delay (float)   - The amount of delay (seconds) between checking whether there is a line available.

        @return (str)  - The oldest read line from the serial port, or None.
        """
        while not self.SerialStringAvailable():
            # if there are no lines available to read and the reading thread is not running,
            # we have entered an infinite loop
            if self.__readThread == None:
                print("__ReadSerialStringBlocking__: Must call StartReading() to start the reading thread beforehand.")
                return None
            
            time.sleep(delay)

        return self.__PopSerialString__()


    def __ReadSerialStringNonblocking__(self) -> str:
        """
        Reads a single line from the serial buffer that is filled from the reading thread.
        It will not block.
        Will return None if there are no lines to read.

        @return (str)  - The oldest read line from the serial port, or None.
        """
        if self.SerialStringAvailable():
            return self.__PopSerialString__()

        # if there are no lines available to read, but this was called, log a warning and return None
        if self.__readThread == None:
            print("__ReadSerialStringNonblocking__: Must call StartReading() to start the reading thread beforehand.")
        return None


    def __GetPacketBufferLength__(self) -> int:
        """
        Gets the length of the serialPacketInputBuffer in a thread-safe manner.

        @return (int)  - The length of the serialPacketInputBuffer
        """
        # Make sure accessing serialPacketInputBuffer is only done inside mutex
        self.serialPacketInputBufferLock.acquire()

        length = len(self.serialPacketInputBuffer)

        self.serialPacketInputBufferLock.release()
        return length


    def __GetSerialStringBufferLength__(self) -> int:
        """
        Gets the length of the serialStringInputBuffer in a thread-safe manner.

        @return (int)  - The length of the serialStringInputBuffer
        """
        # Make sure accessing serialStringInputBuffer is only done inside mutex
        self.serialStringInputBufferLock.acquire()

        length = len(self.serialStringInputBuffer)

        self.serialStringInputBufferLock.release()
        return length


    def __PopPacket__(self) -> dict:
        """
        Pops a packet from the serialPacketInputBuffer in a thread-safe manner.

        @return (dict)  - The packet popped, or None if the buffer is empty
        """
        packet = None
        self.serialPacketInputBufferLock.acquire()
        if (len(self.serialPacketInputBuffer) > 0):
            packet = self.serialPacketInputBuffer.pop(0)

        self.serialPacketInputBufferLock.release()
        return packet


    def __PopSerialString__(self) -> str:
        """
        Pops a packet from the serialStringInputBuffer in a thread-safe manner.

        @return (dict)  - The packet popped, or None if the buffer is empty
        """
        string = None
        self.serialStringInputBufferLock.acquire()
        if (len(self.serialStringInputBuffer) > 0):
            string = self.serialStringInputBuffer.pop(0)

        self.serialStringInputBufferLock.release()
        return string


    def __AppendPacket__(self, packet: dict) -> None:
        """
        Pops a packet from the serialPacketInputBuffer in a thread-safe manner.

        @param packet (dict)  - The packet to append to the serialPacketInputBuffer
        """
        self.serialPacketInputBufferLock.acquire()
        self.serialPacketInputBuffer.append(packet)
        self.serialPacketInputBufferLock.release()


    def __AppendSerialString__(self, string: str) -> None:
        """
        Pops a packet from the serialStringInputBuffer in a thread-safe manner.

        @param string (str)  - The string to append to the serialStringInputBuffer
        """
        self.serialStringInputBufferLock.acquire()
        self.serialStringInputBuffer.append(string)
        self.serialStringInputBufferLock.release()


    def ReadFromSerialPort_Blocking(self) -> Tuple[Union[bytearray, str], bool]:
        """
        Reads a single line directly from the serial port if one exists and returns it.
        This is meant to be called from background thread because it is blocking.

        @return (Tuple[Union[str, bytearray], bool])
                - Union[bytearray, str]
                    - bytearray   - The array of bytes that contain the packet's data.
                    - str         - The string read directly from the serial port, or None.
                - bool - True if we are reading a bytearray, False if we are reading a str
        """
        readStr = None
        try:
            readStr = self.__serPort.read_until()
        except Exception as e:
            print("Serial Port Read Failed: " + str(e))
            time.sleep(0.2)
            return None, False

        if readStr != None and readStr != "" and readStr != b'':
            # we are reading in a serial print
            if readStr[0] != "%".encode('ascii')[0]:
                try: 
                    readStr = readStr.decode("ascii").strip().strip("\\r\\n")
                    print("Serial Port Read: [" + readStr + "]")
                except:
                    print("Serial Port Decode Error: " + readStr)
                    readStr = "SerialInterface: DECODE ERROR"
                return readStr, False
            # we are reading in a packet
            else:
                return readStr, True
        return None, False


###################################################################################################
#<!--                                  Reading Thread (Private)                                 -->
###################################################################################################

class ReadingThread(threading.Thread):
    """
    This class represents a background reading thread that the SerialInterface class creates
    to read lines from the serial port and append them to a list.
    """

    def __init__(self, serialInstance: SerialPortInterface) -> None:
        """
        @param serialInstance (SerialPortInterface)  - The SerialInterface object that the thread will append 
                                                       the lines read from the serial port to.
        """
        threading.Thread.__init__(self)
        self.__isAlive = True
        self.__serialInstance = serialInstance # the SerialInterface class instance
        self.__packetParsingFunc = self.__serialInstance.packetParsingFunc
        self.__packetInterruptFunc = self.__serialInstance.packetInterruptFunc
 
        
    def run(self) -> None:
        """
        Method that is called when ReadingThread.start() is called.
        This runs in the background forever until stop() is called.
        It continuosly reads from the serial port and fills up a serial
        buffer inside the SerialInterface class instance.
        """
        while self.__isAlive:
            readStr, didReadPacket = self.__serialInstance.ReadFromSerialPort_Blocking()
            
            if readStr != None:
                if didReadPacket: # We are reading a packet
                    # Make sure that the serial packet buffer is large enough
                    if self.__serialInstance.__GetPacketBufferLength__() > PACKET_BUFFER_SIZE:
                        print("Serial Packet Buffer Full")
                    else:
                        packetID = -1         # The packetID to print to the LCD
                        readStr = readStr[1:] # remove the first char, which is '%'
                        try:
                            packetID = self.__ParsePacket__(readStr)
                        except Exception as e:
                            print("Could not parse packet. " + str(e))

                else: # We are reading a serial print

                    # Make sure that the serial message buffer is large enough
                    if self.__serialInstance.__GetSerialStringBufferLength__() > PACKET_BUFFER_SIZE:
                        print("Serial Message Buffer Full")
                    else:
                        self.__serialInstance.__AppendSerialString__(readStr)


    def stop(self) -> None:
        """
        This stops the thread from reading from the serial port continuously.
        """
        self.__isAlive = False

    
    def __ParsePacket__(self, packetBytes: bytearray) -> int:
        """
        Parses a single packet from packetBytes. Calls the unpacking methods
        to convert the bytes into actual data.

        @param packetBytes (bytearray)  - An array of bytes to parse the packet from.

        @return (int)  - The packet ID read
        """
        packet = {}
        packetID, packetBytes = ReadingThread.UnpackUint32_t(packetBytes)
        packet["packetID"] = packetID
        
        # Parse the universal serial packets
        if packetID == SerialPacketIDs.PING_REQUEST_PACKET_ID:
            packet['sequenceNum'], packetBytes     = ReadingThread.UnpackUint32_t(packetBytes)

        elif packetID == SerialPacketIDs.PING_REPLY_PACKET_ID:
            packet['sequenceNum'], packetBytes     = ReadingThread.UnpackUint32_t(packetBytes)

        # Parse the packets from the helper packet parsing method supplied to the SerialHubInterface constructor
        else:
            # We currently aren't using the bool return in the Tuple
            packet, packetBytes, _ = self.__packetParsingFunc(packet, packetID, packetBytes)

        print("Serial Port Read: [" + packet + "]")

        # Only add this packet to the packet buffer if the interrupt function dictates
        if self.__packetInterruptFunc(packet):
            self.__serialInstance.__AppendPacket__(packet)

        return packetID


    ###################################################################################################
    #<!--                          Unpacking Methods (these are static methods)                     -->
    ###################################################################################################

    # These methods unpack a data type from the packetBytes, which is of type bytearray.
    # They return a tuple
    #   - the data parsed
    #   - packetBytes with the parsed data bytes removed

    def UnpackUint64_t(packetBytes: bytearray) -> Tuple[int, bytearray]:
        return struct.unpack('<Q', packetBytes[0: 8])[0], packetBytes[8:]


    def UnpackUint32_t(packetBytes: bytearray) -> Tuple[int, bytearray]:
        return struct.unpack('<I', packetBytes[0: 4])[0], packetBytes[4:]

    
    def UnpackUint16_t(packetBytes: bytearray) -> Tuple[int, bytearray]:
        return struct.unpack('<H', packetBytes[0: 2])[0], packetBytes[2:]


    def UnpackUint8_t(packetBytes: bytearray) -> Tuple[int, bytearray]:
        return struct.unpack('<B', packetBytes[0: 1])[0], packetBytes[1:]


    def UnpackDouble(packetBytes: bytearray) -> Tuple[float, bytearray]:
        return struct.unpack('<d', packetBytes[0: 8])[0], packetBytes[8:]


    def UnpackFloat(packetBytes: bytearray) -> Tuple[float, bytearray]:
        return struct.unpack('<f', packetBytes[0: 4])[0], packetBytes[4:]
    

    def UnpackChar(packetBytes: bytearray) -> Tuple[str, bytearray]:
        return packetBytes[0], packetBytes[1:]
    

    def UnpackString(packetBytes: bytearray, strLen: int) -> Tuple[str, bytearray]:
        return packetBytes[0:strLen].decode("ascii").strip().strip("\\r\\n"), packetBytes[strLen:]

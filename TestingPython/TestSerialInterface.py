from typing import List, Tuple, Union
import struct
import time
import threading

import libs.Constants as Constants
from libs.Constants import SerialPacketIDs
from libs.SerialInterface import SerialPortInterface
from libs.SerialInterface import ReadingThread
import libs.SerialPortScanner as SerialPortScanner


###################################################################################################
#<!--                                  ButtonHandler Serial Port Interface                      -->
###################################################################################################

class TestSerialInterface(SerialPortInterface):
    def __init__(self) -> None:
        """
        Creates a serial interface for communicating with the ButtonHandler.
        """
        # Auto-detect the serial port if it is not set
        port = Constants.TEST_SERIAL_COM_PORT
        if (port == None):
            port = SerialPortScanner.GetTestSerialPortName()
            if (port == None):
                print('Could not create Test SerialInterface object')
                return
            else:
                print("Detected Test SerialInterface on port " + port)

        # Create the SerialPortInterface object and bind it to the SensorHubInterface class
        super().__init__(port, Constants.TEST_SERIAL_BAUD_RATE, 
                         self.__ParseTestSerialPacket__, self.__PacketReceived__)

        # We can now call any methods from SerialPortInterface using self rather than super()

        # Start reading on the backgrond thread
        self.StartReading()

    ###################################################################################################
    #<!--                                  Write Methods                                            -->
    ###################################################################################################

    def WritePacket_Int(self, value: int) -> bool:
        """
        Writes an LED packet over the serial port to turn an LED on or off.

        @param ledID (Constants.LedIDs) - The LED to control.
        @param state (bool)             - True to turn LED HIGH, or False to set it LOW

        @return (bool)    - True if the packet was successfully written.
        """
        packet = struct.pack('>I', value)
        return self.__WritePacket__(SerialPacketIDs.INT_PACKET_ID, packet)

    ###################################################################################################
    #<!--                          Parsing Packet Helper Functions (Don't Call)                     -->
    ###################################################################################################

    def __PacketReceived__(self, packet: dict) -> bool:
        """
        Is automatically called by SerialInterface after a packet is received and parsed.

        @param packet (dict)  - The packet received

        @return (bool) - Whether to add this packet to the serial packet buffer or not.
        """
        print("Received packet: " + packet)
        # We want to add all packets to the buffer
        return False


    def __ParseTestSerialPacket__(self, packet: dict, packetID: int, packetBytes: bytearray) -> Tuple[dict, bytearray, bool]:
        """
        Parses serial packets specific to the Test Serial Interface.

        @param packet (dict)           - The current packet to parse the data into
        @param packetID (int)          - The packetID to parse
        @param packetBytes (bytearray) - The bytes of the packet read over the serial port

        @return (Tuple[dict, bytearray, bool])
                - dict      - The parsed packet.
                - bytearray - The remaining bytes that were not parsed into the packet.
                - bool      - Whether the packet was parsed or not.
        """
        didParsePacket = False

        if packetID == SerialPacketIDs.INT_PACKET_ID:
            packet["value"], packetBytes    = ReadingThread.UnpackUint32_t(packetBytes)
            didParsePacket = True

        return (packet, packetBytes, didParsePacket)
import re
import serial
import serial.tools.list_ports
from typing import List, Tuple
from libs.Constants import TEST_SERIAL_DEVICE_NAME, IS_ON_PI

def GetSerialPorts() -> List[Tuple[str, str, str]]:
    """
    Retrieves the list of serial ports that are connected to the system

    @param packet (dict)           - The current packet to parse the data into
    @param packetID (int)          - The packetID to parse
    @param packetBytes (bytearray) - The bytes of the packet read over the serial port

    @return (List[Tuple[str, str, str]])
            - str   - The name of the serial port.
            - str   - The description of the device connected to the port.
            - str   - The hardware ID of the device connected to the port.
    """
    return serial.tools.list_ports.comports()


def GetTestSerialPortName():
    """
    Finds the name of the serial port that the Test Serial is connect to.

    @return (str)  - Returns the port name for Test Serial, or None if not found.
    """
    return __GetSerialPortByDeviceDescription__(TEST_SERIAL_DEVICE_NAME)


def __GetSerialPortByDeviceDescription__(description):
    """
    Finds the name of the first serial port that has a specified device description.

    @param description (str)   - The description to search for in the connected serial ports.

    @return (str)  - Returns the port name for the device, or None if not found.
    """
    connectedPorts = GetSerialPorts()

    for port, desc, hwid in sorted(connectedPorts):
        if IS_ON_PI:
            if (desc == description):
                return port
        else:
            # Windows includes the com port in the description like so.
            # description is `Arduino MKRZERO (COM6)` instead of `Arduino MKRZERO`
            pattern = re.compile('^(.*) \\(COM[1-9]+\\)$')
            match = pattern.match(desc)
            if (match != None) and (match.group(1) == description):
                return port

    print("Could not find serial port with device {description}. Is it connected?\n" +
          "Run this command to find connected device descriptions: 'python -m serial.tools.list_ports -v'")
    return None


def __GetSerialPortByHardwareID__(hardwareID):
    """
    Finds the name of the first serial port that has a specified hardware ID.

    @param hardwareID (str)   - The hardwareID to search for in the connected serial ports.

    @return (str)  - Returns the port name for the device, or None if not found.
    """
    connectedPorts = GetSerialPorts()

    for port, desc, hwid in sorted(connectedPorts):
        if (hwid == hardwareID):
            return port

    print("Could not find serial port with ID {hardwareID}. Is it connected?\n" +
          "Run this command to find connected device descriptions: 'python -m serial.tools.list_ports -v'")
    return None
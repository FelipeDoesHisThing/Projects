import sys
from enum import IntEnum, unique


# This is a constant that determines if the program is running on a Raspberry PI (Linux) or not (Windows)
IS_ON_PI = True if sys.platform == 'linux' else False

###################################################################################################
#<!--                                    Serial Constants                                       -->
###################################################################################################

# These are the connection parameters for Test Serial Interface
TEST_SERIAL_BAUD_RATE = 9600
TEST_SERIAL_COM_PORT = '/dev/serial0'             # This value gets set automatically at runtime if set to None
                                        # Set this to non-None value to override automatic port connecting like: '/dev/ttyACM1' or 'COM11'
TEST_SERIAL_DEVICE_NAME = 'ttyACM0'     # This can be found by connecting it and running the command `python -m serial.tools.list_ports -v`

# All Serial Packet IDs
@unique # Make sure each ID is unique
class SerialPacketIDs(IntEnum):
    # Range [0-199] Reserved for Base Serial Packet Types
    PING_REQUEST_PACKET_ID    = 0
    PING_REPLY_PACKET_ID      = 1

    # Range [600-699] Reserved for Test Serial Interface Packet Types
    INT_PACKET_ID             = 600

    # Type Conversion Methods
    def __get__(self, obj, objtype=None) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value

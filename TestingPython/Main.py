from time import sleep
import signal

# Make sure constants are loaded first to evaluate any runtime dependent constants before anything else is run
import libs.Constants as Constants
from libs.Constants import SerialPacketIDs
from libs.SerialInterface import CloseAllSerialInterfaceObjects
from TestSerialInterface import TestSerialInterface


def signal_handler(sig, frame):
    """
    Handler for catching ctrl+c, which closes all the open serial interfaces.
    """
    print("Exiting...")
    CloseAllSerialInterfaceObjects()
    print("Closed all Serial Port Interfaces")
    exit(0)

# setup signal to catch ctrl+c
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    uart = TestSerialInterface()
    uart.WritePacket_Int(12345)

    sleep(10)


# GCS has completely run through its control loop, so run cleanup and exit
print("\n\n---- GCS Finished Execution! ----")
# Call the signal handler for ctrl+c to properly destroy all the serial interface objects
signal_handler(None, None)
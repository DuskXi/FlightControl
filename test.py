import time

from loguru import logger

from Communication.RadioLayer import RadioConnector
from Communication.DataPacket import DataPacket


def main():
    radio_connector = RadioConnector()
    radio_connector.setRadio()
    radio_connector.startRadioCommunication()
    radio_connector.enableMessageLog = True
    while True:
        if len(radio_connector.recvBuffer) > 0:
            message = radio_connector.recvBuffer.pop(0)
            data: bytes = message["data"]
            # logger.debug(f"Received data(Raw): [{data}]")
            # logger.debug(f"Received data(Decoded): {data.decode('utf-8')}")
            # radio_connector.send(f'Successfully received data, size: [{len(data)}]'.encode("utf-8"))
        time.sleep(0.25)


if __name__ == "__main__":
    print()
    main()

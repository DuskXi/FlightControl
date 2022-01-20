import json
import threading
import time
from enum import Enum

import serial
import os
import re

from loguru import logger
from RadioCommunication.datapacket import DataPacket


def readFile(fileName, encoding='utf-8'):
    with open(fileName, encoding=encoding) as f:
        return f.read()


class RadioConnector:
    def __init__(self, configPath=None):
        if configPath is None:
            configPath = os.path.join(re.sub(r'[^\\/]+$', '', os.path.realpath(__file__)), "config.json")

        self.configPath = configPath
        self.config = json.loads(readFile(configPath))
        # read config
        self.channel = self.config['channel']
        self.baudRate = self.config['baudRate']
        self.serialName = self.config['serialName']
        self.dictBaudRate = self.config['dictBaudRate']
        self.settingBaudRate = self.config['settingBaudRate']
        self.templateSettingCommand = self.config['templateSettingCommand']

        self.timeout = 5
        self.serial = None
        self.recvBuffer = []
        self.recvThread = None
        self.dataPacket = DataPacket()
        self.connectionStatus = ConnectionStatus.Unknown

    def _openSerial(self, deviceName, baudRate):
        self.serial = serial.Serial(deviceName, baudRate, timeout=self.timeout)

    def _closeSerial(self):
        if self.serial is not None:
            self.serial.close()

    def setRadio(self):
        outputBuffer = ""
        start = None
        self._openSerial(self.serialName, self.settingBaudRate)
        while True:
            outputBuffer += self.serial.read_all().decode('utf-8')
            if re.match(r'^#1 UartConfig', outputBuffer):
                outputBuffer = ""
                command = self.templateSettingCommand.format(baudRate=self.baudRate, channel=self.channel)
                self.serial.write(command.encode('utf-8'))
                start = time.time()
            if start is not None:
                if time.time() - start > self.timeout:
                    logger.error('Set radio command timeout')
                    break
                if re.match(r'^#5 done', outputBuffer):
                    logger.info(f"Successfully set radio to: rate=[{self.baudRate}], channel=[{self.channel}]")
                    break
        self._closeSerial()

    def send(self, data: bytes):
        encoded = self.dataPacket.encode(data)
        for rawSize, escapedSize, encodedData in zip(encoded[0], encoded[1], encoded[2]):
            self.serial.write(encodedData)

    def recv(self):
        data = self.serial.read_all()
        outputBuffer = data
        while data == b'':
            data = self.serial.read_all()
            outputBuffer += data
        return outputBuffer

    def threadReceive(self):
        while self.connectionStatus == ConnectionStatus.Connected:
            buffer = self.recv()
            decoded = self.dataPacket.decode(buffer)
            if type(decoded) != bool:
                for decodedData in decoded:
                    self.recvBuffer.append({"data": decodedData, "time": time.time()})

    def startRadioCommunication(self):
        self._openSerial(self.serialName, self.baudRate)
        self.recvThread = threading.Thread(target=self.threadReceive)
        self.recvThread.start()


class ConnectionStatus(Enum):
    Connected = "Connected"
    Disconnected = "Disconnected"
    Unknown = "Unknown"

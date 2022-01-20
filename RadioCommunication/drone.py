import json
import time
from enum import Enum

import serial
import os
import re

from loguru import logger


def readFile(fileName, encoding='utf-8'):
    with open(fileName, encoding=encoding) as f:
        return f.read()


class RadioConnector:
    def __init__(self, configPath=None):
        if configPath is None:
            configPath = os.path.join(re.sub(r'[^\\/]+$', '', os.path.realpath(__file__)), "config.json")
        self.configPath = configPath
        self.config = json.loads(readFile(configPath))

        self.serialName = self.config['serialName']
        self.baudRate = self.config['baudRate']
        self.settingBaudRate = self.config['settingBaudRate']
        self.templateSettingCommand = self.config['templateSettingCommand']
        self.channel = self.config['channel']
        self.dictBaudRate = self.config['dictBaudRate']

        self.connectionStatus = ConnectionStatus.Unknown
        self.serial = None
        self.timeout = 5

    def _openSerial(self, deviceName, baudRate):
        self.serial = serial.Serial(deviceName, baudRate, timeout=self.timeout)

    def _closeSerial(self):
        self.serial.close()

    def setRadio(self):
        outputBuffer = ""
        start = None
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

    def send(self, data: bytes):
        self.serial.write(data)

    def recv(self):
        data = self.serial.read_all()
        outputBuffer = data
        while data == b'':
            data = self.serial.read_all()
            outputBuffer += data
        return outputBuffer

    def threadBuffer(self):
        buffer = b''
        index = 0
        while self.connectionStatus == ConnectionStatus.Connected:
            buffer += self.recv()
            if len(buffer) > 0:
                if buffer[index] == b'\\':
                    pass

    def startRadioCommunication(self):
        self._openSerial(self.serialName, self.baudRate)


class ConnectionStatus(Enum):
    Connected = "Connected"
    Disconnected = "Disconnected"
    Unknown = "Unknown"

import os
import struct
import sys
import threading
import time
from queue import Queue

import crcmod
import serial

import prettytable as pt
from reprint import output


class IMU:
    frame_header = 0xFC
    frame_end = 0xFD
    type_imu = 0x40
    len_imu = 56
    type_ahrs = 0x41
    len_ahrs = 48

    def __init__(self, com, baudRate=921600):
        self.com = com
        self.baudRate = baudRate
        self.serial = None

        self.serialBuffer: list = []
        self.framesBuffer: Queue = Queue()
        self.queueIMU: Queue = Queue()
        self.queueAHRS: Queue = Queue()
        self.imuData: list = []
        self.ahrsData: list = []

        self.isRunning = True

        self.receiveThread = None
        self.decodeThread = None
        self.IMUParseThread = None
        self.AHRSParseThread = None

    def connect(self):
        self.serial = serial.Serial(self.com, self.baudRate)

    def disconnect(self):
        self.serial.close()

    def startIMU(self):
        self.connect()
        self.receiveThread = threading.Thread(target=self.threadReceive)
        self.receiveThread.start()
        self.decodeThread = threading.Thread(target=self.threadDecode)
        self.decodeThread.start()
        self.IMUParseThread = threading.Thread(target=self.threadIMUParse)
        self.IMUParseThread.start()
        self.AHRSParseThread = threading.Thread(target=self.threadAHRSParse)
        self.AHRSParseThread.start()

    def removeInvalidData(self):
        for i in range(len(self.serialBuffer)):
            if self.serialBuffer[i] == IMU.frame_header:
                self.serialBuffer = self.serialBuffer[i:]
                break

    def threadReceive(self):
        while self.isRunning:
            data = self.serial.read_all()
            index = 0
            if data != '':
                buffer = list(data)
                self.serialBuffer += buffer

                if len(self.serialBuffer) > 0:
                    if self.serialBuffer[0] == IMU.frame_header:
                        for i in range(index, len(self.serialBuffer)):
                            if IMU.frame_end == self.serialBuffer[i]:
                                frame = self.serialBuffer[:i + 1]
                                if len(frame) >= 9:
                                    self.framesBuffer.put(frame)
                                self.serialBuffer = []
                                index = 0
                                break

                        if len(self.serialBuffer) > 263:
                            self.serialBuffer.pop(0)
                            self.removeInvalidData()
                    else:
                        self.removeInvalidData()
            time.sleep(0.0005)

    def threadDecode(self):
        while self.isRunning:
            if self.framesBuffer.qsize() > 0:
                frame: list = self.framesBuffer.get()
                header = bytes(frame[:5])
                headerChar, dataType, dataLength, number, CRC8 = struct.unpack('BBBBB', header)
                resultCRC8 = crcmod.mkCrcFun(0x107, rev=False)(header[:-1])
                if dataLength + 8 == len(frame):
                    CRC16 = struct.unpack("<H", bytes(frame[5:7]))
                    dataBody = bytes(frame[7:-1])
                    resultCRC16 = crcmod.mkCrcFun(0x18005)(dataBody)
                    if dataType == self.type_imu:
                        if dataLength == self.len_imu:
                            self.queueIMU.put(dataBody)
                    if dataType == self.type_ahrs:
                        if dataLength == self.len_ahrs:
                            self.queueAHRS.put(dataBody)
            time.sleep(0.001)

    def threadIMUParse(self):
        index = 0
        with output(output_type='dict') as output_lines:
            output_lines["Type"] = "Count"
            while self.isRunning:
                if self.queueIMU.qsize() > 0:
                    data = self.queueIMU.get()
                    information = struct.unpack("<ffffffffffffQ", data)
                    angularVelocityX, angularVelocityY, angularVelocityZ = information[0:3]
                    accelerationX, accelerationY, accelerationZ = information[3:6]
                    magneticInductionX, magneticInductionY, magneticInductionZ = information[6:9]
                    IMUTemp, Pressure, PressureTemp = information[9:12]
                    timeStamp = information[12]
                    self.imuData.append(
                        IMUData(angularVelocityX=angularVelocityX, angularVelocityY=angularVelocityY, angularVelocityZ=angularVelocityZ, accelerationX=accelerationX, accelerationY=accelerationY,
                                accelerationZ=accelerationZ, magneticInductionX=magneticInductionX, magneticInductionY=magneticInductionY, magneticInductionZ=magneticInductionZ, IMUTemp=IMUTemp,
                                Pressure=Pressure, PressureTemp=PressureTemp, timeStamp=timeStamp))

    def threadAHRSParse(self):
        while self.isRunning:
            if self.queueAHRS.qsize() > 0:
                data = self.queueAHRS.get()
                information = struct.unpack("<ffffffffffQ", data)
                rollSpeed, pitchSpeed, headingSpeed = information[0:3]
                roll, pitch, heading = information[3:6]
                Q1, Q2, Q3, Q4 = information[6:10]
                timeStamp = information[10]
                self.ahrsData.append(
                    AHRSData(rollSpeed=rollSpeed, pitchSpeed=pitchSpeed, headingSpeed=headingSpeed, roll=roll, pitch=pitch, heading=heading, Q1=Q1, Q2=Q2, Q3=Q3, Q4=Q4, timeStamp=timeStamp))

    def print(self):
        with output(output_type='dict') as output_lines:
            while self.isRunning:
                p = None
                p2 = None
                if len(self.imuData) > 0:
                    tableHeader = ['X轴角速度', 'Y轴角速度', 'Z轴角速度', 'X轴加速度', 'Y轴加速度', 'Z轴加速度', 'X轴磁感应', 'Y轴磁感应', 'Z轴磁感应', '温度', '时间戳']
                    imuData = self.imuData[-1]
                    tableData = [imuData.angularVelocityX, imuData.angularVelocityY, imuData.angularVelocityZ, imuData.accelerationX, imuData.accelerationY, imuData.accelerationZ,
                                 imuData.magneticInductionX, imuData.magneticInductionY, imuData.magneticInductionZ, imuData.IMUTemp, imuData.timeStamp]
                    tableData = ['%.6f' % round(x, 6) for x in tableData]
                    p = pt.PrettyTable()
                    p.field_names = tableHeader
                    p.add_row(tableData)

                if len(self.ahrsData) > 0:
                    tableHeader2 = ['翻滚角速度', '俯仰角速度', '航向角速度', '翻滚角', '俯仰角', '航向角', 'Q1', 'Q2', 'Q3', 'Q4', '时间戳']
                    ahrsData = self.ahrsData[-1]
                    tableData2 = [ahrsData.rollSpeed, ahrsData.pitchSpeed, ahrsData.headingSpeed, ahrsData.roll, ahrsData.pitch, ahrsData.heading, ahrsData.Q1, ahrsData.Q2, ahrsData.Q3, ahrsData.Q4,
                                  ahrsData.timeStamp]

                    tableData2 = ['%.6f' % round(x, 6) for x in tableData2]
                    p2 = pt.PrettyTable()
                    p2.field_names = tableHeader2
                    p2.add_row(tableData2)
                outputStr = ""
                if p is not None:
                    outputStr += f"{p}"

                if p2 is not None:
                    outputStr += f"\n{p2}"
                os.system('cls')
                print(outputStr)
                time.sleep(0.5)


class AttitudeData:
    def __init__(self, **kwargs):
        self.angularVelocityX = kwargs.get('angularVelocityX', 0)
        self.angularVelocityY = kwargs.get('angularVelocityY', 0)
        self.angularVelocityZ = kwargs.get('angularVelocityZ', 0)
        self.accelerationX = kwargs.get('accelerationX', 0)
        self.accelerationY = kwargs.get('accelerationY', 0)
        self.accelerationZ = kwargs.get('accelerationZ', 0)
        self.magneticInductionX = kwargs.get('magneticInductionX', 0)
        self.magneticInductionY = kwargs.get('magneticInductionY', 0)
        self.magneticInductionZ = kwargs.get('magneticInductionZ', 0)
        self.IMUTemp = kwargs.get('IMUTemp', 0)
        self.timeStamp = kwargs.get('timeStamp', 0)


class IMUData:
    def __init__(self, **kwargs):
        self.angularVelocityX = kwargs.get('angularVelocityX', 0)
        self.angularVelocityY = kwargs.get('angularVelocityY', 0)
        self.angularVelocityZ = kwargs.get('angularVelocityZ', 0)
        self.accelerationX = kwargs.get('accelerationX', 0)
        self.accelerationY = kwargs.get('accelerationY', 0)
        self.accelerationZ = kwargs.get('accelerationZ', 0)
        self.magneticInductionX = kwargs.get('magneticInductionX', 0)
        self.magneticInductionY = kwargs.get('magneticInductionY', 0)
        self.magneticInductionZ = kwargs.get('magneticInductionZ', 0)
        self.IMUTemp = kwargs.get('IMUTemp', 0)
        self.timeStamp = kwargs.get('timeStamp', 0)


class AHRSData:
    def __init__(self, **kwargs):
        self.rollSpeed = kwargs.get('rollSpeed', 0)
        self.pitchSpeed = kwargs.get('pitchSpeed', 0)
        self.headingSpeed = kwargs.get('headingSpeed', 0)
        self.roll = kwargs.get('roll', 0)
        self.pitch = kwargs.get('pitch', 0)
        self.heading = kwargs.get('heading', 0)
        self.Q1 = kwargs.get('Q1', 0)
        self.Q2 = kwargs.get('Q2', 0)
        self.Q3 = kwargs.get('Q3', 0)
        self.Q4 = kwargs.get('Q4', 0)
        self.timeStamp = kwargs.get('timeStamp', 0)

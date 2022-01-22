from enum import Enum

import RPi.GPIO as GPIO


class GPIOInterface:
    def __init__(self, gpioType):
        if gpioType not in [GPIO.BCM]:
            raise ValueError("Invalid GPIO type")

        self.gpioType = gpioType

        self.pinList = []
        self.pinStatusList = {}

        self.dictPWM = {}

    def initGPIO(self):
        GPIO.setmode(self.gpioType)

    def openPinIn(self, pin):
        GPIO.setup(pin, GPIO.IN)
        self.pinList.append(pin)
        self.pinStatusList[pin] = PinStatus.IN

    def openPinOut(self, pin):
        GPIO.setup(pin, GPIO.OUT)
        self.pinList.append(pin)
        self.pinStatusList[pin] = PinStatus.OUT

    def closePin(self, pin):
        GPIO.cleanup(pin)
        self.pinList.remove(pin)
        del self.pinStatusList[pin]

    def setLevel(self, pin, level):
        if pin not in self.pinList:
            raise ValueError("Pin not initialized")

        if self.pinStatusList[pin] == PinStatus.OUT:
            GPIO.output(pin, level)
        else:
            raise ValueError("Pin is not an output")

    def getLevel(self, pin):
        if pin not in self.pinList:
            raise ValueError("Pin not initialized")

        if self.pinStatusList[pin] == PinStatus.IN:
            return GPIO.input(pin)
        else:
            raise ValueError("Pin is not an input")

    def openPWM(self, pin, frequency):
        if pin in self.pinList:
            raise ValueError("Pin already used")

        self.pinList.append(pin)
        self.pinStatusList[pin] = PinStatus.PWM
        self.dictPWM[pin] = GPIO.PWM(pin, frequency)

    def changePWMFrequency(self, pin, frequency):
        if pin not in self.pinList:
            raise ValueError("Pin not initialized")

        if self.pinStatusList[pin] == PinStatus.PWM:
            self.dictPWM[pin].ChangeFrequency(frequency)
        else:
            raise ValueError("Pin is not a PWM")

    def changePWMDutyCycle(self, pin, dutyCycle):
        if pin not in self.pinList:
            raise ValueError("Pin not initialized")

        if self.pinStatusList[pin] == PinStatus.PWM:
            self.dictPWM[pin].ChangeDutyCycle(dutyCycle)
        else:
            raise ValueError("Pin is not a PWM")

    def closePWM(self, pin):
        if pin not in self.pinList:
            raise ValueError("Pin not initialized")

        if self.pinStatusList[pin] == PinStatus.PWM:
            self.dictPWM[pin].stop()
            self.pinList.remove(pin)
            del self.dictPWM[pin]
            del self.pinStatusList[pin]
        else:
            raise ValueError("Pin is not a PWM")

    def isPinActive(self, pin):
        if pin in self.pinList:
            return True
        else:
            return False

    def getPinStatus(self, pin):
        if pin in self.pinList:
            return self.pinStatusList[pin]
        else:
            raise ValueError("Pin not initialized")

    def getWholePinInformation(self):
        return {
            "type": self.gpioType,
            "activatedPinList": self.pinList,
            "pinStatusList": self.pinStatusList
        }


class PinStatus(Enum):
    IN = "In"
    OUT = "Out"
    PWM = "Pwm"

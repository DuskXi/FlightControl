import json

from Communication.RadioLayer import RadioConnector


class DataInterface:
    def __init__(self, configType, encoding="utf-8", configPath=None):
        self.radioConnector = RadioConnector(configType, configPath)
        self.radioConnector.callbackMessageUpdate = self.onMessageUpdate
        self.encoding = encoding
        self.jsonMessageBuffer = []
        self.shortMessageBuffer = []

    def connect(self):
        self.radioConnector.startRadioCommunication()

    def disconnect(self):
        self.radioConnector.stopRadioCommunication()

    def changeRadioSetting(self):
        self.radioConnector.setRadio()

    def sendNormal(self, data: dict):
        dataJson: str = json.dumps(data)
        dataComplete: str = "JSON-" + dataJson
        dataBytes = dataComplete.encode(self.encoding)
        self.radioConnector.send(dataBytes)

    def sendShort(self, data: bytes):
        dataBytes = "SHORT".encode(self.encoding) + data
        self.radioConnector.send(dataBytes)

    def onMessageUpdate(self):
        while self.radioConnector.hasMessage():
            message = self.radioConnector.getMessage()
            header: bytes = message["data"][:5]
            body: bytes = message["data"][5:]
            if header.decode(self.encoding) == "SHORT":
                self.shortMessageBuffer.append({"data": body.decode(self.encoding), "time": message["time"]})
            else:
                self.jsonMessageBuffer.append({"data": json.loads(body.decode(self.encoding)), "time": message["time"]})

    def getMessageNormal(self):
        if len(self.jsonMessageBuffer) > 0:
            message = self.jsonMessageBuffer.pop(0)
            return message["data"], message["time"]

        return None, None

    def getMessageShort(self):
        if len(self.shortMessageBuffer) > 0:
            message = self.shortMessageBuffer.pop(0)
            return message["data"], message["time"]

        return None, None

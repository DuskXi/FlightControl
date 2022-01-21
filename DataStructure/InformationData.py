from DataStructure.JsonModel import JObject


class InertiaInfo(JObject):
    def __init__(self, **kwargs):
        self.xAxisAcceleration: float = 0
        self.yAxisAcceleration: float = 0
        self.zAxisAcceleration: float = 0

        super().__init__(**kwargs)


class PowerInfo(JObject):
    def __init__(self, **kwargs):
        self.batteryVoltage: float = 0
        self.batteryCurrent: float = 0
        self.sensorPower: float = 0

        super().__init__(**kwargs)


class EngineInfo(JObject):
    def __init__(self, **kwargs):
        self.engine1Thrust: float = 0
        self.engine2Thrust: float = 0
        self.engine3Thrust: float = 0
        self.engine4Thrust: float = 0

        super().__init__(**kwargs)


class GPSInfo(JObject):
    def __init__(self, **kwargs):
        self.latitude: float = 0
        self.longitude: float = 0
        self.altitude: float = 0
        self.speed: float = 0
        self.course: float = 0

        super().__init__(**kwargs)

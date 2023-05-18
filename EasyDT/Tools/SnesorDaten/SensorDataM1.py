import pymongo
import datetime
import logging
import pprint
import time
from collections import UserList
import uuid


class SensorDataM1(UserList):
    """
    M1:Methode1. Daten are saved as a list. A class for saving a timeserie Data from a Sensor. It is a extension of list:Python. It kann use append() like list to add a value. And you could also use dict(A Instance of SensorData) to create a Dict, which include ["sensorID", "values", "startTime", "stopTime", "deltaTime", "sensorArt"(Opt. unless it is gived.)]. The Start and Stoptime will be updated after the first value is inserted and neu value is inserted. You can also manuell set time with function setStartTime() and setStopTime(), but please remember the workflow: newvalue->set Time manuelly -> result!

    Attributes:
        dataUnit:str The Unit of the Data
        sensorID:str The ID of sensor
        sensorArt:str[opt] The Art of Sensor, like "TemperaturSensor..."

    Functions:
    setStartTime()->None
    setStopTime()->None
    getStartTime()->datetime.datetime
    getEndTime()->datetime.datetime
    getDeltaTimeMS()->float
    getDeltaTime()->float
    append()->None
    getSensorID()->str
    getObjID()->str
    getValues()->list
    getWithUnit()->dict(values:[],"unit":str)
    getUnit()->str
    getfreq()->float
    """

    def __init__(
        self,
        dataUnit: str,
        objID: str,
        sensorID: str,
        # uri: str,
        sensorArt: str | None = "",
        description:str|None = ""
    ):
        super().__init__()
        self.__startTime = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        self.__stopTime = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        self.__counter = 0
        self.__sensorID = sensorID
        self.__objID = objID
        self.__unit = dataUnit
        self.__sensorArt = sensorArt
        # self.__uri = uri
        self.__description = description
        if not self.__sensorArt:
            logging.warning("Sensor name is not defined!")

    def __updateStopTime(self):
        self.__stopTime = datetime.datetime.now()

    def __updateStartTime(self):
        self.__startTime = datetime.datetime.now()

    def setStartTime(self, time: datetime.datetime):
        """set Starttime manulle"""
        self.__startTime = time

    def setStopTime(self, time: datetime.datetime):
        """set Stoptime manulle"""
        self.__stopTime = time

    def insert(self, *args, **kwrgs):
        raise Exception("You should not add a sensor Data at first place!!")
    

    def pop(self, item):
        raise Exception("You should not remove sensor Data!!")

    def remove(self, item):
        raise Exception("You should not remove sensor Data!!")

    def append(self, item):
        """Add a value. The updateEndTime will be updated. UpdateStartTime is only updated, when the first value is added."""
        if not self:
            self.__updateStartTime()
        super().append(item)
        self.__updateStopTime()
        self.__counter += 1

    def extend(self, iter):
        logging.warning(
            "You are trying to add many values at onetime. Are you sure? you are supposed to add values one by one"
        )
        if not self:
            self.__updateStartTime()
        __counter_before = self.__counter
        super().extend(iter)
        self.__counter += len(self) - __counter_before
        self.__updateStopTime()

    def __add__(self, item):
        self.__updateStopTime()
        self.__counter += 1
        super().__add__(item)

    def getStartTime(self) -> datetime.datetime:
        """Get strat update time"""
        return self.__startTime

    def getEndTime(self) -> datetime.datetime:
        """Get end update time"""
        return self.__stopTime

    def getDeltaTimeMS(self) -> float:
        """Get Time difference in millisecond"""
        return float((self.__stopTime - self.__startTime).total_seconds() * 1000)

    def getDeltaTime(self) -> float:
        """Get Time difference in second"""
        return float((self.__stopTime - self.__startTime).total_seconds())

    def getSensorID(self) -> str:
        return self.__sensorID

    def getObjID(self) -> str:
        return self.__objID

    # def getUri(self) -> str:
    #     return self.__uri

    def getValues(self) -> list:
        return list(self)

    def getUnit(self) -> str:
        """"""
        return self.__unit

    def getWithUnit(self) -> dict:
        """Export values with Unit"""
        return {"values": list(self), "unit": self.__unit}

    def getFreq(self) -> float:
        """return the update rate"""
        return round(self.__counter / self.getDeltaTime(), 4)

    def keys(self) -> list[str]:
        __keys = [
            "sensorID",
            "objID",
            "values",
            "startTime",
            "stopTime",
            "deltaTime",
            "freq",
            "sensorArt",
            "unit",
            # "uri",
        ]
        if not self.__sensorArt:
            __keys.remove("sensorArt")

        return __keys

    def __getitem__(self, __i):
        if isinstance(__i, str):
            res = {
                "sensorID": self.__sensorID,
                "objID": self.__objID,
                # "uri": self.__uri,
                "values": list(self),
                "startTime": self.__startTime,
                "stopTime": self.__stopTime,
                "deltaTime": self.getDeltaTimeMS(),
                "freq": self.getFreq(),
                "unit": self.__unit,
            }
            return res[__i]

        else:
            return super().__getitem__(__i)

    def exportLikeJson(self):
        return dict(self)

    def getMongoDoc(self):
        return {
            "timeField": {"startTime": self.__startTime, "stopTime": self.__stopTime},
            "metaField": {
                "sensorID": self.__sensorID,
                "objID": self.__objID,
                # "uri": self.__uri,
                "freq": self.getFreq(),
                "unit": self.__unit,
                "description":self.__description,
            },
            "value": list(self),
        }
    def clear(self):
        print("List is Empty!")
        super().clear()

if __name__ == "__main__":
    # client = pymongo.MongoClient(port=27018)
    # mydb = client["testdb"]
    # mycol = mydb["testcol"]
    # document = {"numbers": [1.1, 5.2, 2, 0.1, 9, 1, 3, 4, 4, 2, 2]}
    # id = mycol.insert_one(document).inserted_id
    # print(mycol.find_one({"_id": id}))

    sensor1 = SensorDataM1(
        sensorID=str(uuid.uuid4()),
        objID=str(uuid.uuid4()),
        dataUnit="Cercius",
        # uri="Optical.UVLicht.Kleben.Temperatur",
    )
    for x in range(10):
        sensor1.append(x)
        time.sleep(0.1)

    pprint.pprint(sensor1.getStartTime())
    pprint.pprint(sensor1.getEndTime())
    pprint.pprint(sensor1.getDeltaTime())
    pprint.pprint(sensor1.getDeltaTimeMS())
    pprint.pprint(sensor1.getSensorID())
    pprint.pprint(sensor1.getValues())
    pprint.pprint(sensor1.getUnit())
    pprint.pprint(sensor1.getWithUnit())
    pprint.pprint(sensor1.__dict__)
    pprint.pprint(dict(sensor1))
    pprint.pprint(sensor1.getMongoDoc())

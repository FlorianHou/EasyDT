import asyncio
import random
import sys
import pymongo
from pymongo.errors import ConnectionFailure
import datetime
import logging
import pprint
import time
import uuid
from collections import UserDict
from typing import Dict, Union, List, Any


class SensorDataM2(UserDict):
    def __init__(
        self,
        timestamp: datetime.datetime,
        sensorId: str,
        objId: str,
        unit: str,
        value: Union[float, bool],
        description: str = "",
    ):
        super().__init__()
        self.__timestamp: datetime.datetime = timestamp
        self.__sensorId: str = sensorId
        self.__objId: str = objId
        self.__unit: str = unit
        self.__description: str = description
        self.__value: Union[float, bool] = value

    def toDict(self):
        return {
            "timeField": self.__timestamp,
            "metaField": {
                "sensorId": self.__sensorId,
                "objId": self.__objId,
                "unit": self.__unit,
                "description": self.__description,
            },
            "value": self.__value,
        }

    def getMongoDoc(self):
        return {
            "timeField": self.__timestamp,
            "metaField": {
                "sensorId": self.__sensorId,
                "objId": self.__objId,
                "unit": self.__unit,
                "description": self.__description,
            },
            "value": self.__value,
        }

    def keys(self):
        return self.toDict().keys()

    def __getitem__(self, key: str):
        return self.toDict()[key]

    def __call__(self):
        return self.toDict()

    def getSensorId(self):
        return self.__sensorId

    def getObjId(self):
        return self.__objId

    def getUnit(self):
        return self.__unit

    def getDescription(self):
        return self.__description

    def getTimestamp(self):
        return self.__timestamp

    def getValue(self):
        return self.__value

    def setObjId(self, newVal: str):
        self.__objId = newVal
        return self.__objId

    def setTimestamp(self, newVal: datetime.datetime):
        self.__timestamp = newVal
        return self.__timestamp

    def setSensorid(self, newVal: str):
        self.__sensorId = newVal
        return self.__sensorId

    def setObjid(self, newVal: str):
        self.__objId = newVal
        return self.__objId

    def setUnit(self, newVal: str):
        self.__unit = newVal
        return self.__unit

    def setDescription(self, newVal: str):
        self.__description = newVal
        return self.__description

    def setValue(self, newVal: Union[float, bool]):
        self.__value = newVal
        self.setTimestamp(datetime.datetime.now())
        return self.__value


class PushSensorDaten:
    """ "push daten to MongoDB Server"""

    import datetime
    import asyncio

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 27018,
        dbName: str = "Records",
        collName: str = "SensorDaten",
        maxTime: float = 10,
        maxVolume: int = 20,
        isDebug: Union[bool, None] = None,
        errorLogPath: str = "pushError.txt",
        dataBackupPath: str = "dataBackup.txt",
    ) -> None:
        """
        push Daten to MongoDBServer. It like a Queue, when a Queue is full(@param:maxVolume) or time(@param:timeout) ist out.
        It will push the Daten to MongoDB. Before this Class is deleted. It will do a last push before it is actually deleted. This is a Async Programm, so
        you have to write the main code in '''async def main()''' Function, and run it in main process with '''asyncio.run(main())'''. When an Error within push rasies, errors will
        be saved under pushError.txt and the data, that haven't been pushed to DB, will be saved under dataBackup.txt.

        Attributes:
            host: str = The host of MongoDBServer,
            port: int = The Port of MongoDBServer,
            dbName: str = Name of the DBName,
            collName: str = Name of Collection,
            timeout: float = time in secs,
            maxVolume: int = max Volume of container,
            isDebug: bool = you can manual set Debug Mode oder Release Mode. Debug Mode will give you a little bit more informations for Debug. if you don't set, it will check by itself, wether you are using a Debuger.

        Functions:
            append(val:Union[dict,list,bool,float,int]): usually this is the only one function,that you use. it will put a value in a container.
            clearContainer(): it will clean up the Container. you can use it, if you really want.
            push(): it pushes the container to the MongoDB Server and clean up the container, normally it will be automatisch excuted which base of time and
                maxVolume.
            simpush(): the pushed Data will be shown on screen not to MongoDB
            getPaths(): returns the"errorLogPath" and "dataBackupPath"

        """

        self.__client = pymongo.MongoClient(host=host, port=port)
        try:
            # The ping command is cheap and does not require auth.
            self.__client.admin.command("ping")
        except ConnectionFailure:
            print("Server not available")
        self.__db = self.__client[dbName]
        self.__collection = self.__db[collName]
        self.__startTime: datetime.datetime = datetime.datetime.now()
        self.__timeout: float = maxTime
        self.__maxVolume: int = maxVolume
        self.__container = []
        self.__errorLogPath = errorLogPath
        # Try writeabel
        with open(self.__errorLogPath, "a+"):
            pass
        self.__dataBackupPath = dataBackupPath
        # Try writeable
        with open(self.__dataBackupPath, "a+"):
            pass
        # Check Debug
        if not isDebug:
            self.__isDebug = True if sys.gettrace() else False
        else:
            self.__isDebug = isDebug
        if self.__isDebug:
            print("Create asyAsyTask!!")
        self.__createAsyTask()

    def getPaths(self):
        return {
            "errorLogPath": self.__errorLogPath,
            "dataBackup": self.__dataBackupPath,
        }

    def __del__(self):
        if self.__isDebug:
            print(f"{self.__class__.__name__} will be deleted")
            if self.__isDebug:
                pprint.pprint(f"Last push before delete: {self.__container}")
        self.push()

    def append(self, val: Union[dict, list, bool, float, int]):
        self.__container.append(val)

    def __resetTime(self):
        self.__startTime = datetime.datetime.now()
        return self.__startTime

    def __isFull(self):
        """Return True if container is full"""
        return len(self.__container) >= self.__maxVolume

    def __isTimeout(self):
        """Return True if time is out"""
        return datetime.datetime.now() - self.__startTime > datetime.timedelta(
            seconds=self.__timeout
        )

    def __isEmpty(self):
        """Check if container is full"""
        if self.__container:
            return False
        else:
            return True

    def clearContainer(self):
        if self.__isDebug:
            print("Container is cleaned!")
        self.__container = []

    def push(self):
        try:
            if not self.__isEmpty():
                self.__collection.insert_many(self.__container)
                if self.__isDebug:
                    print(f"PUSH:{self.__container}")
                    print(f"PUSH Length: {len(self.__container)}")
                self.clearContainer()
            self.__resetTime()
        except Exception as e:
            self.__handleException(e)

    def __handleException(self, e):
        print(e)
        with open(self.__errorLogPath, "a+") as f:
            f.write(f"{datetime.datetime.now()}:{e}\n")
        with open(self.__dataBackupPath, "a+") as f:
            f.write(f"{str(self.__container)}\n")
        sys.exit()

    def simpush(self):
        if not self.__isEmpty():
            if self.__isDebug:
                print(f"PUSH:{self.__container}")
            self.clearContainer()
        self.__resetTime()

    async def __checkTimeout(self):
        while True:
            if self.__isTimeout():
                self.push()
                if self.__isDebug:
                    print("timeout!")
            await asyncio.sleep(0.1)

    async def __checkVolume(self):
        while True:
            if self.__isFull():
                self.push()
                if self.__isDebug:
                    print("isfull!!")
            await asyncio.sleep(0.1)

    def __createAsyTask(self):
        chktimeTask = asyncio.create_task(self.__checkTimeout())
        chkvolumeTask = asyncio.create_task(self.__checkVolume())


async def main():
    sensor1Data = SensorDataM2(
        datetime.datetime.now(),
        sensorId=str(uuid.uuid4()),
        objId=str(uuid.uuid4()),
        unit="Circus",
        value=12.5,
    )
    Sensor1Push = PushSensorDaten(
        port=27017, collName="SensorDatenNotTimeSerie", maxTime=5, maxVolume=50
    )
    Sensor1Push.append(sensor1Data())
    random.seed(444)
    while True:
        sensor1Data.setValue(random.random() * 100)
        # sensor1Data.setTimestamp(datetime.datetime.now())
        Sensor1Push.append(sensor1Data())
        await asyncio.sleep(random.random() * 0.05)
        # if random.choice([True, False, False, False]):
        #     print("waiting")
        #     await asyncio.sleep(0.01)
        #     if random.choice([True, False, False, False, False, False, False]):
        #         print("wait 5s")
        #         await asyncio.sleep(5)

        client = pymongo.MongoClient()
        db = client["Records"]
        coll = db["SensorDatenNotTimeSerie"]
        if coll.count_documents({}) >= 5000:
            break


if __name__ == "__main__":
    asyncio.run(main())

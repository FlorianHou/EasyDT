import pymongo
from pymongo.errors import ConnectionFailure
import datetime
import logging
import pprint
import time
import uuid
from collections import UserDict
from typing import Dict, Union, List, Any
import asyncio
import random


class SensorDataManager_async:
    """ "push daten to MongoDB Server"""

    import datetime

    def __init__(
        self,
        isSim: bool,
        host: str = "127.0.0.1",
        port: int = 27017,
        dbName: str = "phonixD",
        collName: str = "sensorDaten",
        timeout: float = 10,
        maxVolume: int = 20,
    ) -> None:
        # multiprocess
        if not isSim:
            self.__client = pymongo.MongoClient(host=host, port=port)
            try:
                # The ping command is cheap and does not require auth.
                self.__client.admin.command("ping")
            except ConnectionFailure:
                print("Server not available")
            self.__db = self.__client[dbName]
            self.__collection = self.__db[collName]
        self.__startTime: datetime.datetime = datetime.datetime.now()
        self.__timeout: float = timeout
        self.__maxVolume: int = maxVolume
        self.__container = []
        print("Start async")
        self.__createAsyTask()
        # asyncio.run(self.run())
        # await self.run()

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.__container

    def getContainer(self):
        return self.__container

    def append(self, val):
        self.__container.append(val)

    def resetTime(self):
        self.__startTime = datetime.datetime.now()
        return self.__startTime

    def isFull(self):
        """Return True if container is full"""
        return len(self.__container) >= self.__maxVolume

    def isTimeout(self):
        """Return True if time is out"""
        return datetime.datetime.now() - self.__startTime > datetime.timedelta(
            seconds=self.__timeout
        )

    def isEmpty(self):
        """Check if container is full"""
        if self.__container:
            return False
        else:
            return True

    def clearContainer(self):
        self.__container = []

    def push(self):
        if not self.isEmpty():
            self.__collection.insert_many(self.__container)
            self.clearContainer()
        self.resetTime()

    def simpush(self):
        if not self.isEmpty():
            print(f"PUSH:{self.__container}")
            self.clearContainer()
        self.resetTime()

    async def checkTimeout(self):
        while True:
            if self.isTimeout():
                self.simpush()
                print("timeout!")
            await asyncio.sleep(0.1)

    async def checkvolume(self):
        while True:
            if self.isFull():
                self.simpush()
                print("isfull!!")
            await asyncio.sleep(0.1)

    def __createAsyTask(self):
        chktimeTask = asyncio.create_task(self.checkTimeout())
        chkvolumeTask = asyncio.create_task(self.checkvolume())

        # await chktimeTask
        # await chkvolumeTask


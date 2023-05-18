from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import pprint
from typing import Union


# def initDB(ServerStru, port: int = 27017, host: str = "127.0.0.1"):
#     with MongoClient(port=port, host=host) as client:
#         try:
#             client.admin.command("ping")
#         except ConnectionFailure:
#             print("Not Connected!!")
#         for key, val in ServerStru.items():
#             print(f"drop database -- {key}")
#             client.drop_database(key)
#             print(f"Create Database {key}")
#             dbPtr = client[key]
#             for coll in val:
#                 print(f"Create Collection({coll}) under Database({key})")
#                 dbPtr.create_collection(coll)

#         print("finished!!")
#         print(f"Name of Databases under Server:'{host}:{port}'")
#         pprint.pprint([db["name"] for db in client.list_databases()])


class CreateDB:
    """
    这个用于创建数据库，内部已经内嵌了一个默认的数据库结构，如果想要自定义，可以在初始化的时候以字典的形式设置一个新的结构，注意，字典的深度不应该超过一层，数据库的名字为字典的键名，Collection的名字以列表的形式储存在键名对应的值中。两个方法创建逻辑，一个是直接覆写，另一个是先检查要创建的数据库是否已经存在，如果有重名的会先报错。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 27017,
        url: Union[str, None] = None,
        timeserieDB: list[str] = ["SensorData"],
        dbStructur: Union[dict, None] = None,
    ) -> None:
        # The Structure of Database
        if dbStructur:
            self.dbStruktur = dbStructur
        else:
            self.dbStruktur = {
                "ProductData": ["Productions", "Templates"],
                "LogData": ["ProductionLog", "SystemLog"],
                "SensorData": ["Temperatur"],
            }
        self.timeserieDB = timeserieDB
        # Create a client
        if url:
            self.__client = MongoClient(url=url)
        else:
            self.__client = MongoClient(host=host, port=port)
        # Test Connection
        try:
            self.__client.admin.command("ping")
        except ConnectionFailure:
            print("Not Connected!!")

    def overwriteAndCreate(self) -> MongoClient:
        for dbName, collectionNames in self.dbStruktur.items():
            print(f"drop database -- {dbName}")
            self.__client.drop_database(dbName)
            print(f"Create Database {dbName}")
            dbPtr = self.__client[dbName]

            if dbName in self.timeserieDB:
                for collectionName in collectionNames:
                    print("Create Collection for timeserie")
                    dbPtr.create_collection(
                        collectionName,
                        timeseries={
                            "timeField": "timeField",
                            "metaField": "metaField",
                            "granularity": "seconds",
                        },
                    )
            else:
                for collectionName in collectionNames:
                    print(
                        f"Create Collection({collectionName}) under Database({dbName})"
                    )
                    dbPtr.create_collection(collectionName)
        print("finished!!")
        pprint.pprint(f"Server INFO:\n{self.__client.server_info}")
        pprint.pprint(
            f"Name of Databases under this Server: {self.__client.list_database_names()}"
        )

        return self.__client

    def safeCreate(self) -> MongoClient:
        """
        首先检查是否已经存在这个数据库，如果已经存在了就报错。
        """
        for dbName, collectionNames in self.dbStruktur.items():
            if dbName in self.__client.list_database_names():
                raise Exception(
                    f"{dbName} is already existed! All DBs in this Server: {self.__client.list_database_names()}"
                )

        for dbName, collectionNames in self.dbStruktur.items():
            dbPtr = self.__client[dbName]
            if dbName in self.timeserieDB:
                for collectionName in collectionNames:
                    print("Create Collection for timeserie")
                    dbPtr.create_collection(
                        collectionName,
                        timeseries={
                            "timeField": "timeField",
                            "metaField": "metaField",
                            "granularity": "seconds",
                        },
                    )
            else:
                for collectionName in collectionNames:
                    print(
                        f"Create Collection({collectionName}) under Database({dbName})"
                    )
                    dbPtr.create_collection(collectionName)
        print("finished!!")
        pprint.pprint(f"Server INFO:\n{self.__client.server_info}")
        pprint.pprint(
            f"Name of Databases under this Server: {self.__client.list_database_names()}"
        )
        # Close Connection
        self.closeConnect()
        return self.__client

    def closeConnect(self):
        print("Close Client")
        self.__client.close()

    def __exit__(self, *args, **kwargs):
        # close Connection,when finished
        self.closeConnect()


if __name__ == "__main__":
    # ServerStru = {
    #     "PXD": ["Productions", "Templates"],
    #     "Records": ["SensorData", "Log"],
    # }
    # initDB(port=27018, ServerStru=ServerStru)

    dbClient = CreateDB(port=27019).safeCreate()

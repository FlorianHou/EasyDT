from .CreateComponent import CreateComponent
import pymongo
from typing import Union
import pprint


class ModifyComponent(CreateComponent):
    def __init__(self, dict=None, host: str = "127.0.0.1", port: int = 27017):
        super().__init__(dict, host, port)

    def loadFromDB(
        self,
        id,
        dbName: str = "ProductData",
        collName: str = "Productions",
        templateName: str = "",
        timeKey: str = "createDate",
    ):
        """
        load a component from DB. the id will not be removed
        """
        res = super().loadFromDB(dbName, collName, id, templateName, timeKey)
        id = self.checkId(id)
        res["_id"] = id
        self.update(res)
        return self

    def deleteComponentFromDB(self, dbName: str = "ProductData", collName: str = "Productions"):
        """
        To remove a Component, you have to load a Component at first. #TODO set all childs to notUsing
        @params:
            dbName,
            collName
        @returns:
            to be removed Component
        """
        if not self:
            raise Exception("Please load a Component from DB at first")
        elif not self["_id"]:
            raise Exception("_id is not found")
        else:
            client = pymongo.MongoClient(host=self.host, port=self.port)
            db = client[dbName]
            collection = db[collName]
            print(f"{self['componentName']}--{self['_id']} will be removed")
            collection.delete_one({"_id": self["_id"]})
            self.pushLog2DB(
                f"{self['componentName']}--{self['_id']} was removed",
                host=self.host,
                port=self.port,
            )
            print("Is removed!")
            return self

    def updateOneChild(self, oldId, newId, path2Child: str = "child", isSame=True):
        """update a child. The Template"""
        childs = self._Cursor(path2Child)
        oldId = self.checkId(oldId)
        newId = self.checkId(newId)
        newChild = ModifyComponent(host=self.host, port=self.port).loadFromDB(id=newId)
        oldChild = ModifyComponent(host=self.host, port=self.port).loadFromDB(id=oldId)
        if newChild["templateId"] == oldChild["templateId"]:
            for child in childs:
                if child["_id"] == oldId:
                    #TODO Check new and old Component
                    for k, v in child.items():
                        if isSame:
                            if k != "_id" and v != newChild[k]:
                                raise Exception(
                                    "the {k}:{v} of old one is different to the new one {k}:{newChild[k]}"
                            )
                        else:
                            child[k] = newChild[k]
                    child["_id"] = newId
                    break
            self._set2IsUsing(newId)
            self._set2NotUsing(oldId)
            return self
        else:
            raise Exception(
                "The new child and the old child are different, Please Check templateId"
            )

    def updateOneChildAndPush(self, oldId, newId, path2Child: str = "child",isSame=True,**kwargs):
        self.updateOneChild(oldId, newId, path2Child=path2Child,isSame=isSame)
        insert_id = self.push2Mongo(**kwargs)
        return insert_id

    def setValueAndPush(self, modifyObj, allowAddNewNode=False,**kwargs):
        """Update will first remove the document from DB and then push new Document to DB"""
        self.setValue(modifyObj, allowAddNewNode)
        insert_id = self.push2Mongo(**kwargs)
        return insert_id

    def push2Mongo(
        self,
        dbName: str = "ProductData",
        dbNameTemplate=None,
        collName: str = "Productions",
        path2CreateTime: str = "createDate",
        path2TempalteName: str = "templateName",
        path2TempalteId: str = "templateId",
        isTemplate: bool = False,
        checkList: Union[list, None] = None,
    ):
        self.deleteComponentFromDB()
        return super().push2Mongo(
            self["_id"],
            dbName,
            dbNameTemplate,
            collName,
            path2CreateTime,
            path2TempalteName,
            path2TempalteId,
            isTemplate,
            checkList,
        )

    def parent(self, id):
        """find the parent of the Component"""
        client = pymongo.MongoClient(port=self.port, host=self.host)
        db = client["ProductData"]
        collection = db["Productions"]
        doc = collection.find_one({"child._id": id})
        pprint.pprint(doc)
        if doc:
            return doc["_id"]
        else:
            print("Find Nothing")
            return None


if __name__ == "__main__":
    # ModifyComponent(port=27018).parent(id="d732c658-d492-4099-8495-e33f0cb8269c")
    Model = ModifyComponent(port=27018).loadFromDB(id="d732c658-d492-4099-8495-e33f0cb8269c").get3DModel()
    if Model:
        Model.save2File(f"./model{Model.getSuffix()}")
    

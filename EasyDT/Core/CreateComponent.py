from .Template import Template, ChildType
import uuid
import pymongo
import bson
from typing import Union, Any
from pydantic import BaseModel
import datetime


class CreateComponent(Template):
    """Use This for create new Component"""

    def __init__(self, dict=None, host: str = "127.0.0.1", port: int = 27017):
        super().__init__(dict, host, port)
        self.createComponentCheckList = [
            "createDate",
            "_id",
        ]
        self.setListBeforePush = [{"status": "Produced"}]

        self.ignoreKeys = [
            "createDate",
            "templateId",
            "_id",
            "componentName",
            "productionDate",
            "installationDate",
            "uninstallationDate",
            "nextMaintenanceDate",
            "lastMaintenanceDate",
        ]

    def addIgnoreKeys(self, ignoredList):
        self.ignoreKeys += ignoredList
        return self.ignoreKeys

    def showIgnoreKeys(self):
        print(f"Ignored Key: {self.ignoreKeys}")
        return self.ignoreKeys

    def loadFromDB(
        self,
        dbName: str = "ProductData",
        # TODO Productions oder Templates?
        collName: str = "Templates",
        id=None,
        templateName: str = "",
        timeKey: str = "createDate",
    ):
        """
        Use this function for loading a Tempalte from DB and use this Template for creating a new Component. You can specify a id for Template. If you don't set the id but only the templateName. It will return the newest Template, which has the same TempalteName. If you load from Production, the Template of the Component will also be loaded and the Template will be filled up with the Information from Component, because the Components, which stores in Productions, only has the Informations, that differtent with the Template.
        @params
            dbName:str -- The Name of Database, where you want your Document load from
            collName: str -- The Name of Collection, where you want your Document load from
            id: Any -- You can specify the id of the document, which you want
            templateName -- if you don't set id, but only templateName. The lastest one will be returned. If you give both, it will use both of them for finding the Result.
            timeKey: str -- You should set name of the Key for sorting the documents if you only set templateName. default is "createDate"
        """
        # ToDo Path2id
        res = super().loadFromDB(dbName, collName, id, templateName, timeKey)

        if res["templateId"] and collName == "Productions":
            tmp = Template(host=self.host, port=self.port).loadFromDB(
                id=res["templateId"], collName="Templates"
            )
            tmp.setValueWithDict(dict(res))
            # tmp.update(res)
            res = tmp
            self.update(res)
            return self
        else:
            return self

    def loadFromDBAggregate(
        self,
        dbName: str = "ProductData",
        # TODO Productions oder Templates?
        collName: str = "Templates",
        id=None,
        templateName: str = "",
        timeKey: str = "createDate",
    ):
        """
        Use this function for loading a Tempalte from DB and use this Template for creating a new Component. You can specify a id for Template. If you don't set the id but only the templateName. It will return the newest Template, which has the same TempalteName. If you load from Production, the Template of the Component will also be loaded and the Template will be filled up with the Information from Component, because the Components, which stores in Productions, only has the Informations, that differtent with the Template.
        @params
            dbName:str -- The Name of Database, where you want your Document load from
            collName: str -- The Name of Collection, where you want your Document load from
            id: Any -- You can specify the id of the document, which you want
            templateName -- if you don't set id, but only templateName. The lastest one will be returned. If you give both, it will use both of them for finding the Result.
            timeKey: str -- You should set name of the Key for sorting the documents if you only set templateName. default is "createDate"
        """
        # ToDo Path2id
        res = super().loadFromDB(dbName, collName, id, templateName, timeKey)

        if res["templateId"] and collName == "Productions":
            client = pymongo.MongoClient(host=self.host, port=self.port)
            db = client[dbName]
            coll = db[collName]

            result = coll.aggregate(
                [
                    {"$match": {"_id": id}},
                    {
                        "$lookup": {
                            "from": "Templates",
                            "localField": "templateId",
                            "foreignField": "_id",
                            "as": "fromTemplates",
                        }
                    },
                    {
                        "$replaceRoot": {
                            "newRoot": {
                                "$mergeObjects": [
                                    {"$arrayElemAt": ["$fromTemplates", 0]},
                                    "$$ROOT",
                                ]
                            }
                        }
                    },
                    {"$project": {"fromTemplates": 0}},
                ]
            )
            self.update(next(result))
            return self
        else:
            return self

    def checkChildsEmpty(self, path2Childs="child"):
        """
        Check, wether the childs has Empty value
        @params:
            path2Childs:str -- path to the key of child relativ to the root

        """
        childsList = self._Cursor(path2Childs)
        if not isinstance(childsList, list):
            raise KeyError("The Type of childs Field is not a list")
        else:
            for child in childsList:
                for key, val in child.items():
                    if val == None:
                        raise Exception(f"{child} has empty Value by {key}\n")

    def fillOneChild(
        self, aComponent: dict, matchKey: str = "componentName", path2Childs="child"
    ):
        """
        fill only one Child. The matchKey is used for matching between the child of Component and the component to be added from the manufacturer. This function will not check, whether all childs are fully filled.
        @params:
            aComponent: dict -- you can use createOneChild() to create a standard Child,
            matchKey: str = "componentName",
            path2Childs="child"
        @returns:
            list -- the childs of the component
        """
        childsList = self._Cursor(path2Childs)
        for child in childsList:
            self.checkKeyinDict(aComponent, matchKey)
            if (child[matchKey] == aComponent[matchKey]) and (not child["_id"]):
                print(f"Child{child} matches with Component{aComponent}")
                for k, v in aComponent.items():
                    child[k] = v
                child.update({"_id": aComponent["_id"]})
                self._set2IsUsing(id=aComponent["_id"])
                break
        print(f"New childsList:{self._Cursor(path2Childs)}")
        return childsList

    def _set2IsUsing(
        self,
        id,
        path2componentStatus="componentStatus",
        path2installationDate="installationDate",
    ):
        client = pymongo.MongoClient(host=self.host, port=self.port)
        db = client["ProductData"]
        collection = db["Productions"]
        collection.update_one({"_id": id}, {"$set": {"componentStatus": "isUsing"}})
        collection.update_one(
            {"_id": id}, {"$set": {"installationDate": datetime.datetime.now()}}
        )
    def _set2NotUsing(
        self,
        id,
        path2componentStatus="componentStatus",
        path2installationDate="installationDate",
    ):
        client = pymongo.MongoClient(host=self.host, port=self.port)
        db = client["ProductData"]
        collection = db["Productions"]
        collection.update_one({"_id": id}, {"$set": {"componentStatus": "notUsing"}})
        collection.update_one(
            {"_id": id}, {"$set": {"installationDate": datetime.datetime.now()}}
        )
    def cleanChilds(self, path2Childs: str = "child"):
        """
        Clean up the childs. It will use the childs from Template and replace the childs of this instacne.
        @params:
            path2Childs:str -- path to the key of childs
        @returns:
            list -- the child of this component
        """
        tmp = Template(host=self.host, port=self.port).loadFromDB(
            id=self["templateId"], collName="Templates"
        )
        self.setValue([{path2Childs: tmp.getValue(path2Childs)}])
        return self.getChilds(path2Childs)

    # TODO: Check type of elements in compoentList
    def fillAllChilds(
        self, compoentList: list, matchKey: str = "componentName", keyChildName="child"
    ):
        """
        If you have a component list, which has all childs for this Componen. you can use this to automatically fill all the childs of the Component. After filling the values of Childs will be checked. In order to make sure, that all childs are fully filled.
        @params:
            aComponent: dict -- you can use createOneChild() to create a standard Child,
            matchKey: str = "componentName",
            path2Childs="child"
        @returns:
            list -- the childs of the component
        """
        childsList = self._Cursor(keyChildName)
        for child in childsList:
            for component in compoentList:
                component=dict(component)
                self.checkKeyinDict(component, matchKey)
                if child[matchKey] == component[matchKey]:
                    print(f"Child{child} matches with Component{component}")
                    for k, v in component.items():
                        if k in child and not (k=="transform" and not v):
                            child[k] = v
                    child.update({"_id": component["id"]})
                    self._set2IsUsing(id=component["id"])
                    compoentList.remove(component)
                    break
        print(f"New childsList:{self._Cursor(keyChildName)}")
        assert childsList == self._Cursor(keyChildName)
        self.checkChildsEmpty(keyChildName)
        return childsList

    # TODO: Check Type of _id and convert
    # def fillChildsInput(self):
    #     childsList = []
    #     keyChildName = str()
    #     while True:
    #         keyChildName = input("Where is childs field? ")
    #         childsList = self._Cursor(keyChildName)
    #         if isinstance(childsList, list):
    #             break
    #         else:
    #             print(
    #                 f"{keyChildName} is not right. It returns a {childsList}({type(childsList)})"
    #             )

    #     for child in childsList:
    #         for key, val in child.items():
    #             if not val:
    #                 if isinstance(val, list):
    #                     tf = []
    #                     while True:
    #                         try:
    #                             print(f"Please give the value of -'{key}'- for {child}")
    #                             res_input = input(
    #                                 "Please give a 4*4 Matrix in 1D, You should use ',' for separating the values \n"
    #                             )
    #                             tf = self.string2TFMatrix(res_input)
    #                             break
    #                         except Exception as e:
    #                             print(e)

    #                     child[key] = tf
    #                 else:
    #                     child[key] = input(
    #                         f"Please give the value of -'{key}'- for {child} \n"
    #                     )
    #     return self._Cursor(keyChildName)

    def string2TFMatrix(self, aString: str):
        res = []
        aString = aString.replace(" ", "")
        for s in aString.split(","):
            try:
                res.append(float(s))
            except:
                pass
        if len(res) != 16:
            raise ValueError(
                f"You are supposed for giving 16 Values. But only {len(res)}"
            )
        return res

    def push2Mongo(
        self,
        docId,
        dbName: str = "ProductData",
        dbNameTemplate=None,
        collName: str = "Productions",
        path2CreateTime: str = "createDate",
        path2TempalteName: str = "templateName",
        path2TempalteId: str = "templateId",
        isTemplate: bool = False,
        checkList: Union[list, None] = None,
    ):
        return super().push2Mongo(
            docId,
            dbName,
            dbNameTemplate,
            collName,
            path2CreateTime,
            path2TempalteName,
            path2TempalteId,
            isTemplate,
            checkList,
        )

    # def getOneComponent(
    #     self,
    #     id,
    #     dbName: str = "ProductData",
    #     collName: str = "Productions",
    #     otherQuery: dict = {},
    # ):
    #     client = pymongo.MongoClient(host=self.host, port=self.port)
    #     db = client[dbName]
    #     collection = db[collName]
    #     res = collection.find_one({"_id": id, **otherQuery})
    #     if not res:
    #         raise Exception("find no Document")
    #     else:
    #         return res

    def searchAllChilds(self, tfKeyName: str = "transform", path2Childs: str = "child"):
        """
        You will get all childs of a combination. The childs will be recursively loaded. The paths from this combination to end component will be save in a list. The transformationsmatrix of every end component relativ to this combination saves in a list. The paths and transformationsmatrix are corresponding with each other.
        @params:
            tfKeyName: str -- the key name of transform,
            path2Childs: str -- the path to childs relativ to root
        @returns:
            paths:list -- for example: ["combination1.combination11.endComponent1","combination1.combination11.endComponent1",...]
            tfs:list -- for example: [[tf1],[tf2],....]
        """
        import numpy as np

        paths = []
        tfs = []

        def goNext(objs, aPath, tf):
            if objs and isinstance(objs, list) and objs[0]["_id"]:
                for obj in objs:
                    if obj["_id"]:
                        loadObj = CreateComponent(
                            port=self.port, host=self.host
                        ).loadFromDB(collName="Productions", id=obj["_id"])

                        _tf = self.convert1dTF2TRTE(
                            np.array(obj[tfKeyName], dtype=np.float64)
                        )

                        goNext(
                            loadObj._Cursor(path2Childs),
                            aPath + obj["componentName"] + ".",
                            tf @ _tf["TF44"],
                        )
            else:
                paths.append(aPath)
                tfs.append(tf)

        childsList = self._Cursor(path2Childs)
        goNext(childsList, f"{self.componentName}.", np.eye(4))
        return paths, tfs

    def setBeforePush(
        self,
        id,
        path2CreateTime: str,
        path2Id: str,
        path2TemplateId: str,
        path2TemplateName: str,
        createTime: datetime.datetime = datetime.datetime.now(),
    ):
        """
        There are servel basic settings before push. It's extracted from push2Mongo for flexibility. You could rewrite it as you want in a new Class to change the behavior before push to mongoDB. It will run automatically before push. Here is only a demo for the setting before push. Careful: path2* should be a sting and like"a.aa.aa". You can custom setListBeforePush in __init__ for some individual purposes
        @params
        id -- id of the document
        path2CreateTime: str
        path2Id: str
        path2TempalteId: str
        path2TempalteName: str
        createTime:datetime.datetime=datetime.datetime.now()
        """
        self.setValue({path2Id: id})
        self.setValue({path2CreateTime: createTime})
        self.setValue({path2TemplateName: self._Cursor("templateName")})
        if self.setListBeforePush:
            self.setValue(self.setListBeforePush)
            print(self.setListBeforePush)

    def checkBeforeUpload(self, checkList=None):
        """
        some fileds should not empty before push to Server. if the Parameter checkList is not set, it will use a BaseCheckList, which unter __init__
        @Parameters
            checkLists --  the path to the field can be putted under this list. If you want to make sure, that the leaf value of {"a":{"aa":{"aaa": 123}}} should not empty. you can put "a.aa.aaa"into checkList. checkList=["a.aa.aaa" ]
        @Returns
            0 -- if it's ok

        """
        if not checkList:
            checkList = self.baseCheckList
        for check in checkList:
            if not self._Cursor(check):
                raise Exception(f"value of {check} is not Set. Do nothing")
        return 0


if __name__ == "__main__":
    component = CreateComponent(port=27018).loadFromDB(
        id="b7406b55-2ab3-4b61-8523-fe553034ec81", collName="Productions"
    )
    # component.genSnippet().save2File()
    # component.ignoreKeys += ["properties.Opitcal_Properties.Optical_Power_Target"]
    print("------------------------")
    # component.push2Mongo(uuid.uuid4())
    component.pprint()

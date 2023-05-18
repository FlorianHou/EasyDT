from ..Tools import Model3D
import copy
import datetime
import functools
import logging
import pymongo
import bson
import uuid
from collections import UserDict
from pydantic import BaseModel
from typing import Any, Union


class PydanticObjectId(bson.ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, bson.ObjectId):
            raise TypeError("ObjectId required")
        return str(v)


class ChildType(BaseModel):
    id: Union[None, str, int, uuid.UUID, PydanticObjectId]
    componentName: str
    templateName: str
    templateId: Union[None, str, int, uuid.UUID, PydanticObjectId]
    transform: list


class Template(UserDict):
    """
    This Class is inherited from UserDict, which is same as Dict but implemented with python not like normal Dict with C, in order to avoid some implicitly Promblems. This Class is used for dealing somethings for making, pushing or loading a Template. The __getattr__() function realized the getting value with dot. You can get the Created Time with: "Template.CreatedTime". Others are same as a normal Dict. You can also create a instace with Template(aDict).

    Functions:
    ------------------
    class Template(dict) -- You can directly create a Instance with a dict, which contains the Template.

    loads(dictlikeobj) --  load a Tempalte and save in this instance.

    loadFromstr(aStr:str) -- parse strings to Dict and save in this instance

    loadFromJson(stFilepath:str) -- load a Template from a json File. The Path of the file should be gaved.

    loadFromDict(aDict:dict) -- load from a Dict

    loadFromDB(host: str, port: int, dbName: str, collName: str, _id: str, templateName: str, timeKey: str) -- load from MongoDB

    jsonParse(source) -- parse and check the Obj and try to convert to a Dict. If a List is loaded. It will check the length, if length is bigger than one. It will print errors.
    parse(template:dict) -- save the input object in itself.

    checkNames(__client:MongoClient, dbName:str, collName:str) -- check the Name of Database, Collection, in order to aviod create a new Database or Collection

    isExist(iter, beTest) -> bool -- check if beTest is in a iterable Object

    setValue(modifyobj:Union[List,Dict],allowAddingNewNode) -> you could change values of a Tempalte like modifing a Dict, or use this function to modify the Template.

    pprint() -- it will print this Template

    push2Mongo(host: str ,port: int ,dbName: str, collName: str, _id: str, timeKey: str) -- Push the new Template to the MongoDB

    tempalte2Snippet() ->  GenSnipp() -- return a Instance of GenSnipp()
    """

    def __init__(self, dict=None, host: str = "127.0.0.1", port: int = 27017):
        if dict:
            super().__init__(**dict)
        else:
            super().__init__()

        self.host = host
        self.port = port
        self.baseCheckList = [
            "createDate",
            "templateId",
            "_id",
        ]
        self.setListBeforePush = []
        self.checkListBeforePush = []

        # this keys should not be removed, when this document compares with the Template
        self.ignoreKeys = []

    def __getattr__(self, __name: str):
        # skip "__deepcopy__", "__getstate__", "__setstate__"
        # TODO skip all attr with "__**__"??
        if __name in ["__deepcopy__", "__getstate__", "__setstate__"]:
            return super().__getattribute__(__name)
        else:
            val = self.__getitem__(__name)
            if isinstance(val, dict):
                # print(type(self.__class__(**val)))
                return self.__class__(dict=val)
            elif isinstance(val, list):
                feedback = []
                for d in val:
                    if isinstance(d, dict):
                        feedback.append(self.__class__(**d))
                    elif isinstance(d, list):
                        feedback.append(d)
                    else:
                        feedback.append(d)
                return feedback
            else:
                return val

    def setDBHost(self, host: str):
        """
        Set the Host after Initialize
        @Parameters
        host:str - host for MongoDB
        @Returns:
        host:str - host for MongoDB
        """
        self.host = host
        return host

    def setDBPort(self, port: int):
        """
        Set the Port after Initialize
        @Parameters
        port:int - port for MongoDB
        @Returns:
        port:int - port for MongoDB
        """
        self.port = port
        return port

    def loads(self, dictLikeObj):
        """
        load a Tempalte and save in this instance.

        Parameters:
        ------------------
        dictLikeObj -- It could be a dict, a list, or stings. Strings can be a Dict like Strings or the Path to a json File
        """
        if isinstance(dictLikeObj, dict):
            self.loadFromDict(dictLikeObj)
        elif isinstance(dictLikeObj, list):
            self.jsonParse(dictLikeObj)
        elif isinstance(dictLikeObj, str):
            self.loadFromStr(dictLikeObj)
        else:
            logging.error(f"TYPE: {type(dictLikeObj)} is not supported")
        return self

    def loadFromStr(self, aStr: str):
        """
        parse strings to Dict and save in this instance

        Parameters:
        ------------------
        aStr -- a Dict like strings or a Path to a json file"""

        import json

        try:
            json.loads(aStr)
            self.jsonParse(json.loads(aStr))
        except json.decoder.JSONDecodeError:
            self.loadFromJsonFile(aStr)
        return self

    def jsonParse(self, source):
        """
        parse and check the Obj and try to convert to a Dict. If a List is loaded. It will check the length, if length is bigger than one. It will print errors.

        Parameters:
        ------------------
        source: a Object, which could be parsed by json.
        """
        import json

        # try
        if isinstance(source, list):
            if len(source) == 1:
                self._parse(source[0])
            else:
                raise ValueError(
                    "You are importing a list and has more than one dicts under it. You are supposed to import a 'Dict like Object'"
                )
        elif isinstance(source, dict):
            self._parse(source)

        elif isinstance(source, str):
            self._parse(json.loads(source))
        else:
            raise TypeError(
                f"You are supposed to import a 'Dict like Object' not a {type(source)}"
            )
        # except Exception as e:
        #     logging.error(f"failed to load JSON File.\n{e}")
        return self

    def loadFromJsonFile(self, filepath: str):
        """
        You can load a Template from a Json File
        Parameters:
        ------------------
        filePath: str -- a path to the json file
        """
        from pathlib import Path

        filepath_par = Path(filepath)
        try:
            with open(filepath_par, "r") as jsf:
                self.jsonParse(jsf.read())
        except Exception as e:
            logging.error(f"failed to load JSON File.\n{e}")
        return self

    def loadFromDict(self, aDict: dict):
        """
        load from a Dict Object
        @Parameters
            aDict:dict -- a Dict Object
        """
        self._parse(aDict)
        return self

    def loadFromDB(
        self,
        dbName: str = "ProductData",
        collName: str = "Templates",
        id: Any = None,
        templateName: str = "",
        timeKey: str = "createDate",
    ):
        """
        load a Document from DB. You can specify a id for Template. If you don't set the id but only the templateName. It will return the newest Template, which has the same TempalteName.
        @params
            dbName:str -- The Name of Database, where you want your Document load from
            collName: str -- The Name of Collection, where you want your Document load from
            id: Any -- You can specify the id of the document, which you want
            templateName -- if you don't set id, but only templateName. The lastest one will be returned. If you give both, it will use both of them for finding the Result.
            timeKey: str -- You should set name of the Key for sorting the documents if you only set templateName. default is "createDate"
        """

        # TODO: ReadOnly
        if id:
            id = self.checkId(id)
        else:
            print(f"No id is given. The leatest Template{templateName} will be used.")
        client = pymongo.MongoClient(host=self.host, port=self.port)
        [__db, __collection] = self.checkNames(client, dbName, collName)

        loadDoc = None
        if not id and templateName:
            try:
                loadDoc = next(
                    __collection.find({"templateName": templateName}).sort(timeKey, -1)
                )
            except Exception:
                raise Exception("Find Nothing.")
        elif id and not templateName:
            loadDoc = __collection.find_one({"_id": id})
        elif id and templateName:
            loadDoc = __collection.find_one({"_id": id, "templateName": templateName})
        else:
            loadDoc = None
        if not loadDoc:
            logging.warning("Template is empty, Please check your input.")
            raise Exception("Template is empty, Please check your input.")
        else:
            self._parse(dict(loadDoc))
        client.close()
        return self

    def _parse(self, loadDoc: dict, path2_id="_id"):
        """
        all of the load funtions at last will use this function for loading the Data into this Instance. id will be removed after load
        @Parameters:
            loadDoc:dict -- the loaded data before was converted to a dict
            path2_id:str  -- the Name of the field for id in document. Default: "_id"
        """
        self.clear()
        if path2_id in loadDoc:
            loadDoc["_id"] = None
        self.update(loadDoc)
        return self

    def checkNames(self, client: pymongo.MongoClient, dbName: str, collName: str):
        """
        This function check, wether the dbName and colltion Name is all ready exist for avoiding adding a new db or collection in Database
        @Parameters:
        client: pymongo.MongoClient -- a client of DB Server
        dbName: str -- the to be checked name of database
        collName: str -- the to be checked name of collection
        """
        from pymongo.errors import ConnectionFailure, OperationFailure

        myDb = Any
        myCollection = Any
        # check Connection with Server
        try:
            # The ping command is cheap and does not require auth.
            client.admin.command("ping")
        except ConnectionFailure as e:
            print("Server not available")
            raise e
        # check DB Name
        try:
            if not self.isExist(client.list_database_names(), dbName):
                raise OperationFailure(
                    f"DB:{dbName} is not exist, Please Check dbName."
                )
            else:
                myDb = client[dbName]
                logging.warning(f"""you are handling DB: {dbName}""")
        except Exception as e:
            raise e
        # check Collection Name
        try:
            if myDb != None and not self.isExist(
                myDb.list_collection_names(), collName
            ):
                raise OperationFailure(
                    f"Collection:{collName} is not exist, Please Check Collection Name."
                )
            elif myDb != None:
                myCollection = myDb[collName]
                logging.warning(f"""you are handling Collection: {collName}""")
            else:
                print(f"db:{dbName} is not found")
        except Exception as e:
            raise e
        return [myDb, myCollection]

    def isExist(self, iter, obj):
        """
        Check, wether a object in a iterable Object
        @Parameters:
            iter -- a iterable object
            obj -- to be found Object from iter
        @Returns:
            True -- be found
            False -- not be found
        """
        if obj in iter:
            return True
        else:
            # raise KeyError(f"{aKey} is not in {aDict}.")
            return False

    def getValue(self, path2):
        return self._Cursor(path2)

    def setValue(self, modifyobj: Union[dict, list], allowAddingNewNode: bool = False):
        """
        this function helps you set Values of this json liked Instance.
        It offers two methodes. One is setValueWithList and the other one is setValueWithDict.
        Here are the examples:
        with a List:
        if you want to set values with a List.The struct of list should like[{"node1.node11.node111":value1},{"node2.node22.node222":value2}]
        with a Dict:
        {"node1":{"node11":{"node111":value1}},"node2":{"node22":{"node222":value2}}}
        @Parameters:
            modifyobj: dict or list -- the new values
            allowAddingNewNode:bool -- Allow create a new key(Node) under this Instance or not. This means, that if your List contains a new key, which is not existed, it will be created, when you set to true.
        @Returns:
            self
        """
        if isinstance(modifyobj, list):
            self.setValueWithList(modifyobj, allowAddingNewNode=allowAddingNewNode)
        elif isinstance(modifyobj, dict):
            self.setValueWithDict(modifyobj, allowAddingNewNode=allowAddingNewNode)
        else:
            raise TypeError("a Dict or List for modifyobj is Expected.")

    def setValueWithList(self, modifyList: list, allowAddingNewNode: bool = False):
        """
        this function helps you set Values of this json liked Instance.
        Here are the examples:
        with a List:
        if you want to set values with a List.The struct of list should like[{"node1.node11.node111":value1},{"node2.node22.node222":value2}]
        @Parameters:
            modifyobj: list -- the new values
            allowAddingNewNode:bool -- Allow create a new key(Node) under this Instance or not. This means, that if your List contains a new key, which is not existed, it will be created, when you set to true.
        @Returns:
            self
        """
        for d in modifyList:
            ptr = self
            for key, val in d.items():
                nodes = key.split(".")
                if len(nodes) == 1:
                    try:
                        ptr.__getitem__(nodes[0])
                    except KeyError as e:
                        logging.warning(
                            f"Adding a new node! Name:{nodes} under path {key}"
                        )
                        if not allowAddingNewNode:
                            raise e
                    ptr.__setitem__(nodes[-1], val)
                else:
                    for node in nodes[:-1]:
                        try:
                            ptr = ptr.__getitem__(node)
                        except KeyError as e:
                            logging.warning(
                                f"Adding a new node! Name:{node} under path {key}"
                            )
                            if allowAddingNewNode:
                                ptr.__setitem__(node, {})
                                ptr = ptr.__getitem__(node)
                            else:
                                raise e
                    ptr.__setitem__(nodes[-1], val)
        print(f"Update finished.{modifyList}")
        return self

    def setValueWithDict(self, modifyDict: dict, allowAddingNewNode: bool = False):
        """
        this function helps you set Values of this json liked Instance.
        Here are the examples:
        with a Dict:
        {"node1":{"node11":{"node111":value1}},"node2":{"node22":{"node222":value2}}}
        @Parameters:
            modifyobj: dict or list -- the new values
            allowAddingNewNode:bool -- Allow create a new key(Node) under this Instance or not. This means, that if your List contains a new key, which is not existed, it will be created, when you set to true.
        @Returns:
            self
        """
        modifyList = self.__searchDict(aDict=modifyDict)
        return self.setValueWithList(modifyList, allowAddingNewNode=allowAddingNewNode)

    def __searchDict(self, aDict):
        """
        search all the paths of a Dict Type and return a List contains the Path and value pairs
        @Parameters
        aDict -- a Dict like obj
        @Returns
        a List contains the Path and value pairs. [{"pathToValue1":value1},{"pathToValue2":value2}....]
        """
        pathValuePairs = []

        def goNext(path2subNode, element):
            if isinstance(element, dict):
                rest = list(element.items())

                while rest:
                    select = rest.pop()
                    goNext(f"{path2subNode}.{select[0]}", select[1])
            else:
                path2subNode = path2subNode[1:]
                pathValuePairs.append({path2subNode: element})
                # print(path2subNode)

        goNext("", aDict)
        return pathValuePairs

    def pprint(self):
        import pprint

        pprint.pprint(self)

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
        There are servel basic settings before push. It's extracted from push2Mongo for flexibility. You could rewrite it as you want in a new Class to change the behavior before push to mongoDB. It will run automatically before push. Here is only a demo for the setting before push. Careful: path2* should be a sting and like"a.aa.aa"
        @Parameters
        id -- id of the document
        path2CreateTime: str
        path2Id: str
        path2TempalteId: str
        path2TempalteName: str
        createTime:datetime.datetime=datetime.datetime.now()
        """
        self.setValue([{path2Id: id}])
        self.setValue([{path2CreateTime: createTime}])
        self.setValue([{path2TemplateId: id}])
        self.setValue([{path2TemplateName: self._Cursor("templateName")}])
        if self.setListBeforePush:
            self.setValue(self.setListBeforePush)
            print(self.setListBeforePush)

    def checkId(self, docId: Union[PydanticObjectId, int, str, uuid.UUID]):
        """
        Check the Input id for document. the id can be ObjectId, int, str. We recommand use uuid4 and save as string for compatibility.
        @Parameters:
        docId -- ID for the document
        """
        if isinstance(docId, Union[PydanticObjectId, int, str]):
            pass
        elif isinstance(docId, uuid.UUID):
            docId = str(docId)
        else:
            raise ValueError("Unexpect _id Type")
        return docId

    def push2Mongo(
        self,
        docId,
        dbName: str = "ProductData",
        dbNameTemplate=None,
        collName: str = "Templates",
        path2CreateTime: str = "createDate",
        path2TemplateName: str = "templateName",
        path2TemplateId: str = "templateId",
        isTemplate: bool = True,
        checkList: Union[list, None] = None,
    ):
        """
        This will push the instance itself to MmongoDB. It will set some values based of function setBeforePush() and do some checks with function checkBeforeUpload(). Id and time will be set before push.
        @Parameters:
            dbName: str -- the Name of Database for saving the document. default:"ProductData"
            dbNameTemplate -- TODO
            collName: str -- the Name of Collection for saving the document. default:"Templates"
            path2CreateTime: str -- Tell the function where is the field of CreateTime. default: "createDate"
            path2TempalteName: str -- Tell the function where is the field of TemplateName. default: "inheritTemplateName"
            path2TempalteId: str -- Tell the function where is the field of TempalteId. default: "templateId"
            isTemplate: bool -- If this is a Tempalte, the function for removing the same values between Instance and the Tempaltes of this instacne will not excuse. default: True
            checkList: list -- the checkList before push to MongoDB. If not set, it will use a dafault baseCheckList, which defined under __init__. default: []
        @Returns:
            insert_id
        """

        # login DB Server
        __client = pymongo.MongoClient(
            host=self.host, port=self.port, uuidRepresentation="standard"
        )
        [__db, __collection] = self.checkNames(__client, dbName, collName)

        if not dbNameTemplate:
            dbNameTemplate = dbName

        # Check ID Type and Set ID
        docId = self.checkId(docId)
        # Set before push
        self.setBeforePush(
            id=docId,
            path2CreateTime=path2CreateTime,
            path2Id="_id",
            path2TemplateId=path2TemplateId,
            path2TemplateName=path2TemplateName,
        )

        pushedData = copy.deepcopy(self)
        # compare and cleanup
        if not isTemplate:
            template: Template = Template(host=self.host, port=self.port).loadFromDB(
                dbName=dbNameTemplate,
                collName="Templates",
                id=self["templateId"],
            )
            pushedData = pushedData._cleanup(pushedData._compare(pushedData, template))
            # pushedData = pushedData._compare(pushedData._cleanup(pushedData), template)

        # Check Before push

        pushedData.checkBeforeUpload(checkList)

        # Push to Server
        insert_id = __collection.insert_one(dict(pushedData)).inserted_id

        # Log the Push
        self.pushLog2DB(
            {"insert_id": insert_id, "LogType": "add a Template with UUID"},
            host=self.host,
            port=self.port,
        )
        __client.close()
        return insert_id

    def genSnippet(self):
        """
        create a Instance of Snippet and based of the current Instance
        @Returns:

        """
        from ..Tools import GenSnippM1

        Snippets = GenSnippM1(dict(self))
        return Snippets

    def addOneChild(self, childObj, path2Childs: str = "child"):
        """
        add a child to this Template, It's supposed to add a Standard ChildType. You Could use createOneChild for creating a new Standard Child.
        @Parameters
            childObj -- a Object can be convert to a Dict. You could Create it by using function createOneChild(). When you add one to Template , the _id can be empty.

            path2Childs -- Our Template field of child is directly under root. If it was setted somewhere else. you should declaer the way to the field of child relativ to the root  with dot like:"submodels.child".
        @Returns:
            self
        """
        childList = self._Cursor(path2Childs)
        # clear the child, when it runs firsttime.
        if len(childList) == 1 and (
            True not in [bool(val) for val in list(childList[0].values())]
        ):
            print("Firsttime add a Child. Clean child")
            childList.clear()
        if isinstance(childObj, ChildType) and isinstance(childList, list):
            childList.append(childObj.dict())
        elif isinstance(childList, list):
            print("You are using a custemized childObj")
            print("Try to convert to dict")
            childList.append(dict(childObj))
        else:
            raise Exception(f"{path2Childs} is not point to a list")
        return self

    def autoCreateOneChild(
        self,
        templateId: Union[None, uuid.UUID, PydanticObjectId, str, int] = None,
        componentId: Union[None, uuid.UUID, PydanticObjectId, str, int] = None,
        templatesCollectionName: str = "Templates",
        productionCollectionName: str = "Productions",
        dbName: str = "ProductData",
        path2componentName: str = "componentName",
        path2templateName: str = "templateName",
        path2templateId: str = "templateId",
        transform: list = [],
    ):
        """
        This function is used for quick generate a child. It could be choosed from Template or Productions. If you only give a  templateId, it will create a standard Child without the id of component. If only the component id was gived, the informations will be searched from collection of productions
        @Parameters:
            templateId -- id of the template,
            componentId -- id of the component,
            templatesCollectionName -- the name of collection for templates,
            productionCollectionName -- the name of collection for porctions,
            dbName -- the name of Database,
            path2componentName -- the path to component name. For Example "a.b.componentName",
            path2templateName -- the path to tempalte name, which relative to root. For Example "a.b.templateName",
            path2templateId -- the path to tempalte id, which relative to root. For Example "a.b.templateId",
            transform: list = [],
        """
        if not templateId and not componentId:
            raise Exception(
                "You should at least give one id, either of templateId or componentId"
            )

        if componentId:
            template = Template(host=self.host, port=self.port).loadFromDB(
                id=componentId, collName=productionCollectionName, dbName=dbName
            )
            template = self.__class__(host=self.host,port=self.port).loadFromDB(dbName=dbName,collName=productionCollectionName,id=componentId)
            
            componentId = self.checkId(componentId)
            if not template:
                raise Exception("No matched component")
            if type(self)==type(Template):
                componentId = None
            return ChildType(
                id=componentId,
                componentName=str(template.getValue(path2componentName)),
                templateName=str(template.getValue(path2templateName)),
                templateId=str(template.getValue(path2templateId)),
                transform=transform,
            ).dict()
        elif templateId:
            template = Template(host=self.host, port=self.port).loadFromDB(
                id=templateId, collName=templatesCollectionName, dbName=dbName
            )
            templateId = self.checkId(templateId)
            if not template:
                raise Exception("No matched template")
            return ChildType(
                id=None,
                componentName=str(template.getValue(path2componentName)),
                templateName=str(template.getValue(path2templateName)),
                templateId=str(templateId),
                transform=transform,
            ).dict()

    def createOneChild(
        self,
        componentName: str,
        templateName: str,
        templateId: Union[uuid.UUID, PydanticObjectId, str],
        transform: list,
        id: Union[None, uuid.UUID, PydanticObjectId] = None,
    ):
        """
        Use this, you can easily create a StandardChild Obj, If it's a Template, id could be None
        @Parameters:
            componentName: str -- Name of the component
            templateName:str -- Name of the Template
            templateId:str -- id of the Template
            transform: list -- Transformations Matrix
            id[option] -- id of the component
        @Return:
            an object of ChildType

        """
        return ChildType(
            id=id,
            componentName=componentName,
            templateName=templateName,
            templateId=templateId,
            transform=transform,
        )

    def removeOneChild(self, query: dict, path2Childs: str = "child"):
        """
        remove a child, the first one, which matches the componentName or templateName will be removed. You are allowed to given either of it
        @Parameters:
            query: dict -- a query for find a child. For Example query={"_id" = 123}. It will find a child with _id=123 and remove it
            path2Childs:str -- where is the child relativ to root. default:"child"
        @Return:
            child -- the removed child
            1 -- matches nothing

        """
        childs: Any = self._Cursor(path2Childs)
        for child in childs:
            matchRes = []
            for key, val in query.items():
                if key not in list(child.keys()):
                    matchRes.append(False)
                    print("key does not exist!\ndo nothing!")
                    break
                elif child[key] == val:
                    matchRes.append(True)
                else:
                    matchRes.append(False)
            if matchRes and False not in matchRes:
                childs.remove(child)
                print(f"child: {child} is removed")
                return child
            elif (matchRes) and (True in matchRes) and (False in matchRes):
                print(f"has conflict. Please check your query:{query}")
            else:
                print("no match")
        return 1

    def getChilds(self, path2Childs: str = "child"):
        """
        List all childs under this Instance
        @Paramters
            path2Childs:str -- the path to the childs, relativ to the root
        @Returns
            all the childs as list
        """
        childs = self._Cursor(path2Childs)
        return list(childs)

    def checkBeforeUpload(self, checkList=None):
        """
        some fileds should not empty before push to Server. if the Parameter checkList is not set, it will use a BaseCheckList, which unter __init__
        @Parameters
            checkLists --  the path to the field can be putted under this list. If you want to make sure, that the leaf value of {"a":{"aa":{"aaa": 123}}} should not empty. you can put "a.aa.aaa"into checkList. checkList=["a.aa.aaa" ]
        @Returns
            0 -- if it's ok

        """
        if self["templateName"] != "BaseTemplate":
            if not checkList:
                checkList = self.baseCheckList
            for check in checkList:
                if not self._Cursor(check):
                    raise Exception(f"value of {check} is not Set. Do nothing")
            return 0

    # TODO login function
    def deleteDocuments(self, collection, ids: list):
        """
        Delete Documents from DB based of id and push a Log to DB Server
        @Parameters:
            collection -- the collection of DB

            ids -- ids of to be removed documents
        """
        for id in ids:
            collection.delete_one({"_id": id})
            self.pushLog2DB(f"{id} from {collection.name} is removed")

    # TODO make it as a decorate
    def DBModifyLog(self, mofifyType: str):
        def decorate(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    insert_id = func(*args, **kwargs)
                    self.pushLog2DB(
                        {"type": mofifyType, "insert_id": insert_id},
                        port=self.port,
                        host=self.host,
                    )
                    return insert_id
                except Exception as e:
                    self.pushLog2DB(
                        f"Error: {e}",
                        port=self.port,
                        host=self.host,
                    )
                    return e

            return wrapper

        return decorate

    def pushLog2DB(
        self,
        msg,
        host: Union[str, None] = None,
        port: Union[int, None] = None,
        dbName: str = "Records",
        collName: str = "Log",
    ):
        """
        push a Log to Database. if host and port are None, It will use the same host and port as the Instance itself.
        @Parameters
            msg -- a Message to be pushed
            host: Union[str,None] -- host of Log Server. default: None
            port:  Union[int,None] -- port of Log Server,
            dbName: str -- DBName of Log Server. default:"Records",
            collName: str -- DBName of Log Server. default: "Log",
        @Returns
            inserted_id -- id of the Log Info

        """
        import pymongo
        import datetime

        # if host and port are None, It will use a same host and port as the Instance
        if not host:
            host = self.host
            port = self.port

        with pymongo.MongoClient(host=host, port=port) as client:
            db = client[dbName]
            coll = db[collName]
            inserted_id = coll.insert_one(
                {"info": msg, "time": datetime.datetime.now()}
            ).inserted_id
            return inserted_id

    def _Cursor(self, nodePath: str):
        """
        go to a node
        @Parameters:
            nodePath:str -- For example path to a value under a dict{"a":{"aa":{"aaa":value}}}. The nodePath should be "a.aa.aaa"
        """
        cursor = self
        for node in nodePath.split("."):
            cursor = cursor[node]
        return cursor

    def checkKeyinDict(self, aDict, aKey):
        if not aKey in aDict:
            raise KeyError(f"{aKey} is not in {aDict}.")

    def setTF(
        self,
        componentList: list,
        matchKey: str = "componentName",
        path2Childs: str = "child",
    ):
        """
        set the childs under the instance
        @Parameters:
            compoentList: list -- You could use function createOneChild to create a standard child and adds into a List.

            matchKey: str -- use this key for matching the child between the componentList and the childs in the instance. default: "componentName",

            path2Childs:str -- path to the childs. default:"child"
        @Returns:
            self
        """
        childsList = self._Cursor(path2Childs)
        if len(componentList) == len(childsList):
            raise Exception(
                "Length of compoentList doesn't match the length of childsList"
            )
            # print(
            #     Exception(
            #         "Length of compoentList doesn't match the length of childsList"
            #     )
            # )
        for child in childsList:
            for component in componentList:
                self.checkKeyinDict(component, matchKey)
                if child[matchKey] == component[matchKey]:
                    print(f"Child{child} matches with Component{component}")
                    child.update({"tf": component["tf"]})
                    componentList.remove(component)
                    break

        print(f"New childsList:{self._Cursor(path2Childs)}")
        return self

    def convert1dTF2TRTE(self, TF1D):
        """
        convertiert a 1x16 Vector to a 4x4 Matrix and some other informations like Euler(zxy)
        @Parameters
            TF1D -- a 1x16 Vector
        @Returns
        :dict -- {  "TF44": 4x4 Transformations Matrix
                    "RotMat": 3x3 Rotationsmatrix
                    "TransVec": 1x3 Translationsvector
                    "Euler": 1x3 Eulerwinkel with "zxy"
                }

        """
        import numpy as np
        from scipy.spatial.transform import Rotation

        tf = np.array(TF1D, dtype=np.float64).reshape((4, 4))
        rotMat = tf[:3, :3]
        transVector = tf[:3, 3]
        rotMat = Rotation.from_matrix(rotMat)
        return {
            "TF44": tf,
            "RotMat": rotMat.as_matrix(),
            "TransVec": transVector.T,
            "Euler": rotMat.as_euler("zxy"),
        }

    def getTF(
        self,
        componentName: Union[str, None] = None,
        id: Union[str, None] = None,
        path2Childs: str = "child",
        path2TF: str = "transform",
    ):
        """
        Get transformations of the childs of this instance, based of componentName oder id. if you don't give componentName and id, all child tranforamtions will be given.
        @Parameters:
            componentName:str -- to
            id: Uniio = None,
            path2Childs: str = "child",
            path2TF: str -- path relativ to the root of the child to transformation Matrix in the instance. dafault:"transform"
        @Returns:
        [{  "child":componentName,
            "TF44": 4x4 Transformations Matrix
            "RotMat": 3x3 Rotationsmatrix
            "TransVec": 1x3 Translationsvector
            "Euler": 1x3 Eulerwinkel with "zxy"},.....]
        """
        res = []

        childList = self._Cursor(path2Childs)
        for child in childList:
            if not child[path2TF]:
                break
            if id:
                if id == child["_id"]:
                    TRTE = self.convert1dTF2TRTE(child[path2TF])
                    TRTE.update({"child": child["componentName"]})
                    res.append(TRTE)

            elif componentName:
                if child["componentName"] == componentName:
                    TRTE = self.convert1dTF2TRTE(child[path2TF])
                    TRTE.update({"child": child["componentName"]})
                    res.append(TRTE)
            else:
                TRTE = self.convert1dTF2TRTE(child[path2TF])
                TRTE.update({"child": child["componentName"]})
                res.append(TRTE)
        return res

    def _compare(self, objA, objB):
        """
        objA is the to be modified Dict. objA will compare with objB. The same values of objA from objB will be removed. objA itself will be returned.
        @Parameters:
            objA -- to be modified Dict.
            objB -- objA will compare with objB
        @Returns:
            objA
        """
        import copy

        objACopy = copy.deepcopy(objA)
        objBCopy = copy.deepcopy(objB)

        def goNext(obja, objb, modiobj, path):
            if path[:-1] not in self.ignoreKeys:
                for key, val in obja.items():
                    if isinstance(val, dict):
                        goNext(obja[key], objb[key], modiobj[key], path + key + ".")

                    else:
                        # TODO Ignore List
                        fullPath = path + key
                        if obja[key] == objb[key] and fullPath not in self.ignoreKeys:
                            modiobj.pop(key)

        goNext(objACopy, objBCopy, objA, "")
        return objA

    def _cleanup(self, obj):
        """
        clean up a dict. All the itemes, which has null value, will be removed.
        @Parameters:
            obj -- a to be cleaned dict
        @Return:
            obj -- a obj after the clean up
        """

        def goNext(base, modiobj, path):
            for key, val in base.items():
                if isinstance(val, dict):
                    if path[:-1] not in self.ignoreKeys:
                        if val:
                            goNext(val, modiobj[key], path + key + ".")
                        else:
                            modiobj.pop(key)
                else:
                    tmp_path = path + key
                    if not val and tmp_path not in self.ignoreKeys:
                        modiobj.pop(key)

        tmp = {}
        while tmp != obj:
            tmp = copy.deepcopy(obj)
            base = copy.deepcopy(obj)
            goNext(base, obj, "")
        return obj

    def get3DModel(self, path2Model: str = "3Dmodel"):
        """
        Get 3DModel. A Instance of Model3D will be returned.
        @params:
            path2Model:str = the path to the key of 3D Model
        @returns:
            class Model3D
        """
        modelDoc = self._Cursor(path2Model)
        if modelDoc["data"]:
            model3D = Model3D().loadFromBase64S(modelDoc["data"])
            model3D.setSuffix(modelDoc["type"])
            return model3D
        else:
            print("3D Model is empty. Please Check.")

    def set3DModel(
        self,
        modelInstance: Model3D,
        path2Data: str = "3Dmodel.data",
        path2Type: str = "3Dmodel.type",
    ):
        """
        Use this for setting the 3D Model to Document
        @params:
            modelInstance: Model3D -- you can create it use package Model2Base64
            path2Data:str -- the path to data key of 3DModel
            path2Type:str -- the path to type key of 3DModel
        @returns:
            self
        """
        modelData = [
            {path2Data: modelInstance.getBase64S()},
            {path2Type: modelInstance.getType()},
        ]
        self.setValue(modelData)
        print(f"The length of Data:{len(self._Cursor(path2Data))}")
        print(f"The Type of adding Data: {self._Cursor(path2Type)}")

        return self


if __name__ == "__main__":
    tempalte = Template(port=27018)
    import pprint

    pprint.pprint(
        tempalte.createOneChild(
            componentName="L375P70MLD",
            templateName="Template_L375P70MLD",
            templateId="b7880b6f-81eb-4fa8-9d7f-29e369f63a87",
            transform=[],
        ).dict()
    )
## Ergebnis:
# {
# 	'componentName': 'L375P70MLD',
#   'templateName': 'Template_L375P70MLD',
#   'templateId': 'b7880b6f-81eb-4fa8-9d7f-29e369f63a87',
#   'transform': []
# }

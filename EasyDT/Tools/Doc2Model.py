class Doc2Model:
    def __init__(self, aDict, systemName: str) -> None:
        self.__toBeConvertObj = {systemName: aDict}
        self.__systemName = systemName
        self.nodeSetXMLRes = {}
        # run
        self.genNodeset()

    def _searchNeu(self, aDict):
        res = {}

        def goAraound(pathTo, element):
            if isinstance(element, dict):
                for key, val in element.items():
                    if key == "child":
                        pass
                    else:
                        goAraound(f"{pathTo}.{key}", val)
            else:
                res[pathTo] = element

        goAraound("", aDict)
        return res

    def _construct(self, kLS, vLS):
        obj = self._baseobj(self.__systemName)
        for k, v in zip(kLS, vLS):
            dictptr = obj

            for indexkk, kk in enumerate(k[1:]):
                isfound = [0, False]
                try:
                    for index, child in enumerate(dictptr["Children"]["Object"]):
                        # if child["name"] == kk:
                        if child["@SymbolicName"] == f"pxd:{kk}":
                            isfound = [index, True]
                except KeyError:
                    pass
                try:
                    for index, child in enumerate(dictptr["Children"]["Property"]):
                        # if child["name"] == kk:
                        if child["@SymbolicName"] == f"pxd:{kk}":
                            isfound = [index, True]
                except KeyError:
                    pass

                if isfound[1]:
                    dictptr = dictptr["Children"]["Object"][isfound[0]]
                else:
                    if indexkk == len(k[1:]) - 1:
                        try:
                            dictptr["Children"]["Property"].append(
                                self._variableobj(kk, v)
                            )
                        except KeyError:
                            dictptr["Children"]["Property"] = []
                            dictptr["Children"]["Property"].append(
                                self._variableobj(kk, v)
                            )

                    else:
                        try:
                            dictptr["Children"]["Object"].append(self._baseobj(kk))
                        except KeyError:
                            dictptr["Children"]["Object"] = []
                            dictptr["Children"]["Object"].append(self._baseobj(kk))

                        dictptr = dictptr["Children"]["Object"][-1]
        return {"Object": {**obj, **self._orgRef()}}

    def _baseobj(self, name="Laserdiode", category="Laserdiode"):
        return {
            # "Object": {
            "@SymbolicName": f"pxd:{name}",
            "@Category": f"{category}",
            "@ModellingRule": "Mandatory",
            "@TypeDefinition": "ua:BaseObjectType",
            "Description": "Eine LaserDiode von Optiksytem des PhoenixD",
            "Children": {},
            # }
        }

    def _variableobj(self, name, value):
        return {
            # "Property": {
            "@SymbolicName": f"pxd:{name}",
            "@DataType": "ua:String",
            "@ModellingRule": "Mandatory",
            "@AccessLevel": "Read",
            "DefaultValue": {"uax:String": str(value)},
            # }
        }

    def _baseModelDesign(self):
        return {
            "ModelDesign": {
                "@xmlns:uax": "http://opcfoundation.org/UA/2008/02/Types.xsd",
                "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "@xmlns:ua": "http://opcfoundation.org/UA/",
                "@xmlns:pxd": "https://www.match.uni-hannover.de/de/binnemann/forschungsprojekte/projects/phoenixd/UA/",
                "@xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
                "@TargetNamespace": "https://www.match.uni-hannover.de/de/binnemann/forschungsprojekte/projects/phoenixd/UA/",
                "@TargetVersion": "0.9.0",
                "@TargetPublicationDate": "2020-05-01T00:00:00Z",
                "@xmlns": "http://opcfoundation.org/UA/ModelDesign.xsd",
                "Namespaces": {
                    "Namespace": [
                        {
                            "@Name": "phoenixD",
                            "@Version": "1.00",
                            "@Prefix": "phoenix.d",
                            "@XmlNamespace": "https://www.match.uni-hannover.de/de/binnemann/forschungsprojekte/projects/phoenixd/UA/Type.xsd",
                            "#text": "https://www.match.uni-hannover.de/de/binnemann/forschungsprojekte/projects/phoenixd/UA/",
                        },
                        {
                            "@Name": "OpcUa",
                            "@Version": "1.03",
                            "@Prefix": "opc.ua",
                            "@PublicationDate": "2013-12-02T00:00:00Z",
                            "#text": "http://opcfoundation.org/UA/",
                        },
                    ]
                },
            }
        }

    def _orgRef(self):
        return {
            "References": {
                "Reference": {
                    "@IsInverse": "true",
                    "ReferenceType": "ua:Organizes",
                    "TargetId": "ua:ObjectsFolder",
                }
            }
        }

    def __genChild(self, aDict):
        __res = {}
        aListwithDict = aDict["child"]
        for ele in aListwithDict:
            for k, v in ele.items():
                __res[f'.{self.__systemName}.child.{ele["componentName"]}_{ele["_id"]}.{k}'] = v
        return __res

    def genNodeset(self):
        __childs = self.__genChild(self.__toBeConvertObj[self.__systemName])
        __pathValuePaar = self._searchNeu(self.__toBeConvertObj)
        __pathValuePaar.update(__childs)
        __kLS = [i.split(".")[1:] for i in __pathValuePaar.keys()]
        __vLS = __pathValuePaar.values()
        # kLS = [i.split(".")[1:] for i in kLS]
        obj = self._construct(__kLS, __vLS)

        __output = self._baseModelDesign()
        __output["ModelDesign"] = dict(**__output["ModelDesign"], **obj)
        self.nodeSetXMLRes = __output

    def save2File(self, save2Path):
        import json
        import xmltodict

        # with open(save2Path, "w") as f:
        #     f.write(json.dumps(self.nodeSetXMLRes, indent=4))
        with open(save2Path, "w") as f:
            f.write(xmltodict.unparse(self.nodeSetXMLRes))
    
    def pprint(self):
        import pprint
        pprint.pprint(self.nodeSetXMLRes)


if __name__ == "__main__":
    from EasyDT.Core import ModifyComponent

    product = ModifyComponent(port=27020).loadFromDB(
        id="8c916671-2f33-4cf2-bc8c-dcd8cd7bdd7f"
    )
    product.pop("3Dmodel")
    product.pprint()
    nodeset = Doc2Model(aDict=dict(product),systemName=product.componentName)
    nodeset.pprint()
    nodeset.save2File("Model.xml")
    

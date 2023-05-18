from typing import Union, Any


class GenSnippM1:
    """
    This Class is used for generate Code Snippets for vscode. You should give a dictLikeObj to the Class, when you initial the Class. It uses deep first Algorithmus to search the hole dictLikeObj and generate the path(nodes) to the end value(leaf).

    Parameters:
    -----------------
        dictLikeObj: Union[dict, bytes, str] -- The Type of this can be directly a dict or json file in str or bytes. It's up to you~

        genFullPath: bool -- This means, that the path from root to end will be fully gernerated. So the Path could be very long and the result of Inteli___ will be not very visualable.like:".node1.node2.node3.......nodeN". default = False

        genNeighbourPath: bool -- With this parameter only the neighour Nodes(2 Nodes) be set together. Like:".node1.node2". default = True

        savePath: str -- You will set where to save the snippet.  Default is: "./.vscode/snipp.code-snippets". This Path leads to the workspace of snippet only unter this workspace.

    Functions:
    -----------------
        genOneSnipp(self, prefix, body, description="") -- Generate only one snippet

        __2NodePath(self) -- Generally you can't used this function outside the class. But it is important for the Methode of generate paths(nodes). This function will cut the full path, which path from root to end value. you can switch this with (genNeighbourPath: bool)

        __fullNodePath(self) -- same as before this function will generate a full path to the end value

        switchFullNeigh(__isGenFullPath:bool, __isGenNeighbourPath:bool) -- You could reset generate full path, only neighbours or both after initialization with this function.

        save2File(self, path:[None,str]) -- The parameter of path could be set when you initial this instance with ""savePath:
        str"". You could also redefine the path, when you run this function with instance.save2File(path="a path").  The extention name should be ".code-snippets". so vscode will know, that this is a Snippet. If you set nothing, it will use the path, which defined, when you initialize the instance. if you also don't set it at initialization, it will use a default value ""./.vscode/snipp.code-snippets"", which limit the scope of Snippets only in this workspace.

        getSnippDict() -- it will return the the result of Snippet in type Dict. you kann also call this function directly call the instance like: ""aTemplate = Tempalte()"" then "result:dict = aTemplate()" it's same with ""aTemplate.getSnippDict()""

        genSnipp() -- it will generate the Snippets, which base of the dictLikeObj, for vscode and save in the Attribute __snippDict. It will auto run, when you initialize a instance.

        replaceSourceObj(dictLikeObj: Union[dict, bytes, str]) -- replace the source dictLikeObj with a new one
    """

    def __init__(
        self,
        dictLikeObj: Union[dict, bytes, str],
        genFullPath: bool = False,
        genNeighbourPath: bool = True,
        savePath: str = "./.vscode/snipp.code-snippets",
        rootName="",
    ) -> None:
        self.__aDict = self.__toDict(dictLikeObj)
        self.__snippDict = {}
        self.__NDpaths = []
        self.__snippPrefixs = []
        self.__isGenFullPath: bool = genFullPath
        self.__isGenNeighbourPath: bool = genNeighbourPath
        self.__savePath: str = savePath
        self.__rootName = rootName
        self.genSnipp()

    def __call__(self) -> Any:
        return self.getSnippDict()

    def replaceSourceObj(self, dictLikeObj: Union[dict, bytes, str]):
        """
        replace the source dictLikeObj, when inialize.

        Parameters:
        ------------------
        dictLikeObj:dictLikeObj:Union[dict, bytes, str]
        """
        print("the source dictLikeObj will be replaced.")
        self.__aDict = self.__toDict(dictLikeObj)
        print("regenerating the Snippets.")
        self.genSnipp()

    def genOneSnipp(self, prefix, body, description=""):
        """Stelle nur ein Snipp block"""

        snipp = {
            "prefix": prefix,
            "body": f"{body}$0",
            "description": description,
        }
        return snipp

    def __2NodePath(self):
        """
        nur die zwei nebeneinander liegende Nodes werden zusammen gesetzt
        ["node1.node2", "node2.node3".......]
        """
        for x in self.__NDpaths:
            tmp = str(x).split(".")
            for index in range(len(tmp[:-1])):
                if not tmp[index + 1][0] == "$":
                    self.__snippPrefixs.append(f"{tmp[index]}.{tmp[index+1]}")
                else:
                    self.__snippPrefixs.append(
                        f"{tmp[index-1]}.{tmp[index]}.{tmp[index+1]}"
                    )

    def switchFullNeigh(self, __isGenFullPath: bool, __isGenNeighbourPath: bool):
        self.__isGenFullPath = __isGenFullPath
        self.__isGenNeighbourPath = __isGenNeighbourPath
        print(
            f"""Switch to {dict({"GenFullPath":self.__isGenFullPath, "GenNeighbourPath":self.__isGenNeighbourPath})}"""
        )
        self.genSnipp()

    def __fullNodePath(self):
        """
        die alle Noden, die in einer Reihe legen, werden zusammengestellt
        ["node1.node2.node3.->.Endepunkt"]
        """
        for x in self.__NDpaths:
            self.__snippPrefixs.append(x)

    def genSnipp(self):
        """
        Generiere die vollständige Snippet
        """
        print("generating the Snippets")
        self.__snippPrefixs.clear()
        self.__searchDict()
        self.__snippDict.clear()
        if self.__isGenFullPath:
            self.__fullNodePath()
        if self.__isGenNeighbourPath:
            self.__2NodePath()

        for x in self.__snippPrefixs:
            if x:
                self.__snippDict[x] = self.genOneSnipp(x, x)
        print("generating the Snippets is finished.")

    def __toDict(self, dictLikeObj):
        """
        Konvertiere ein dictLikeObj zu dict
        """
        if isinstance(dictLikeObj, dict):
            return dictLikeObj

        if isinstance(dictLikeObj, str) or isinstance(dictLikeObj, bytes):
            import json

            tmp = json.loads(dictLikeObj)
            dictLikeObj = tmp

        if isinstance(dictLikeObj, list):
            tmp = {}
            for m in dictLikeObj:
                for key, val in m.items():
                    tmp[key] = val
            dictLikeObj = tmp

        if not isinstance(dictLikeObj, dict):
            raise InterruptedError(
                f"Please Check the Type of dictLikeObj {type(dictLikeObj)}"
            )
        return dictLikeObj

    def __searchDict(self):
        """
        Recusive durchsuchen ein Dict
        """

        def goNext(path2subNode, element):
            if isinstance(element, dict):
                rest = list(element.items())
                self.__snippPrefixs.append(path2subNode)

                while rest:
                    select = rest.pop()
                    goNext(f"{path2subNode}.{select[0]}", select[1])
            else:
                self.__snippPrefixs.append(path2subNode)
                print(path2subNode)

        goNext(self.__rootName, self.__aDict)
        return 0

    def save2File(self, path: Union[None, str] = None):
        """
        Speichen in einem File mit JSON Format
        """
        import json
        from pathlib import Path, PurePath

        if not path:
            path = self.__savePath

        # check folder
        pathdir = PurePath().joinpath(*path.split("/" if "/" in path else "\\")[:-1])
        if not Path(pathdir).exists():
            Path(pathdir).mkdir()
            print(f"make dir under: {Path(pathdir)}")

        if bool(self.__aDict):
            with open(Path(path), "w") as f:
                f.write(json.dumps(self.__snippDict, ensure_ascii=False, indent=4))
                print(f"Save in {Path(path)}")
        else:
            raise InterruptedError("You haven't gen Snipp")

    def getSnippDict(self):
        """
        Get the result of Snippets in dict

        Returns:
        ------------------
        dict -- result of Snippets

        """
        return self.__snippDict


if __name__ == "__main__":
    aDict = {
        "_id": {"blabla": {"bbb": "bbb"}, "a": "aa", "b": "bb"},
        "overview": {"a": "aa", "b": "bb"},
        "working": {"a": "aa", "b": "bb"},
    }
    f = open("testJson.json", "r")
    gensnipp2 = GenSnipp(f.read(), genFullPath=False, genNeighbourPath=True)
    f.close()
    gensnipp2.save2File("./.vscode/snipp.code-snippets")

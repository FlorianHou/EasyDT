import base64
from pathlib import Path
from typing import Any, Union


class Model3D:
    """
    This is a Class for saving the 3DModel. For save the 3DModel in MongoDB. I choose the Base64 as the encoder of Binary. The Binary will be convertiert to str. The export() function or directly Model3d() will return the bytes of the original file, the bytes of base64 , the str of the original file in base64 format and the Type of file as dictionary.
    """

    def __init__(self) -> None:
        self._modelFile: bytes = bytes()
        self._base64S: str = str()
        self._base64B: bytes = bytes()
        self._fileSuffix: str = str()
        self._supportSuffixs = [".stl", ".fbx", ".gltf", ".glb"]

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.export()

    def loadFromFile(self, path: Union[str, Path]):
        """
        load the file from local
        @params:
            path:str -- the path to the file
        @returns:
            self:Model3D
        """
        with open(Path(path), "rb") as f:
            print(f"Load file from {path}")
            self._modelFile = f.read()
            print(f"file size: {len(self._modelFile)}")
            self.setSuffix(Path(path).suffix)
            print(f"Suffix of the file: {self._fileSuffix}")
            self._modelFile2Base64B()
            self._base64B2Base64S()
        return self

    def loadFromBase64S(self, data: str):
        """
        load from the strings containing the result after encoding with base64.
        @params
            data:str
        @return
            self:Model3D
        """
        self._fileSuffix = str()
        print(f"Load from str, File Size:{len(self._modelFile)}")
        self._modelFile = base64.b64decode(data)
        print("Create Base64 Bytes")
        self._modelFile2Base64B()
        print("Create Base64 Str")
        self._base64B2Base64S()
        print("Don't forget to set file suffix")
        return self

    def getBase64S(self):
        if self._base64S:
            return self._base64S
        else:
            print("It's empty!")
            return None

    def getType(self):
        if self._fileSuffix:
            return self._fileSuffix
        else:
            print("Type is not setted. Please set it before get.")
            return None

    def _modelFile2Base64B(self):
        """
        use b64encode to encode the file, b64encode will return the data in bytes format after encode.
        """
        if self._modelFile:
            self._base64B = base64.b64encode(self._modelFile)
        return self

    def _base64B2Base64S(self):
        """
        converts the bytes from base64 to str. The bytes are converted with utf-8
        """
        if self._modelFile:
            if not self._base64B:
                self._base64B = base64.b64encode(self._modelFile)
            else:
                self._base64S = str(self._base64B, encoding="utf-8")
        return self

    def setSuffix(self, suffix: str):
        """
        If you load from a file, the suffix, which is used for declaring the type of file, will be automatisch setted. The suffix should be same as '.stl','.fbx'. The suffix will be checked before setting. You can find the supported suffixs in self._supportSuffixs.

        @params
            suffix:str -- set a suffix
        """
        if suffix.lower() in self._supportSuffixs:
            self._fileSuffix = suffix.lower()

        else:
            print(
                f"Error failed to set suffix,because it is supported. The supported suffixs are {self._supportSuffixs}. Your input is: {suffix}"
            )

    def getSuffix(self):
        return self._fileSuffix

    def getSupportSuffix(self):
        """
        This will first print the supported suffix and return the list of supported suffixs
        @returns:
            supportSuffixs:list
        """
        print(f"supported suffixs: {self._supportSuffixs}")
        return self._supportSuffixs

    def export(self):
        """
        This will return a dictionary. It contains a modelFile_Bytes, base64_Str,base64_Bytes,type
        @returns
            {
                "modelFile_Bytes": bytes,
                "base64_Str": str,
                "base64_Bytes": bytes,
                "type": str,
            }
        """
        if self._fileSuffix:
            return {
                "modelFile_Bytes": self._modelFile,
                "base64_Str": self._base64S,
                "base64_Bytes": self._base64B,
                "type": self._fileSuffix,
            }
        else:
            print(
                "Suffix of the file is not setted! Please use setModelSuffix() to set it.\nDo nothing!"
            )

    def save2File(self, path: str):
        """save it to file"""
        with open(Path(path), "wb") as f:
            f.write(self._modelFile)
            f.flush()
        print(f"file is saved to {Path(path)}")
        return Path(path)


if __name__ == "__main__":
    # Create a Model
    Model = Model3D()

    # load from a local file
    Model.loadFromFile("stl\\Laserdiode.STL")

    # show support Suffix
    supportList = Model.getSupportSuffix()
    print(supportList)

    # get the result
    # Method 1
    res = Model.export()
    # Method 2
    res = Model()

    # get base64 str
    b64Str = res["base64_Str"]

    # load a Model with b64 str
    Model2 = Model3D().loadFromBase64S(b64Str)
    # save it to a file
    Model2.save2File("LSTest.stl")

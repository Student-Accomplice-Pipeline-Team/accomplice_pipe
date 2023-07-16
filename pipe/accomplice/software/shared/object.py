import json
from typing import Type, Union, Iterable
from enum import Enum


class JsonSerializable():

    def __init__(self, **kwargs) -> None:
        """Initialize a JsonSerializable from a dictionary.

        This function is required to deserialize from JSON.
        """
        # Set values for existing attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(
                    f"{self.__class__.__name__} has no attribute '{key}'")

    @classmethod
    def from_json(cls: "Type[JsonSerializable]", json_data: Union[str, bytes, bytearray]):
        data = json.loads(json_data)
        return cls(data)

    def to_json(self):
        return json.dumps(vars(self), default=lambda o: o.__dict__, indent=4)


class Asset(JsonSerializable):
    name = None
    path = None
    version = None
    checked_out = False
    variants : Iterable[str] = None

    def __init__(self, name: str) -> None:
        self.name = name

    def get_geo_path(self):
        return f"{self.path}/geo/"

    def get_material_path(self):
        return f"{self.path}/mats/materials.usd" if self.path else None
    
    def get_textures_path(self):
        pass

class MaterialType(Enum):
        BASIC = 1
        METAL = 2
        GLASS = 3
        CLOTH = 4
        SKIN = 5

class Material(JsonSerializable):
    name = None
    materialPath = None
    version = None
    hasUDIMs = False

    isPxr = True
    matType = 1

    def __init__(self, name: str, hasUDIMs: bool, 
                isPxr=True, matType=MaterialType.BASIC.value) -> None:
        self.name = name
        self.materialPath = '/mtl/' + name
        self.hasUDIMs = hasUDIMs
        self.isPxr = isPxr
        self.matType = matType

class MaterialsAsset(JsonSerializable):
    textureSets = None
    name = None

    def __init__(self, name: str, textureSets=[]) -> None:
        super().__init__()
        self.name = name
        self.textureSets = textureSets

    @staticmethod
    def from_string(json_str):
        json_dct = json.loads(json_str)
        textureSets = []
        for textureSet in json_dct['textureSets']:
            mat = Material(textureSet['name'], textureSet['hasUDIMs'],
                            textureSet['isPxr'], textureSet['matType'])
            textureSets.append(mat)

        obj = MaterialsAsset(json_dct['name'], textureSets)
        return obj


class Shot(JsonSerializable):
    name = None
    checked_out = False

    def __init__(self, name: str) -> None:
        self.name = name

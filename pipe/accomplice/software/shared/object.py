import json
import os
import re
from pathlib import Path
from typing import Type, Union, Iterable, Optional
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

class Effect(JsonSerializable):
    name = None
    path = None
        
    def __init__(self, name: str, path: Optional[str] = None) -> None:
        self.name = name
        self.path = path

class Asset(JsonSerializable):
    name = None
    path = None
    version = None
    checked_out = False
    variants : Iterable[str] = None

    def __init__(self, name: str, path: Optional[str] = None) -> None:
        self.name = name
        self.path = path

    def get_geo_path(self):
        return f"{self.path}/geo/"
    
    def get_shader_geo_path(self, geo_variant):
        path = f"{self.path}/geo/"
        if os.name == "nt":
            path = path.replace('/groups/', 'G:\\')

        path = path.replace('/pipeline/production/', '/shading/')
        path = path + self.name + '_' + geo_variant + '.fbx'
        return path
        
    def get_shading_path(self):
        path = f"{self.path}"
        if os.name == "nt":
            path = path.replace('/groups/', 'G:\\')

        path = path.replace('/pipeline/production/', '/shading/')
        return path

    
    def get_metadata_path(self):
        meta_path = f"{self.path}/textures/meta.json"

        if os.name == "nt":
            meta_path = meta_path.replace('/groups/', 'G:\\')

        return meta_path
    
    def get_metadata(self):
        meta_path = self.get_metadata_path()

        if os.path.isfile(meta_path):
            with open(meta_path, 'r') as f:
                data = AssetMaterials.from_string(f.read())

            return data
            
        return None
    
    def create_metadata(self):
        meta_path = self.get_metadata_path()
        data = AssetMaterials(self.name)
        geovars = self.get_geo_variants()

        hierarchy = {}
            
        for geovar in geovars:
            hierarchy[geovar] = {}
        
        data.hierarchy = hierarchy
    
        with open(meta_path, 'w') as outfile:
            outfile.write(data.to_json())

    def get_geo_variants(self):
        if os.name == "nt":
            path = Path(self.get_geo_path().replace('/groups/', 'G:\\'))
        else:
            path = Path(self.get_geo_path())

        geo_variants = []
        if os.path.isdir(path):
            

            path, _, files = next(os.walk(path))

            if files:
                for file in files:
                    geo_variants.append(file.split('.')[0])

        return geo_variants

    def get_mat_variants(self, geo_variant):
        if os.name == "nt":
            path = Path(self.get_geo_path().replace('/groups/', 'G:\\'))
        else:
            path = Path(self.get_geo_path())
        path = path / 'textures'
        mat_variants = []

        if path.exists():
            files = path.glob('*_DiffuseColor*1001.png.tex')

            for file in files:
                mat_variants.append(re.search('(.*_).*(_DiffuseColor_.*1001.*\.tex)', str(file)).group())
        return mat_variants

    def get_textures_path(self, geo_variant, material_variant):
        if os.name == "nt":
            path = Path(self.path.replace('/groups/', 'G:\\'))
        else:
            path = Path(self.path)

        path = path / 'textures' / geo_variant / material_variant

        return str(path)

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

class AssetMaterials(JsonSerializable):
    hierarchy = {}
    name = None

    def __init__(self, name: str, hierarchy = {}) -> None:
        super().__init__()
        self.name = name
        self.hierarchy = hierarchy

    @staticmethod
    def from_string(in_str):
        dct = json.loads(in_str)
        hier = {}
        for geovar in dct['hierarchy']:
          variants = {}
          for matvar in dct['hierarchy'][geovar]:
            materials = {}
            for material, data in dct['hierarchy'][geovar][matvar]['materials'].items():
              mat = Material(material, data['hasUDIMs'],
                            data['isPxr'], data['matType'])
              materials[material] = mat


            variants[matvar] = MaterialVariant(matvar, materials)


          hier[geovar] = variants

        return AssetMaterials(dct['name'], hier)

class MaterialVariant(JsonSerializable):
    materials = None
    name = None

    def __init__(self, name: str, materials=[]) -> None:
        super().__init__()
        self.name = name
        self.materials = materials

    @staticmethod
    def from_string(json_str):
        json_dct = json.loads(json_str)
        materials = {}
        for material in json_dct['materials']:
            mat = Material(material['name'], material['hasUDIMs'],
                            material['isPxr'], material['matType'])
            materials[material['name']] = mat

        obj = MaterialVariant(json_dct['name'], materials)
        return obj


class Shot(JsonSerializable):
    name = None
    path = None
    checked_out = False

    def __init__(self, name: str, path: Optional[str] = None) -> None:
        self.name = name
        self.path = path
    
    def get_shotfile(self, type: Optional[str] = None) -> str:

        if type not in [None, 'main', 'anim', 'camera', 'fx', 'layout', 'lighting']:
            raise ValueError('type must be one of "main", "anim", "camera", "fx", "layout", "lighting"')

        if type == 'main' or type == None:
            return self.path + '/' + self.name + '.hipnc'
        else:
            return os.path.join(self.path, type, f'{self.name}_{type}.hipnc')
    
    def get_layout_path(self):
        return os.path.join(self.path, 'layout', f'{self.name}_layout.usdc')

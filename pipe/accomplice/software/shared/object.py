import json
import os
import re
from pathlib import *
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
    _path = None
    version = None
    checked_out = False
    variants : Iterable[str] = None # TODO: It looks lik this is outdated or depreciated? 
    id = None

    def __init__(self, name: str, path: Optional[str] = None, id: Optional[int] = None) -> None:
        self.name = name
        self._path = self._get_first_path(path)
        self.id = id

    def _get_first_path(self, path: str) -> str:
        if path is None:
            return None
        return path.split(',')[0]

    def get_usd_path(self):
        return os.path.join(self._path, f"{self.name}.usd")

    def get_geo_path(self):
        return f"{self._path}/geo/"
    
    def get_shader_geo_path(self, geo_variant):
        path = f"{self._path}/geo/"
        if os.name == "nt":
            path = path.replace('/groups/', 'G:\\')

        path = path.replace('/pipeline/production/', '/shading/')
        path = path + self.name + '_' + geo_variant + '.fbx'
        return path
        
    def get_shading_path(self):
        path = f"{self._path}"
        if os.name == "nt":
            path = path.replace('/groups/', 'G:\\')

        path = path.replace('/pipeline/production/', '/shading/')
        return path

    
    def get_metadata_path(self):
        meta_path = f"{self._path}/textures/meta.json"

        if os.name == "nt":
            meta_path = meta_path.replace('/groups/', 'G:\\')

        return meta_path
    
    def get_metadata(self):
        meta_path = self.get_metadata_path()

        if os.path.isfile(meta_path):
            with open(meta_path, 'r') as f:
                data = AssetMaterials.from_string(f.read())
                f.close()

            return data
            
        return None
        
    
    # Because we weren't able to figure out how to query the database for assets that don't have any parents
    # We decided to just make it so the path variable only includes the first path that's returned.
    @property
    def path(self):
        return self._get_first_path(self._path)
    
    @path.setter
    def path(self, value):
        self._path = self._get_first_path(value)
        #self.create_metadata() # Recreate the path metadata if needed
    
    def create_metadata(self):
        meta_path = self.get_metadata_path()
        path = meta_path.replace('meta.json', '')
        data = AssetMaterials(self.name)
        geovars = self.get_geo_variants()

        hierarchy = {}
            
        for geovar in geovars:
            hierarchy[geovar] = {}
            matvars = self.get_mat_variants(geovar)
            for matvar in matvars:
                texture_sets = self.get_texture_sets(geovar, matvar)
                material = MaterialVariant(matvar, texture_sets)
                hierarchy[geovar][matvar] = material
            
        data.hierarchy = hierarchy

        if not os.path.exists(path):
            os.makedirs(path)
    
        with open(meta_path, 'w') as outfile:
            outfile.write(data.to_json())
            
    def update_metadata(self):
        meta = self.get_metadata()
        print('updating HAHAHAH')
        
        if not meta:
            print('no metadata found')
            self.create_metadata()
            meta = self.get_metadata()
            
        geovars = self.get_geo_variants()
        
        for geovar in geovars:
            if geovar not in meta.hierarchy.keys():
                meta.hierarchy[geovar] = {}
            matvars = self.get_mat_variants(geovar)
            for matvar in matvars:
                if matvar not in meta.hierarchy[geovar].keys():
                    texture_sets = self.get_texture_sets(geovar, matvar)
                    material = MaterialVariant(matvar, texture_sets)
                    meta.hierarchy[geovar][matvar]
                    meta.hierarchy[geovar][matvar] = material
    
        #print(meta.hierarchy)
        
        metadata_path = self.get_metadata_path()
 
        with open(metadata_path, 'w') as outfile:
            toFile = meta.to_json()
            outfile.write(toFile)

    def get_geo_variants(self):
        if str(os.name) == "nt":
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

        path = Path(self.get_geo_path().replace('geo', 'textures'))
        
        path = path / geo_variant
        print(path)
        mat_variants = []

        if path.exists():
            files = path.glob('*/')

            for file in files:
                mat_variants.append(str(file.name))
        return mat_variants
    
    def get_texture_sets(self, geo_variant, material_variant):
        path = Path(self.get_textures_path(geo_variant, material_variant))
        
        files = path.glob(self.name + '_' + geo_variant + '_' + material_variant + '_*.1001.*')
        materials = {}
        for file in files:
            texture_set = re.match('(?:[^_]*_){3}(.*)_', os.path.basename(file)).group(1)
            materials[texture_set] = Material(texture_set, True)
                
        return materials

    def get_textures_path(self, geo_variant, material_variant):
        if os.name == "nt":
            path = Path(self._path.replace('/groups/', 'G:\\'))
        else:
            path = Path(self._path)

        path = path / 'textures' / geo_variant / material_variant

        return str(path)

    def get_turnaround_path(self, geo_variant, material_variant):
        path = self._path
        path = path.replace('pipeline/production/assets', 'renders/assetTurnarounds')

        path = Path(path)

        path = path / geo_variant / material_variant

        return str(path)

class Character(Asset):

    def __init__(self, name: str, path: Optional[str] = None) -> None:
        self.name = name
        self._path = None

    def get_shader_geo_path(self):
        return correct_path(self.path) + '/' + self.name + '_geo.fbx'

    def get_material_path(self):
        return correct_path(self.path) + '/' + self.name + '_materials.usd'

    def get_textures_path(self):
        return os.path.join(correct_path(self._path), 'textures', self.name)

    def create_metadata(self):
        meta_path = self.get_metadata_path()
        path = meta_path.replace('meta.json', '')
        data = AssetMaterials(self.name)
        geovars = ['Standard']

        hierarchy = {}
            
        for geovar in geovars:
            hierarchy[geovar] = {}
        
        data.hierarchy = hierarchy

        if not os.path.exists(path):
            os.makedirs(path)
    
        with open(meta_path, 'w') as outfile:
            outfile.write(data.to_json())
            
    def get_hip_file(self):
        return os.path.join(self.path, self.name + '.hipnc')
    
    @property
    def path(self):
        return self._path
    
def correct_path(path):
        if str(os.name) == "nt":
            path = path.replace('/groups/', 'G:\\')
        return path


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

    def __init__(self, name: str, materials={}) -> None:
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
    available_departments = ['main', 'anim', 'camera', 'fx', 'cfx', 'layout', 'lighting']
    checked_out = False

    def __init__(self, name: str, cut_in: Optional[int] = None, cut_out: Optional[int] = None) -> None:
        self.name = name
        self.path = self._get_path_from_name(name)
        self.cut_in = cut_in
        self.cut_out = cut_out
        
    def _get_path_from_name(self, name):
        name_components = name.split('_')
        # TODO: obviously, this isn't super modular to have the path hardcoded like this, but the benefits seem to outweigh the costs in my mind
        # Ideally, there would be a single file that holds all of the base folders.
        return f'/groups/accomplice/pipeline/production/sequences/{name_components[0]}/shots/{name_components[1]}'
    
    def get_total_frames_in_shot(self):
        return self.cut_out - self.cut_in + 1
    
    def get_shotfile_folder(self, department: Optional[str] = None) -> str:
        if department == 'main' or department == None:
            return self.path 
        elif department not in self.available_departments:
            raise ValueError('type must be one of ' + ', '.join(self.available_departments))
        else:
            return os.path.join(self.path, department)
    
    def get_shot_frames(self, global_start_frame=1001, handle_frames=5):
            """
            Returns the start and end frames for a shot, along with extra frames for handles.

            Args:
                global_start_frame (int): The global start frame for the shot.
                handle_frames (int): The number of extra frames to include for handles.

            Returns:
                Tuple[int, int, int, int]: the handle start frame, shot start frame, shot end frame, and handle end frame.
            """
            # handle_start = global_start_frame
            # shot_start = global_start_frame + handle_frames
            # shot_end = shot_start + self.get_total_frames_in_shot() - 1
            # handle_end = shot_end + handle_frames
            # return handle_start, shot_start, shot_end, handle_end
            shot_start = global_start_frame + self.cut_in # self.cut_in is 0 based, so we don't need to subtract 1 from global_start_frame
            handle_start = shot_start - handle_frames
            
            shot_end = global_start_frame + self.cut_out
            handle_end = shot_end + handle_frames

            return handle_start, shot_start, shot_end, handle_end


    
    def get_shotfile(self, department: Optional[str] = None) -> str:
        shot_folder = self.get_shotfile_folder(department)

        if department == 'main' or department == None:
            return os.path.join(shot_folder, self.name + '.hipnc')
        else:
            return os.path.join(shot_folder, f'{self.name}_{department}.hipnc')
        
    def get_camera(self, cam_type):
        if cam_type not in ['FLO', 'RLO']:
            raise ValueError('type must be "FLO" or "RLO"')
        
        sequence, shot = self.name.split('_')
        folder = os.path.join(self.path, 'camera', cam_type)
        path_obj = Path(folder)
        
        files = list(path_obj.glob('camera_' + self.name + '*.usd'))
        
        if len(files) != 1:
            return None
        else:
            return str(files[0])
    
    def get_shot_usd_path(self, department: Optional[str] = None) -> str:
        """ Returns the path to the usd file that contains each subdepartment's usd file."""
        return self.get_shotfile(department).replace('.hipnc', '.usd')
    
    def get_maya_shotfile_path(self):
        houdini_file_path = self.get_shotfile('anim')
        assert houdini_file_path.endswith('hipnc')
        return houdini_file_path.replace('.hipnc', '.mb')
    
    def get_layout_path(self):
        return os.path.join(self.path, 'layout', f'{self.name}_layout.usda')

    def get_playblast_path(self, destination):
        sequence, shot = self.name.split('_')
        return os.path.join('/groups/accomplice/edit/shots/', destination, sequence, shot, self.name + '.mov')
    
    def get_name(self):
        return self.name
    
    def get_sequence(self):
        return self.name.split('_')[0]
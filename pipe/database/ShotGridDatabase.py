import os
import logging as log
from typing import Iterable, Set, Sequence, Union
from abc import ABC, abstractmethod

from .baseclass import Database
from shared.object import Asset

import sys
if str(os.name) == "nt":
    log.info('Running in Windows')
    sys.path.append('G:\\accomplice\\pipeline\\lib')
else:
    sys.path.append('/groups/accomplice/pipeline/lib')

import shotgun_api3 # Here's some good API reference: https://developer.shotgridsoftware.com/python-api/reference.html

# TODO: One thing that's a little messy about this class is that it handles both the JSON/dictionaries and the Asset objects. It would be nice to separate these out.

class ShotGridDatabase(Database):
    def __init__(self,
                 shotgun_server: str,
                 shotgun_script: str,
                 shotgun_key:    str,
                 project_id:     int,
                ):
        self.sg= shotgun_api3.Shotgun(shotgun_server, shotgun_script, shotgun_key)
        self.PROJECT_ID = project_id
        super().__init__()
        pass

    def get_asset(self, name: str) -> Asset:
        asset = GetOneAssetByName(self, name).get()
        sg_path = asset['sg_path']
        asset_name = os.path.basename(sg_path)
        assert name.lower() == asset_name
        return Asset(asset_name, path = asset['sg_path'])
        
    def get_assets(self, names: Iterable[str]) -> Set[Asset]:
        assets = GetAllAssetsByName(self, names).get()
        return set(
            Asset(
                os.path.basename(asset['sg_path']),
                path = asset['sg_path']
            ) for asset in assets
        )

    def get_asset_id(self, name: str) -> int:
        return GetOneAssetByName(self, name, ['id']).get()['id']

    def get_shot_id(self, name: str): # TODO: update to use query helper if you have time to avoid code duplication :)
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ],
            [ 'sg_status_list', 'is_not', 'oop' ],
            [ 'code', 'is', name ]
        ]
        fields = [
            'code',
            'id'
        ]
        shot = self.sg.find_one('Shot', filters, fields)
        return shot['id']

    def get_asset_list(self) -> Sequence[str]:
        query = GetAllAssets(self, ['tags', 'parents']).get() # By default, this now filters out variants (child assets)
        
        # Filter the query
        to_return = []
        for asset in query:
            # Filter out any assets with _Set_ in any of their tags
            for tag in asset['tags']:
                if not "_Set_" in tag['name']:
                    sg_path = asset['sg_path']
                    split_path = sg_path.split("/")
                    file_name = split_path[len(split_path) - 1]
                    to_return.append(file_name)
        return to_return

    # TODO: For consistency, you could convert these to use the query helper, but for now I don't want to fix something that's not broken :)
    def get_set_list(self) -> Sequence[str]:
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ],
            [ 'sg_status_list', 'is_not', 'oop' ],
            { 
                'filter_operator': 'all',
                'filters': [ 
                    [ 'sg_asset_type', 'is_not', t ] for t in self._untracked_asset_types
                ], 
            },
        ]
        fields = [
            'code',
            'tags'
        ]
        query = self.sg.find('Asset', filters, fields)
        to_return = []
        for asset in query:
            add = False
            # Only assets with _Set_ in one of their tags
            for tag in asset['tags']:
                if "_Set_" in tag['name']:
                    add = True
            if add:
                to_return.append(asset['code'])
        return to_return

    # TODO: For consistency, you could convert these to use the query helper, but for now I don't want to fix something that's not broken :)
    def get_shot_list(self) -> Sequence[str]:
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ],
        ]
        fields = [
            'code'
        ]
        query = self.sg.find('Shot', filters, fields)
        to_return = []
        for shot in query:
            shot_name = shot['code']
            if not 't' in shot_name.lower(): # This excludes the test shots, which begin 'T_0...'
                to_return.append(shot['code'])
        return to_return

    def set_asset_field(self, asset, field, value): 
        data = {field: value}
        asset_id = self.get_asset_id(asset)
        self.sg.update("Asset", asset_id, data)

    def set_shot_field(self, shot, field, value):
        data = {field: value}
        shot_id = self.get_shot_id(shot)
        self.sg.update("Shot", shot_id, data)
    
    def create_asset(self, name, asset_type, asset_path, parent_name=None) -> dict:
        id = self.get_asset_id(parent_name) # TODO: we need to guarantee that this always returns the ID of the parent asset, not the ID of the first asset with the same name!
        data = {
            'project': {'type': 'Project', 'id': self.PROJECT_ID},
            'code': name,
            'sg_asset_type': asset_type,
            'sg_path': asset_path,
            'parents': [{'type': 'Asset', 'id':id}]
        }
        return self.sg.create('Asset', data)

    def delete_asset_by_id(self, id: int):
        self.sg.delete('Asset', id)


class ShotGridQueryHelper(ABC):
    _untracked_asset_types = [ 
                        'Character', 
                        'FX', 
                        'Graphic', 
                        'Matte Painting', 
                        'Tool', 
                        'Font'
                    ]
    def __init__(self, database: ShotGridDatabase, additional_fields: list = [], override_fields=False, filter_out_variants=True):
        self.shot_grid_database = database
        self.shot_grid = database.sg
        self.fields = self._get_all_fields(additional_fields, override_fields)
        self.filter_out_variants = filter_out_variants
        
    def _get_all_fields(self, additional_fields: list = [], override_fields=False):
        if override_fields:
            return additional_fields
        else:
            return list(set(self._create_base_fields() + additional_fields)) # Remove duplicates
    
    def _construct_path_name_filter(self, names: Iterable[str]) -> dict:
        return {
            'filter_operator': 'any',
            'filters': [
                [ 'sg_path', 'ends_with', name.lower() ] for name in names
            ],
        }
    
    def _construct_code_name_filter(self, name: str) -> list:
        return [
            [ 'code', 'is', name ]
        ]
    
    def _create_base_filter(self) -> list:
        return [
            [ 'project', 'is', { 'type': 'Project', 'id': self.shot_grid_database.PROJECT_ID } ],
            [ 'sg_status_list', 'is_not', 'oop' ],
            { 
                'filter_operator': 'all',
                'filters': [ 
                    [ 'sg_asset_type', 'is_not', t ] for t in self._untracked_asset_types
                ], 
            },
        ]
    def _create_base_fields(self) -> list:
        return [
            'code',
            'sg_path',
            'parents' # Parents are now included by default so that we can filter for everything that doesn't have parents.
        ]
    

    def _construct_filter_by_path_end_name(self, name: str) -> list:
        base_filters = self._create_base_filter()
        base_filters.append(self._construct_path_name_filter([name]))
        return base_filters
    
    def _construct_filter_by_path_end_names(self, names: Iterable[str]) -> list:
        base_filters = self._create_base_filter()
        base_filters.append(self._construct_path_name_filter(names))
        return base_filters
    
    def _get_all_asset_json_by_name(self, filters, fields):
        assets = self.shot_grid.find('Asset', filters, fields)
        if self.filter_out_variants:
            assets = self._filter_out_child_assets(assets)
        return assets
    
    def _filter_out_child_assets(self, assets):
        return [asset for asset in assets if asset['parents'] == []] # Filter out child assets (variants)
    
    @abstractmethod
    def get(self):
        pass
    
class GetAllAssetsByName(ShotGridQueryHelper):
    def __init__(self, database: ShotGridDatabase, names: Iterable[str], additional_fields: list = [], override_fields=False, filter_out_variants=True):
        self.names = names
        super().__init__(database, additional_fields, override_fields, filter_out_variants)

    def _get_all_assets_by_name(self, names: Iterable[str]):
        filters = self._construct_filter_by_path_end_names(names)
        return self._get_all_asset_json_by_name(filters, self.fields)
    
    # Override
    def get(self):
        return self._get_all_assets_by_name(self.names)

class GetOneAssetByName(ShotGridQueryHelper):
    def __init__(self, database: ShotGridDatabase, name: Iterable[str], additional_fields: list = [], override_fields=False, filter_out_variants=True):
        self.name = name
        self.get_all_assets_by_name = GetAllAssetsByName(database, [name], additional_fields + ['parents'], override_fields, filter_out_variants)
        super().__init__(database, additional_fields, override_fields, filter_out_variants)

    def _get_one_asset_by_name(self, name: str):
        assets = self.get_all_assets_by_name.get()
        if self.filter_out_variants:
            assets = self._filter_out_child_assets(assets)
        assert len(assets) == 1, f"Expected to find one asset with name {name}, but found {len(assets)}"
        return assets[0]
    
    def get(self):
        return self._get_one_asset_by_name(self.name)
    
class GetAllAssets(ShotGridQueryHelper):
    def __init__(self, database: ShotGridDatabase, additional_fields: list = [], override_fields=False, filter_out_variants=True):
        super().__init__(database, additional_fields, override_fields, filter_out_variants)

    # Override
    def get(self):
        assets = self._get_all_asset_json_by_name(self._create_base_filter(), self.fields)
        if self.filter_out_variants:
            assets = self._filter_out_child_assets(assets)
        return assets
    
# class GetOneShotByName(ShotGridQueryHelper):
#     def __init__(self, database: ShotGridDatabase, name: Iterable[str], additional_fields: list = [], override_fields=False):
#         super().__init__(database, additional_fields, override_fields)

#     def _get_one_shot_by_name(self, name: str):
#         filters = self._construct_code_name_filter(name)
#         fields = [
#             'code',
#             'id'
#         ]
#         shot = self.sg.find_one('Shot', filters, fields)
#         return shot
    
#     def get(self):
#         pass
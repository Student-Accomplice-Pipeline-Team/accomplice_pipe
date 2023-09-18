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

class ShotGridDatabase(Database):
    def __init__(self,
                 shotgun_server: str,
                 shotgun_script: str,
                 shotgun_key:    str,
                 project_id:     int,
                ):
        sg= shotgun_api3.Shotgun(shotgun_server, shotgun_script, shotgun_key)
        self.PROJECT_ID = project_id
        self.shot_grid_query_helper = ShotGridQueryHelper(self, sg)
        super().__init__()
        pass

    def get_asset(self, name: str) -> Asset:
        asset = self.shot_grid_query_helper.get_one_asset_by_name(name)
        sg_path = asset['sg_path']
        name = os.path.basename(sg_path)
        return Asset(name, path = asset['sg_path'])
        
    def get_assets(self, names: Iterable[str]) -> Set[Asset]:

        assets = self.shot_grid_query_helper.get_all_assets_by_name(names)

        return set(
            Asset(
                os.path.basename(asset['sg_path']),
                path = asset['sg_path']
            ) for asset in assets
        )

    def get_asset_id(self, name: str) -> Asset:
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ],
            [ 'sg_status_list', 'is_not', 'oop' ],
            [ 'code', 'is', name ],
            { 
                'filter_operator': 'all',
                'filters': [ 
                    [ 'sg_asset_type', 'is_not', t ] for t in self._untracked_asset_types
                ]
            }
        ]
        fields = [
            'code',
            'sg_path',
            'id'
        ]
        asset = self.sg.find_one('Asset', filters, fields)
        return asset['id']

    def get_shot_id(self, name: str):
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
            'tags',
            'parents',
            'sg_path'
        ]
        query = self.sg.find('Asset', filters, fields)
        to_return = []
        for asset in query:
            add = True
            # Filter out any assets with _Set_ in any of their tags
            for tag in asset['tags']:
                if "_Set_" in tag['name']:
                    add = False
            # Filter out child assets (variants)
            if len(asset['parents']) > 0:
                add = False
            if add:
                sg_path = asset['sg_path']
                split_path = sg_path.split("/")
                file_name = split_path[len(split_path) - 1]
                to_return.append(file_name)
        return to_return

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
    
    def create_asset(self, name, asset_type, asset_path, parent_name=None):
        id = self.get_asset_id(parent_name) # TODO: we need to guarantee that this always returns the ID of the parent asset, not the ID of the first asset with the same name!
        data = {
            'project': {'type': 'Project', 'id': self.PROJECT_ID},
            'code': name,
            'sg_asset_type': asset_type,
            'sg_path': asset_path,
            'parents': [{'type': 'Asset', 'id':id}]
        }
        self.sg.create('Asset', data)

    def delete_asset(self, name):
        asset_id = self.get_asset_id(name)
        self.sg.delete('Asset', asset_id)


class ShotGridQueryHelper():
    _untracked_asset_types = [ 
                        'Character', 
                        'FX', 
                        'Graphic', 
                        'Matte Painting', 
                        'Tool', 
                        'Font'
                    ]
    def __init__(self, database: ShotGridDatabase, shot_grid):
        self.shot_grid_database = database
        self.shot_grid = shot_grid
        
    def _construct_name_filter(self, names: Iterable[str]) -> dict:
        return {
            'filter_operator': 'any',
            'filters': [
                [ 'sg_path', 'ends_with', name.lower() ] for name in names
            ],
        }
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
        ]

    def _construct_filter_by_path_end_name(self, name: str) -> list:
        return self._create_base_filter().append(self._construct_name_filter([name]))
    
    def _construct_filter_by_path_end_names(self, names: Iterable[str]) -> list:
        return self._create_base_filter().append(self._construct_name_filter(names))
    
    def _get_all_asset_json_by_name(self, filters, fields):
        assets = self.sg.find('Asset', filters, fields)
        return assets
    
    def get_all_assets_by_name(self, names: Iterable[str], additional_fields: list = []):
        filters = self._construct_filter_by_path_end_names(names)
        fields = self._create_base_fields() + additional_fields
        return self._get_all_asset_json_by_name(filters, fields)
    
    def get_one_asset_by_name(self, name: str, additional_fields: list = []):
        assets = self.get_all_assets_by_name([name], additional_fields)
        assert len(assets) == 1, f"Expected to find one asset with name {name}, but found {len(assets)}"
        return assets[0]
    
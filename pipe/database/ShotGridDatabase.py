import os
import logging as log
from typing import Iterable, Set, Sequence, Union

from .baseclass import Database
from shared.object import Asset

import sys
if str(os.name) == "nt":
    log.info('Running in Windows')
    sys.path.append('G:\\accomplice\\pipeline\\lib')
else:
    sys.path.append('/groups/accomplice/pipeline/lib')

import shotgun_api3


class ShotGridDatabase(Database):
    
    _untracked_asset_types = [ 
                        'Character', 
                        'FX', 
                        'Graphic', 
                        'Matte Painting', 
                        'Tool', 
                        'Font'
                    ]
    
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
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ],
            [ 'sg_status_list', 'is_not', 'oop' ],
            [ 'sg_path', 'ends_with', f'/{name}' ],
            { 
                'filter_operator': 'all',
                'filters': [ 
                    [ 'sg_asset_type', 'is_not', t ] for t in self._untracked_asset_types
                ], 
            },
        ]

        fields = [
            'code',
            'sg_path',
            'id'
        ]

        asset = self.sg.find_one('Asset', filters, fields)
        sg_path = asset['sg_path']
        name = os.path.basename(sg_path)
        return Asset(name, path = asset['sg_path'], id = asset['id'])
        
    def get_assets(self, names: Iterable[str]) -> Set[Asset]:
        # TODO: Ideally it'd be nice to not grab assets that have a parent, but since I can't figure that out, I'm going to just limit the path that's returned from an asset.
        # Our quick fix for now is to add the:
            # @property
            # def path(self):
        # lines to the Asset object. This will only return the first path that's returned from the database instead of the list of them :)
        
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ],
            [ 'sg_status_list', 'is_not', 'oop' ],
            {
                'filter_operator': 'any',
                'filters': [
                    [ 'sg_path', 'ends_with', f'/{name}' ] for name in names
                ],
            },
            { 
                'filter_operator': 'all',
                'filters': [ 
                    [ 'sg_asset_type', 'is_not', t ] for t in self._untracked_asset_types
                ], 
            },
        ]

        fields = [
            'code',
            'sg_path',
        ]

        assets = self.sg.find('Asset', filters, fields)

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
        id = self.get_asset_id(parent_name)
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
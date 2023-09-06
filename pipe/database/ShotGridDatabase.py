from typing import Iterable, Set, Sequence, Union

from .baseclass import Database

from sys import path as sys_path
sys_path.append('/groups/accomplice/pipeline/lib')
import shotgun_api3

from shared.object import Asset

from pprint import pprint

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
            [ 'code', 'is', name ],
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

        asset = self.sg.find_one('Asset', filters, fields)
        return Asset(asset['code'], path = asset['sg_path'])
        
    def get_assets(self, names: Iterable[str]) -> Set[Asset]:
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ],
            [ 'sg_status_list', 'is_not', 'oop' ],
            {
                'filter_operator': 'any',
                'filters': [
                    ['code', 'is', name] for name in names
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

        return set(Asset(asset['code'], path = asset['sg_path']) for asset in assets)

    def get_asset_id(self, name: str) -> Asset:
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ],
            [ 'sg_status_list', 'is_not', 'oop' ],
            [ 'code', 'is', name ],
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
        # fields = [
        #     'code',
        #     'sg_asset_type',
        #     'sg_status_list',
        # ]
        fields = [
            'code'
        ]

        query = self.sg.find('Asset', filters, fields)

        return [ asset['code'] for asset in query ]

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
            'tags'
        ]
        query = self.sg.find('Asset', filters, fields)
        to_return = []
        for asset in query:
            add = True
            # Filter out any assets with _Set_ in any of their tags
            for tag in asset['tags']:
                if "_Set_" in tag['name']:
                    add = False
            if add:
                to_return.append(asset['code'])
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
            if not 't' in shot_name.lower():
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
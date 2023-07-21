from typing import Iterable, Set, Sequence, Union

from .baseclass import Database

import shotgun_api3

from shared.object import Asset

from pprint import pprint

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
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ],
            [ 'code', 'is', name ],
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
            {
                'filter_operator': 'any',
                'filters': [
                    ['code', 'is', name] for name in names
                ],
            },
        ]

        fields = [
            'code',
            'sg_path',
        ]

        assets = self.sg.find('Asset', filters, fields)

        return set(Asset(asset['code'], path = asset['sg_path']) for asset in assets)

    def get_asset_list(self) -> Sequence[str]:
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ],
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

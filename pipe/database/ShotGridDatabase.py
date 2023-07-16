from typing import Sequence

from .baseclass import Database

import shotgun_api3

from shared.object import Asset

class ShotGridDatabase(Database):
    
    
    def __init__(self,
                 shotgun_server: str,
                 shotgun_script: str,
                 shotgun_key:    str,
                 project_id:     int,
                ):
        self.sg = shotgun_api3.Shotgun(shotgun_server, shotgun_script, shotgun_key)
        self.PROJECT_ID = project_id
        super().__init__()
        pass
    
    def get_asset(self, name: str) -> Asset:

        return super().get_asset(name)

    def get_asset_list(self) -> Sequence[str]:
        filters = [
            [ 'project', 'is', { 'type': 'Project', 'id': self.PROJECT_ID } ]
        ]
        return super().get_asset_list()

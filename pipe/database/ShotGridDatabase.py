import os
import logging as log
from typing import Iterable, Set, Sequence, Optional
from abc import ABC, abstractmethod

from .baseclass import Database
from shared.object import Asset # I think this one works, but for some reason the IDE wasn't getting it
# from ..accomplice.software.shared.object import Shot, Asset

import sys
if str(os.name) == "nt":
    log.info('Running in Windows')
    sys.path.append('G:\\accomplice\\pipeline\\lib')
else:
    sys.path.append('/groups/accomplice/pipeline/lib')

import shotgun_api3 # Here's some good API reference: https://developer.shotgridsoftware.com/python-api/reference.html

# TODO: One thing that's a little messy about this class is that it handles both the JSON/dictionaries and the Asset objects. It would be nice to separate these out.
# It seems like much of the object creation is being done in the proxy.py file

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
        return Asset(asset_name, path = asset['sg_path'], id = asset['id'])
        
    def get_assets(self, names: Iterable[str]) -> Set[Asset]:
        assets = GetAllAssetsByName(self, names).get()
        return set(
            Asset(
                os.path.basename(asset['sg_path']),
                path = asset['sg_path']
            ) for asset in assets
        )
    
    def get_shot(self, name: str) -> dict:
        shot_dictionary = GetOneShotByName(self, name).get()
        return shot_dictionary

    def get_asset_id(self, name: str) -> int:
        return GetOneAssetByName(self, name).get()['id']

    def get_shot_id(self, name: str):
        return GetOneShotByName(self, name).get()['id']

    def get_asset_list(self) -> Sequence[str]:

        def is_set_in_tag_name(asset):
            for tag in asset['tags']:
                if "_Set_" in tag['name']:
                    return True
            return False
        query = GetAllAssets(self, ['tags', 'parents']).get() # By default, this now filters out variants (child assets)
        
        # Filter the query
        to_return = []
        for asset in query:
            assert len(asset['parents']) == 0
            # Filter out any assets with _Set_ in any of their tags
            if not is_set_in_tag_name(asset):
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
            [ 'sg_status_list', 'is_not', 'oop' ],
        ]
        fields = [
            'code'
        ]
        query = self.sg.find('Shot', filters, fields)
        log.debug(query)
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
    
    def create_asset(self, name, asset_path, asset_type='Environment', parent_id: Optional[int]=None) -> dict:
        data = {
            'project': {'type': 'Project', 'id': self.PROJECT_ID},
            'code': name,
            'sg_asset_type': asset_type,
            'sg_path': asset_path,
        }

        if parent_id is not None:
            data['parents'] = [{'type': 'Asset', 'id': parent_id}]

        return self.sg.create('Asset', data)
    
    def create_variant(self, name, parent_name) -> dict:
        parent = self.get_asset(parent_name)
        asset_path = parent.path
        parent_id = parent.id
        return self.create_asset(name, asset_path, parent_id=parent_id)

    def delete_asset_by_id(self, id: int):
        self.sg.delete('Asset', id)


class ShotGridQueryHelper(ABC):
    _untracked_asset_types = [ 
                        'Character', 
                        'FX', 
                        'Graphic', 
                        'Matte Painting', 
                        'Vehicle',
                        'Tool', 
                        'Font'
                    ]
    def __init__(self, database: ShotGridDatabase, additional_fields: list = [], override_fields=False):
        self.shot_grid_database = database
        self.shot_grid = database.sg
        self.fields = self._construct_all_fields(additional_fields, override_fields)
        base_filters = self._create_base_filter()
        base_filters.insert(0, [ 'project', 'is', { 'type': 'Project', 'id': self.shot_grid_database.PROJECT_ID } ]) # The project filter is common to all queries
        self.filters = base_filters
        
    def _construct_all_fields(self, additional_fields: list = [], override_fields=False):
        if override_fields:
            return additional_fields
        else:
            return list(set(self._create_base_fields() + additional_fields)) # Remove duplicates
    
    def _get_code_name_filter(self, names: Iterable[str]) -> dict:
        return {
            'filter_operator': 'any',
            'filters': [
                [ 'code', 'is', name ] for name in names # You could also lowercase it, but in my tests it didn't matter
            ],
        }

    @abstractmethod
    def _create_base_filter(self) -> list:
        pass

    @abstractmethod
    def _create_base_fields(self) -> list:
        pass

    @abstractmethod
    def get(self):
        pass
    

class AssetQueryHelper(ShotGridQueryHelper):
    """ An abstract class containing shared methods for querying assets."""
    def __init__(self, database: ShotGridDatabase, additional_fields: list = [], override_fields=False, filter_out_variants=True):
        self.filter_out_variants = filter_out_variants
        super().__init__(database, additional_fields, override_fields)

    # Override
    def _create_base_fields(self) -> list:
        return [
            'code',
            'sg_path',
            'id',
            'parents' # Parents are now included by default so that we can filter for everything that doesn't have parents.
        ]
    # Override
    def _create_base_filter(self) -> list:
        return [
            [ 'sg_status_list', 'is_not', 'oop' ],
            { 
                'filter_operator': 'all',
                'filters': [ 
                    [ 'sg_asset_type', 'is_not', t ] for t in self._untracked_asset_types
                ], 
            },
        ]

    def _get_path_name_filter(self, names: Iterable[str]) -> dict:
        return {
            'filter_operator': 'any',
            'filters': [
                [ 'sg_path', 'ends_with', name.lower() ] for name in names
            ],
        }
    
    def _get_all_asset_json(self):
        assets = self.shot_grid.find('Asset', self.filters, self.fields)
        if self.filter_out_variants:
            assets = self._filter_out_child_assets(assets)
        return assets
    
    def _filter_out_child_assets(self, assets):
        return [asset for asset in assets if asset['parents'] == []] # Filter out child assets (variants)
    
    def _construct_filter_by_path_end_name(self, name: str) -> list:
        return self._get_path_name_filter([name])
    
    def _construct_filter_by_path_end_names(self, names: Iterable[str]) -> list:
        return self._get_path_name_filter(names)
    
    
class GetAllAssetsByName(AssetQueryHelper):
    def __init__(self, database: ShotGridDatabase, names: Iterable[str], additional_fields: list = [], override_fields=False, filter_out_variants=True):
        self.names = names
        super().__init__(database, additional_fields, override_fields, filter_out_variants)

    def _get_all_assets_by_path_end_name(self, names: Iterable[str]):
        self.filters.append(self._construct_filter_by_path_end_names(names))
        return self._get_all_asset_json()
    
    def _get_all_assets_by_code_names(self, names: Iterable[str]):
        self.filters.append(self._get_code_name_filter(names))
        return self._get_all_asset_json()
    
    def _remove_assets_that_do_not_match_name_explicitly(self, assets_json, names: Iterable[str]):
        new_assets = []
        for asset in assets_json:
            path = asset['sg_path']
            # base_name = os.path.basename(path) # I'd do this, but IDK if it'll work on Windows
            base_name = path.split('/')[-1]
            if base_name.lower() in names:
                new_assets.append(asset)
        return new_assets
    
    # Override
    def get(self):
        attempt_by_path_end = self._get_all_assets_by_path_end_name(self.names)
        if len(attempt_by_path_end) > 0: # First attempt to find assets by path end
            print('Assets found by path end name.')
            return self._remove_assets_that_do_not_match_name_explicitly(attempt_by_path_end, self.names)

        # If that fails, try to find assets by code name
        print('No assets found by path end name. Attempting to find assets by code name.')
        self.filters = self._create_base_filter()
        return self._get_all_assets_by_code_names(self.names)

class GetOneAssetByName(GetAllAssetsByName):
    def __init__(self, database: ShotGridDatabase, name: Iterable[str], additional_fields: list = [], override_fields=False, filter_out_variants=True):
        self.name = name
        super().__init__(database, [name], additional_fields, override_fields, filter_out_variants)

    def _get_one_asset_by_name(self, name: str):
        assets = super().get()
        if self.filter_out_variants:
            assets = self._filter_out_child_assets(assets)
        assert len(assets) == 1, f"Expected to find one asset with name {name}, but found {len(assets)}"
        return assets[0]
    
    def get(self):
        return self._get_one_asset_by_name(self.name)
    
class GetAllAssets(AssetQueryHelper):
    def __init__(self, database: ShotGridDatabase, additional_fields: list = [], override_fields=False, filter_out_variants=True):
        super().__init__(database, additional_fields, override_fields, filter_out_variants)

    # Override
    def get(self):
        assets = self._get_all_asset_json()
        if self.filter_out_variants:
            assets = self._filter_out_child_assets(assets)
        return assets
    

# If we had all the time in the world, you could go ahead and continue writing classes like this one...
class ShotQueryHelper(ShotGridQueryHelper):
    def __init__(self, database: ShotGridDatabase, additional_fields: list = [], override_fields=False):
        super().__init__(database, additional_fields, override_fields)

    # Override
    def _create_base_filter(self) -> list:
        return [
            [ 'sg_status_list', 'is_not', 'oop' ],
        ]

    # Override
    def _create_base_fields(self) -> list:
        return [
            'code',
            'id',
            'sg_cut_in',
            'sg_cut_out'
        ]
    
    def _get_all_shot_json(self):
        return self.shot_grid.find('Shot', self.filters, self.fields)
    
    def _get_all_shots_by_code_names(self, names: Iterable[str]):
        self.filters.append(self._get_code_name_filter(names))
        return self._get_all_shot_json()

class GetOneShotByName(ShotQueryHelper):
    def __init__(self, database: ShotGridDatabase, shot_name, additional_fields: list = [], override_fields=False):
        self.shot_name = shot_name
        super().__init__(database, additional_fields, override_fields)

    def _get_one_shot_by_name(self):
        shots = self._get_all_shots_by_code_names([self.shot_name])
        assert len(shots) == 1 # Make sure we only get one shot
        return shots[0]
    
    def get(self):
        return self._get_one_shot_by_name()

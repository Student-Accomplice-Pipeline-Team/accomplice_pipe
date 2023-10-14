from pxr import Usd
import os

class UsdUtils:
    @staticmethod
    def create_empty_usd_at_filepath(filepath, root_prim_name=None, overwrite=False):
        if not overwrite:
            assert not os.path.exists(filepath), f"File already exists at {filepath}"

        stage = Usd.Stage.CreateNew(filepath)
        
        if root_prim_name:
            root_prim = stage.DefinePrim("/" + root_prim_name)
        
        stage.GetRootLayer().Save()

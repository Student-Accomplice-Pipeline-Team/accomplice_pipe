from pxr import Usd

class UsdUtils:
    def create_empty_usd_at_filepath(filepath):
        stage = Usd.Stage.CreateNew(filepath)
        stage.GetRootLayer().Save()
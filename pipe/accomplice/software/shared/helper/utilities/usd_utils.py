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

    @staticmethod
    def create_usd_with_department_prim(filepath, department_prim_name, root_prim_name='scene', overwrite=False):
        if not overwrite:
            assert not os.path.exists(filepath), f"File already exists at {filepath}"

        stage = Usd.Stage.CreateNew(filepath)

        root_prim = stage.DefinePrim("/" + root_prim_name)

        if department_prim_name:
            child_prim = stage.DefinePrim("/" + root_prim_name + "/" + department_prim_name)

        stage.GetRootLayer().Save()


    @staticmethod
    def is_primitive_in_usd(usd_file_path, primitive_path):
        """
        Checks if a primitive with a given path exists in the specified USD file.

        Parameters:
        usd_file_path (str): The path to the USD file.
        primitive_path (str): The path of the primitive to check for.

        Returns:
        bool: True if the primitive exists, False otherwise.
        """
        # Open the USD file
        stage = Usd.Stage.Open(usd_file_path)

        # Check if the primitive exists
        prim = stage.GetPrimAtPath(primitive_path)

        # Return True if the prim is valid and active, False otherwise
        return prim.IsValid() and prim.IsActive()
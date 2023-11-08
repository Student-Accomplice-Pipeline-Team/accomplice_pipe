import hou
from pipe.shared.helper.utilities.houdini_utils import (
    HoudiniUtils,
    HoudiniFXUtils,
    HoudiniNodeUtils,
)
from time import time


class InvertTransformSystem:
    @staticmethod
    def on_created(myself):
        InvertTransformSystem.set_fbx_file_location(myself)
        imported_fbx_null = InvertTransformSystem.import_fbx(myself)
        myself.parm("imported_null").set(imported_fbx_null.path())
        InvertTransformSystem.update_transforms(myself)

    @staticmethod
    def get_imported_fbx_null_path(myself):
        return myself.parm("imported_null").eval()

    @staticmethod
    def set_fbx_file_location(myself):
        shot = HoudiniUtils.get_shot_for_file()
        location_of_fbx = HoudiniFXUtils.get_car_fbx_transform_path(shot)
        myself.parm("fbx_file_location").set(location_of_fbx)

    @staticmethod
    def import_fbx(myself) -> hou.Node:
        location_of_fbx = myself.parm("fbx_file_location").eval()
        imported_fbx_null = hou.hipFile.importFBX(location_of_fbx)[0].children()[0]
        myself.parm("fbx_import_timestamp").set(time())
        return imported_fbx_null

    @staticmethod
    def update_transforms(myself):
        assert (
            InvertTransformSystem.get_imported_fbx_null_path(myself) != ""
        ), "No imported null path"
        imported_fbx_null = hou.node(
            InvertTransformSystem.get_imported_fbx_null_path(myself)
        )

        HoudiniNodeUtils.link_parms(
            imported_fbx_null,
            myself.node(
                "dive_target/invert_transform"
            ),  # NOTE: the scale isn't imported... If the scale comes in wrong, we need to use the convert_units flag in the importFBX function
            ["tx", "ty", "tz", "rx", "ry", "rz"],
        )

    @staticmethod
    def reimport_fbx_from_file(myself):
        # Ask the user if they want to delete the old null
        delete_old_null = hou.ui.displayMessage(
            'Do you want to delete the old null? (In most cases, select yes. Only select "no" if for some reason you want other nodes to still be referencing the old animation.)',
            buttons=("Yes", "No"),
        )

        if delete_old_null == 0:  # If the user chooses to delete the old null
            print("Deleting old null")
            imported_fbx_null_path = InvertTransformSystem.get_imported_fbx_null_path(
                myself
            )
            if imported_fbx_null_path != "":
                imported_fbx_null = hou.node(imported_fbx_null_path)
                if imported_fbx_null is not None:
                    parent = imported_fbx_null.parent()
                    # imported_fbx_null.destroy()
                    parent.destroy()

        imported_fbx_null = InvertTransformSystem.import_fbx(myself)
        myself.parm("imported_null").set(imported_fbx_null.path())
        InvertTransformSystem.update_transforms(myself)

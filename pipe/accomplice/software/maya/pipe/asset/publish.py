from maya import cmds
from pipe.asset.modelChecker import modelChecker_UI


def publish():
    cmds.confirmDialog(
        title="Not Implemented",
        message=f"This button has not yet been implemented. Script location: {__file__}",
        button=["OK"],
        defaultButton="OK"
    )

    # modelChecker_UI.UI.show_UI()

    # Get list of all assets and display them to a window

    # Get the name of the asset selected by the user
    # asset_name = "test"

    # Get the path of the asset
    # asset_path = pipe.server.get_asset(asset_name)

    # Save the asset to the path
    # doMaterial = 0
    # doNormals = 1
    # options = f"groups=0; ptgroups=0; materials={doMaterial}; smoothing=1; normals={doNormals}"
    # cmds.file(asset_path + asset_name + ".obj", force=True, op=options, typ="OBJexport", pr=True, es=True)
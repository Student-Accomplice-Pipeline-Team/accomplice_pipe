import os
import pipe
from maya import cmds
import mayaUsd
from pxr import Usd, Tf

# NOTE: There's currently an issue where if you delete an anonymous stage, Maya sometimes crashes. 
# Here's the issue (currently unresolved) related to it: https://github.com/Autodesk/maya-usd/issues/2985

## HELPER FUNCTIONS ##

def get_filename_from_path(path, include_extension=True):
    filename = os.path.basename(path)
    if not include_extension:
        filename = filename.split('.')[0]
    return filename

def show_results_window(success, path):
    window_tag = "export_layout_results"
    if cmds.window(window_tag, exists=True):
        cmds.deleteUI(window_tag, window=True)
    window = cmds.window(window_tag, title="Export Layout Results")

    # Write out a message about the results of the export
    results_contents = ""
    if success:
        results_contents += "New stage successfully exported! \nExported to "
    else:
        results_contents += "Export unsuccessful. \nAttempted to export to "
    results_contents += path + "."

    window_layout = cmds.columnLayout(adjustableColumn=True)
    text = cmds.text(results_contents)
    cmds.showWindow(window)

def _get_sublayer_info():
    # Get all proxy shapes
    # NOTE: If we didn't need access to the shapes, we could just do mayaUsd.ufe.getAllStages()
    maya_usd_shapes = cmds.ls(type="mayaUsdProxyShape")

    sublayers_info = {}

    for shape in maya_usd_shapes:
        usd_proxy_node = cmds.ls(shape, long=True)[0]
        # Get the stage and the stage's root layer (the models are USD representations)
        stage = mayaUsd.ufe.getStage(usd_proxy_node)
        root_layer = stage.GetRootLayer()
        # Get the sublayers
        sublayer_paths = root_layer.subLayerPaths
        for sublayer_path in sublayer_paths:
            sublayer_filename = get_filename_from_path(sublayer_path, include_extension=False)
            sublayers_info[sublayer_filename] = {
                'path': sublayer_path,
                'root_layer': root_layer,
                'maya_shape': shape
            }

    return sublayers_info

def export_layout():
    # Handle window
    window_tag = "export_layout"
    if cmds.window(window_tag, exists=True):
        cmds.deleteUI(window_tag, window=True)
    window = cmds.window(window_tag, title="Export Layout")

    # Get sublayer information
    sublayers_info = _get_sublayer_info()
    # NOTE: Validation of the layout names? could be from anywhere
    # For right now, only look at sublayers that are layouts
    sublayer_names = list(sublayers_info.keys())
    layout_sublayers = filter(lambda x: ("layout" in x), sublayer_names)

    # Show sublayer names in window
    window_layout = cmds.columnLayout(adjustableColumn=True)
    window_text = cmds.text("Select layout to export as RLO.")
    window_layout_list = cmds.textScrollList(allowMultiSelection=False, numberOfRows=30, append=layout_sublayers)

    def _export(*args):
        selection = cmds.textScrollList(window_layout_list, q=1, si=1)

        if selection and selection[0]:
            # Get the selected layout
            layout_name = selection[0]

            # Get the sublayer, stage information based on the selected layout
            sublayer_info = sublayers_info[layout_name]
            root_layer = sublayer_info['root_layer']
            sublayer_path = sublayer_info['path']
            maya_node = sublayer_info['maya_shape']

            # Put the new layout in the same directory as the old one
            sublayer_dir = os.path.dirname(sublayer_path)
            save_filename = f"{layout_name}_rlo"
            save_filepath = f"{sublayer_dir}/{save_filename}.usda"
            
            # Export the new layout
            success = root_layer.Export(filename=save_filepath)
            show_results_window(success, path=save_filepath)

            # TODO: If the layout was successfully exported, then import that layout back into Maya
            # Doing this currently crashes maya
            # cmds.delete(maya_node)
            # Load in the saved new stage
            # shape_node = cmds.createNode('mayaUsdProxyShape', skipSelect=True, name=save_filename)
            # cmds.connectAttr('time1.outTime', shape_node + '.time')
            # stage_proxy = cmds.ls(shape_node, long=True)[0]
            # cmds.setAttr(stage_proxy + '.filePath', save_filepath, type='string')
            # cmds.select(stage_proxy, replace=True)

        else:
            cmds.error("Selection failed.")
        
        cmds.deleteUI(window_tag, window=True)

    export_button = cmds.button(label="Export RLO", command=_export)

    cmds.showWindow(window)


################################################

# def _get_all_stages():
#     if hasattr(mayaUsd.ufe, 'getAllStages'):
#         # Get all active stages in Maya
#         stages = mayaUsd.ufe.getAllStages()
#     else:
#         shapes = cmds.ls(type="mayaUsdProxyShape")
#         usd_proxy_nodes = [cmds.ls(shape_node, long=True)[0] for shape_node in shapes]
#         stages = [mayaUsd.ufe.getStage(proxy) for proxy in usd_proxy_nodes]
#     return stages
    

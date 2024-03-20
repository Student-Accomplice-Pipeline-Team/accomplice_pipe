import os
import pipe
from maya import cmds, mel
import mayaUsd

# TODO: Fix crash when delete created stage node

def import_layout():
    window_tag = "import_layout"
    if cmds.window(window_tag, exists=True):
        cmds.deleteUI(window_tag, window=True)
    window = cmds.window(window_tag, title="Import Layout")
    
    shot_names = pipe.server.get_shot_list()
    layout_names = []
    for shot_name in shot_names:
        shot = pipe.server.get_shot(shot_name)
        if os.path.isfile(shot.get_layout_path(anim=True)) or os.path.isfile(shot.get_layout_path()):
            layout_names.append(shot_name)
    
    layout = cmds.columnLayout(adjustableColumn=True)
    layout_list = cmds.textScrollList(allowMultiSelection=False, numberOfRows=30, append=sorted(layout_names))
    
    def _import(*args):
        selection = cmds.textScrollList(layout_list, q=1, si=1)
        
        if selection and selection[0]:
            shot_name = selection[0]
            shot = pipe.server.get_shot(shot_name)

            # Get the path to the selected shot's layout. With `anim=True`, the pipe will attempt return the path
            # to a layout file without instancing. (USD files with instancing crash Maya 2024.)
            layout_path = shot.get_layout_path(anim=True) or shot.get_layout_path()
            layout_filename = os.path.basename(layout_path).split('.')[0]
            new_layer_name = layout_filename + "_rlo"

            # Create a new stage to sublayer the layout into
            shape_node = cmds.createNode('mayaUsdProxyShape', skipSelect=True, name=new_layer_name + "Shape")
            usd_proxy_node = cmds.ls(shape_node, long=True)[0]
            cmds.connectAttr('time1.outTime', shape_node + '.time')

            # Get the root layer
            usd_stage = mayaUsd.ufe.getStage(usd_proxy_node)
            root_layer = usd_stage.GetRootLayer()

            # Sublayer the layout into the new stage
            mel.eval(f'mayaUsdLayerEditor -edit -insertSubPath 0 "{layout_path}" "{root_layer.identifier}";')

            # Open the layer editor window
            cmds.select(shape_node, replace=True)
            cmds.mayaUsdLayerEditorWindow(reload=True)

            # Scale up layout
            cmds.scale(100, 100, 100)

        cmds.deleteUI(window_tag, window=True)
    
    import_button = cmds.button(label="Import Layout", command=_import)

    cmds.showWindow(window)

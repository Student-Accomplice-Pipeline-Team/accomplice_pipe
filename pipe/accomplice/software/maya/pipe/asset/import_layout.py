import os
import pipe
from maya import cmds
import mayaUsd


def import_layout():
    cmds.polyCube()
    window_tag = "import_layout"
    if cmds.window(window_tag, exists=True):
        cmds.deleteUI(window_tag, window=True)
    window = cmds.window(window_tag, title="Import Layout")
    
    shot_names = pipe.server.get_shot_list()
    layout_names = []
    for shot_name in shot_names:
        shot = pipe.server.get_shot(shot_name)
        layout_path = shot.get_layout_path()
        if os.path.isfile(layout_path):
            layout_names.append(shot_name)

    layout = cmds.columnLayout(adjustableColumn=True)
    layout_list = cmds.textScrollList(allowMultiSelection=False, numberOfRows=30, append=layout_names)
    
    def _import(*args):
        selection = cmds.textScrollList(layout_list, q=1, si=1)

        if selection and selection[0]:
            shot_name = selection[0]
            shot = pipe.server.get_shot(shot_name)
            layout_path = shot.get_layout_path()

            cmds.polyCube()
            shapeNode = cmds.createNode('mayaUsdProxyShape', skipSelect=True, name=shot_name+"Shape")
            cmds.connectAttr('time1.outTime', shapeNode+'.time')
            cmds.setAttr(shapeNode + '.filePath', layout_path, type='string')
            cmds.select(shapeNode, replace=True)

            # cmds.file(layout_path, r=True)
        
        cmds.deleteUI(window_tag, window=True)
    
    import_button = cmds.button(label="Import Reference", command=_import)

    cmds.showWindow(window)

    # cmds.window()
    # cmds.paneLayout()
    # scroll_list = cmds.textScrollList( numberOfPopupMenus=1, append=shot_names)
    # cmds.showWindow()

    # cmds.confirmDialog(
    #     title="Not Implemented",
    #     message=f"This button has not yet been implemented. Script location: {__file__}",
    #     button=["OK"],
    #     defaultButton="OK"
    # )

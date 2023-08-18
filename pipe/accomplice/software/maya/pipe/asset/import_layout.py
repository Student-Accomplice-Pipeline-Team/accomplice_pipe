import pipe
from maya import cmds


def import_layout():
    shot_names = pipe.server.get_shot_list()

    window_tag = "import_layout"
    if cmds.window(window_tag, exists=True):
        cmds.deleteUI(window_tag, window=True)
    
    window = cmds.window(window_tag, title="Import Layout")
    layout = cmds.columnLayout(adjustableColumn=False)
    layout_list = cmds.textScrollList(allowMultiSelection=False, numberOfRows=20, append=shot_names)
    import_button = cmds.button(label="Import", command=_import)

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


def _import(*args):
    window_tag = "import_layout"
    cmds.deleteUI(window_tag, window=True)
    print("Hi!")
    # shot_name = cmds.textScrollList()

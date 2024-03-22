import maya.cmds as cmds
import maya.mel as mel

import pipe
from pipe.animation.operation_runner import OperationRunner
from pipe.shared.helper.utilities.file_path_utils import FilePathUtils
from pipe.animation.logger import SimpleLogger

def enable_hud():
    # Get a list of all existing HUDs
    hud_list = cmds.headsUpDisplay(query=True, listHeadsUpDisplays=True)

    # Set visibility of each HUD to False
    for hud in hud_list:
        cmds.headsUpDisplay(hud, edit=True, visible=False)

    # Turn on overall HUD
    model_panels = cmds.getPanel(type="modelPanel")
    for panel in model_panels:
        cmds.modelEditor(panel, e=True, hud=True)

    # Turn on visibility for current frame HUD
    mel.eval("setCurrentFrameVisibility(1);")

    cams = cmds.ls(ca=True)
    for cam in cams:
        parentCam = cmds.listRelatives(cam, parent=True)[0]
        cmds.camera(parentCam, edit=True, displayResolution=False)
        cmds.camera(parentCam, edit=True, displayGateMask=False)
        cmds.camera(parentCam, edit=True, displayFilmGate=False)

def set_camera_for_shot(shot_name):
    logger = SimpleLogger("PlayblastExporter")
    cam_name = f"{shot_name}_CAM"

    if cmds.objExists(cam_name):
        # Set the camera view
        cmds.lookThru(cam_name)
    else:
        logger.error(f"Camera with name '{cam_name}' does not exist in the scene.")
        return False

    return True

def playblast():
    logger = SimpleLogger("PlayblastExporter")
    fileName = ""
    videoFormat = "qt"
    videoScalePct = 100
    videoCompression = "Animation"
    videoOutputType = "qt"
    width = 1920
    height = 1080
    start_frame = 995

    shot = pipe.server.get_shot(FilePathUtils.get_shot_name_from_file_path(cmds.file(query=True, sceneName=True)))
    shot_name = shot.get_name()

    if not set_camera_for_shot(shot_name):
        return

    cmds.playbackOptions(minTime=start_frame)

    fileName = shot.get_playblast_path('anim').replace(".mov", "_with_frame_number.mov")
    print("EXPORT PATH:", fileName)

    enable_hud()

    try:
        cmds.playblast(f=fileName, forceOverwrite=True, viewer=False, percent=videoScalePct,
                       format=videoFormat, compression=videoCompression, widthHeight=[width, height])
    except Exception as e:
        logger.error(f"Error exporting playblast: {str(e)}")

playblaster_with_frame = OperationRunner(playblast)
playblaster_with_frame.run()
"""Initialize the Maya pipeline environment on startup."""
import pipe

# Install maya_timeline_marker plugin
from maya import cmds


def main():
    from timeline_marker import install
    install.execute()



if not cmds.about(batch=True):
    cmds.evalDeferred(main)

def postSceneCallback():
    # Set the default clipping plane of the perspective camera
    try:
        cmds.setAttr('perspShape.nearClipPlane', 10)
        cmds.setAttr('perspShape.farClipPlane', 3000000)
    except:
        print("Failed to set default clipping plane for perspective camera.")
    try:
        cmds.setAttr('hardwareRenderingGlobals.defaultLightIntensity', 1)
    except:
        print("Failed to set default light intensity.")

cmds.scriptJob(event=["PostSceneRead", postSceneCallback], protected=True)
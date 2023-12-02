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
    # Set the default clipping plane of the perspective camera to be a min of 0.1 and a max of 1000000
    cmds.setAttr('perspShape.nearClipPlane', 10)
    cmds.setAttr('perspShape.farClipPlane', 3000000)
    cmds.setAttr('hardwareRenderingGlobals.defaultLightIntensity', 1)

cmds.scriptJob(event=["PostSceneRead", postSceneCallback], protected=True)
"""Initialize the Maya pipeline environment on startup."""
import pipe

# Install maya_timeline_marker plugin
from maya import cmds


def main():
    from timeline_marker import install

    install.execute()


if not cmds.about(batch=True):
    cmds.evalDeferred(main)

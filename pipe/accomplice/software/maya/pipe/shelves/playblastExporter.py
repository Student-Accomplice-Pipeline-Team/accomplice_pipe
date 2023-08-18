import os
from PySide2 import QtWidgets, QtCore, QtGui

import pipe.pipeHandlers.environment as env
import pipe.pipeHandlers.permissions as permissions
import pipe.tools.python.stringUtilities as stringUtilities

import maya.cmds as mc


class PlayblastExporter(QtWidgets.QMainWindow):
    def __init__(self):
        super(PlayblastExporter, self).__init__()

        self.fileName = ""
        self.videoFormat = "qt"
        self.videoScalePct = 100
        self.videoCompression = "Animation"
        self.videoOutputType = "qt"
        self.width = 1920
        self.height = 1080

        self.env = env.Environment()
        self.baseDir = os.path.abspath(os.path.join(self.env.project_dir, os.pardir, "Editing", "Animation"))
        print(self.baseDir)

        self.sequences = self.getSequences()
        self.shots = []

        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("Playblast Exporter")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setFixedSize(325, 200)

        self.mainWidget = QtWidgets.QWidget()
        self.mainLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        self.setCentralWidget(self.mainWidget)

        # LISTS
        self.listLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(self.listLayout)

        self.sequenceLayout = QtWidgets.QVBoxLayout()
        self.listLayout.addLayout(self.sequenceLayout)

        self.sequenceLabel = QtWidgets.QLabel("Sequences")
        self.sequenceLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.sequenceLayout.addWidget(self.sequenceLabel)

        self.sequenceListWidget = QtWidgets.QListWidget()
        self.sequenceListWidget.setFixedWidth(150)
        self.sequenceListWidget.addItems(self.sequences)
        self.sequenceLayout.addWidget(self.sequenceListWidget)

        self.shotLayout = QtWidgets.QVBoxLayout()
        self.listLayout.addLayout(self.shotLayout)

        self.shotLabel = QtWidgets.QLabel("Shots")
        self.shotLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.shotLayout.addWidget(self.shotLabel)

        self.shotListWidget = QtWidgets.QListWidget()
        self.shotListWidget.setFixedWidth(150)
        self.shotListWidget.addItems(self.shots)
        self.shotLayout.addWidget(self.shotListWidget)

        self.sequenceListWidget.itemClicked.connect(self.updateUI)

        # BUTTONS
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(self.buttonLayout)

        self.exportButton = QtWidgets.QPushButton("Playblast")
        self.exportButton.clicked.connect(self.playblast)
        self.buttonLayout.addWidget(self.exportButton)

        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.buttonLayout.addWidget(self.cancelButton)

        self.cancelButton.clicked.connect(self.close)

    def updateUI(self):
        self.shotListWidget.clear()
        self.shotListWidget.addItems(self.getShots())

    def getSequences(self):
        """Returns an alphabetically sorted list of sequences in the project.
        @return: list of sequences"""

        sequences = [d for d in os.listdir(self.baseDir) if d.startswith(("SEQ"))]
        sequences.sort()
        return sequences

    def getShots(self):
        """Returns a list of shots in the current sequence. Returns an empty list if no sequence is selected.
        @return: list of shots"""

        if self.sequenceListWidget.currentItem() is None:
            return []

        currentSequence = self.sequenceListWidget.currentItem().text()[-1]
        # shots = os.listdir(os.path.join(self.baseDir, currentSequence))
        shots = os.listdir(self.env.get_shot_dir())
        shots = [shot for shot in shots if shot.startswith(currentSequence)]
        shots.sort()
        return shots

    def playblast(self):
        """Exports a playblast of the current scene to the current sequence and shot."""
        if self.sequenceListWidget.currentItem() is None:
            return

        if self.shotListWidget.currentItem() is None:
            return

        currentSequence = self.sequenceListWidget.currentItem().text()
        currentShot = f"{self.shotListWidget.currentItem().text()}_main"

        fileName = os.path.join(self.baseDir, currentSequence, currentShot)

        try:
            mc.playblast(f=fileName, forceOverwrite=True, viewer=False, percent=self.videoScalePct,
                         format=self.videoFormat, compression=self.videoCompression, widthHeight = [self.width, self.height])

            # Set permissions
            permissions.set_permissions(f"{fileName}.mov")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error",
                                           "Error exporting playblast. See the script editor for details.")
            print(e)
            return

        messageBox = QtWidgets.QMessageBox(self)
        messageBox.setText("Playblast exported successfully!")
        openOutputFolderButton = messageBox.addButton("Open Output Folder", QtWidgets.QMessageBox.AcceptRole)
        openOutputFolderButton.clicked.connect(lambda: os.system('xdg-open "%s"' % os.path.dirname(fileName)))
        openOutputFolderButton.clicked.connect(self.close)
        closeButton = messageBox.addButton("Close", QtWidgets.QMessageBox.RejectRole)
        closeButton.clicked.connect(self.close)
        messageBox.exec_()


class mayaRun():
    def run(self):
        self.playblastExporter = PlayblastExporter()
        self.playblastExporter.show()

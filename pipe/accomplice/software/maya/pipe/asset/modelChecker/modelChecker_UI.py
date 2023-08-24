"""
    modelChecker v.0.1.1
    Reliable production ready sanity checker for Autodesk Maya
    Contact: jakobjk@gmail.com
    https://github.com/JakobJK/modelChecker
"""

from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance
from functools import partial


import importlib
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import pipe.asset.modelChecker.modelChecker_commands as mcc
importlib.reload(mcc)
import pipe.asset.modelChecker.modelChecker_list as mcl
importlib.reload(mcl)
import os,re,sys

import pipe


def getMainWindow():
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        mainWindow = wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        mainWindow = wrapInstance(long(main_window_ptr), QtWidgets.QWidget)
    return mainWindow


class UI(QtWidgets.QMainWindow):

    qmwInstance = None
    version = '0.1.1'
    SLMesh = om.MSelectionList()
    commandsList = mcl.mcCommandsList
    reportOutputUI = QtWidgets.QTextEdit()
    categoryLayout = {}
    categoryWidget = {}
    categoryButton = {}
    categoryHeader = {}
    categoryCollapse = {}
    command = {}
    commandWidget = {}
    commandLayout = {}
    commandLabel = {}
    commandCheckBox = {}
    errorNodesButton = {}
    commandRunButton = {}
    checkRunButton = {}
    checkExportRunButton = {}
    topNode = ""
    extraAttribs = {}
    assetType = ""

    @classmethod
    def show_UI(cls):
        if not cls.qmwInstance:
            cls.qmwInstance = UI()
        if cls.qmwInstance.isHidden():
            cls.qmwInstance.show()
        else:
            cls.qmwInstance.raise_()
            cls.qmwInstance.activateWindow()

    def __init__(self, parent=getMainWindow()):
        super(UI, self).__init__(
            parent)

        self.setObjectName("ModelCheckerUI")
        self.setWindowTitle('Model Checker (BYU Adaptation) ' + self.version)

        mainLayout = QtWidgets.QWidget(self)
        self.setCentralWidget(mainLayout)

        columns = QtWidgets.QHBoxLayout(mainLayout)
        report = QtWidgets.QVBoxLayout()
        checks = QtWidgets.QVBoxLayout()

        columns.addLayout(checks)
        columns.addLayout(report)

        selectedModelVLayout = QtWidgets.QHBoxLayout()
        checks.addLayout(selectedModelVLayout)

        reportBoxLayout = QtWidgets.QHBoxLayout()
        reportLabel = QtWidgets.QLabel("Report:")

        reportBoxLayout.addWidget(reportLabel)
        report.addLayout(reportBoxLayout)

        self.reportOutputUI.setMinimumWidth(600)
        report.addWidget(self.reportOutputUI)

        checkButtonsHLayout = QtWidgets.QHBoxLayout()

        self.checkRunButton = QtWidgets.QPushButton("Check Selected")
        self.checkRunButton.clicked.connect(self.sanityCheck)
        checkButtonsHLayout.addWidget(self.checkRunButton)

        self.checkExportRunButton = QtWidgets.QPushButton("Check Export Group(s)")
        self.checkExportRunButton.clicked.connect(self.sanityCheckExport)
        checkButtonsHLayout.addWidget(self.checkExportRunButton)

        report.addLayout(checkButtonsHLayout)

        clearButton = QtWidgets.QPushButton("Clear")
        clearButton.setMaximumWidth(150)
        clearButton.clicked.connect(partial(self.reportOutputUI.clear))
        reportBoxLayout.addWidget(clearButton)
        self.resize(1000, 900)
        category = self.getCategories(self.commandsList)

        for obj in category:
            self.categoryWidget[obj] = QtWidgets.QWidget()
            self.categoryLayout[obj] = QtWidgets.QVBoxLayout()
            self.categoryHeader[obj] = QtWidgets.QHBoxLayout()
            self.categoryButton[obj] = QtWidgets.QPushButton(obj)
            if sys.version_info.major >= 3:
                text = '\u2193'
            else:
                text = u'\u2193'.encode('utf-8')
            self.categoryCollapse[obj] = QtWidgets.QPushButton(text)
            self.categoryCollapse[obj].clicked.connect(
                partial(self.toggleUI, obj))
            self.categoryCollapse[obj].setMaximumWidth(30)
            self.categoryButton[obj].setStyleSheet(
                "background-color: grey; text-transform: uppercase; color: #000000; font-size: 18px;")
            self.categoryButton[obj].clicked.connect(
                partial(self.checkCategory, obj))
            self.categoryHeader[obj].addWidget(self.categoryButton[obj])
            self.categoryHeader[obj].addWidget(self.categoryCollapse[obj])
            self.categoryWidget[obj].setLayout(self.categoryLayout[obj])
            checks.addLayout(self.categoryHeader[obj])
            checks.addWidget(self.categoryWidget[obj])

        # Creates the buttons with their settings
        for obj in self.commandsList:
            name = obj['func']
            label = obj['label']
            category = obj['category']
            check = obj['defaultChecked']

            self.commandWidget[name] = QtWidgets.QWidget()
            self.commandWidget[name].setMaximumHeight(40)
            self.commandLayout[name] = QtWidgets.QHBoxLayout()

            self.categoryLayout[category].addWidget(self.commandWidget[name])
            self.commandWidget[name].setLayout(self.commandLayout[name])

            self.commandLayout[name].setSpacing(4)
            self.commandLayout[name].setContentsMargins(0, 0, 0, 0)
            self.commandWidget[name].setStyleSheet(
                "padding: 0px; margin: 0px;")
            self.command[name] = name
            self.commandLabel[name] = QtWidgets.QLabel(label)
            self.commandLabel[name].setMinimumWidth(120)
            self.commandLabel[name].setStyleSheet("padding: 2px;")
            self.commandCheckBox[name] = QtWidgets.QCheckBox()

            self.commandCheckBox[name].setChecked(check)
            self.commandCheckBox[name].setMaximumWidth(20)

            self.commandRunButton[name] = QtWidgets.QPushButton("Run")
            self.commandRunButton[name].setMaximumWidth(30)

            self.commandRunButton[name].clicked.connect(
                partial(self.commandToRun, [obj]))

            self.errorNodesButton[name] = QtWidgets.QPushButton(
                "Select Problems")
            self.errorNodesButton[name].setEnabled(False)
            self.errorNodesButton[name].setMaximumWidth(200)

            self.commandLayout[name].addWidget(self.commandLabel[name])
            self.commandLayout[name].addWidget(self.commandCheckBox[name])
            self.commandLayout[name].addWidget(self.commandRunButton[name])
            self.commandLayout[name].addWidget(self.errorNodesButton[name])

        checks.addStretch()

        heroButton = QtWidgets.QRadioButton("Hero")
        heroButton.toggled.connect(lambda:self.setAssetType("hero"))
        checks.addWidget(heroButton)

        layoutButton = QtWidgets.QRadioButton("Layout")
        layoutButton.toggled.connect(lambda:self.setAssetType("layout"))
        checks.addWidget(layoutButton)
        
        setDressingButton = QtWidgets.QRadioButton("Set Dressing")
        setDressingButton.toggled.connect(lambda:self.setAssetType("setdressing"))
        setDressingButton.setChecked(True)
        checks.addWidget(setDressingButton)
        
        riggedButton = QtWidgets.QRadioButton("Rigged")
        riggedButton.toggled.connect(lambda:self.setAssetType("rigged"))
        checks.addWidget(riggedButton)

        self.setAssetType("setdressing")

        exportButtonLayout = QtWidgets.QHBoxLayout()
        checks.addLayout(exportButtonLayout)


        exportButton = QtWidgets.QPushButton("EXPORT")
        exportButton.clicked.connect(self.export)
        exportButton.setStyleSheet(
                "background-color: DarkRed; color: #ffffff;")

        exportButtonLayout.addWidget(exportButton)

    def setAssetType(self, assetType):
        self.assetType = assetType

    def getCategories(self, incomingList):
        allCategories = []
        for obj in incomingList:
            allCategories.append(obj['category'])
        return set(allCategories)

    def checkState(self, name):
        return self.commandCheckBox[name].checkState()

    def checkAll(self):
        for obj in self.commandsList:
            name = obj['func']
            self.commandCheckBox[obj['func']].setChecked(True)

    def getArrow(self):
        pass

    def toggleUI(self, obj):
        state = self.categoryWidget[obj].isVisible()
        if state:
            if sys.version_info.major >= 3:
                text = u'\u21B5'
            else:
                text = u'\u21B5'.encode('utf-8')
            self.categoryCollapse[obj].setText(text)
            self.categoryWidget[obj].setVisible(not state)
            self.adjustSize()
        else:
            if sys.version_info.major >= 3:
                text = u'\u2193'
            else:
                text = u'\u2193'.encode('utf-8')
            self.categoryCollapse[obj].setText(text)
            self.categoryWidget[obj].setVisible(not state)

    def export(self):
        #OSTRICH_ROOT = os.environ.get('OSTRICH_ROOT', 'invalidfilepath')
        
        theErrors = self.sanityCheckExport()
        if theErrors != []:
            cmds.warning("Resolve Model Problems Before Publishing")
            return
        
        for exportGrp in self.getExportGrps():
            assetName = self.getAssetName(exportGrp)

            asset = pipe.server.get_asset(assetName)
            
            asset.get_modelling_path()
            
            finalFilePath = '/'.join([finalAssetFolder, self.assetType, assetName])
            if not os.path.exists(finalFilePath):
                os.makedirs(finalFilePath)

            finalFileName = '/'.join([finalFilePath, f"{assetName}_GEO.fbx"])

            # set FBX settings
            mel.eval('FBXResetExport')
            fbxSettings = [
                "AdvOptGrp|UI|ShowWarningsManager",
                "IncludeGrp|Animation",
                "IncludeGrp|CameraGrp|Camera",
                "IncludeGrp|Geometry|SmoothMesh",
                "IncludeGrp|LightGrp|Light",
            ]
            for prop in fbxSettings:
                mel.eval(f'FBXProperty Export|{prop} -v false')
            
            self.selectExportGrp(exportGrp)

            # export file
            cmds.file(finalFileName, exportSelected=True, type='FBX export', force=True)
            #os.chmod(finalFileName, 0o770)
            cmds.confirmDialog(
                message=f"Path: {finalFileName}", 
                defaultButton="OK",
                title="Export Completed!"
            )

    def invertCheck(self):
        for obj in self.commandsList:
            name = obj['func']
            self.commandCheckBox[name].setChecked(
                not self.commandCheckBox[name].isChecked())

    def checkCategory(self, category):

        uncheckedCategoryButtons = []
        categoryButtons = []

        for obj in self.commandsList:
            name = obj['func']
            cat = obj['category']
            if cat == category:
                categoryButtons.append(name)
                if self.commandCheckBox[name].isChecked():
                    uncheckedCategoryButtons.append(name)

        for obj in categoryButtons:
            if len(uncheckedCategoryButtons) == len(categoryButtons):
                self.commandCheckBox[obj].setChecked(False)
            else:
                self.commandCheckBox[obj].setChecked(True)


    # Filter Nodes
    def filterNodes(self):
        nodes = []
        self.SLMesh.clear()
        allUsableNodes = []
        allNodes = cmds.ls(transforms=True)
        for obj in allNodes:
            if not obj in {'front', 'persp', 'top', 'side'}:
                allUsableNodes.append(obj)

        selection = cmds.ls(sl=True)

        topNode = self.topNode
        if len(selection) > 0:
            print(selection)
            selectionSet = set()
            for obj in selection:
                if relatives := cmds.listRelatives(obj, allDescendents=True, path=True, typ="transform"):
                    selectionSet |= set(relatives)
                selectionSet.add(obj)
            nodes = list(selectionSet)
            print("NODES:", nodes)
        else:
            # for topNode in topNodes:
            if cmds.objExists(topNode):
                topRelatives = cmds.listRelatives(
                    topNode, allDescendents=True, path=True, typ="transform")
                if not topRelatives:
                    topRelatives = [topNode]
                nodes += topRelatives
            else:
                response = "Object in Top Node doesn't exists\n"
                self.reportOutputUI.clear()
                self.reportOutputUI.insertPlainText(response)
        print(nodes)
        for node in nodes:
            shapes = cmds.listRelatives(node, shapes=True, typ="mesh")
            if shapes:
                self.SLMesh.add(node)
        return nodes

    def commandToRun(self, commands):
        nodes = self.filterNodes()
        myErrors = []
        self.reportOutputUI.clear()
        if len(nodes) == 0:
            self.reportOutputUI.insertPlainText("Error - No nodes to check\n")
        else:
            for currentCommand in commands:
                command = currentCommand['func']
                label = currentCommand['label']
                self.errorNodes = getattr(
                    mcc, command)(nodes, self.SLMesh, self.extraAttribs)
                if self.errorNodes:
                    self.reportOutputUI.insertHtml(
                        label + " -- <font color='#996666'>FAILED</font><br>")
                    for obj in self.errorNodes:
                        self.reportOutputUI.insertPlainText(
                            "    " + obj + "\n")
                        myErrors.append(obj)

                    self.errorNodesButton[command].setEnabled(True)
                    self.errorNodesButton[command].clicked.connect(
                        partial(self.selectErrorNodes, self.errorNodes))
                    self.commandLabel[command].setStyleSheet(
                        "background-color: #664444; padding: 2px;")
                else:
                    self.commandLabel[command].setStyleSheet(
                        "background-color: #446644; padding: 2px;")
                    self.reportOutputUI.insertHtml(
                        label + " -- <font color='#669966'>SUCCESS</font><br>")
                    self.errorNodesButton[command].setEnabled(False)
        #print(myErrors)
        return myErrors

    def sanityCheck(self):
        self.reportOutputUI.clear()
        checkedCommands = []
        for obj in self.commandsList:
            name = obj['func']
            if self.commandCheckBox[name].isChecked():
                checkedCommands.append(obj)
            else:
                self.commandLabel[name].setStyleSheet(
                    "background-color: none; padding: 2px;")
                self.errorNodesButton[name].setEnabled(False)
        if len(checkedCommands) == 0:
            print("You have to select something")
        else:
            errorList = self.commandToRun(checkedCommands)
        return errorList

    def getExportGrps(self):
        for obj in self.commandsList:
            name = obj['func']
            self.commandCheckBox[name].setChecked(True)
        
        allUsableNodes = []
        allNodes = cmds.ls(transforms=True)
        for obj in allNodes:
            if not obj in {'front', 'persp', 'top', 'side'}:
                allUsableNodes.append(obj)

        grpPattern = re.compile("^export_(?:[a-zA-Z0-9]+_)?GRP$")
        return [n for n in allUsableNodes if grpPattern.match(n)]

    def selectExportGrp(self, exportGrp):
        cmds.select(clear=True)
        exportGrpChildren = cmds.listRelatives(exportGrp, shapes=False)
        cmds.select(exportGrpChildren, hierarchy=True)
        shapes = cmds.ls(selection=True,type="shape")
        cmds.select(shapes, deselect=True)
        
        exportGrpChildren = cmds.ls(selection=True)
        
        if len(exportGrpChildren) < 2:
            exportGrpChildren = exportGrpChildren[0]
        
        cmds.select(exportGrpChildren)

    def getAssetName(self, exportGrp):
        variantPattern = re.compile("^export(_[a-zA-Z0-9]+)?_GRP$")
        filePath = cmds.file(query=True, sceneName=True)
        
        modelFolder, _ = os.path.split(filePath)
        *_, assetName = modelFolder.split('/')

        if variant := variantPattern.search(exportGrp).group(1):
            assetName += variant
        
        return assetName


    def sanityCheckExport(self):
        exportGrps = self.getExportGrps()

        if not len(exportGrps):
            cmds.warning("No matching export groups found (export_GRP or export_Variant_GRP)")

        for exportGrp in exportGrps:
            print(exportGrp)
            
            self.topNode = exportGrp
            self.extraAttribs['matname'] = self.getAssetName(exportGrp) + '_MAT'
            
            self.selectExportGrp(exportGrp)

            theErrors = self.sanityCheck()
            
            self.topNode = ""
            self.extraAttribs['matname'] = ""
            
            if len(theErrors):
                return theErrors

        return []

    def selectErrorNodes(self, list):
        cmds.select(list)


if __name__ == '__main__':
    try:
        win.close()
    except:
        pass
    win = UI(parent=getMainWindow())
    win.show()
    win.raise_()

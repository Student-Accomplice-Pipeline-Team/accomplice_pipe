import os
import sys
import importlib
import pathlib
import json
import subprocess

#pipe modules
import pipe
from pipe.shared import object

# Substance 3D Painter modules
import substance_painter.ui
import substance_painter.export
import substance_painter.project
import substance_painter.textureset

# PySide module to build custom UI
from PySide2 import QtWidgets, QtCore
from PySide2.QtWidgets import QApplication, QWidget, QRadioButton, QComboBox, QLabel, QSizePolicy, QPushButton

plugin_widgets = []


def start_plugin():

	# Create a text widget for a menu
    Action = QtWidgets.QAction("Accomplice - Publish Asset")
    Action.triggered.connect(launch_exporter)

	# Add this widget to the existing File menu of the application
    substance_painter.ui.add_action(
		substance_painter.ui.ApplicationMenu.File,
		Action )

	# Store the widget for proper cleanup later when stopping the plugin
    plugin_widgets.append(Action)

def close_plugin():
	# Remove all widgets that have been added to the UI
	for widget in plugin_widgets:
		substance_painter.ui.delete_ui_element(widget)

	plugin_widgets.clear()

if __name__ == "__main__":
	window = start_plugin()
	
def launch_exporter():

    if not substance_painter.project.is_open():
        QtWidgets.QMessageBox.warning(None, "No project open", "Please open a project before trying to publish, IDIOT!!!")
        return
    
    # Check for existing windows and close them before opening a new one
    for widget in plugin_widgets:
        if isinstance(widget, SubstanceExporterWindow):
            widget.close()
            substance_painter.ui.delete_ui_element(widget)
            plugin_widgets.remove(widget)
            break

    #Start window
    global window
    window = SubstanceExporterWindow()
    window.show()

    print("Launching Substance Exporter")


class TexSetWidget(QtWidgets.QWidget):
      
    def __init__(self, name, pWidge, parent=None):
        super(TexSetWidget, self).__init__(parent)
        self.name = name
        self.pWidge = pWidge

        self.setup_UI()

    def setup_UI(self):

        self.verticalLayout = QtWidgets.QVBoxLayout()

        ####label####
        self.tex_label = QLabel(self.name)
        self.verticalLayout.addWidget(self.tex_label)

        '''''''''setup radio buttons'''''''''
        self.buttons = []
        ButtonLayout = QtWidgets.QHBoxLayout()

        #Basic setup
        self.isBasic = QRadioButton("Basic")
        self.buttons.append(self.isBasic)
        self.isBasic.setChecked(False)
        self.isBasic.toggled.connect(self.pWidge.radio_checked)
        
        ButtonLayout.addWidget(self.isBasic)

        #isMetal setup
        self.isMetal = QRadioButton("Metal")
        self.buttons.append(self.isMetal)
        self.isMetal.setChecked(False)
        self.isMetal.toggled.connect(self.pWidge.radio_checked)

        ButtonLayout.addWidget(self.isMetal)

        #isGlass setup
        self.isGlass = QRadioButton("Glass")
        self.buttons.append(self.isGlass)
        self.isGlass.setChecked(False)
        self.isGlass.toggled.connect(self.pWidge.radio_checked)

        ButtonLayout.addWidget(self.isGlass)

        #isCloth setup
        self.isCloth = QRadioButton("Cloth")
        self.buttons.append(self.isCloth)
        self.isCloth.setChecked(False)
        self.isCloth.toggled.connect(self.pWidge.radio_checked)

        ButtonLayout.addWidget(self.isCloth)

        #isSkin setup
        self.isSkin = QRadioButton("Skin")
        self.buttons.append(self.isSkin)
        self.isSkin.setChecked(False)
        self.isSkin.toggled.connect(self.pWidge.radio_checked)

        ButtonLayout.addWidget(self.isSkin)

        self.verticalLayout.addLayout(ButtonLayout)
        self.setLayout(self.verticalLayout)
        ''''''''''''''''''''''''''''''''''''''''''''''''

    def get_type(self) -> object.MaterialType:
        if self.isBasic.isChecked():
            return object.MaterialType.BASIC
        if self.isMetal.isChecked():
            return object.MaterialType.METAL
        if self.isGlass.isChecked():
            return object.MaterialType.GLASS
        if self.isCloth.isChecked():
            return object.MaterialType.CLOTH
        if self.isSkin.isChecked():
            return object.MaterialType.SKIN
        else:
             return object.MaterialType.BASIC

class SubstanceExporterWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(SubstanceExporterWindow, self).__init__(parent)
        
        self.setup_UI()

    def setup_UI(self):
        self.setWindowTitle("Exporter")
        self.resize(400, 300)

        self.tex_set_widgets = []

        # Make sure the window always stays on top
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.central_widget.setLayout(self.mainLayout)

        self.title = QtWidgets.QLabel("EXPORTER OOOOO AAAA")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        font = self.title.font()
        font.setPointSize(30)
        self.title.setFont(font)
        self.mainLayout.addWidget(self.title, 0)

        ####Title####
        self.title = QtWidgets.QLabel("Choose an asset to publish")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        font = self.title.font()
        font.setPointSize(30)
        self.title.setFont(font)
        self.mainLayout.addWidget(self.title, 0)

        #######Asset List#######
        self.comboBox = QComboBox()
        self.comboBox.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.comboBox.currentIndexChanged.connect(self.on_change)

        assets = sorted(pipe.server.get_asset_list())
        self.comboBox.addItems(assets)

        #self.comboBox2 = QComboBox()
        #self.comboBox2.setEnabled(False)

        self.mainLayout.addWidget(self.comboBox, 1)
        #self.mainLayout.addWidget(self.comboBox2)

        ##########Buttons##########
        buttonSizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.close)

        self.exportButton = QPushButton("Export")
        self.exportButton.setEnabled(False)
        self.exportButton.clicked.connect(self.do_export)

        #####Text Sets#####
        self.texture_sets_dict = dict.fromkeys(substance_painter.textureset.all_texture_sets(), None)

        for texture_set in self.texture_sets_dict:
            
            widget = TexSetWidget(texture_set.name(), self)
            self.texture_sets_dict[texture_set] = widget

            self.mainLayout.addWidget(widget)

        ButtonsLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(ButtonsLayout)

        ButtonsLayout.addWidget(self.cancelButton)
        ButtonsLayout.addWidget(self.exportButton)

    #Called when the asset combo box changes
    def on_change(self, newIndex):
        self.comboBox2.setEnabled(True)
        self.comboBox2.clear()
        asset = pipe.server.get_asset(self.comboBox.currentText())
    
        variants = asset.variants

        self.comboBox2.addItems(sorted(variants))

    #called every time on of the radio buttons is clicked. Enables export button when all filled.
    def radio_checked(self):
        disabled = True
        widgets = list(self.texture_sets_dict.values())
        for tex_set_widget in widgets:
            isChecked = False
            for button in tex_set_widget.buttons:
                 if button.isChecked() == True:
                      isChecked = True
            if isChecked == False:
                 disabled = False
        
        self.exportButton.setEnabled(disabled)

    def do_export(self):

        #repath for windows
        asset = pipe.server.get_asset(self.comboBox.currentText())
        asset_path = pathlib.Path(asset.path.replace('/groups/', 'G:\\'))

        materials = []

        print(asset.name)
        print(asset_path)

        resource_dir = pathlib.Path().cwd() / 'resources'

        export_path = asset_path / 'mats' / 'textures'
  
        if not os.path.exists(str(export_path)):
            os.makedirs(str(export_path))
        
        metadata_path = asset_path / 'mats' / 'metadata'

        if not os.path.exists(str(metadata_path)):
            os.makedirs(str(metadata_path))

        #Define export preset
        RMAN_preset = substance_painter.resource.import_project_resource(str(resource_dir / 'RMAN.spexp'),
            substance_painter.resource.Usage.EXPORT)
        
        #export each texture set
        for texture_set in self.texture_sets_dict:
            widget = self.texture_sets_dict[texture_set]
            
            print(texture_set.name())

            #create material JSON object for further down the pipe
            mat = object.Material(
                texture_set.name(),
                texture_set.has_uv_tiles(),
                isPxr=True,
                matType=widget.get_type().value)

            materials.append(mat)
            
            
            #write out metadata
            #with open(str(pathlib.Path.joinpath(metadata_path, texture_set.name() + '_meta.json')), 'w') as outfile:
            #    toFile = mat.to_json()
            #    outfile.write(toFile)
            
            #Get the currently active layer stack (paintable)
            stack = texture_set.all_stacks()[0]

            #Define export config for RenderMan
            
            RMAN_config = {
                "exportShaderParams" 	: False,
                "exportPath" 			: str(export_path),
                "exportList"			: [ { "rootPath" : str(stack) } ],
                "exportPresets" 		: [ { "name" : "default", "maps" : [] } ],
                "defaultExportPreset" 	: RMAN_preset.identifier().url(),
                "exportParameters" 		: [
                    {
                        "parameters"	: 
                            { 
                                "paddingAlgorithm": "infinite",
                            }
                    }
                ]
            }

            error = False

            try:
                substance_painter.export.export_project_textures(RMAN_config)
            except Exception as e:
                error = True
                print(e)
                QtWidgets.QMessageBox.warning(self, "Error",
                                            "YOu screwed up....... Maaaaaan")
            
            if error:
                QtWidgets.QMessageBox.warning(self, "Error", "An error occurred while exporting textures. Please check the console for more information.")
                return
            
        #write out materials asset json file
        #texture_sets = [tex_set.name() for tex_set in self.texture_sets_dict]
        texture_sets = materials
        materials_asset = object.MaterialsAsset(name=asset.name, textureSets=texture_sets)
        #print(materials_asset)

        with open(str(pathlib.Path.joinpath(metadata_path, asset.name + '_meta.json')), 'w') as outfile:
            toFile = materials_asset.to_json()
            outfile.write(toFile)

        QtWidgets.QMessageBox.information(self, "Export complete", "Textures exported successfully.")

        self.close()

def create_material():
    pass
import os
import sys
import importlib
import pathlib
import json
import subprocess
import shutil

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
        QtWidgets.QMessageBox.warning(None, "No project open", "Please open a project before trying to publish.")
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

        self.title = QtWidgets.QLabel("Publish Textures")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        font = self.title.font()
        font.setPointSize(30)
        self.title.setFont(font)
        self.mainLayout.addWidget(self.title, 0)

        '''####Title####
        self.title = QtWidgets.QLabel("Choose an asset to publish")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        font = self.title.font()
        font.setPointSize(30)
        self.title.setFont(font)
        self.mainLayout.addWidget(self.title, 0)'''

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

        data = substance_painter.project.Metadata('accomplice')
        asset = pipe.server.get_asset(data.get('asset'))
        geo_variant = data.get('geo_variant')

        asset_path = pathlib.Path(asset.path.replace('/groups/', 'G:\\'))

        material_variant = data.get('material_variant')

        materials = {}

        print(asset.name)
        print(asset_path)
        print('this works?')

        resource_dir = pathlib.Path().cwd() / 'resources'

        export_path = asset_path / 'textures' / geo_variant / material_variant
        tmp_path = asset_path / 'textures' / geo_variant / material_variant / 'tmp'
  
        if not os.path.exists(str(export_path)):
            os.makedirs(str(export_path))

        if not os.path.exists(str(tmp_path)):
            os.makedirs(str(tmp_path))

        print(tmp_path)
        
        meta = asset.get_metadata()

        if not meta:
            QtWidgets.QMessageBox.warning(self, "Error", "Missing Metadata file")
            return

        metadata_path = asset.get_metadata_path()

        if not os.path.exists(str(metadata_path)):
            os.makedirs(str(metadata_path))

        #Define RenderMan export preset
        RMAN_preset = substance_painter.resource.import_project_resource(os.path.join(resource_dir, "RMAN-ACCOMP.spexp"),
            substance_painter.resource.Usage.EXPORT)

        #Define export preset
        PBRMR_preset = substance_painter.resource.import_project_resource(os.path.join(resource_dir, "PBRMR_ACCOMP.spexp"),
            substance_painter.resource.Usage.EXPORT)

        create_version(str(export_path))
        
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

            materials[texture_set.name()] = mat
            
            
            #write out metadata
            #with open(str(pathlib.Path.joinpath(metadata_path, texture_set.name() + '_meta.json')), 'w') as outfile:
            #    toFile = mat.to_json()
            #    outfile.write(toFile)
            
            #Get the currently active layer stack (paintable)
            stack = texture_set.all_stacks()[0]

            #Define export config for RenderMan
            
            RMAN_config = {
                "exportShaderParams" 	: False,
                "exportPath" 			: str(tmp_path),
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

            PBRMR_config = {
                "exportShaderParams" 	: False,
                "exportPath" 			: str(export_path),
                "exportList"			: [ { "rootPath" : str(stack) } ],
                "exportPresets" 		: [ { "name" : "default", "maps" : [] } ],
                "defaultExportPreset" 	: PBRMR_preset.identifier().url(),
                "exportParameters" 		: [
                    {
                        "parameters"	: 
                            {
                                "paddingAlgorithm": "infinite" ,
                            }
                    }
                ]
            }

            error = False

            try:
                substance_painter.export.export_project_textures(PBRMR_config)
            except Exception as e:
                error = True
                print(e)
                QtWidgets.QMessageBox.warning(self, "Error",
                "An error occurred while exporting PBRMR textures. Please check the console for more information.")

            try:
                substance_painter.export.export_project_textures(RMAN_config)

            except Exception as e:
                error = True
                print(e)
                QtWidgets.QMessageBox.warning(self, "Error",
                                            "An error occurred while exporting RMAN textures. Please check the console for more information.")
            
            if error:
                QtWidgets.QMessageBox.warning(self, "Error", "An error occurred while exporting textures. Please check the console for more information.")
                return
            
        #Convert to tex
        try:
            txmake(export_path, tmp_path)
            shutil.rmtree(tmp_path)
        except Exception as e:
            error = True
            print(e)
            QtWidgets.QMessageBox.warning(self, "Error",
                                            "Oh whoops, I screwed up")
        
        if error:
                QtWidgets.QMessageBox.warning(self, "Error", "An error occurred while exporting textures. Please check the console for more information.")
                return

        meta.hierarchy[geo_variant][material_variant].materials = materials

        with open(metadata_path, 'w') as outfile:
            toFile = meta.to_json()
            outfile.write(toFile)

        QtWidgets.QMessageBox.information(self, "Export complete", "Textures exported successfully.")

        self.close()

def startupInfo():
    """Returns a Windows-only object to make sure tasks launched through
    subprocess don't open a cmd window.

    Returns:
        subprocess.STARTUPINFO -- the properly configured object if we are on
                                  Windows, otherwise None
    """
    startupinfo = None
    if os.name is 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo

def txmake(export_path, tmp_path):
    rmantree = os.environ['RMANTREE']
    binary = os.path.join(rmantree,'bin', 'txmake.exe')
    cmd = [binary]

    cmd += ['-resize', 'round-',
            '-mode', 'clamp',
            '-format', 'pixar',
            '-compression', 'lossless',
            '-newer',
            'src', 'dst']
    
    for img in os.listdir(tmp_path):
        cmd[-2] = os.path.join(tmp_path, img)
        dirname, filename = os.path.split(img)
        print("Converting " + filename + " to .tex! Be Patient!")
        texfile = os.path.splitext(filename)[0] + '.tex'
        cmd[-1] = os.path.join(export_path, texfile)
        
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             startupinfo=startupInfo())
        p.wait()

def create_version(path):
    #print(path)
    if os.path.exists(path):

        files = os.listdir(path)

        if 'versions' in files:
            #print('cleaning files')
            files.remove('versions')

        if files:
            if not os.path.exists(path + '/versions'):
                #print('making folder')
                os.mkdir(path + '/versions')

            max_ver = 0

            for file in os.listdir(path + '/versions'):
                if int(file) > max_ver:
                        max_ver = int(file)

            for file in files:

                #print(file)
                
                old_path = path + '/' + str(file)
                new_path = path + '/versions/' + str(max_ver + 1).zfill(3) + '/'

                if not os.path.exists(new_path):
                    #print('making folder')
                    os.mkdir(new_path)
                    
                shutil.move(old_path, new_path + str(file))

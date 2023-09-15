import os
import sys
import importlib
import shutil
import re

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
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QWidget, QRadioButton, QPushButton, QFileDialog, QTextEdit, QMainWindow, QComboBox, QLineEdit, QSizePolicy, QMessageBox

plugin_widgets = []

def start_plugin():

	# Create a text widget for a menu
	Action = QtWidgets.QAction("Accomplice - Import Asset")
	Action.triggered.connect(launch_importer)

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
	
def launch_importer():
    # Check for existing windows and close them before opening a new one
    for widget in plugin_widgets:
        if isinstance(widget, QMainWindow):
            widget.close()
            substance_painter.ui.delete_ui_element(widget)
            plugin_widgets.remove(widget)
            break


    #Start window
    ui_file = QFile('importer_UI.ui')
    ui_file.open(QFile.ReadOnly)
    
    #Start window
    global window
    window = SubstanceImporterWindow()
    window.show()

    
    print("Launching Substance Importer")

class SubstanceImporterWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(SubstanceImporterWindow, self).__init__(parent)
        
        self.setup_UI()

    #store metadata here
    asset = None
    geo_variant = None
    meta = None
    material_variant = None

    def setup_UI(self):
        self.setWindowTitle("Importer")
        self.resize(400, 100)

        # Make sure the window always stays on top
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        #central widget and Vertical Layout
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.central_widget.setLayout(self.mainLayout)

        ####Title####
        self.title = QtWidgets.QLabel("Choose an asset, geo variant, and material variant to shade...")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        font = self.title.font()
        font.setPointSize(30)
        self.title.setFont(font)
        self.mainLayout.addWidget(self.title, 0)

        #######Asset List#######
        self.comboBox = QComboBox()
        self.comboBox2 = QComboBox()

        self.comboBox.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.comboBox.currentIndexChanged.connect(self.on_change)

        assets = sorted(pipe.server.get_asset_list())
        self.comboBox.addItems(assets)

        #######Geo Variant List###########
        self.comboBox2.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.comboBox2.currentIndexChanged.connect(self.on_change_variant)

        self.comboBox2.setEnabled(False)

        self.mainLayout.addWidget(self.comboBox, 1)
        self.mainLayout.addWidget(self.comboBox2)

        #######Material Variant List###########
        self.comboBox3 = QComboBox()
        self.comboBox3.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.comboBox3.currentIndexChanged.connect(self.on_select_matvar)

        self.comboBox3.setEnabled(False)
        self.comboBox3.setEditable(True)

        self.mainLayout.addWidget(self.comboBox3)

        ##########Buttons##########
        buttonSizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        ButtonsLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(ButtonsLayout)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(close_plugin)

        ButtonsLayout.addWidget(self.cancelButton)

        self.importButton = QPushButton("Import")
        self.importButton.setEnabled(False)
        self.importButton.clicked.connect(self.import_button)

        ButtonsLayout.addWidget(self.importButton)

        #######Popup Warnings############
        self.matvar_warn = QtWidgets.QMessageBox()
        self.matvar_warn.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.matvar_warn.buttonClicked.connect(self.msgbtn)

        #Called when the asset combo box changes
    def on_change(self, newIndex):
        global asset
        global meta

        self.comboBox2.setEnabled(True)
        self.comboBox2.clear()
        asset = pipe.server.get_asset(self.comboBox.currentText())
    
        meta = asset.get_metadata()
        if not meta:
            print('no metadata found')
            asset.create_metadata()
            meta = asset.get_metadata()

        variants = meta.hierarchy.keys()

        if variants:
            self.comboBox2.addItems(sorted(variants))

    def on_change_variant(self, newIndex):
        global asset
        global geo_variant
        global meta

        self.comboBox3.setEnabled(True)
        self.comboBox3.clear()
        geo_variant = self.comboBox2.currentText()

        variants =  meta.hierarchy[geo_variant].keys()

        if variants:
            self.comboBox3.addItems(sorted(variants))

    def on_select_matvar(self, newIndex):
        global geo_variant
        global asset
        global meta
        global material_variant

        self.importButton.setEnabled(True)

        material_variant = self.comboBox3.currentText()

    def msgbtn(self, i):
        print(i.text())
        if i.text() != '&Yes':
            print('closing')

        else:
            mesh_path = asset.get_shader_geo_path(geo_variant)
            save_path = asset.get_shading_path() + '/substance/'+ geo_variant + '/' + asset.name + '_' + geo_variant + '_' + material_variant + '.spp'
            print(save_path)
            #move current version out of the way
            if os.path.isfile(save_path):
                new_version(save_path)

            project_settings = substance_painter.project.Settings(
                default_save_path=save_path,
                project_workflow=substance_painter.project.ProjectWorkflow.UVTile,
                default_texture_resolution=2048
            )

            
            substance_painter.project.create(
                mesh_file_path=mesh_path,
                settings=project_settings
            )

            #substance_painter.project.save_as(save_path)

            #Set Project Metadata
            data = substance_painter.project.Metadata('accomplice')
            data.set('asset', asset.name)
            data.set('geo_variant', geo_variant)
            data.set('material_variant', material_variant)

            meta.hierarchy[geo_variant][material_variant] = object.MaterialVariant(material_variant, {})

            metadata_path = asset.get_metadata_path()
            with open(metadata_path, 'w') as outfile:
                toFile = meta.to_json()
                outfile.write(toFile)
                outfile.close()

            self.close()
            #substance_painter.project.execute_when_not_busy(substance_painter.project.save())

    def import_button(self):

        global material_variant
        global asset
        global geo_variant
        global meta

        if material_variant not in  meta.hierarchy[geo_variant]:
            self.matvar_warn.setWindowTitle("Create a new material variant?")
            self.matvar_warn.setText("You're about to create a new material variant in the pipeline under " + asset.name + '/' + geo_variant + '/' + material_variant + ' Are you sure you want to do this?')
            self.matvar_warn.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes)
            self.matvar_warn.show()

        else:
            self.matvar_warn.setWindowTitle("Create new material variant Substance file?")
            self.matvar_warn.setText("You're about to create a new Substance file for " + asset.name + '/' + geo_variant + '/' + material_variant + ' which may already exist. Proceed? Existing files will be archived.')
            self.matvar_warn.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes)
            self.matvar_warn.show()

def new_version(path):
    if os.path.isfile(path):

        sub_folder = re.search('(?<=substance)(.*)(?<=\/)', path).group()
        file_name = re.search('(?<=substance)(.*)(?<=\/)(.*)(?=\.)', path).group().replace(sub_folder, '')
        ext = re.search('(?<=\.).*', path).group()
        folder = path.replace(file_name + '.' + ext, '')

        print(folder)
        print(sub_folder)
        print(file_name)
        print(ext)

        max_ver = 0

        for file in os.listdir(folder):
            ver_num = re.search('(?<=_v)[0-9]+(?=\.)', file)
            if ver_num:
                ver_int = int(ver_num.group())

                if ver_int > max_ver:
                    max_ver = ver_int

        new_path = folder + 'versions/' + file_name + '_v' + str(max_ver + 1).zfill(3) + '.' + ext

        if not os.path.exists(folder + 'versions'):
            print('making folder')
            os.mkdir(folder + 'versions')

        shutil.move(path, new_path)

       

        
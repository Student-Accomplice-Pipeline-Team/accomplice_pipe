import maya.cmds as cmds
import time
import pymel.core as pm
from pathlib import Path
import os, shutil
import pipe.shared.permissions as p
from pipe.shared.helper.utilities.file_path_utils import FilePathUtils
import maya.mel as mel
from pipe.shared.helper.utilities.ui_utils import ListWithCheckboxFilter

import pipe
from pxr import Sdf

'''from pipe.tools.maya.UnMaya_PipeHandlers import unMaya_Element as umEl
from pipe.tools.maya.UnMaya_PipeHandlers import unMaya_Environment as umEnv
import pipe.pipeHandlers.permissions as permissions
import pipe.config as config'''

#TODO: Get frame range from shotgrid

class Exporter():
    
    def __init__(self):
        self.ANIM_DIR = "anim"
        self.ALEMBIC_EXPORTER_SUFFIX = ":EXPORTSET_Alembic"
        
    def run(self):
        print("Alembic Exporter not ready yet")
        
        # self.check_if_selected() # I commented this out so that ideally the script selects the object automatically
        self.object_select_gui()
    
    def check_if_selected(self):
        curr_selection = cmds.ls(selection=True)
        if len(curr_selection) == 0:
            confirm = cmds.confirmDialog(title='WARNING', message="Nothing is selected", button=['Ok'],
                                         defaultButton='Ok', dismissString='Other')
            if confirm == "Ok":
                pass
        else:
            self.object_select_gui()
    
    #Receives a textScrollList and returns the currently selected list item
    def getSelected(self, scrollList):
        selected = cmds.textScrollList(scrollList, q=1, si=1)
        return selected
    
    #This is a GUI that presents four options of what you are exporting. The one selected will determine the location that the object is created in    
    def object_select_gui(self):
        self.alembic_objects = cmds.ls("*" + self.ALEMBIC_EXPORTER_SUFFIX)
        self.alembic_objects = sorted(self.alembic_objects)
        self.alembic_objects = [obj.replace(self.ALEMBIC_EXPORTER_SUFFIX, "") for obj in self.alembic_objects]
        self.checked_objects = []
    
        if cmds.window("ms_selectObject_GUI", exists=True):
            cmds.deleteUI("ms_selectObject_GUI")

        win = cmds.window("ms_selectObject_GUI", title="SELECT OBJECT GUI") 
        cmds.showWindow(win)
        cmds.columnLayout()

        for obj in self.alembic_objects:
            cmds.checkBox(label=obj, onc=lambda x, obj=obj: self.add_to_checked_objects(obj),
                          ofc=lambda x, obj=obj: self.remove_from_checked_objects(obj))

        
        # selection = cmds.textScrollList( "Object_List", numberOfRows=8,
	    # 	        	append=object_list,
	    # 		        selectIndexedItem=1, showIndexedItem=1)
        
        cmds.rowLayout(numberOfColumns=1)

        
        # cmds.button(label="Next", c=lambda x: self.save_object(self.getSelected(selection)[0]))
        cmds.button(label="Next", c=lambda x: self.choose_shot())
        cmds.setParent("..")
    
    #Stores the selected object in a variable to be used later. Triggers a text prompt if "other" was selected. Else triggers the Shot select gui
    def add_to_checked_objects(self, obj):
        if obj not in self.checked_objects:
            self.checked_objects.append(obj)

    def remove_from_checked_objects(self, obj):
        if obj in self.checked_objects:
            self.checked_objects.remove(obj)

    def choose_shot(self):
        try:
            shot_name = FilePathUtils.get_shot_name_from_file_path(cmds.file(q=True, sn=True))
        except AssertionError:
            self.shot_select_gui()
        
        if shot_name is None:
            self.shot_select_gui()
        else:
            self.save_shot(shot_name)
    
    def save_object(self, selected_object):
        
        #Delete Object Select GUI
        if cmds.window("ms_selectObject_GUI", exists=True):
            cmds.deleteUI("ms_selectObject_GUI")   
        
        self.object_selection = selected_object
        
        # Select the object in the scene for alembic exporting
        cmds.select(self.object_selection + self.ALEMBIC_EXPORTER_SUFFIX, replace=True)


        # If we can determine the shot name from the current maya file, then we can skip the shot selection GUI
        try:
            shot_name = FilePathUtils.get_shot_name_from_file_path(cmds.file(q=True, sn=True))
        except AssertionError:
            self.shot_select_gui()
        
        if shot_name is None:
            self.shot_select_gui()
        else:
            self.save_shot(shot_name)
    
    #Stores the selected shot in a variable to be used later and triggers the framerange gui
    def save_shot(self, selected_shot):
        self.shot_selection = selected_shot
        self.get_frameRange_gui()
        
        if cmds.window("ms_selectShot_GUI", exists=True):
                cmds.deleteUI("ms_selectShot_GUI")
        
        #self.exporter()
     
    #This GUI shows a list of the shots to select    
    def shot_select_gui(self):
        self.shot_list = pipe.server.get_shot_list()
        self.shot_list = sorted(self.shot_list)
        

    
        if cmds.window("ms_selectShot_GUI", exists=True):
                cmds.deleteUI("ms_selectShot_GUI")

        win = cmds.window("ms_selectShot_GUI", title="SELECT SHOT") 
        cmds.showWindow(win)
        cmds.columnLayout()
        
        cmds.rowLayout(nc=3)
        self.prefix = cmds.textFieldGrp('search_field')
        cmds.button(label="Search", c=lambda x: self.search())
        cmds.button(label="X", c=lambda x: self.base_list())
        cmds.setParent('..')
        
        selection = cmds.textScrollList( "Shot_List", numberOfRows=8,
	    	        	append=self.shot_list,
	    		        selectIndexedItem=1, showIndexedItem=1)
        
        cmds.rowLayout(numberOfColumns=2)
        #cmds.button(label="Select Current Shot", c=lambda x: self.select_current_shot(selection))
        cmds.button(label="Next", c=lambda x: self.save_shot(self.getSelected(selection)[0]))
        cmds.setParent("..")
    
    #Supports the Shot select gui by implementing a search function
    def search(self):
        searchEntry = cmds.textFieldGrp('search_field', q=True, text=True)
        cmds.textScrollList( "Shot_List", edit=True, removeAll=True)
            
        tempList = []
        for element in self.shot_list:
            if searchEntry.lower() in element.lower():
                tempList.append(element)
        cmds.textScrollList( "Shot_List", edit=True, append=tempList)
    
    #Supports the Shot selection by clearing the search function and returning to the base list        
    def base_list(self):
        cmds.textScrollList( "Shot_List", edit=True, removeAll=True)
        cmds.textScrollList( "Shot_List", edit=True, append=self.shot_list)
        cmds.textFieldGrp('search_field', edit=True, text="")  
    
    #Selects from the list displayed in the shot selection gui, the shot item correlation to the current maya file
    def select_current_shot(self, scrollList):
        
        fullNamePath = cmds.file( q =1, sn = 1)
        dirPath = os.path.dirname(fullNamePath)
        shotName = dirPath.split('/')[-1]
        print(fullNamePath, dirPath, shotName)
       
        if shotName in self.shot_list:
            #Sets the selection to the currently opened shot
            cmds.textScrollList( scrollList, edit=True, selectItem=shotName)
        else: 
            confirm = cmds.confirmDialog ( title='WARNING', message="The current Maya file is not in the shot list", button=['Ok'], defaultButton='Ok', dismissString='Other' )
            if confirm == "Ok":
                pass

    
    #Gets object name, changes spaces to underscores if any   
    def object_name_results(self):
        self.object_selection = cmds.textFieldGrp('comment', q=True, text=True)
        self.object_selection = self.object_selection.replace(" ", "_")

        if cmds.window('msOtherObjWindowID', exists=True):
            cmds.deleteUI('msOtherObjWindowID')
            
        self.shot_select_gui()
            
     #Generates the file path where the alembic will be stored. If there is an alembic there already, versions
     #   if not, it creates a base version and an .element file and an object_main.abc   
    def exporter(self):

        asset = self.object_selection.lower()
        if asset == "herocar": # This is due to a descrepancy with the naming convention between the Maya and Houdini files. In Maya, the rig is called heroCar, and in Houdini, everything is set up for it to be studentcar.
            asset = "studentcar"

        print(asset)
        shot = pipe.server.get_shot(self.shot_selection)
        
        #File path for exporting alembics for CFX
        cfx_filepath = shot.get_shotfile_folder('cfx')
        if not self.dir_exists(cfx_filepath):
            os.mkdir(cfx_filepath)
            p.set_RWE(cfx_filepath)
            
        self.alem_filepath = cfx_filepath + "/" + asset + ".abc"

        #File path for exporting wrapped alembics from ANIM
        anim_filepath = shot.get_shotfile_folder('anim')
        if not self.dir_exists(anim_filepath):
            os.mkdir(anim_filepath)
            p.set_RWE(anim_filepath)

        self.usd_filepath = anim_filepath + '/' + asset + '/' + asset + '.usd'
        print(self.usd_filepath)
        
        command = self.get_alembic_command()
        
        self.version_alembic(command)
        self.version_usd()
        
        

    
    def dir_exists(self, dir_path) -> bool:
        """ Checks if the given directory exists, returns True or False """
        my_file = Path(dir_path)
        return my_file.is_dir()
    
    def dir_isEmpty(self, dir_path) -> bool:
        """ Checks if the given directory is empty, returns True or False """

        dir_list = os.listdir(dir_path)
        
        if len(dir_list) == 0:
            return True
        else:
            return False
    
    def get_alembic_command(self):
        """ Gets the command needed to export the alembic. Updates the alem_filepath to match"""

        start = str(self.startFrame)
        end = str(self.endFrame)
        root = ""
        curr_selection = cmds.ls(selection=True)
        for obj in curr_selection:
            if root != "":
                root = root + " "
            root = root + "-root " + obj

        command = "-frameRange " + start + " " + end + " -attr shop_materialpath" + " -uvWrite -worldSpace -stripNamespaces " + root + " -file " + self.alem_filepath
        print("command: " + command)
        return command
    
    def version_alembic(self, command):
        """ Exports the alembic and versions it """
        #Export alembic to $TEMP_DIR
        cmds.AbcExport(j=command)


        #Get new version number
        #self.ver_num = self.el.get_latest_version() + 1 
        #dir_name = ".v" + f"{self.ver_num:04}"
        #Make hidden directory with version number
        #new_dir_path = os.path.join(self.curr_env.get_file_dir(self.el.filepath), dir_name)
        #os.mkdir(new_dir_path)
        #Copy alembic into the new directory and rename it
        #new_file_path = new_dir_path + "/" + self.el.get_file_parent_name() + self.el.get_file_extension()
        #shutil.copy(self.el.filepath, new_file_path)

        # Set permissions
        #permissions.set_permissions(self.el.filepath)
        #permissions.set_permissions(new_file_path)

    #Finds the alembic in the temp folder, converts to usd and saves in pipe
    def version_usd(self):
        file_path = self.alem_filepath
        output_file = self.usd_filepath

        usd_data = Sdf.Layer.FindOrOpen(file_path)
        usd_data.Export(output_file)
    
    def update_element_file(self):
        """Updates the element file with the comment and latest version"""
        #Adds new publish log to list of publishes
        self.comment = "v" + str(self.ver_num) + ": " + self.comment
        self.el.add_publish_log(self.comment)

        #Set latest version
        self.el.set_latest_version(self.ver_num)

        #Write the .element file to disk
        self.el.write_element_file()
    
        
    def comment_gui(self):
        """ Make list of past comments for the gui """
        publishes = self.el.get_publishes_list()
        if len(publishes) > 10:
            publishes = publishes[-10:]
        publishes_list = []
        if len(publishes) != 0:
            for publish in publishes:
                label = publish[0] + ' ' + publish[1] + ' ' + publish[2] + '\n'
                publishes_list.insert(0, label)
                            
        # Make a new default window
        windowID = 'msCommentWindowID'
        
        if cmds.window(windowID, exists=True):
            cmds.deleteUI(windowID)

        self.window = cmds.window(windowID, title="Comment", sizeable=False, iconName='Short Name',
                                  resizeToFitChildren=True)

        cmds.rowColumnLayout(nr=5)

        cmds.textScrollList( "Publish_List", numberOfRows=8, append=publishes_list)

        # Comment box
        cmds.rowLayout(nc=1)
        self.prefix = cmds.textFieldGrp('comment', label='Comment:')
        cmds.setParent('..')


        # Create export button
        cmds.columnLayout(adjustableColumn=True, columnAlign='center')
        cmds.button(label='Export', command=lambda x: self.comment_results())
        cmds.setParent('..')
        cmds.showWindow(self.window)
    
    #Gets comment, versions the file and updates the .element file    
    def comment_results(self):
        self.comment = cmds.textFieldGrp('comment', q=True, text=True)
        self.update_element_file()
        
        if cmds.window('msCommentWindowID', exists=True):
            cmds.deleteUI('msCommentWindowID')
    
    #Inputs the current playback range frames into the FrameRangeWindow text fields
    def select_playback_range(self):
        start_frame = cmds.playbackOptions(q=True, min=True)
        end_frame = cmds.playbackOptions(q=True, max=True)
        
        cmds.textFieldGrp('startFrame', edit=True, text=int(start_frame))
        cmds.textFieldGrp('endFrame', edit=True, text=int(end_frame))

    #GUI: Prompts for the first and last frame to export
    def get_frameRange_gui(self):
        # Make a new default window
        windowID = 'msFrameRangeWindowID'
        if cmds.window(windowID, exists=True):
            cmds.deleteUI(windowID)

        self.window = cmds.window(windowID, title="Select Frame Range", sizeable=False, iconName='Short Name',
                                  resizeToFitChildren=True)

        cmds.rowColumnLayout(nr=5)

        # StartFrame and EndFram boxes
        cmds.rowLayout(nc=4)
        cmds.textFieldGrp('startFrame', label='Start Frame:')
        cmds.textFieldGrp('endFrame', label='End Frame:')
        cmds.setParent('..')
        cmds.separator(h=30, vis=True)

        # Create a Playback range button
        cmds.rowLayout(nc=2)
        cmds.button(label='PlayBack range', command=lambda x: self.select_playback_range())
        cmds.button(label='Export', command=lambda x: self.get_frameRange())
        cmds.setParent('..')
        cmds.showWindow(self.window)

    # Saves the frame range from the gui, then triggers the exporter    
    def get_frameRange(self):
        
        self.startFrame = cmds.textFieldGrp('startFrame', q=True, text=True)
        self.endFrame = cmds.textFieldGrp('endFrame', q=True, text=True)
        
        
        
        error_message = ""
        if not self.startFrame or not self.endFrame:
            error_message = "Entries can not be empty"
        elif not self.startFrame.isdigit():
            if self.startFrame[0] == '-' and self.startFrame[1:].isdigit():
                pass
            else:
                error_message = "Entries must be integers"
        elif not self.endFrame.isdigit():
            if self.endFrame[0] == '-' and self.endFrame[1:].isdigit():
                pass
            else:
                error_message = "Entries must be integers"
        elif int(self.endFrame) < int(self.startFrame):
            error_message = "End frame must be greater than the start frame"
        
        if error_message != "":
            confirm = cmds.confirmDialog ( title='WARNING', message=error_message, button=['Ok'], defaultButton='Ok', dismissString='Other' )
            if confirm == "Ok":
                pass
        else:
            if cmds.window('msFrameRangeWindowID', exists=True):
                cmds.deleteUI('msFrameRangeWindowID')
            self.export_checked_objects()
    
        
    def export_checked_objects(self):
        num_objects = len(self.checked_objects)
        progressControl = mel.eval('$tmp = $gMainProgressBar')

        # Configure and show the progress bar
        cmds.progressBar(progressControl, edit=True, beginProgress=True, isInterruptable=True, status='Exporting Objects...', maxValue=num_objects)

        for i, obj in enumerate(self.checked_objects, start=1):
            if cmds.progressBar(progressControl, query=True, isCancelled=True):
                break
            if cmds.progressBar(progressControl, query=True, progress=True) >= num_objects:
                break

            cmds.progressBar(progressControl, edit=True, step=1, status=f'Exporting: {obj}')
            self.object_selection = obj
            cmds.select(self.object_selection + self.ALEMBIC_EXPORTER_SUFFIX, replace=True)
            self.exporter()

        # End and delete the progress bar
        cmds.progressBar(progressControl, edit=True, endProgress=True)

        # for obj in self.checked_objects:
        #     self.object_selection = obj
        #     # Ensure the object is selected in Maya
        #     cmds.select(self.object_selection + self.ALEMBIC_EXPORTER_SUFFIX, replace=True)
        #     # Call the exporter method for each selected object
        #     self.exporter()
        # Close the SELECT OBJECT GUI window
        if cmds.window("ms_selectObject_GUI", exists=True):
            cmds.deleteUI("ms_selectObject_GUI")

        # Show completion notification
        exported_objects_str = ", ".join(self.checked_objects)
        cmds.confirmDialog(title='Export Complete', message=f'Exporting of the selected objects ({exported_objects_str}) has been completed.', button=['Ok'])
    
    def open_studini_anim_shot_file(): # TODO: finish this when you have the time :)
        # Run /groups/accomplice/pipeline/pipe/main.py --pipe=accomplice houdini
        import subprocess
        subprocess.Popen(['/groups/accomplice/pipeline/pipe/main.py', '--pipe=accomplice', 'houdini'])
        # Open the anim shot file

class SimpleLogger():
    def __init__(self, main_prefix="SimpleLogger") -> None:
        self.log = ""
        self.print_errors = True
        self.print_info = True
        self.include_timestamps = True
        self.main_prefix = main_prefix

    def add_message(self, prefix, message, should_print):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S") if self.include_timestamps else ""
        new_message = f"{self.main_prefix} \t {prefix} {message} {timestamp}\n"
        self.log += new_message
        if should_print:
            print(new_message)

    def error(self, message):
        self.add_message("ERROR:", message, self.print_errors)

    def info(self, message):
        self.add_message("INFO:", message, self.print_info)

    def get_log(self):
        return self.log

class MultiShotExporter:
    def __init__(self):
        self.logger = SimpleLogger()

    def run(self):
        from .maya_file_manager import MayaFileManager
        if MayaFileManager.check_for_unsaved_changes_and_inform_user():
            return

        shots_to_export = self.get_shots_to_export()
        self.logger.info(f'Shots to export: {shots_to_export}')

        shots_to_export = [pipe.server.get_shot(shot) for shot in shots_to_export] # Convert the shot names to shot objects
        assert all([shot is not None for shot in shots_to_export]), "One or more of the shots you selected does not exist in the database."

        characters_to_export = self.get_rigs_to_export()
        self.logger.info(f'Characters to export: {characters_to_export}')

        for shot in shots_to_export:
            self.logger.info(f'Exporting rigs from shot {shot}')
            self.export_rigs_from_shot(shot, characters_to_export)
    
        print(self.logger.get_log())
    
    def get_shots_to_export(self):
        shot_selection_dialog = ListWithCheckboxFilter("Select Which Shots You Would Like To Export", sorted(pipe.server.get_shot_list()), list_label="Shots", include_filter_field=True)
        shot_selection_dialog.exec_()

        selected_items = shot_selection_dialog.get_selected_items()
        return selected_items
        
    def get_rigs_to_export(self):
        rigs = ['vaughn', 'letty', 'ed', 'heroCar']
        rig_selection_dialog = ListWithCheckboxFilter("Select Which Rigs You Would Like To Export", sorted(rigs), list_label="Rigs", include_filter_field=True)
        rig_selection_dialog.exec_()

        selected_items = rig_selection_dialog.get_selected_items()
        return selected_items
    
    def get_only_characters_in_open_shot(self, characters_to_export):
        characters_to_export_in_shot = []
        for character in characters_to_export:
            exporter = Exporter()
            export_full_name = character + exporter.ALEMBIC_EXPORTER_SUFFIX

            if not cmds.objExists(export_full_name):
                self.logger.error(f'Character {character} does not exist in the scene. Not exporting.')
            else:
                characters_to_export_in_shot.append(character)
        return characters_to_export_in_shot
        
    
    def export_rigs_from_shot(self, shot, rigs):
        # Open the corresponding shot file
        self.logger.info(f'Opening shot file for shot {shot.get_name()}')
        file_path = shot.get_maya_shotfile_path()
        cmds.file(file_path, open=True, force=True)
        self.logger.info(f'Opened shot file for shot {shot.get_name()}')

        # Create an exporter object and set the selected objects and shot_selection attributes... This is kind of a hack, but probably the easiest way to do it for now
        exporter = Exporter()
        exporter.checked_objects = self.get_only_characters_in_open_shot(rigs)
        self.logger.info(f'Exporting characters {exporter.checked_objects} from shot {shot.get_name()}')
        exporter.shot_selection = shot.get_name()
        exporter.startFrame = int(cmds.playbackOptions(q=True, min=True))
        self.logger.info(f'Start frame: {exporter.startFrame}')
        exporter.endFrame = int(cmds.playbackOptions(q=True, max=True))
        self.logger.info(f'End frame: {exporter.endFrame}')
        exporter.export_checked_objects()
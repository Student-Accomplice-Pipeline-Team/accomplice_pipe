import nuke
import os
import re
import argparse
import getpass
from datetime import datetime






def get_artist_name():
    

# Get the current logged-in username
    username = getpass.getuser()
    lighting_team = ["sblancha", "smithj20", "ldemoss", "skjas25"]
    lighting_team_names = ["Spencer Blanchard", "Juliana Smith", "Lisa Bird", "Soo Kyung Park"]
    if username in lighting_team:
        index = lighting_team.index(username)
        return lighting_team_names[index]
    else:
        #check if the current user is on the lighting team
        lighter_name = nuke.getInput("Enter Your Name", "name")
        if lighter_name is not None:
            return lighter_name
        else:
            return "Anonymous artist"






def make_null():
    end_comp_node = nuke.toNode('render_null')

    if end_comp_node:
        # If the node exists, select it
        end_comp_node.setSelected(True)
        return end_comp_node
    else:
        # If the node doesn't exist, create it
        end_comp_node = nuke.createNode('NoOp', 'name END_COMP')
        return end_comp_node

def make_reformat(null_node):
    reformat_node = nuke.createNode('Reformat')
    reformat_node['type'].setValue('to box')  # Set to 'scale' or other types as needed
    reformat_node['box_fixed'].setValue(True)
    reformat_node['box_width'].setValue(1920)
    reformat_node['box_height'].setValue(1080)
    reformat_node.setInput(0, null_node)
    reformat_node.setName('render_reformat')
    return reformat_node



def make_metadata(null_node):
    font_path = '/groups/accomplice/pipeline/pipe/accomplice/software/nuke/plugins/StudentAccomplice_Toolkit/StudentAccomplice_Toolkit/fonts/coolvetica/coolvetica condensed rg.otf'
    deparment = "Beauty Render"
    #artist = get_artist_name()
    artist = "Temp"
    date = datetime.now().strftime('%m-%d-%Y')

    text_node = nuke.createNode("Text")
    text_node['font'].setValue(font_path)
    text_node['message'].setValue(deparment +" pass" + "\n" + artist + "\n" + date)
    text_node['size'].setValue(70)
    text_node['xjustify'].setValue("left")
    text_node['yjustify'].setValue("top")
    bbox_values = [20, 20, 1920, 1080]  # Adjust these values as needed
    text_node['box'].setValue(bbox_values)
    text_node.setInput(0, None)
    current_xpos = null_node['xpos'].value()
    current_ypos = null_node['ypos'].value()
    new_xpos = current_xpos - 150
    text_node['xpos'].setValue(new_xpos)
    text_node['ypos'].setValue(current_ypos)
    text_node.setName('render_text')
    return text_node

def make_dropshadow(metadata_node):
    # Dropshadow
    dropshadow_node = nuke.createNode('DropShadow')
    dropshadow_node['size'].setValue(3)
    dropshadow_node['opacity'].setValue(1)
    dropshadow_node['color'].setValue([0, 0, 0])
    dropshadow_node['dropshadow_distance'].setValue(0)
    dropshadow_node.setInput(0, None)
    dropshadow_node.setInput(1, metadata_node)
    dropshadow_node['xpos'].setValue(metadata_node['xpos'].value())
    dropshadow_node['ypos'].setValue(metadata_node['ypos'].value() + 50)
    dropshadow_node.setName('render_dropshadow')
    return dropshadow_node
    
def make_merge(null_node, dropshadow_node):
    merge_node = nuke.createNode('Merge2')
    merge_node.setInput(0, null_node)
    merge_node.setInput(1, dropshadow_node)
    merge_node.setName('render_merge')


def make_tree():
    null_node = make_null()
    reformat_node = make_reformat(null_node)  # Adding reformat node after END_COMP
    metadata_node = make_metadata(reformat_node)
    dropshadow_node = make_dropshadow(metadata_node)
    merge_node = make_merge(reformat_node, dropshadow_node)







    




def movExport(file_name, first_frame, last_frame):



    make_tree()
    write_node = nuke.createNode('Write')
    write_node.setName('render_writeMOV')


    #setting the file parameter
    #file_name = os.path.splitext(os.path.basename(nuke.root().name()))[0]
    file_path = "/groups/accomplice/edit/shots/comp/" + file_name + "/tempMOVs/"



    # Check if the file path exists
    print(file_path)
    if os.path.exists(file_path):
        print(f"The file '{file_path}' exists.")
    
        all_file_names = os.listdir("/groups/accomplice/edit/shots/comp/" + file_name + "/tempMOVs/")
        # Extract version numbers from versioned file names
        version_numbers = [int(re.search(r'_V(\d+)', file_name).group(1)) for file_name in all_file_names if re.search(r'_V\d+', file_name)]

        max_version = max(version_numbers, default=0) 
        if max_version == 0:
            max_version = 1

        next_version = max_version + 1

        new_file_name = f"{file_name}_V{next_version:03d}.mov"
        #print(new_file_name)

        
        full_path = "/groups/accomplice/edit/shots/comp/" + file_name + "/tempMOVs/" + new_file_name
        write_node['file'].setValue(full_path)

        #We are using index 1 (color_picking (Output - sRGB)) because it looks very close to the way that an aces EXR looks. Eventually when everything is finaled we export in EXR anyways, so the MOV's are temporary.
        dropdown_index = 1 
        write_node['colorspace'].setValue(dropdown_index)

        #create directories
        write_node['create_directories'].setValue(1)

        
        command = 'os.system("touch ' + os.path.join("/groups/accomplice/edit/shots/comp", str(file_name)) + '")'
        write_node['afterRender'].setValue(command)
        write_node['afterRender'].setValue('exec(open("/groups/accomplice/pipeline/pipe/accomplice/software/nuke/plugins/afterMovRender.py").read())')

        nuke.execute(write_node, first_frame, last_frame, 1)
        print("Successfully rendered " + str(new_file_name))


        
def movExportToSpecificDestination(file_destination, first_frame, last_frame):
    """
    Similar to movExport, but allows the user to specify the file destination. Does not perform any versioning.
    """
    make_tree()  # Assuming you want to include the same node setup (null, metadata, dropshadow, merge)

    write_node = nuke.createNode('Write')
    write_node.setName('render_writeMOV_specific')

    # Set the file path to the user specified destination
    write_node['file'].setValue(file_destination)

    # Assuming color space and other settings are similar to the movExport
    dropdown_index = 1  # Example: assuming this corresponds to the correct colorspace
    write_node['colorspace'].setValue(dropdown_index)

    # Option to create directories if they don't exist
    write_node['create_directories'].setValue(1)

    # Execute the node to render the sequence
    nuke.execute(write_node, first_frame, last_frame, 1)

    print("Successfully rendered to " + file_destination)



def main(exr_sequence_path, file_name):    
    # Find all EXR files in the directory
    exr_files = [f for f in os.listdir(os.path.dirname(exr_sequence_path))
                 if re.match(os.path.basename(exr_sequence_path).replace('%04d', '\d{4}'), f)]
    # Extract frame numbers
    frame_numbers = [int(file.split('.')[1]) for file in exr_files]
    
    # Find the highest and lowest frame numbers
    first_frame = min(frame_numbers)
    last_frame = max(frame_numbers)

    # Create a Read node for the EXR sequence
    read_node = nuke.createNode('Read')
    read_node['file'].setValue(exr_sequence_path)
    read_node['first'].setValue(first_frame)
    read_node['last'].setValue(last_frame)
    read_node['on_error'].setValue('black')
    # read_node['colorspace'].setValue('ACES - ACEScg')
    read_node['colorspace'].setValue(10)
    # print(nuke.getColorspaces())


    # Call the function to export to mov
    movExportToSpecificDestination(file_name, first_frame, last_frame)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process EXR files and export a movie")
    parser.add_argument('exr_sequence_path', type=str, help='The path to the EXR sequence')
    parser.add_argument('file_name', type=str, help='The file name for the exported movie')

    args = parser.parse_args()

    main(args.exr_sequence_path, args.file_name)

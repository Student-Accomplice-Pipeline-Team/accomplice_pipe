import nuke
import sys
import os
import re
#the path to the write nodes python script
script_path = '/groups/accomplice/pipeline/pipe/accomplice/software/nuke/plugins'
if script_path not in sys.path:
    sys.path.append(script_path)

import writeNodes_autoBeauty


def main(exr_sequence_path, file_name):    
    # Find all EXR files in the directory
    exr_files = [f for f in os.listdir(os.path.dirname(exr_sequence_path))
                 if re.match(os.path.basename(exr_sequence_path).replace('%04d', '\d{4}'), f)]
    #print(exr_files)
    # Extract frame numbers

    frame_numbers = [int(file.split('.')[1]) for file in exr_files]
    
    # Find the highest and lowest frame numbers
    first_frame = min(frame_numbers)
    last_frame = max(frame_numbers)
    #print(last_frame)
    exr_sequence_path = exr_sequence_path
    
    # Create a Read node for the EXR sequence
    read_node = nuke.createNode('Read')
    read_node['file'].setValue(exr_sequence_path)
    read_node['first'].setValue(first_frame)
    read_node['last'].setValue(last_frame)
#    (file=exr_sequence_path, first=first_frame, last=last_frame)
    read_node['on_error'].setValue('black')
    

    writeNodes_autoBeauty.movExport(file_name, first_frame, last_frame)


exr_sequence_path = "/groups/accomplice/pipeline/production/sequences/A/shots/005/render/Beauty_2024-03-22/Beauty_2024-03-22"  + '.%04d.exr'
file_name= "A_005"
main(exr_sequence_path, file_name)

#To run this in the terminal, do /opt/Nuke14.0v5 -t test.py



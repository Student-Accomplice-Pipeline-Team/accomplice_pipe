import nuke
import sys
import os
import re
import argparse

# Use the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(current_dir, 'writeNodes_autoBeauty.py')

# Add the directory containing the script to sys.path if not already included
if current_dir not in sys.path:
    sys.path.append(current_dir)

import writeNodes_autoBeauty

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

    # Call the function to export to mov
    writeNodes_autoBeauty.movExport(file_name, first_frame, last_frame)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process EXR files and export a movie")
    parser.add_argument('exr_sequence_path', type=str, help='The path to the EXR sequence')
    parser.add_argument('file_name', type=str, help='The file name for the exported movie')

    args = parser.parse_args()

    main(args.exr_sequence_path, args.file_name)

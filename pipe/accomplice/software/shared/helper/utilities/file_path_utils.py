import pipe

def get_shot_name_from_file_path(file_path):
    """ Returns the shot name from a file path """
    from os.path import sep as separator
    # Note that the structure of a file path comes in as /groups/accomplice/pipeline/production/sequences/<SEQUENCE_NAME>/shots/<SHOT_NAME>/...
    path_split = file_path.split(separator)
    shots_index = None
    try:
        shots_index = path_split.index("shots")
    except ValueError:
        # This file path does not contain a shot name
        return None

    # So, the shot_name is composed of <SEQUENCE_NAME>_<SHOT_NAME>
    shot_name = path_split[shots_index - 1] + '_' + path_split[shots_index + 1]

    # Ensure that the shot name is valid
    assert shot_name in pipe.server.get_shot_list()
    return shot_name
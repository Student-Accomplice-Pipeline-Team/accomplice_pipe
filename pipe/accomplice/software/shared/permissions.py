import os


def set_RWE(path):
    try:
        os.chmod(path, stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)
    except:
        print("File does not exist yet.")

import hou
import tractor.api.author as author
import os
import re
import functools
import glob
from typing import Sequence, Optional
from enum import Enum
import pipe
from pxr import Usd

# Tractor requires all neccesiary envionment paths of the job to function.
# Add any additonal required paths to the list: ENV_PATHS
ENV_PATHS = [
    "PATH",
    "RMANTREE",
    "HOUDINI_PATH",
    "OCIO",
    "RMAN_PROCEDURALPATH",
    "RFHTREE",
    "PIXAR_LICENSE_FILE",
]

# Create global variable for the environment key holding paths from ENV_PATHS
ENV_KEY = functools.reduce(
    lambda str, env_var: str + env_var + "=" + os.getenv(env_var) + " ",
    ENV_PATHS,
    "setenv ",
)
# ENV_KEY = [key + '=' + os.getenv(key) for key in ENV_PATHS]


# This function runs when the submit button on the node is pushed
# Creates TractorJob object and submits the job
def farm_render(node: hou.Node) -> None:
    author.setEngineClientParam(hostname="hopps.cs.byu.edu", port=443)
    job = TractorSubmit(node)
    job.spoolJob()


# This class holds all the variables and methods required to gather the paramters
# from the tractor lop user interface and convert them to a tractor job
class TractorSubmit:
    # Constructor method which takes the node and sets the job title variable
    def __init__(self, node):
        # Necessary variables declared here for easy readibility
        # Reference to the lop node
        self.node: hou.Node = node

        # Tractor library Job class object used to submit jobs
        self.job = author.Job()
        # Set job title
        self.job.title = node.parm("jobtitle").eval()
        # Set job environment key
        self.job.envkey = [ENV_KEY]

        # Array of usd paths
        self.filepaths = []
        # Array of frame ranges
        self.frame_ranges = []
        # Array of render override paths
        self.output_path_overrides = []
        self.blades = None

    # Gets the directory paths and render output overrides when
    # USDs are inputted manually with the "From Disk" Render method
    def input_usd_info(self):
        num_sources: hou.Parm = self.node.parm("sources").evalAsInt()

        # For loop for getting variables from dynamically changing parameters
        for source_num in range(1, num_sources + 1):
            source_type = get_source_type(self.node, source_num)

            if source_type == 'file':
                # Get filepaths for the pattern
                filepaths = validate_files(
                    self.node, self.node.parm("filepath" + str(source_num))
                )
            elif source_type == 'node':
                # Prepare for and render the USD
                usd_node = update_usd_node(self.node, source_num)
                filepaths = [usd_node.parm('lopoutput').eval()]
                usd_node.parm('execute').pressButton()

            for filepath in filepaths:
                # Add the file to the filepaths
                self.filepaths.append(filepath)

                # Get the frame range for the file
                frame_range = get_frame_range(self.node, source_num)
                self.frame_ranges.append(frame_range)

                # Get the output path overrides for the file
                output_path_override = None
                if int(self.node.parm(source_type + 'useoutputoverride' + str(source_num)).eval()) == 1:
                    output_path_override = []
                    hou.hscript(
                        f"set -g FILE={os.path.splitext(os.path.basename(filepath))[0]}"
                    )
                    for frame in range(frame_range[0], frame_range[1] + 1):
                        output_path_override.append(
                            self.node.parm(
                                source_type + "outputoverride" + str(source_num)
                            ).evalAtFrame(frame)
                        )

                self.output_path_overrides.append(output_path_override)

        print(self.filepaths, self.frame_ranges, self.output_path_overrides)

    # Gets the job priority from the node user interface
    def input_priority(self):
        self.job.priority = float(self.node.parm("jobpriority").eval())

    # Gets the blade selection info from the node user interface
    def input_blades(self):
        blade_method = self.node.parm("blademethod").evalAsString()

        blade_pattern = self.node.parm(blade_method).eval()

        if blade_method == "profile" or blade_method == "name":
            pattern_list = blade_pattern.split()
            blade_pattern = functools.reduce(
                lambda str, token: str + token + "||", pattern_list, ""
            )[:-2]

        self.job.service = blade_pattern

    # Creates all tasks for each USD and adds them to the job
    def add_tasks(self):
        # For loop creating a task for each USD file inputed into the node
        for file_num in range(0, len(self.filepaths)):
            task = author.Task()
            task.title = os.path.basename(self.filepaths[file_num])
            task.serialsubtasks = 1

            current_file_stage = Usd.Stage.Open(self.filepaths[file_num])
            output_path_attr = current_file_stage.GetPrimAtPath(
                "/Render/Products/renderproduct"
            ).GetAttribute("productName")


            if self.output_path_overrides[file_num] is not None:
                output_dir = os.path.dirname(self.output_path_overrides[file_num][0])
            else:
                output_dir = os.path.dirname(output_path_attr.Get(0))
            
            if not os.path.exists(output_dir):
                directory_task = author.Task()
                directory_task.title = "directory"

                mkdir = [
                    "/bin/bash",
                    "-c",
                    "/usr/bin/mkdir -p "
                    + output_dir
                ]

                directory_command = author.Command()
                directory_command.argv = mkdir
                directory_command.envkey = [ENV_KEY]
                directory_task.addCommand(directory_command)
            
                task.addChild(directory_task)
            
            render_task = author.Task()
            render_task.title = "render"
            
            if self.node.parm("denoise").evalAsInt():
                asymmetry = self.node.parm("denoise_asymmetry").evalAsFloat()
                denoise_task = author.Task()
                denoise_task.title = "denoise"

                for frame in range(self.frame_ranges[file_num][0], self.frame_ranges[file_num][1] + 1):
                    if frame % self.frame_ranges[file_num][2] != 0:
                        continue
                    denoise_frame_task = author.Task()
                    denoise_frame_task.title = f"Denoise Frame {str(frame)}"

                    exr_path = ""
                    if self.output_path_overrides[file_num] != None:
                        exr_path = self.output_path_overrides[file_num][
                            frame - self.frame_ranges[file_num][0]
                        ]
                    else:
                        exr_path = output_path_attr.Get(frame)

                    denoise_command_argv = [
                        "/bin/bash",
                        "-c",
                        "PIXAR_LICENSE_FILE='9010@animlic.cs.byu.edu' "
                        + "/opt/pixar/RenderManProServer-25.2/bin/denoise_batch "
                        + f"--asymmetry {str(asymmetry)} "
                        + "--crossframe "
                        + f"--frame-include {frame - self.frame_ranges[file_num][0]} "
                        + re.sub(r'\.\d{4}\.', '.*.', exr_path)
                    ]

                    denoise_command = author.Command()
                    denoise_command.argv = denoise_command_argv
                    denoise_command.envkey = [ENV_KEY]                    
                    denoise_frame_task.addCommand(denoise_command)

                    varinst = author.Instance(title="Frame $framenum")
                    # prereqs = author.Iterate()
                    # prereqs.varname = "framenum"
                    # prereqs.frm = max(self.frame_ranges[file_num][0], frame - 3)
                    # prereqs.to = min(frame + 3, self.frame_ranges[file_num][1])
                    # prereqs.by = 1
                    # prereqs.addToTemplate(varinst)

                    # prereq_task = author.Task(title=f"Denoise Frame {str(frame)} prereqs")
                    # prereq_task.addChild(prereqs)

                    # denoise_frame_task.addChild(prereqs)

                    for p in range(max(self.frame_ranges[file_num][0], frame - 3), min(frame + 3, self.frame_ranges[file_num][1]) + 1):
                        denoise_frame_task.addChild(author.Instance(title=f"Frame {p}"))

                    denoise_task.addChild(denoise_frame_task)
                
                render_task.addChild(denoise_task)

            # For loop creating a sub-task for each frame to be rendered in the USD
            for frame in range(
                self.frame_ranges[file_num][0], self.frame_ranges[file_num][1] + 1
            ):
                if frame % self.frame_ranges[file_num][2] != 0:
                    continue
                subTask = author.Task()
                subTask.title = "Frame " + str(frame)
                # Build render command from USD info
                # renderCommand = ["/bin/bash", "-c", "/opt/hfs19.5/bin/husk --help &> /tmp/test.log"]
                renderCommand = [
                    "/bin/bash",
                    "-c",
                    "PIXAR_LICENSE_FILE='9010@animlic.cs.byu.edu' /opt/hfs19.5/bin/husk --renderer "
                    + self.node.parm("renderer").eval()
                    + " --frame "
                    + str(frame)
                    + " --frame-inc "
                    + str(self.frame_ranges[file_num][2])
                    + " --make-output-path -V2",
                ]
                if self.output_path_overrides[file_num] != None:
                    renderCommand[-1] += (
                        " --output "
                        + self.output_path_overrides[file_num][
                            frame - self.frame_ranges[file_num][0]
                        ]
                    )
                renderCommand[-1] += (
                    " " + self.filepaths[file_num]
                )  # + " &> /tmp/test.log"
                # renderCommand = ["/opt/hfs19.5/bin/husk", "--renderer", self.node.parm("renderer").eval(),
                #                  "--frame", str(j), "--frame-count", "1", "--frame-inc", str(self.frame_ranges[i][2]), "--make-output-path"]
                # if (self.output_path_overrides[i] != None):
                #     renderCommand.extend(
                #         ["--output", self.output_path_overrides[i]])
                # renderCommand.append(self.filepaths[i])

                # Create command object
                command = author.Command()
                command.argv = renderCommand
                command.envkey = [ENV_KEY]
                # Add command to subtask
                subTask.addCommand(command)

                # Create post task to convert to PNG
                if self.node.parm("createplayblasts").evalAsInt():
                    pngconvert = author.Command()
                    exr_path = ""
                    if self.output_path_overrides[file_num] != None:
                        exr_path = self.output_path_overrides[file_num][
                            frame - self.frame_ranges[file_num][0]
                        ]
                    else:
                        exr_path = output_path_attr.Get(frame)

                    exr_path_split = os.path.split(exr_path)
                    
                    png_dir = exr_path_split[0] + os.path.sep + "png"

                    if not os.path.exists(png_dir):
                        os.makedirs(png_dir, mode=775)
                    
                    png_path = (
                        png_dir
                        + os.path.sep
                        + os.path.splitext(exr_path_split[1])[0]
                        + ".png"
                    )

                    pngconvert.argv = [
                        "/bin/bash",
                        "-c",
                        "OCIO='/opt/pixar/RenderManProServer-25.2/lib/ocio/ACES-1.2/config.ocio' "
                        + "/opt/hfs19.5/bin/hoiiotool "
                        + exr_path
                        + " "
                        + "--ch R,G,B,A "
                        + "--colorconvert linear 'Output - Rec.709' "
                        + "-o "
                        + png_path,
                    ]
                    pngconvert.envkey = [ENV_KEY]
                    subTask.addCommand(pngconvert)

                # Add sub-task to task
                render_task.addChild(subTask)

            task.addChild(render_task)

            # Create playblast file
            if self.node.parm("createplayblasts").evalAsInt():
                create_mov = author.Command()

                # fmt: off
                create_mov.argv = [
                    "/usr/bin/ffmpeg",
                    "-y",
                    "-r", "24",
                    "-f", "image2",
                    "-pattern_type", "glob",
                    "-i", png_dir + os.path.sep + "*.png",
                    "-s", "1920x1080",
                    # "-vcodec", "dnxhd",
                    "-vcodec", "libx264",
                    "-pix_fmt", "yuv422p",
                    "-colorspace:v", "bt709",
                    "-color_primaries:v", "bt709",
                    "-color_trc:v", "bt709",
                    "-color_range:v", "tv",
                    # "-b:v", "440M",
                    "-crf", "25",
                    # png_dir + os.path.sep + "playblast.mov",
                    png_dir + os.path.sep + "playblast.mp4",
                ]
                # fmt: on

                create_mov.envkey = [ENV_KEY]

                create_mov_task = author.Task()
                create_mov_task.title = "playblast"
                create_mov_task.addCommand(create_mov)

                task.addChild(create_mov_task)

            # Add task to job
            self.job.addChild(task)

            # print(self.job.asTcl())

    # Calls all functions in this class required to gather parameter info, create, and spool the Tractor Job
    def spoolJob(self):
        self.input_usd_info()
        if len(self.filepaths) > 0:
            self.input_priority()
            self.input_blades()
            self.add_tasks()
            # print(self.job.asTcl())
            self.job.spool()
            hou.ui.displayMessage("Job sent to tractor")


# def on_input_changed(node: hou.Node, type: hou.NodeType, input_index: int) -> None:
#     # Check if there are any node inputs
#     num_inputs = len(node.inputConnections())
#     if num_inputs < 1:
#         # Check if there are any sources set to the node input
#         node_sources = []
#         for parm_instance in node.parmTuple('sources').multiParmInstances():
#             if parm_instance.name().startswith('sourceoptions'):
#                 if parm_instance.evalAsInts()[0] == 1:
#                     node_sources.append(
#                         parm_instance.name().removeprefix('sourceoptions'))
#         # Warn the user
#         if len(node_sources) > 0:
#             set_warning(
#                 node,
#                 parm_instance.name(),
#                 f"Source(s) {', '.join(node_sources)} set to Node Input but no input is connected",
#             )


def get_source_type_index(node: hou.Node, source_num: int) -> int:
    return node.parm('sourceoptions' + str(source_num) + '1').evalAsInt()


def get_source_type(node: hou.Node, source_num: int) -> str:
    return [
        'file',
        'node',
    ][get_source_type_index(node, source_num)]


def get_frame_range(node: hou.Node, source_num: int) -> Sequence[int]:
    source_type = get_source_type(node, source_num)
    trange = node.parm(
        source_type + 'trange' + str(source_num)
    ).evalAsString()

    frame_range = None

    if trange == 'file':
        if source_type == 'file':
            filepath = node.parm('filepath' + str(source_num)).evalAsString()
            print(filepath)
            file_stage = Usd.Stage.Open(filepath)
            frame_range = [
                int(file_stage.GetStartTimeCode()),
                int(file_stage.GetEndTimeCode()),
                1,
            ]
        elif source_type == 'node':
            current_frame = hou.intFrame()
            frame_range = [
                int(current_frame),
                int(current_frame),
                1
            ]

    elif trange == 'range':
        frame_range = [
            int(node.parm(
                source_type + 'framerange' + str(source_num) + 'x'
            ).eval()),
            int(node.parm(
                source_type + 'framerange' + str(source_num) + 'y'
            ).eval()),
            int(node.parm(
                source_type + 'framerange' + str(source_num) + 'z'
            ).eval()),
        ]

    elif trange == 'single':
        frame = node.parm(
            source_type + 'frame' + str(source_num)).evalAsInt()
        frame_range = [
            frame,
            frame,
            1,
        ]

    return frame_range


def get_usd_node(node: hou.Node):
    usd_node_type = hou.nodeType(hou.lopNodeTypeCategory(), 'usd_rop')
    return [child for child in node.children() if child.type() == usd_node_type][0]


def update_usd_node(node: hou.Node, source_num: int) -> hou.Node:
    # Get the relevant options for the source
    use_usd_override = node.parm('useusdoverride' + str(source_num)).evalAsInt()
    if use_usd_override:
        usd_path = node.parm('usdoverride' + str(source_num)).evalAsString()
    else:
        usd_path = hou.text.expandString(
            '$HIP/render/usd/$HIPNAME-') + str(source_num) + '.usd'

    f1, f2, f3 = get_frame_range(node, str(source_num))
    strip_layer_breaks = node.parm('striplayerbreaks' + str(source_num)).evalAsInt()
    error_saving_implicit_paths = node.parm(
        'errorsavingimplicitpaths' + str(source_num)).evalAsInt()

    # Find the USD node
    usd_node = get_usd_node(node)

    # Set the options on the USD node
    usd_node.parm('trange').set('normal')
    usd_node.parm('f1').deleteAllKeyframes()
    usd_node.parm('f2').deleteAllKeyframes()
    usd_node.parm('f1').set(f1)
    usd_node.parm('f2').set(f2)
    usd_node.parm('f3').set(f3)
    usd_node.parm('lopoutput').set(usd_path)
    usd_node.parm('striplayerbreaks').set(strip_layer_breaks)
    usd_node.parm('errorsavingimplicitpaths').set(error_saving_implicit_paths)

    return usd_node


def execute_usd(node: hou.Node, parm: hou.Parm):
   # Get the number of the source to render a USD for
    source_num = parm.name().removeprefix('usdexecute')

    # Prepare for and render the USD
    usd_node = update_usd_node(node, source_num)
    usd_node.parm('execute').pressButton()


def execute_usd_background(node: hou.Node, parm: hou.Parm):
    # Check if the file is saved
    if hou.hipFile.hasUnsavedChanges():
        hou.ui.displayMessage(
            'Cannot perform background render with unsaved changes.\n' +
            'Save your file before proceeding.',
            severity=hou.severityType.Warning
        )
        return

    # Get the number of the source to render a USD for
    source_num = parm.name().removeprefix('usdexecutebackground')

    # Prepare for and render the USD
    usd_node = update_usd_node(node, source_num)
    hou.hipFile.save()
    usd_node.parm('executebackground').pressButton()

# Expands, validates, and returns the filepaths


def validate_files(node: hou.Node, parm: hou.Parm) -> Sequence[str]:
    file_patterns = parm.evalAsString().split()
    filepaths: Sequence[str] = []

    # Evaluate the file patterns
    for pattern in file_patterns:
        new_filepaths: Sequence[str] = []

        # If the pattern isn't a filepath, expand it
        if os.path.isfile(pattern):
            new_filepaths.append(pattern)
        elif not os.path.isdir(pattern):
            new_filepaths = glob.glob(pattern, recursive=True)
            new_filepaths.sort()

        # Make sure the pattern matched at least one file
        if not len(new_filepaths) > 0:
            set_error(
                node,
                parm.name(),
                f"File pattern didn't match any files:\n{pattern}",
            )
            return new_filepaths

        # Make sure each new filepath is a USD
        for filepath in new_filepaths:
            if os.path.isdir(filepath):
                continue
            if os.path.splitext(filepath)[1] not in [".usd", ".usda", ".usdc", ".usdz"]:
                set_warning(
                    node,
                    parm.name(),
                    f"File pattern captured non-USD file:\n{pattern}\nmatched\n{filepath}",
                )

            filepaths.append(filepath)

    print(filepaths)
    unset_issues(node, parm.name())
    return filepaths


def unset_issues(node: hou.Node, parm_name: str):
    error_dict_parm: hou.Parm = node.parm('errordict')
    errors: dict = error_dict_parm.eval()
    errors.pop(parm_name, None)
    error_dict_parm.set(errors)

    warning_dict_parm = node.parm('warningdict')
    warnings: dict = warning_dict_parm.eval()
    warnings.pop(parm_name, None)
    warning_dict_parm.set(warnings)


def set_error(node: hou.Node, parm_name: str, desc: str):
    set_issue(node.parm('errordict'), hou.severityType.Error, parm_name, desc)


def set_warning(node: hou.Node, parm_name: str, desc: str):
    set_issue(node.parm('warningdict'),
              hou.severityType.Warning, parm_name, desc)


def set_issue(issue_parm: hou.Parm, message_severity: hou.severityType, parm_name: str, desc: str):
    # Commented out because error handling is not fully implemented yet
    # issues: dict = issue_parm.eval()

    # if not issues.get(parm_name) == desc:
    #     issues.update({parm_name: desc})
    #     issue_parm.set(issues)

    hou.ui.displayMessage(desc, severity=message_severity)


def check_issues(node: hou.Node, **kwargs):
    error_dict_parm: hou.Parm = node.parm('errordict')
    errors: dict = error_dict_parm.eval()

    for error_parm, error_desc in errors.items():
        pass

    warning_dict_parm: hou.Parm = node.parm('warningdict')
    warnings: dict = warning_dict_parm.eval()

    for warning_parm, warning_desc in warnings.items():
        pass


def switch_source_type(
    node: hou.Node,
    parm: hou.Parm,
    script_value: str,
    script_multiparm_index: int,
    **kwargs
) -> None:

    SOURCE_TYPES = [
        'file',
        'node',
    ]

    source_type_labels = node.parm(
        'sourceoptions' + script_multiparm_index + '1'
    ).parmTemplate().folderNames()

    type_parm: hou.Node = node.parm('sourcetype' + script_multiparm_index)

    curr_type = SOURCE_TYPES[int(script_value)]
    prev_type = SOURCE_TYPES[type_parm.evalAsInt()]

    PARMTUPLE_BASE_NAMES = [
        'trange',
        'frame',
        'framerange',
        'useoutputoverride',
        'outputoverride',
    ]

    # Make the collapsed source display the current sourcetype, if not a file
    filepath_parm: hou.Parm = node.parm('filepath' + script_multiparm_index)
    filepathholder_parm = node.parm('filepathholder' + script_multiparm_index)
    if curr_type == 'file':
        # Copy filepath# from invisible parm
        filepath_parm.deleteAllKeyframes()
        filepath_parm.setFromParm(filepathholder_parm)
    else:
        # Copy filepath# to invisible parm
        filepathholder_parm.deleteAllKeyframes()
        filepathholder_parm.setFromParm(filepath_parm)

        # Set filepath# to the label of the current source type's tab
        filepath_parm.deleteAllKeyframes()
        filepath_parm.set(source_type_labels[int(script_value)])

    for parmtuple_base in PARMTUPLE_BASE_NAMES:
        prev_option_parmtuple: hou.ParmTuple = node.parmTuple(
            prev_type + parmtuple_base + script_multiparm_index)

        for prev_option_parm in prev_option_parmtuple:
            print(prev_option_parm.name())
            new_option_parm: hou.Parm = node.parm(
                curr_type +
                prev_option_parm.name().removeprefix(prev_type)
            )

            new_option_parm.deleteAllKeyframes()
            new_option_parm.setFromParm(prev_option_parm)

    # Update the sourcetype# parameter
    type_parm.setExpression(script_value)

    # Commented out because warnings should occur at cook time
    # Warn the user if the source is set to Node Input but no input is connected
    # if curr_type == 'node' and len(node.inputConnections()) < 1:
    #     set_warning(node, parm.name(
    #     ), f"Source {script_multiparm_index} set to Node Input but no input is connected")
    #     return

    # unset_issues(node, parm.name())

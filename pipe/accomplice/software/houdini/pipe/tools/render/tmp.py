import hou
import tractor.api.author as author
import os
import re
import functools
import glob
from typing import Sequence
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
def farm_render(node):
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
        num_patterns: hou.Parm = self.node.parm("files").evalAsInt()

        # For loop for getting variables from dynamically changing parameters
        for pattern_num in range(1, num_patterns + 1):
            # Get filepaths for the pattern
            filepaths = validate_files(
                self.node, self.node.parm("filepath" + str(pattern_num))
            )

            for filepath in filepaths:
                # Add the file to the filepaths
                self.filepaths.append(filepath)

                # Get the frame range for the file
                frame_range = None
                trange = self.node.parm("trange" + str(pattern_num)).evalAsString()
                if trange == "file":
                    file_stage = Usd.Stage.Open(filepath)
                    frame_range = [
                        int(file_stage.GetStartTimeCode()),
                        int(file_stage.GetEndTimeCode()),
                        1,
                    ]
                elif trange == "range":
                    frame_range = [
                        self.node.parm(
                            "framerange" + str(pattern_num) + "x"
                        ).evalAsInt(),
                        self.node.parm(
                            "framerange" + str(pattern_num) + "y"
                        ).evalAsInt(),
                        self.node.parm(
                            "framerange" + str(pattern_num) + "z"
                        ).evalAsInt(),
                    ]
                elif trange == "single":
                    frame = self.node.parm("frame" + str(pattern_num)).evalAsInt()
                    frame_range = [
                        frame,
                        frame,
                        1,
                    ]

                self.frame_ranges.append(frame_range)

                # Get the output path overrides for the file
                output_path_override = None
                if (
                    int(self.node.parm("useoutputoverride" + str(pattern_num)).eval())
                    == 1
                ):
                    output_path_override = []
                    hou.hscript(
                        f"set -g FILE={os.path.splitext(os.path.basename(filepath))[0]}"
                    )
                    for frame in range(frame_range[0], frame_range[1] + 1):
                        output_path_override.append(
                            self.node.parm(
                                "outputoverride" + str(pattern_num)
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
                # Add sub-task to task
                task.addChild(subTask)
            # Add task to job
            self.job.addChild(task)

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


# Called when inputting a file into a "usdfile#" parameter
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
            hou.ui.displayMessage(
                f"File pattern didn't match any files:\n{pattern}",
                severity=hou.severityType.Warning,
            )

        # Make sure each new filepath is a USD
        for filepath in new_filepaths:
            if os.path.isdir(filepath):
                continue
            if os.path.splitext(filepath)[1] not in [".usd", ".usda", ".usdc", ".usdz"]:
                hou.ui.displayMessage(
                    f"File pattern captured non-USD file:\n{pattern}\nmatched\n{filepath}",
                    severity=hou.severityType.Error,
                )

            filepaths.append(filepath)

    print(filepaths)
    return filepaths

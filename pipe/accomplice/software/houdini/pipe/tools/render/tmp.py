import hou
import tractor.api.author as author
import os
import re
import functools
import glob
from typing import Sequence, Iterable, Mapping, Any

from pxr import Usd
from pipe.shared.helper.utilities.houdini_utils import HoudiniUtils
from pipe.shared.object import JsonSerializable

# Tractor requires all necessary environment paths of the job to function.
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
        self.job.title = get_parm_str(node, 'jobtitle')
        # Set job environment key
        self.job.envkey = [ENV_KEY]

        # Array of usd paths
        self.filepaths = []
        self.resolutions = []
        # Array of frame ranges
        self.frame_ranges = []
        # Array of render override paths
        self.output_path_overrides = []
        self.do_cryptomattes = []
        self.delete_usd = []
        self.blades = None

    # Gets the directory paths and render output overrides when
    # USDs are inputted manually with the "From Disk" Render method
    def input_usd_info(self):
        num_sources = get_parm_int(self.node, 'sources')

        # For loop for getting variables from dynamically changing parameters
        for source_num in range(1, num_sources + 1):
            source_type = get_source_type(self.node, source_num)

            filepaths = []
            if source_type == 'file':
                # Get filepaths for the pattern
                filepaths = validate_files(
                    self.node, get_parm(self.node, 'filepath', source_num)
                )
                self.delete_usd.extend([False] * len(filepaths))
            elif source_type == 'node':
                # Prepare for and render the USD
                usd_node = get_usd_node(self.node)

                update_source_nodes(self.node, source_num)

                num_layers: hou.Parm = get_parm_int(self.node, 'nodelayers', source_num)
                for layer_num in range(1, num_layers + 1):
                    update_layer_nodes(self.node, source_num, layer_num)
                    
                    filepaths.append(get_parm_str(usd_node, 'lopoutput'))
                    self.delete_usd.append(get_parm_bool(self.node, 'deleteusd', source_num, layer_num))

                    usd_node.parm('execute').pressButton()


                # Create a lopimportcam node in /obj
                # sop_cam_node = hou.node('/obj').createNode('lopimportcam')
                # sop_cam_node.parm('loppath').set(self.node.path())
                # sop_cam_node.parm('primpath').setFromParm(get_parm(self.node, 'nodecamera', source_num))

                ## DEPRECATED, HERE FOR POSTERITY
                # Prepare for and render the camera alembic
                # alembic_node = update_alembic_node(self.node, source_num, sop_cam_node.path())
                # alembic_node.parm('execute').pressButton()

                # Destroy the lopimportcam node
                # sop_cam_node.destroy()

            for filepath in filepaths:
                # Add the file to the filepaths
                self.filepaths.append(filepath)

                # Get the frame range for the file
                frame_range = get_frame_range(self.node, source_num)
                self.frame_ranges.append(frame_range)

                # Get the output path overrides for file sources
                output_path_override = None
                do_cryptomatte = False
                resolution = None
                if source_type == 'file':
                    if get_parm_bool(self.node, source_type + 'useoutputoverride' + str(source_num)):
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
                elif source_type == 'node':
                    do_cryptomatte = get_parm_bool(self.node, source_type + 'cryptomatteenable', source_num)
                    resolution = get_resolution(self.node, source_num)
                
                self.resolutions.append(resolution)
                self.do_cryptomattes.append(do_cryptomatte)
                self.output_path_overrides.append(output_path_override)

        print(self.filepaths, self.frame_ranges, self.output_path_overrides)

    # Gets the job priority from the node user interface
    def input_priority(self):
        self.job.priority = get_parm_float(self.node, "jobpriority")

    # Gets the blade selection info from the node user interface
    def input_blades(self):
        blade_method = get_parm_str(self.node, "blademethod")

        blade_pattern = get_parm_str(self.node, blade_method)

        if blade_method == "profile" or blade_method == "name":
            pattern_list = blade_pattern.split()
            blade_pattern = functools.reduce(
                lambda str, token: str + token + "||", pattern_list, ""
            )[:-2]

        self.job.service = blade_pattern

    # Creates all tasks for each USD and adds them to the job
    def add_tasks(self):
        denoise = get_parm_bool(self.node, 'denoise')
        playblast = get_parm_bool(self.node, 'createplayblasts')

        # Create all tasks for each USD file
        for file_num in range(0, len(self.filepaths)):
            do_cryptomatte = self.do_cryptomattes[file_num]
            delete_usd = self.delete_usd[file_num]
            frame_start, frame_end, frame_increment = self.frame_ranges[file_num]

            usd_file_task = author.Task(
                title=os.path.basename(self.filepaths[file_num]),
                serialsubtasks=1,
            )

            # Create the cleanup commands if necessary
            if delete_usd:
                delete_usd_command = author.Command(argv=[
                    "/bin/bash",
                    "-c",
                    f"/usr/bin/rm '{self.filepaths[file_num]}'",
                ])
                usd_file_task.addCleanup(delete_usd_command)

            # Open the USD file's stage
            current_file_stage = Usd.Stage.Open(self.filepaths[file_num])
            resolution_attr = current_file_stage.GetAttributeAtPath(
                "/Render/Products/renderproduct.resolution"
            )
            output_path_attr = current_file_stage.GetAttributeAtPath(
                "/Render/Products/renderproduct.productName"
            )

            # Get the resolution if necessary
            if self.resolutions[file_num] != None:
                resolution = self.resolutions[file_num]
            else:
                resolution = resolution_attr.Get(0)

            # Create the output directory if necessary
            if self.output_path_overrides[file_num] != None:
                output_dir = os.path.dirname(self.output_path_overrides[file_num][0])
            else:
                output_dir = os.path.dirname(output_path_attr.Get(0))
            
            if not os.path.exists(output_dir):
                usd_file_task.addChild(create_directory_task(output_dir))

            # Handle denoise-specific behavior
            if denoise:
                # Create the denoised directory if necessary
                denoised_exr_dir = os.path.join(output_dir, 'denoised')
                if not os.path.exists(denoised_exr_dir):
                    usd_file_task.addChild(create_directory_task(denoised_exr_dir))

                # Create the undenoised directory if necessary
                undenoised_exr_dir = os.path.join(output_dir, 'undenoised')
                if not os.path.exists(undenoised_exr_dir):
                    usd_file_task.addChild(create_directory_task(undenoised_exr_dir))
            
            # Create the png directory if necessary
            if playblast:
                png_dir = os.path.join(output_dir, 'png')
                if not os.path.exists(png_dir):
                    usd_file_task.addChild(create_directory_task(png_dir))
            
            # Create the cryptomatte directory if necessary
            cryptomatte_dir = None
            if do_cryptomatte:
                cryptomatte_dir = os.path.dirname(get_render_settings_node(self.node).parm('xn__risamplefilter0PxrCryptomattefilename_70bno').eval())

                if not os.path.exists(cryptomatte_dir):
                    usd_file_task.addChild(create_directory_task(cryptomatte_dir))
            
            # Create any necessary base tasks
            render_task = author.Task(title='render')
            usd_file_task.addChild(render_task)

            if denoise or playblast:
                post_task = author.Task(title='post')
                usd_file_task.addChild(post_task)
                framerate = 24. / frame_increment

                if playblast:
                    # fmt: off
                    playblast_command = [
                        "/usr/bin/ffmpeg",
                        "-y",
                        "-r", framerate,
                        "-f", "image2",
                        "-pattern_type", "glob",
                        "-i", os.path.join(png_dir, "*.png"),
                        "-s", 'x'.join(resolution),
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

                    playblast_task = author.Task(title='playblast', argv=playblast_command)
                    post_task.addChild(playblast_task)

                if denoise:
                    denoise_task = author.Task(title='denoise')
                    render_task.addChild(denoise_task)

            # Create the tasks for each frame
            for frame in range(frame_start, frame_end + 1, frame_increment):
                # Get the output path of the frame
                frame_output_path = None
                final_frame_path = None
                output_path_overridden = False
                if self.output_path_overrides[file_num] != None:
                    frame_output_path = self.output_path_overrides[file_num][frame - frame_start]
                    output_path_overridden = True
                else:
                    frame_output_path = output_path_attr.Get(frame)
                
                final_frame_path = frame_output_path

                if denoise:
                    frame_output_path = os.path.join(undenoised_exr_dir, os.path.basename(frame_output_path))

                # Create and add the render frame task
                render_frame_task = create_render_frame_task(
                    title = f"Frame {str(frame)} f{file_num}",
                    usd_file = self.filepaths[file_num],
                    frame = frame,
                    frame_increment = frame_increment,
                    renderer = get_parm_str(self.node, 'renderer'),
                    output_path = frame_output_path if output_path_overridden or denoise else None,
                )
                render_task.addChild(render_frame_task)

                # Create task to denoise the frame
                if denoise:
                    asymmetry = get_parm_float(self.node, "denoise_asymmetry")
                    
                    # Determine the crossframe-denoising frame range
                    crossframe_start = max(frame_start, frame - (3 * frame_increment))
                    crossframe_end = min(frame + (3 * frame_increment), frame_end)

                    # Get the dependencies for the denoising task
                    dependencies = []
                    for crossframe in range(crossframe_start, crossframe_end + 1):
                       dependencies.append(author.Instance(title=f"Frame {crossframe} f{file_num}"))

                    # Create and add the denoise frame task
                    denoise_frame_task = create_denoise_frame_task(
                        title = f"Denoise Frame {str(frame)} f{file_num}",
                        frame = frame,
                        exr_path = frame_output_path,
                        asymmetry = asymmetry,
                        crossframe_range = (crossframe_start, crossframe_end),
                        frame_increment = frame_increment,
                        dependencies = dependencies,
                    )
                    denoise_task.addChild(denoise_frame_task)
                
                # Create post task to transfer the frame's cryptomattes
                if do_cryptomatte:
                    cryptomatte_path = get_render_settings_node(self.node).parm('xn__risamplefilter0PxrCryptomattefilename_70bno').evalAtFrame(frame)
                    
                    # Get the dependencies for the cryptomatte transfer task
                    dependency_title = f"Frame {str(frame)} f{file_num}"
                    if denoise:
                        dependency_title = "Denoise " + dependency_title
                    dependencies = [author.Instance(title=dependency_title)]
                    
                    transfer_cryptomatte_task = create_cryptomatte_transfer_task(
                        title = f"Cryptomatte Transfer Frame {str(frame)} f{file_num}",
                        exr_path = final_frame_path,
                        cryptomatte_path = cryptomatte_path,
                        dependencies = dependencies,
                    )
                    post_task.addChild(transfer_cryptomatte_task)
                    

                # Create post task to convert to PNG
                if playblast:
                    frame_filename = os.path.basename(final_frame_path)
                    png_filename = os.path.splitext(frame_filename)[0] + '.png'
                    png_path = os.path.join(output_dir, 'png', png_filename)

                    # Get the dependencies for the conversion task
                    dependency_title = f"Frame {str(frame)} f{file_num}"
                    if denoise:
                        dependency_title = "Denoise " + dependency_title
                    dependencies = [author.Instance(title=dependency_title)]

                    # Determine the channel names for the conversion
                    channels = ['Ci.r', 'Ci.g', 'Ci.b', 'a']
                    if denoise:
                        channels = ['r', 'g', 'b', 'a']
                    
                    convert_frame_task = create_convert_frame_task(
                        title = f"Convert Frame {str(frame)} f{file_num}",
                        exr_path = final_frame_path,
                        output_path = png_path,
                        dependencies = dependencies,
                        channels = channels,
                    )
                    playblast_task.addChild(convert_frame_task)

            # Add task to job
            self.job.addChild(usd_file_task)


    # Calls all functions in this class required to gather parameter info, create, and spool the Tractor Job
    def spoolJob(self):
        self.input_usd_info()
        if len(self.filepaths) > 0:
            self.input_priority()
            self.input_blades()
            self.add_tasks()
            # print(self.job.asTcl())
            self.job.spool()
            self.cleanup()
            if get_parm_bool(self.node, 'ui_notify_on_job_submission'):
                hou.ui.displayMessage("Job sent to tractor")
    
    def cleanup(self):
        fetch_node = get_fetch_node(self.node)
        fetch_expression: str = fetch_node.parm('loppath').rawValue()

        new_fetch = re.subn(r'(input_index\s*=\s*)(\d+|None)', r'\g<1>0', fetch_expression)[0]
        fetch_node.parm('loppath').setExpression(new_fetch)


# def on_input_changed(node: hou.Node, type: hou.NodeType, input_index: int) -> None:
#     # Check if there are any node inputs
#     num_inputs = len(node.inputConnections())
#     if num_inputs < 1:
#         # Check if there are any sources set to the node input
#         node_sources = []echo
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


class DenoiseConfig(JsonSerializable):
    primary: Sequence[str] = None
    aux: set[str, Sequence[Mapping[str, Sequence[str]]]] = None
    config: Mapping[str, Any] = None

    def __init__(
            self,
            files: Sequence[str],
            asymmetry: float = 0.0,
            flow: bool = False,
            debug: bool = False,
            output_dir: str = None,
            frame_include: int = None,
            passes: Sequence[str] = ['diffuse', 'specular', 'alpha', 'albedo', 'irradiance'],
            parameters: str = '/opt/pixar/RenderManProServer-25.2/lib/denoise/20970-renderman.param',
            topology: str = '/opt/pixar/RenderManProServer-25.2/lib/denoise/full_w7_4sv2_sym_gen2.topo',
        ) -> None:
        self.primary = files
        self.aux = {}
        
        for render_pass in passes:
            if render_pass == 'diffuse' or render_pass == 'specular':
                self.aux.update(
                    {
                        render_pass: [
                            {
                                'paths': files,
                                'layers': ['directdiffuse', 'subsurface'] if render_pass == 'diffuse' else ['directspecular'],
                            }
                        ]
                    }
                )
            else:
                self.aux.update({render_pass: []})
        
        self.config = {
            'asymmetry': asymmetry,
            'flow': flow,
            'debug': debug,
            'output-dir': output_dir,
            'frame-include': str(frame_include),
            'passes': passes,
            'parameters': parameters,
            'topology': topology,
        }


def create_convert_frame_task(
    title: str,
    exr_path: str,
    output_path: str,
    dependencies: Iterable[author.Task],
    channels: Sequence[str] = ['Ci.r', 'Ci.g', 'Ci.b', 'a'],
):
    convert_frame_command = [
        "/bin/bash",
        "-c",
        "OCIO='/opt/pixar/RenderManProServer-25.2/lib/ocio/ACES-1.2/config.ocio' "
        + "/opt/hfs19.5/bin/hoiiotool "
        + exr_path
        + " "
        + f"--ch {','.join(channels)} "
        + "--colorconvert linear 'Output - Rec.709' "
        + "-o "
        + output_path,
    ]

    # Create the convert frame task
    convert_frame_task = author.Task(
        title=title,
        argv=convert_frame_command,
    )

    # Add dependencies
    for dependency in dependencies:
        convert_frame_task.addChild(dependency)

    return convert_frame_task
    

def create_render_frame_task(
        title: str,
        usd_file: str,
        frame: int,
        frame_increment: int,
        renderer: str,
        output_path: str = None,
    ):
    # Build render command from USD info
    # renderCommand = ["/bin/bash", "-c", "/opt/hfs19.5/bin/husk --help &> /tmp/test.log"]
    render_frame_command = [
        "/bin/bash",
        "-c",
        "PIXAR_LICENSE_FILE='9010@animlic.cs.byu.edu' "
        + "RMAN_SHADERPATH=/groups/accomplice/shading/hGeoPatterns/shaders "
        + "RMAN_RIXPLUGINPATH=/groups/accomplice/shading/hGeoPatterns/rixplugins " 
        + "/opt/hfs19.5/bin/husk --renderer "
        + str(renderer)
        + " --frame "
        + str(frame)
        + " --frame-inc "
        + str(frame_increment)
        + " --make-output-path -V2",
    ]
    if output_path != None:
        render_frame_command[-1] += f" --output '{str(output_path)}'"
    
    render_frame_command[-1] += f" '{usd_file}'"
    # + " &> /tmp/test.log"
    # renderCommand = ["/opt/hfs19.5/bin/husk", "--renderer", get_parm_str(self.node, "renderer"),
    #                  "--frame", str(j), "--frame-count", "1", "--frame-inc", str(self.frame_ranges[i][2]), "--make-output-path"]

    return author.Task(
        title=title,
        argv=render_frame_command,
    )


def create_aov_transfer_argv(src_exr_path: str, dest_exr_path: str) -> str:
    return [
        "/bin/bash",
        "-exc",
        """
            src_exr_path='%(src_exr_path)s'
            dest_exr_path='%(dest_exr_path)s'
            og_channels_commas=\"$(/opt/hfs19.5/bin/hoiiotool \"$src_exr_path\" --printinfo | /usr/bin/awk '/channel list/{ $1 = \"\"; $2 = \"\"; gsub(/^[ \\t]+/, \"\", $0); gsub(\" \", \"\", $0); print $0; exit }')\"
            og_channels_newlines=\"$(/usr/bin/echo \"$og_channels_commas\" | /usr/bin/tr ',' '\\n')\"
            denoised_channels_commas=\"$(/opt/hfs19.5/bin/hoiiotool \"$dest_exr_path\" --printinfo | /usr/bin/awk '/channel list/{ $1 = \"\"; $2 = \"\"; gsub(/^[ \\t]+/, \"\", $0); gsub(\" \", \"\", $0); print $0; exit }')\"
            denoised_channels_newlines=\"$(/usr/bin/echo \"$denoised_channels_commas\" | /usr/bin/tr ',' '\\n')\"
            shared_channels=\"$(comm -12 <(/usr/bin/echo \"$og_channels_newlines\" | /usr/bin/sort) <(/usr/bin/echo \"$denoised_channels_newlines\" | /usr/bin/tr [:upper:] [:lower:] | /usr/bin/sort))\"
            transfer_channels_commas=\"$(/usr/bin/grep -vxf <(/usr/bin/echo -e \"$shared_channels\\nCi.r\\nCi.g\\nCi.b\") <(/usr/bin/echo \"$og_channels_newlines\") | /usr/bin/tr '\\n' ',')\"
            /opt/hfs19.5/bin/hoiiotool --metamerge \"$dest_exr_path\" --ch \"$denoised_channels_commas\" \"$src_exr_path\" --ch \"$transfer_channels_commas\" --chappend -o \"$dest_exr_path\"
        """ % {'src_exr_path':src_exr_path, 'dest_exr_path':dest_exr_path},
    ]

def create_cryptomatte_transfer_task(
        title: str,
        exr_path: str,
        cryptomatte_path: str,
        dependencies: Iterable[author.Task]
    ) -> author.Task:
    cryptomatte_transfer_task = author.Task(
        title = title,
        argv = create_aov_transfer_argv(cryptomatte_path, exr_path)
    )
    
    # Add dependencies for cryptomatte transfer
    for dependency in dependencies:
        cryptomatte_transfer_task.addChild(dependency)
    
    return cryptomatte_transfer_task
    

def create_denoise_frame_task(
        title: str,
        frame: int,
        exr_path: str,
        asymmetry: int,
        crossframe_range: tuple,
        frame_increment: int,
        dependencies: Iterable[author.Task],
    ) -> author.Task:
    crossframe_start, crossframe_end = crossframe_range

    denoise_frame_task = author.Task(title=title)
    
    frame_dir = os.path.join(os.path.dirname(exr_path), os.path.pardir)
    output_dir = os.path.join(frame_dir, 'denoised')
    
    final_exr_path = os.path.join(frame_dir, os.path.basename(exr_path))
    denoised_exr_path = os.path.join(frame_dir, 'denoised', os.path.basename(exr_path))

    # denoise_command_argv = [
    #     "/bin/bash",
    #     "-c",
    #     "PIXAR_LICENSE_FILE='9010@animlic.cs.byu.edu' "
    #     + "/opt/pixar/RenderManProServer-25.2/bin/denoise_batch "
    #     + f"--asymmetry {asymmetry} "
    #     + "--crossframe "
    #     + f"--frame-include {int((frame - crossframe_start) / frame_increment)} "
    #     + re.sub(r'\.\d{4}\.', '.####.', exr_path) + f" {crossframe_start}-{crossframe_end} "
    #     + f"--output {os.path.join(frame_dir, 'denoised')} "
    #     + "&& "
    #     + "/usr/bin/test "
    #     + "-f "
    #     + denoised_exr_path
    # ]

    frame_paths = [re.sub(r'\.\d{4}\.', f'.{frame_num:>04}.', exr_path) for frame_num in range(crossframe_start, crossframe_end + 1, frame_increment)]

    frame_conf = DenoiseConfig(
        files = frame_paths,
        asymmetry = asymmetry,
        output_dir = output_dir,
        frame_include = int((frame - crossframe_start) / frame_increment),
        passes = ['diffuse', 'specular', 'alpha', 'albedo'],
    ).to_json()
    config_path = os.path.join(output_dir, f"config.{frame:>04}.json")

    # Create the denoising config file
    denoise_frame_task.newCommand(argv=[
        "/bin/bash",
        "-c",
        f"/usr/bin/echo "
        + f"'{frame_conf}' "
        + "> "
        + f"'{config_path}' "
        + "&& "
        + "/usr/bin/test "
        + "-f "
        + f"'{config_path}'"
    ])

    # Denoise the frame (and verify that it was)
    denoise_frame_task.newCommand(argv=[
        "/bin/bash",
        "-c",
        "PIXAR_LICENSE_FILE='9010@animlic.cs.byu.edu' "
        + "/opt/pixar/RenderManProServer-25.2/bin/denoise_batch "
        + "-j "
        + f"'{config_path}'"
    ])

    # Transfer unique AOVs from the original frame to the denoised frame
    denoise_frame_task.newCommand(argv=create_aov_transfer_argv(exr_path, denoised_exr_path))

    # Move the denoised frame file to the final location
    denoise_frame_task.newCommand(argv=[f"/usr/bin/mv", denoised_exr_path, final_exr_path])

    # Add dependencies for denoising
    for dependency in dependencies:
        denoise_frame_task.addChild(dependency)
    
    return denoise_frame_task
    

def create_directory_task(directory: str) -> author.Task:
    directory_task_title = f"{os.path.basename(directory)} directory"
    directory_task = author.Task(title=directory_task_title)

    mkdir = [
        "/bin/bash",
        "-c",
        "/usr/bin/mkdir -p "
        + f"'{directory}'"
    ]

    directory_command = author.Command()
    directory_command.argv = mkdir
    directory_command.envkey = [ENV_KEY]
    directory_task.addCommand(directory_command)
    return directory_task
    

def get_source_type_index(node: hou.Node, source_num: int) -> int:
    return get_parm_int(node, 'sourceoptions' + str(source_num) + '1')


def get_source_type(node: hou.Node, source_num: int) -> str:
    return [
        'file',
        'node',
    ][get_source_type_index(node, source_num)]

def get_resolution(node: hou.Node, source_num: int) -> Sequence[int]:
    resolution_ctl = get_parm_str(node, 'noderesolutionctl', source_num)
    if resolution_ctl == 'custom':
        resolution_x = get_parm_int(node, 'noderesolution' + str(source_num) + 'x')
        resolution_y = get_parm_int(node, 'noderesolution' + str(source_num) + 'y')
    else:
        resolution_x, resolution_y = resolution_ctl.split('x')
    
    return [resolution_x, resolution_y]

def get_frame_range(node: hou.Node, source_num: int) -> Sequence[int]:
    source_type = get_source_type(node, source_num)
    trange = node.parm(
        source_type + 'trange' + str(source_num)
    ).evalAsString()

    frame_range = None

    if trange == 'file':
        if source_type == 'file':
            filepath = get_parm_str(node, 'filepath', source_num)
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

def get_fetch_node(node: hou.Node) -> hou.Node:
    return get_child_lop_node(node, 'fetch')

def get_prune_node(node: hou.Node) -> hou.Node:
    return get_child_lop_node(node, 'prune')

def get_camera_node(node: hou.Node) -> hou.Node:
    return get_child_lop_node(node, 'camera')

def get_motion_blur_node(node: hou.Node) -> hou.Node:
    return get_render_geo_settings_node(node, 'motionblur_rendergeometrysettings1')

def get_matte_node(node: hou.Node) -> hou.Node:
    return get_render_geo_settings_node(node, 'matte_rendergeometrysettings1')

def get_phantom_node(node: hou.Node) -> hou.Node:
    return get_render_geo_settings_node(node, 'phantom_rendergeometrysettings1')

def get_render_geo_settings_node(node: hou.Node, name: str) -> hou.Node:
    return get_child_lop_node(node, 'rendergeometrysettings', name)

def get_render_settings_node(node: hou.Node) -> hou.Node:
    return get_child_lop_node(node, 'hdprmanrenderproperties')

def get_usd_node(node: hou.Node) -> hou.Node:
    return get_child_lop_node(node, 'usd_rop')

def get_alembic_node(node: hou.Node) -> hou.Node:
    alembic_node_type = hou.nodeType(hou.ropNodeTypeCategory(), 'alembic')
    return get_child_node(node, child_type=alembic_node_type)

def get_ropnet(node: hou.Node) -> hou.Node:
    return get_child_lop_node(node, 'ropnet')

def get_child_lop_node(node: hou.Node, child_type_name: str, child_name: str = None) -> hou.Node:
    child_type = hou.nodeType(hou.lopNodeTypeCategory(), child_type_name)
    return get_child_node(node, child_name, child_type)

def get_child_node(node: hou.Node, child_name: str = None, child_type: hou.NodeType = None) -> hou.Node:
    matched_children = [
        child for child in node.children() if
            (child_name == None or child.name() == child_name) and
            (child_type == None or child.type() == child_type)
    ]

    if len(matched_children) == 1:
        return matched_children[0]
    else:
        raise Exception(f'Found more than one match for child node')
    

def update_source_nodes(node: hou.Node, source_num: int):
    for update_source_node in [
        update_fetch_node,
        update_render_settings_node,
    ]:
        update_source_node(node, source_num)


def update_layer_nodes(node: hou.Node, source_num: int, layer_num: int):
    for update_layer_node in [
        update_motion_blur_node,
        update_prune_node,
        update_matte_node,
        update_phantom_node,
        update_camera_edit_node,
        update_usd_node,
    ]:
        update_layer_node(node, source_num, layer_num)


def update_fetch_node(node: hou.Node, source_num: int) -> hou.Node:
    # Get the relevant options for the source
    input_index = get_parm_int(node, 'nodeindex', source_num)

    # Find the fetch node
    fetch_node = get_fetch_node(node)

    # Set the options on the fetch node
    fetch_expression: str = fetch_node.parm('loppath').rawValue()
    new_fetch = re.subn(r'(input_index\s*=\s*)(\d+|None)', r'\g<1>' + str(source_num - 1), fetch_expression)[0]
    fetch_node.parm('loppath').setExpression(new_fetch, hou.exprLanguage.Python)

    return fetch_node


def update_motion_blur_node(node: hou.Node, source_num: int, layer_num: int) -> hou.Node:
    # Get the relevant options for the layer
    motion_blur = get_parm(node, 'layermotionblur', source_num, layer_num)

    # Find the motion blur node
    motion_blur_node = get_motion_blur_node(node)

    # Set the options on the motion blur node
    motion_blur_node.parm('xn__primvarsriobjectmblur_cbbcg').setFromParm(motion_blur)

    return motion_blur_node


def update_prune_node(node: hou.Node, source_num: int, layer_num: int) -> hou.Node:
    # Get the relevant options for the layer
    exclude_parm = get_parm(node, 'layerexclude', source_num, layer_num)

    # Find the prune node
    prune_node = get_prune_node(node)

    # Set the options on the prune node
    prune_node.parm('primpattern1').setFromParm(exclude_parm)

    return prune_node


def update_matte_node(node: hou.Node, source_num: int, layer_num: int) -> hou.Node:
    # Get the relevant options for the layer
    matte_parm = get_parm(node, 'layermatte', source_num, layer_num)

    # Find the matte node
    matte_node = get_matte_node(node)

    # Set the options on the matte node
    matte_node.parm('primpattern').setFromParm(matte_parm)
    
    return matte_node


def update_phantom_node(node: hou.Node, source_num: int, layer_num: int) -> hou.Node:
    # Get the relevant options for the layer
    phantom_parm = get_parm(node, 'layerphantom', source_num, layer_num)

    # Find the phantom node
    phantom_node = get_phantom_node(node)

    # Set the options on the phantom node
    phantom_node.parm('primpattern').setFromParm(phantom_parm)

    return phantom_node


def update_render_settings_node(node: hou.Node, source_num: int) -> hou.Node:
    # Get camera settings
    camera = get_parm_str(node, 'nodecamera', source_num)
    resolution_x, resolution_y = get_resolution(node, source_num)
    
    # Get rendered image settings
    denoise = get_parm_bool(node, 'denoise')
    output_path_parm = get_parm(node, 'nodeoutputpath', source_num)

    sample_filter = 'PxrCryptomatte' if get_parm_bool(node, 'nodecryptomatteenable', source_num) else 'None'
    cryptomatte_layer_parm = get_parm(node, 'nodecryptomatteproperty', source_num)
    cryptomatte_attr_parm = get_parm(node, 'nodecryptomatteattribute', source_num)

    # Find the render settings node
    render_settings_node = get_render_settings_node(node)

    # Set the camera settings
    render_settings_node.parm('camera').set(camera)
    render_settings_node.parm('resolutionx').set(resolution_x)
    render_settings_node.parm('resolutiony').set(resolution_y)

    # Set rendered image settings
    render_settings_node.parm('enableDenoise').set(denoise)
    render_settings_node.parm('xn__driverparametersopenexrasrgba_bobkh').set(not denoise)
    render_settings_node.parm('picture').setFromParm(output_path_parm)

    render_settings_node.parm('xn__risamplefilter0name_w6an').set(sample_filter)
    render_settings_node.parm('xn__risamplefilter0PxrCryptomattelayer_cwbno').setFromParm(cryptomatte_layer_parm)
    render_settings_node.parm('xn__risamplefilter0PxrCryptomatteattribute_u2bno').setFromParm(cryptomatte_attr_parm)
    
    return render_settings_node


def update_camera_edit_node(node: hou.Node, source_num: int, layer_num: int) -> hou.Node:
    # Get the relevant options for the layer
    camera_parm = get_parm(node, 'nodecamera', source_num)
    do_dof = get_parm_int(node, f'layerdof{str(source_num)}_{str(layer_num)}')
    
    dof_control_setting = 'set' if do_dof == 0 else 'none'

    # Find the camera edit node
    camera_edit_node = get_camera_node(node)

    # Set the options on the camera edit node
    camera_edit_node.parm('primpattern').setFromParm(camera_parm)
    camera_edit_node.parm('fStop_control').set(dof_control_setting)

    return camera_edit_node


def update_alembic_node(node: hou.Node, source_num: int, camera_sop_path: str) -> hou.Node:
    # Get the relevant options for the source
    f1, f2, f3 = get_frame_range(node, str(source_num))

    # Find the alembic node
    alembic_node = get_alembic_node(get_ropnet(node))

    # Set the options on the alembic node
    alembic_node.parm('root').set('/obj')
    alembic_node.parm('objects').set(camera_sop_path)
    alembic_node.parm('f1').deleteAllKeyframes()
    alembic_node.parm('f2').deleteAllKeyframes()
    alembic_node.parm('f1').set(f1)
    alembic_node.parm('f2').set(f2)
    alembic_node.parm('f3').set(f3)
    
    return alembic_node

def update_usd_node(node: hou.Node, source_num: int, layer_num: int) -> hou.Node:
    # Set the $LAYER variable to the layer name
    layer_name = get_parm_str(node, f'layername{str(source_num)}_{str(layer_num)}')
    hou.hscript(
        f"set -g LAYER={layer_name}"
    )

    # Get the relevant options for the source
    usd_path = get_parm_str(node, f'usdpath{str(source_num)}_{str(layer_num)}')
    f1, f2, f3 = get_frame_range(node, str(source_num))
    strip_layer_breaks_parm = get_parm(node, 'striplayerbreaks', source_num, layer_num)
    error_saving_implicit_paths_parm = get_parm(node, 'errorsavingimplicitpaths', source_num, layer_num)

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
    usd_node.parm('striplayerbreaks').setFromParm(strip_layer_breaks_parm)
    usd_node.parm('errorsavingimplicitpaths').setFromParm(error_saving_implicit_paths_parm)

    return usd_node

def execute_usd(node: hou.Node, parm: hou.Parm):
   # Get the number of the source to render a USD for
    source_num, layer_num = parm.name().removeprefix('usdexecute').split('_')

    # Prepare for and render the USD
    usd_node = update_usd_node(node, source_num, layer_num)
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
    source_num, layer_num = parm.name().removeprefix('usdexecutebackground').split('_')

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
    pass
    # error_dict_parm: hou.Parm = node.parm('errordict')
    # errors: dict = error_dict_parm.eval()
    # errors.pop(parm_name, None)
    # error_dict_parm.set(errors)

    # warning_dict_parm = node.parm('warningdict')
    # warnings: dict = warning_dict_parm.eval()
    # warnings.pop(parm_name, None)
    # warning_dict_parm.set(warnings)


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
    source_num = script_multiparm_index

    SOURCE_TYPES = [
        'file',
        'node',
    ]

    source_type_labels = node.parm(
        'sourceoptions' + source_num + '1'
    ).parmTemplate().folderNames()

    type_parm: hou.Parm = get_parm(node, 'sourcetype', source_num)

    curr_type = SOURCE_TYPES[int(script_value)]
    prev_type = SOURCE_TYPES[type_parm.evalAsInt()]

    PARMTUPLE_BASE_NAMES = [
        'frame',
        'framerange',
    ]

    # Make the collapsed source display the current sourcetype, if not a file
    filepath_parm: hou.Parm = get_parm(node, 'filepath', source_num)
    filepathholder_parm = get_parm(node, 'filepathholder', source_num)
    if curr_type == 'file':
        # Copy filepath# from invisible parm
        filepath_parm.deleteAllKeyframes()
        filepath_parm.setFromParm(filepathholder_parm)
    else:
        # Copy filepath# to invisible parm
        filepathholder_parm.deleteAllKeyframes()
        filepathholder_parm.setFromParm(filepath_parm)

        # Set filepath# to the label of the current source type's tab
        source_label = source_type_labels[int(script_value)]

        if curr_type == 'node':
            # If the source is node input, add the index to the label
            source_label += ' ' + get_parm_str(node, 'nodeindex', source_num)
        
        filepath_parm.deleteAllKeyframes()
        filepath_parm.set(source_label)

    for parmtuple_base in PARMTUPLE_BASE_NAMES:
        prev_option_parmtuple: hou.ParmTuple = node.parmTuple(
            prev_type + parmtuple_base + source_num)

        for prev_option_parm in prev_option_parmtuple:
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
    #     ), f"Source {source_num} set to Node Input but no input is connected")
    #     return

    # unset_issues(node, parm.name())


def get_render_camera_path(node: hou.Node) -> str:
    # Determine the render camera
    ls = hou.LopSelectionRule(pattern='%rendercamera')
    return ls.expandedPaths(node.inputs()[0])[0].pathString


def update_layer_parms(
        node: hou.Node,
        parm: hou.Parm,
        script_value: str,
        script_multiparm_index: int,
        script_multiparm_index2: int,
        **kwargs
    ):

    layer_num = script_multiparm_index
    source_num = script_multiparm_index2

    def invert_primitive_pattern(primitive_pattern: str) -> str:
        return f'%children(%ancestors({primitive_pattern})) ^ {primitive_pattern}'
    
    def exclude_camera_from_pattern(primitive_pattern: str) -> str:
        return f"{primitive_pattern} ^ /scene/camera**"

    LAYER_PRESETS = {
        'anim': {
            'primitive': '/scene/anim',
        },
        'letty': {
            'primitive': '/scene/anim/letty',
        },
        'vaughn': {
            'primitive': '/scene/anim/vaughn',
        },
        'ed': {
            'primitive': '/scene/anim/ed',
        },
        'car': {
            'primitive': '/scene/anim/studentcar',
        },
        'layout': {
            'primitive': '/scene/layout',
        },
        'cops': {
            'primitive': '/scene/anim/cops',
        },
        'fx_sparks': {
            'primitive': '/scene/fx/sparks',
        },
        'fx_smoke': {
            'primitive': '/scene/fx/smoke',
        },
    }

    if script_value.startswith('preset:'):
        preset_string = script_value.split(':', 1)[-1]
        if preset_string.find('.') != -1:
            preset_name, preset_type = preset_string.split('.', 1)

            if preset_name in LAYER_PRESETS.keys():
                preset_pattern = exclude_camera_from_pattern(
                    invert_primitive_pattern(
                        LAYER_PRESETS[preset_name]['primitive']
                    )
                )

                clear_type = 'phantom' if preset_type == 'matte' else 'matte'

                parm.set(preset_name)
                get_parm(node, 'layer' + preset_type, source_num, layer_num).set(preset_pattern)
                get_parm(node, 'layer' + clear_type, source_num, layer_num).set('')



def get_layer_list():
    return [
        'preset:anim.matte', 'Anim (Matte)',
        'preset:anim.phantom', 'Anim (Phantom)',
        'preset:letty.matte', 'Letty (Matte)',
        'preset:letty.phantom', 'Letty (Phantom)',
        'preset:vaughn.matte', 'Vaughn (Matte)',
        'preset:vaughn.phantom', 'Vaughn (Phantom)',
        'preset:ed.matte', 'Ed (Matte)',
        'preset:ed.phantom', 'Ed (Phantom)',
        'preset:car.matte', 'Car (Matte)',
        'preset:car.phantom', 'Car (Phantom)',
        'preset:layout.matte', 'Layout (Matte)',
        'preset:layout.phantom', 'Layout (Phantom)',
        'preset:cops.matte', 'Cops (Matte)',
        'preset:cops.phantom', 'Cops (Phantom)',
        'preset:fx_sparks.matte', 'FX Sparks (Matte)',
        'preset:fx_sparks.phantom', 'FX Sparks (Phantom)',
        'preset:fx_smoke.matte', 'FX Smoke (Matte)',
        'preset:fx_smoke.phantom', 'FX Smoke (Phantom)',
        ]


def is_valid_aov_name(aov_name: str):
    return len(aov_name) > 1 or aov_name == 'a'


def get_invalid_aov_paths(stage) -> Sequence[str]:
    ls = hou.LopSelectionRule(pattern="%rendervars ~ (/* ^ /Render)")
    render_vars = ls.expandedPaths(stage=stage)
    invalid_aov_paths = [
        path.pathString for path in render_vars
        if not is_valid_aov_name(
            stage.GetAttributeAtPath(
                path.pathString + '.driver:parameters:aov:name'
            ).Get()
        )
    ]
    return invalid_aov_paths


def check_aov_names_error() -> int:
    return (
        get_parm_bool(hou.parent(), 'denoise') and
        len(hou.hscriptExpression("lopinputprims('.', 0)")) > 0
    )


def get_parm(
        node: hou.Node,
        parm_name: str,
        source_num: int = None,
        layer_num: int = None,
    ) -> hou.Parm:
    if source_num != None:
        parm_name += str(source_num)

        if layer_num != None:
            parm_name += '_' + str(layer_num)
    
    return node.parm(parm_name)

    
def get_parm_bool(
        node: hou.Node,
        parm_name: str,
        source_num: int = None,
        layer_num: int = None,
    ) -> bool:
    parm = get_parm(node, parm_name, source_num, layer_num)
    return bool(parm.evalAsInt())


def get_parm_float(
        node: hou.Node,
        parm_name: str,
        source_num: int = None,
        layer_num: int = None,
    ) -> float:
    parm = get_parm(node, parm_name, source_num, layer_num)
    return float(parm.eval())


def get_parm_int(
        node: hou.Node,
        parm_name: str,
        source_num: int = None,
        layer_num: int = None,
    ) -> int:
    parm = get_parm(node, parm_name, source_num, layer_num)
    return int(parm.evalAsInt())


def get_parm_str(
        node: hou.Node,
        parm_name: str,
        source_num: int = None,
        layer_num: int = None,
    ) -> str:
    parm = get_parm(node, parm_name, source_num, layer_num)
    return parm.evalAsString()

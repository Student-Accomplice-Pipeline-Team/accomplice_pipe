import hou
import importlib
from render import RenderSettings

# importlib.reload(render)
# import pipe.pipeHandlers.environment as env
import os, shutil

# for dist in __import__('pkg_resources').working_set:
#    print(dist.project_name.replace('Python', ''))


def test(node):
    pass


def buildLayers(node):
    node.allowEditingOfContents()
    # Environment object
    # e = env.Environment()
    # Delete nodes
    children = node.children()
    for child in children:
        child.destroy()
    # Get json data
    r = RenderSettings()
    AOVs = r.getAOVs()
    layerSettings = r.getLayers()
    # Check if any layers are written
    if node.parm("layer_count").eval() < 1:
        hou.ui.displayMessage("No layers built")
        return
    # For loop for each layer
    for i in range(1, node.parm("layer_count").eval() + 1):
        # Build layer check
        if node.parm("buildlayer" + str(i)).eval() == 0:
            continue
        # Get settings from node
        layerName = node.parm("layer_name" + str(i)).eval()
        # Check if layer has name
        if len(layerName) < 1:
            children = node.children()
            for child in children:
                child.destroy()
            hou.ui.displayMessage("Layer missing name\nBuild aborted")
            return
        # Settings continued
        matte = node.parm("matte_pattern" + str(i)).eval()
        phantom = node.parm("phantom_pattern" + str(i)).eval()
        dof = node.parm("dof" + str(i)).eval()
        motionBlur = node.parm("motion_blur" + str(i)).eval()
        # Get settings from json
        jsonSettings = None
        if (
            layerName == "beauty"
            and node.parm("low_quality_render" + str(i)).eval() == 1
        ):
            jsonSettings = layerSettings["low_quality"]["settings"]
        elif layerName in layerSettings:
            jsonSettings = layerSettings[layerName]["settings"]
        elif layerName.find("layout") != -1:
            jsonSettings = layerSettings["layout"]["settings"]
        elif layerName.find("fx") != -1:
            jsonSettings = layerSettings["fx"]["settings"]
        else:
            jsonSettings = layerSettings["basic"]["settings"]
        # Subnet input
        input = node.indirectInputs()[0]
        # Check/build node for depth of field
        if node.parm("dof" + str(i)).eval() == 0:
            dof_edit = node.createNode("camera", node_name="DOF_camera_edit")
            dof_edit.parm("primpath").set(node.parm("camera").eval())
            for p in dof_edit.parms():
                if p.name().find("control") != -1:
                    p.set("none")
            dof_edit.parm("aperture").set("none")
            dof_edit.parm("fStop_control").set("set")
            dof_edit.parm("fStop").set(0)
            dof_edit.setInput(0, input, 0)
            input = dof_edit
        # Check/build node for motion blur
        if node.parm("motion_blur" + str(i)).eval() == 0:
            mb_geo = node.createNode(
                "rendergeometrysettings", node_name="MOTION_BLUR_rendergeometrysettings"
            )
            mb_geo.parm("primpattern").set("/*")
            mb_geo.parm("xn__primvarsriobjectmblur_control_dobcg").set("set")
            mb_geo.parm("xn__primvarsriobjectmblur_cbbcg").set(0)
            mb_geo.setInput(0, input, 0)
            input = mb_geo
        # Build exclude prune node
        exclude_geo = node.createNode("prune", node_name="EXCLUDE_prune")
        exclude_geo.parm("method").set("deactivate")
        exclude_geo.parm("primpattern1").set(
            node.parm("exclude_pattern" + str(i)).eval()
        )
        exclude_geo.setInput(0, input, 0)
        input = exclude_geo
        # Build matte render geometry settings node
        mat_geo = node.createNode(
            "rendergeometrysettings", node_name="MATTE_rendergeometrysettings"
        )
        mat_geo.parm("primpattern").set(node.parm("matte_pattern" + str(i)).eval())
        mat_geo.parm("xn__primvarsriattributesRiMatte_control_4xbckc").set("set")
        mat_geo.parm("xn__primvarsriattributesRiMatte_3kbckc").set(1)
        mat_geo.setInput(0, input, 0)
        # Build phantom render geometry settings node
        pha_geo = node.createNode(
            "rendergeometrysettings", node_name="PHANTOM_rendergeometrysettings"
        )
        pha_geo.parm("primpattern").set(node.parm("phantom_pattern" + str(i)).eval())
        pha_geo.parm("xn__primvarsriattributesvisibilitycamera_control_sdcckk").set(
            "set"
        )
        pha_geo.parm("xn__primvarsriattributesvisibilitycamera_rzbckk").set(0)
        pha_geo.setInput(0, mat_geo, 0)
        # Build render properties node
        rprop = node.createNode("hdprmanrenderproperties")
        rprop.parm("camera").set(node.parm("camera").eval())
        rprop.parm("resolutionx").set(node.parm("resolutionx").eval())
        rprop.parm("resolutiony").set(node.parm("resolutiony").eval())

        if layerName == "beauty":
            name = node.parm("render_name" + str(i)).eval()
            rprop.parm("picture").set("$HIP/render/" + name + "/" + name + ".$F4.exr")
            # Make directory
            path = os.path.dirname(hou.hipFile.path()) + "/render/" + name
            if not os.path.exists(path):
                os.mkdir(path)
        else:
            rprop.parm("picture").set(
                "$HIP/render/" + layerName + "/" + layerName + ".$F4.exr"
            )
            # Make directory
            path = os.path.dirname(hou.hipFile.path()) + "/render/" + layerName
            if not os.path.exists(path):
                os.mkdir(path)
        rprop.parm("productType").set("openexr")
        rprop.setInput(0, pha_geo, 0)
        for AOV in AOVs:
            rprop.parm(AOV).set(1)
        for setting in jsonSettings:
            rprop.parm(setting).set(jsonSettings[setting])

        rprop.parm("xn__riintegratorname_01ak").set("PxrUnified")
        rprop.parm("xn__riRiPixelVariance_n3ac").set(0.05)  # pixel variance
        rprop.parm("xn__rihiderminsamples_n3af").set(16)  # min samples
        rprop.parm("xn__rihidermaxsamples_n3af").set(256)  # max samples
        # Build render rop
        usd_rop = node.createNode("usd_rop", node_name=layerName.upper() + "_usd_rop")
        usd_rop.parm("trange").set(1)
        usd_rop.parm("f1").set(node.parm("framerange_x"))
        usd_rop.parm("f2").set(node.parm("framerange_y"))
        usd_rop.parm("f3").set(node.parm("framerange_z"))
        usd_rop.parm("fileperframe").set(1)
        if layerName == "beauty":
            name = node.parm("render_name" + str(i)).eval()
            usd_rop.parm("lopoutput").set(
                "$HIP/renderUSD/" + name + "/" + name + ".$F4.usda"
            )
        else:
            usd_rop.parm("lopoutput").set(
                "$HIP/renderUSD/" + layerName + "/" + layerName + ".$F4.usda"
            )
        usd_rop.setInput(0, rprop, 0)

        # TEMP FIX [Matthew]
        # usd_rop.parm('errorsavingimplicitpaths').set(0)

        node.layoutChildren()
    hou.ui.displayMessage("Layers built successfully")


def get_usd_rops(node):
    usd_rop_list = []
    children = node.children()
    for child in children:
        if child.type().name() == "usd_rop":
            usd_rop_list.append(child)
    return usd_rop_list


def ribLayers(node):
    # Delete old ribs
    for usd_rop in get_usd_rops(node):
        save_path = usd_rop.parm("lopoutput").eval()
        rib_dir = os.path.dirname(save_path)
        if os.path.exists(rib_dir):
            for filename in os.listdir(rib_dir):
                file_path = os.path.join(rib_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print("Failed to delete %s, Reason %s" % (file_path, e))
    # Rib new ribs
    for usd_rop in get_usd_rops(node):
        print(usd_rop)
        usd_rop.parm("execute").pressButton()
    hou.ui.displayMessage("Ribbing process finished")


def submitTractorJob(node):
    # Delete old node
    tsl = node.node("tractor_submit_dir1")
    if tsl != None:
        tsl.destroy()
    # Get rop node list
    rops = get_usd_rops(node)
    # Stop if no rops
    if len(rops) < 1:
        hou.ui.displayMessage("No layers built\nJob not submitted")
        return
    # Create new node
    tsl = node.createNode("tractor_submit_dir")
    tsl.parm("jobtitle").set(node.parm("job_title"))
    # Fill out usd info
    tsl.parm("numDirs").set(len(rops))
    for i in range(1, len(rops) + 1):
        path = rops[i - 1].parm("lopoutput").eval()
        dir = os.path.dirname(path)
        tsl.parm("dir" + str(i)).set(dir)
    # Set priority
    tsl.parm("jobpriority").set(node.parm("jobpriority").eval())
    # Set blades
    if node.parm("submissionlist").eval() == "0":
        tsl.parm("submissionlist").set("0")
        tsl.parm("profile").set(node.parm("profile").eval())
    elif node.parm("submissionlist").eval() == "1":
        tsl.parm("submissionlist").set("1")
        tsl.parm("machines").set(node.parm("machines").eval())
    elif node.parm("submissionlist").eval() == "2":
        tsl.parm("submissionlist").set("2")
        tsl.parm("servicekey").set(node.parm("servicekey").eval())
    else:
        print(node.parm("submissionlist").eval())
    node.layoutChildren()
    # Submit job
    # print("tried to submit")
    tsl.parm("submit").pressButton()

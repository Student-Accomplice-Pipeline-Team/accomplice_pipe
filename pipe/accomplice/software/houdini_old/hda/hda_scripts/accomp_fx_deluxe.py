import hou


def build(node):
    node.allowEditingOfContents()
    cacheNodes = []
    # Get all uncache nodes
    for child in node.children():
        if child.type().name() == "uncache":
            cacheNodes.append(child.name())
        elif child.type().name() == "switch":
            cacheNodes.append(child.name())
    # Delete cache nodes
    for fx in cacheNodes:
        print(cacheNodes)
        node.node(fx).destroy()
        cacheNodes = []
    for i in range(1, node.parm("fxlist").eval() + 1):
        # Get FX info
        name = node.parm("fxname" + str(i)).eval()
        sopPath = node.parm("soppath" + str(i)).eval()
        primPath = node.parm("primpath").eval()
        # Check for incomplete asset definitions
        if len(name) == 0 or len(sopPath) == 0 or len(primPath) == 0:
            hou.ui.displayMessage("Incomplete Asset Definition")
            return
        # Create cache hda
        cache = node.createNode("uncache", node_name=name)
        cache.allowEditingOfContents()
        cache.parm("framerangex").set(node.parm("framerange_" + str(i) + "x"))
        cache.parm("framerangey").set(node.parm("framerange_" + str(i) + "y"))
        cache.parm("framerangez").set(node.parm("framerange_" + str(i) + "z"))
        cache.parm("fxname").set(node.parm("fxname" + str(i)))
        cache.parm("soppath").set(node.parm("soppath" + str(i)))
        cache.parm("primpath").set(node.parm("primpath"))
        cache.parm("fxdir").set("env")
        # Change settings for volume caching
        if node.parm("vol" + str(i)).eval() == 1:
            usd_rop = cache.node("usd_rop")
            usd_rop.parm("lopoutput").set(
                '$HIP/fx/`chs("../fxdir")`/`chs("../fxname")`/`chs("../fxname")`.usda'
            )
            # usd_rop.parm('savestyle').set('flattenimplicitlayers')
            usd_rop.parm("fileperframe").set(0)
            reference = (
                cache.node("reference1")
                .parm("filepath1")
                .set(
                    '$HIP/fx/`chs("../fxdir")`/`chs("../fxname")`/`chs("../fxname")`.usda'
                )
            )
        # Reference primitive path
        ref = (
            cache.node("reference1")
            .parm("primpath")
            .set("/" + node.parm("primpath").eval().split("/")[1])
        )
        # Visibility, preview, and velocity blur settings
        vis(node, node.parm("vis" + str(i)))
        preview(node, node.parm("preview" + str(i)))
        vel_blur(node, node.parm("velocity_blur" + str(i)))
        # Create frame range switch
        switch = node.createNode("switch", node_name=name + "_frame_range_switch")
        switch.parm("input").setExpression(
            "($F<"
            + str(node.parm("framerange_" + str(i) + "x").eval())
            + ")||($F>"
            + str(node.parm("framerange_" + str(i) + "y").eval())
            + ")",
            language=hou.exprLanguage.Hscript,
        )
        # switch.parm('ch("../fxlist")')
        switch.setInput(0, cache, 0)
    # Get switch nodes
    for child in node.children():
        if child.type().name() == "switch":
            cacheNodes.append(child.name())
    # Connect cache hdas to merge
    merge = node.node("merge")
    for input in merge.inputs():
        merge.setInput(0, None)
    input = node.indirectInputs()[0]
    merge.setInput(0, input, 0)
    for i in range(len(cacheNodes)):
        merge.setInput(i + 1, node.node(cacheNodes[i]), 0)
    # Change material save path
    mat_file_name = node.parm("primpath").eval().split("/")[-1]
    if len(mat_file_name) == 0:
        mat_file_name = node.parm("primpath").eval().split("/")[-2]
    node.node("configure_mat_layer").parm("savepath").set(
        "$HIP/fx/env/" + mat_file_name + ".usda"
    )
    node.layoutChildren()
    hou.ui.displayMessage("Networks Built")


def vis(node, parm):
    num = parm.name().replace("vis", "")
    name = node.parm("fxname" + num).eval()
    cache = node.node(name)
    vis = cache.node("visibility")
    vis.parm("input").set(parm.eval())


def preview(node, parm):
    num = parm.name().replace("preview", "")
    name = node.parm("fxname" + num).eval()
    cache = node.node(name)
    vis = cache.node("preview")
    vis.parm("input").set(parm.eval())


def cache(node, parm):
    num = parm.name().replace("cache", "")
    name = node.parm("fxname" + num).eval()
    cache = node.node(name)
    cache.node("usd_rop").parm("execute").pressButton()
    if (node.parm("vol" + num)).eval() == 0:
        stitch = cache.node("ropnet").node("usdstitchclips")
        stitch.parm("execute").pressButton()


def vel_blur(node, parm):
    num = parm.name().replace("velocity_blur", "")
    name = node.parm("fxname" + num).eval()
    cache = node.node(name)
    vel = cache.node("rendergeometrysettings1")
    if parm.eval() == 0:
        vel.parm("xn__primvarsriobjectvblur_cbbcg").set("No Velocity Blur")
    elif parm.eval() == 1:
        vel.parm("xn__primvarsriobjectvblur_cbbcg").set("Velocity Blur")


def stitch(node, parm):
    num = parm.name().replace("stitch", "")
    name = node.parm("fxname" + num).eval()
    cache = node.node(name)
    stitch = cache.node("ropnet").node("usdstitchclips")
    stitch.parm("execute").pressButton()


def unlock(node):
    node.allowEditingOfContents()

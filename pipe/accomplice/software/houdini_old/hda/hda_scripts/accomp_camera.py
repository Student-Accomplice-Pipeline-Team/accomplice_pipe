import hou
import os

def updateCamera(node):
    node.allowEditingOfContents()
    
    uncameraObjNet = hou.node(node.path() + '/objnet') # path to objnet
    
    # get existing camera in objnet if there is one
    existing_camera = None
    if len(uncameraObjNet.children()) > 1:
        # iterate over the children nodes of the objnet to find the camera node
        objnet_children = uncameraObjNet.children()
        for child in objnet_children:
            # find the camera node as the one with camera in the title
            if 'camera' in child.name():
                existing_camera = child
                break
                
    # if there is an exisitng camera, see if the user really wants to override it
    if existing_camera is not None:
        message = 'Do you want to reimport the camera from the fbx on disk? \nThis will erase any camera changes done in Houdini.'
        button0 = 'yes'
        button1 = 'no'
        title = 'FBX Import'

        userInput = hou.ui.displayMessage(message,buttons=(button0,button1),title=title)
        #Stop process if the user does not want to reimport
        if userInput == 1:
            return
        #Delete old camera if reimporting
        uncameraObjNet.deleteItems([existing_camera])
        
    # Import fbx file into obj context
    # find an fbx file in the camera directory the HIP file is in
    hip = os.path.dirname(hou.hipFile.path()) # hip directory
    for file in os.listdir(os.path.join(hip, 'camera')):
        if file[-len('.fbx'):] == '.fbx':
            fbx_filename = file
    if fbx_filename is None:
        # No camera found (no file with extension fbx in camera directory)
        print("Camera file not found in \'camera\' folder. Make sure there is an fbx file there to import.")
        hou.NodeError("Camera file not found in \'camera\' folder. Make sure there is an fbx file there to import.")
    
    fbx_path = os.path.join('$HIP', 'camera', fbx_filename)
    
    # import fbx using hscript
    # options: -k for keyframe animations, -i import as subnet
    hscriptCommand = 'fbximport -k on -a maya -i off ' + fbx_path
    hou.hscript(hscriptCommand)
    
    # Move obj context camera subnet into the correct lop objnet
    fbx_nodename = fbx_filename.replace(".", "_")
    objContextCameraSubnet = hou.node('/obj/' + fbx_nodename)
    cameraSubnet = hou.moveNodesTo([objContextCameraSubnet], uncameraObjNet)[0]
    
    # add the rescaling null to the camera
    topNode = cameraSubnet.children()[0]
    scaleNull = cameraSubnet.createNode('null', node_name = 'scaling_fix')
    scaleNull.parm('scale').set(0.01)
    topNode.setInput(0, scaleNull, 0)
    
    # get the camera
    for camNode in cameraSubnet.children():
        if camNode.type().name() == 'cam':
            # if camNode.name().find('Shake') == -1:
            camera = camNode
    
    # delete camera children -- WHY?
    for delNode in camera.outputs():
        delNode.destroy()
        
    # fix the clipping plane
    mayaClip = camera.parm('near').eval()
    camera.parm('near').set(mayaClip * 0.01)
    
    # fix camera aspect ratio
    # FIXME: what is our aspect ratio?
    camera.parm('resy').set(692)
    
    cameraSubnet.layoutChildren()
    
    # reenter scene import parameter to make the camera appear
    sceneImport = node.node('camera')
    # rename the parameter based on the actual camera name
    objects = sceneImport.parm('objects')
    objects.set('../objnet/' + fbx_nodename + "/*")
    parm = sceneImport.parm('objects').eval()
    sceneImport.parm('objects').set(parm)

    # update the uncamera/camera scene import
    
    # return user to the stage context
    node.setPicked(1)
    hou.ui.displayMessage('Camera FBX Imported from disk')

def exportUSD(node):
    camrop = node.node('CAM_ROP')
    camrop.parm('execute').pressButton()
    #hou.ui.displayMessage('Camera USD exported')
    

def reloadUSD(node):
    usdImport = node.node('usd_import')
    usdImport.parm('reload').pressButton()

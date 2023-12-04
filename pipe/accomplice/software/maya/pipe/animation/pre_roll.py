'''
INSTRUCTIONS:
1. Set the variables below to what you want them to be
2. Run the script to color the timeline and set-up all the automatic pre-roll

NOTE: Coloring timeline section requires TimelineMarker to be installed: https://github.com/robertjoosten/maya-timeline-marker
NOTE: Uses StudioLibrary to apply the A-Pose
'''




#anim_dur        = 127 #temporarily overriden below by user input

preHandle_start = 1001

#in order:
aPose_dur       = 21
aToWindup_dur   = 24
windupPose_dur  = 11
windup_dur      = 15
preHandle_dur   = 5
postHandle_dur  = 5






import maya.cmds as cmds

prompt_dialog = "integerPromptDialog"
if cmds.window(prompt_dialog, exists=True):
    cmds.deleteUI(prompt_dialog)

ans = cmds.promptDialog(
    title="Accomplice Pre-Roll Auto-Setup",
    message="This Shot Anim Duration (in frames):",
    button=["OK", "Cancel"],
    defaultButton="OK",
    cancelButton="Cancel",
    dismissString="Cancel"
)
if ans == 'Cancel':
    mc.error('Canceled by user')

anim_dur = cmds.promptDialog(query=True, button=True)
try:
    anim_dur = int(anim_dur)
except:
    mc.error('Something other than a number was entered')

'''
if mc.playbackOptions(max=True,q=True) > 1000:
    anim_dur = mc.playbackOptions(max=True,q=True) - 1000
else:
    anim_dur = mc.playbackOptions(max=True,q=True)
'''

aPose_start = preHandle_start-windup_dur-windupPose_dur-aToWindup_dur-aPose_dur
aToWindup_start = preHandle_start-windup_dur-windupPose_dur-aToWindup_dur
windupPose_start = preHandle_start-windup_dur-windupPose_dur
windup_start = preHandle_start-windup_dur
# prehandle_start
anim_start = preHandle_start+preHandle_dur
postHandle_start = preHandle_start+preHandle_dur+anim_dur

#Select all anim curves in scene
import maya.cmds as mc
anim_curves = mc.ls(type=['animCurveTA', 'animCurveTL', 'animCurveTT', 'animCurveTU'])

objects_with_anim_list = []
for anim_curve in anim_curves:
    object = mc.listConnections(anim_curve, destination=1, shapes=0)
    if object is not None:
        object = object[0]
        if object not in objects_with_anim_list:
            objects_with_anim_list.append(object)

mc.select(objects_with_anim_list, replace=1)
objsWithKeyframes = mc.ls(sl=True)
mc.select(objsWithKeyframes)

#Set the timeline view to be from "aPose_start" to the last frame of "postHandle_duration"
timelineStart = mc.playbackOptions(min=True,q=True)
timelineEnd = mc.playbackOptions(max=True,q=True)

mc.playbackOptions(min=aPose_start)
mc.playbackOptions(animationStartTime=aPose_start)

mc.playbackOptions(max=postHandle_start+postHandle_dur-1)
mc.playbackOptions(animationEndTime=postHandle_start+postHandle_dur-1)

#Color the timeline
from timeline_marker.ui import TimelineMarker
def colorFrames(frames,color,comment):
    if color == 'red':
        colorVal = (225,0,0)
    elif color == 'purple':
        colorVal = (130,0,225)
    elif color == 'dark blue':
        colorVal = (0,0,225)
    elif color == 'light blue':
        colorVal = (0,225,225)
    elif color == 'yellow':
        colorVal = (225,225,0)
    elif color == 'green':
        colorVal = (0,50,0)
    for frame in range(int(frames[0]),int(frames[1])+1):
        TimelineMarker.add(frame,colorVal,comment)

TimelineMarker.clear()
colorFrames([aPose_start,aToWindup_start-1],                     'red',   'A Pose')
colorFrames([aToWindup_start,windupPose_start-1],                'purple','A Pose -> Windup Pose')
colorFrames([windupPose_start,windup_start-1],                   'dark blue','Windup Pose')
colorFrames([windup_start,preHandle_start-1],                    'light blue',  'Windup')
colorFrames([preHandle_start,anim_start-1],                      'yellow','Pre-Handle')
colorFrames([anim_start,postHandle_start-1],                     'green', 'Anim')
colorFrames([postHandle_start,postHandle_start+postHandle_dur-1],'yellow','Post-Handle')

#Set full scene keyframe on pre-handle start frame
mc.currentTime(preHandle_start)
mc.select(objsWithKeyframes)
mc.setKeyframe()

#Set full scene keyframe on windupPose start frame
mc.currentTime(windupPose_start)
mc.select(objsWithKeyframes)
mc.setKeyframe()

#Set full scene keyframe on windup start frame
mc.currentTime(windup_start)
mc.select(objsWithKeyframes)
mc.setKeyframe()

#Put Letty in A Pose and set full scene keyframe on A Pose start frame and Windup Pose start frame
import sys
if '/groups/accomplice/pipeline/lib/studiolibrary' not in sys.path:
    sys.path.insert(0, '/groups/accomplice/pipeline/lib/studiolibrary')
import studiolibrary
studiolibrary.setLibraries([{'name': 'Accomplice Poses', 'path': r'/groups/accomplice/anim/pose-library', 'default': True, 'theme': {'accentColor': 'rgb(3,252,211)',},},])
import mutils

mc.currentTime(preHandle_start)
mc.select(objsWithKeyframes)
mc.setKeyframe()

def preRollPose(character,ns='',aPose=False,ik=True,objsWithKeyframes=objsWithKeyframes):
    
    if ns == '':
        ns = character
    if character == 'letty':
        if aPose == True:
            if ik == True:
                path = r"/groups/accomplice/anim/pose-library/PREROLL_POSES/Letty_APOSE_IK.pose/pose.json"
            elif ik == False:
                path = r"/groups/accomplice/anim/pose-library/PREROLL_POSES/Letty_APOSE_FK.pose/pose.json"
        else:
            path = r"/groups/accomplice/anim/pose-library/PREROLL_POSES/Letty_TPOSE.pose/pose.json"
    elif character == 'ed':
        path = r"/groups/accomplice/anim/pose-library/PREROLL_POSES/Ed_TPOSE.pose/pose.json"
    elif character == 'vaughn':
        path = r"/groups/accomplice/anim/pose-library/PREROLL_POSES/Vaughn_TPOSE.pose/pose.json"
    
    pose = mutils.Pose.fromPath(path)
    
    mc.currentTime(aPose_start)
    try:
        pose.load(namespaces=[ns])
    except:
        print('Character: "' + character + "' not found in scene")
        return
    try:
        mc.matchTransform(ns+':root_CTRL','heroCar'+':worldForward_CTRL')
    except:
        mc.warning('heroCar not found in scene')
    mc.select(objsWithKeyframes)
    mc.setKeyframe()
    
    mc.currentTime(aToWindup_start)
    pose.load(namespaces=[ns])
    try:
        mc.matchTransform(ns+':root_CTRL','heroCar'+':worldForward_CTRL')
    except:
        mc.warning('heroCar not found in scene')
    mc.select(objsWithKeyframes)
    mc.setKeyframe()


preRollPose(character='letty')
lettyIkFk = mc.getAttr('letty:SWITCH_ARM_CTRL_R.Arm_IK')
preRollPose(character='letty',aPose=True,ik=lettyIkFk)

#preRollPose(character='ed',ns='ed1')
preRollPose(character='ed')
preRollPose(character='vaughn')

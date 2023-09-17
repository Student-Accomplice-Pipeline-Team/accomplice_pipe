# Student Accomplice Pipeline

## Description
This is the pipeline for BYU Animation's *Student Accomplice (2024)* short film, and is a fork of the [previous film's pipeline](https://github.com/gabrieljreed/unfamiliar_pipe).

Development started on *CentOS 7*, but final deployment is intended for a *RHEL 8* derivative.

Since all of the film's files are on the department's fileserver and mounted at `/groups/accomplice/` in the TMCB animation and gaming labs, this pipeline has no need for and so does not provide tools for sharing assets between users/computers.

### Setting up a dev environment in the labs
1. Generate a GitHub SSH key and upload it to your GitHub
   - ```bash
     ssh-keygen -t ed25519 -C "yourgithubemail@email.com"
     cat ~/.ssh/github.pub
     ```
   - When it asks for a path, type '/users/animation/yournetid/.ssh/github'
   - Only provide a passphrase if you want to type that every time you push or pull
   - Go to https://github.com/settings/keys and add the contents of `~/.ssh/github.pub` as a **New SSH key**
1. Make a local copy of the git repo
   ```bash
   cd ~/Documents
   git clone -c core.sshCommand='ssh -i ~/.ssh/github' git@github.com:Student-Accomplice-Pipeline-Team/accomplice_pipe.git
   cd accomplice_pipe
   ```
1. Configure the git repo to use the new SSH key and our git hooks
   ```bash
   git config --add --local core.sshCommand 'ssh -i ~/.ssh/github'
   git config --local core.hooksPath .githooks/
   ```
1. Check out your personal dev branch
   ```bash
   git checkout -B yourname-dev 
   # don't need -B if it already exists
   git push --set-upstream origin yourname-dev
   ```

### Using your personal dev environment
1. Make changes the code. Edit the pipe code, modify some shelf tools, whatever your heart desires.
1. If you want, you can periodically take snapshots of your work with `git commit`.
   1. Save your work
   1. Stage your changes with `git add path/to/file1 path/to/file2 ...`
   1. Commit your chages with `git commit -m "Message explaining what changes I made"`
   1. Push your changes up to GitHub with `git push`
1. *Test* your changes. Make sure everything works the way you think it should and that nothing new is broken. 
1. When your changes are ready to be added to production, create a *pull request* to merge your code into the `prod` branch of the GitHub repository:
   1. Make sure that your changes don't conflict with changes someone else has already made. Run `git pull origin prod` to make sure you have the most recent chages to the `prod` branch downloaded.
      - If git encounters an error downloading the most recent changes, it will tell you what the problem is and you'll need to resolve it before continuing.
   1. Once you have successfully run `git pull origin prod`, commit and push all your changes if you haven't already done so (see step 2)
   1. Next, go to the project page on GitHub and switch from `prod` to your dev branch (top left, underneath the name of the repo). If you have committed and pushed correctly, you should see a message that says something like "This branch is *X commit(s) ahead of prod.". Click on the *Contribute* button and press *Open pull request*
   1. Name your pull request and write a small description of what changes you are making. 
   1. Make sure the merge mode is set to *Squash and merge*, then click the big green button to merge your changes into `prod`.
   1. Finally, navigate to `/groups/accomplice/pipeline` and run `git pull` to update production code with your changes.

## Table of Contents
- [Usage and features](#usage--features) (for artists)
  - [Maya](#maya)
  - [Houdini](#houdini)
  - [Nuke](#nuke)

- [Development](#development) (for programmers)
  - [Maya](#autodesk-maya-2023)
  - [Houdini](#sidefx-houdini-195)
  - [Nuke](#nuke-1)

## Usage & Features
<!-- TODO: Update for Student Accomplice -->
<!--
### Maya
Unmaya can be started by clicking the unmaya icon in the `icons` folder or running the `maya.sh` script directly, (e.g. `/groups/unfamiliar/anim_pipeline/launch/maya.sh`).
#### Shelves
UnMaya provides several custom shelves with functionality specifically for Unfamiliar and other silly things.
- UnAnim
  - **Kelleth:** References the Kelleth rig into the current scene
  - **Maggie:** References the Maggie rig into the current scene
  - **Singe:** References the Singe rig into the current scene
  - **Dolls:** References the dolls rigs into the current scene
  - **Frog:** References the frog rig into the current scene
  - **Amogus:** References the Amogus rig into the current scene
  - **Previous Rig:** Launches a dialog to reference a previous version of a rig into current scene
  - **Layout:** Imports the USD layout into the current scene
  - **Cam:** References the exported production camera
  - **Prod Ref:** Converts a selected prop in the USD layout into an FBX reference that can be animated on
  - **Ref:** Refreshes all prop references to their most recent USD version
  - **Export Alembic:** Launches a dialog to export the current shot as an alembic and publish it into the pipe
  - **StudioLibrary:** Loads the StudioLibrary plugin for animators
  - **Discord:** Launches the Maya to Discord tool
  - **AnimBot:** Loads the AnimBot plugin for animators
- UnPipe
  - **Get Asset List:**  
  - **Get Shot List:**
- UnRig
  - **Publish:** Publishes a rig and versions it in its correct location within the `production` folder
- UnFiles
  - **Checkout:** Launches a dialog to check out a shot
  - **Publish:** Publishes a shot
- UnDev
  - **Debug:** Launches a debug session using `debugpy` that can be attached to with VS Code. 
  - **Unload:** Unloads all python packages allowing for code refreshes without having to reopen Maya.
  - **Report:** Launches a dialog allowing the user to report an issue on the Github page. 
- UnPrevis
  - **Import DAG:** brings model in as a Maya shape
  - **Export DAG:** bakes animation back into USD (very buggy!)
  - **Cam FBX:** exports camera for both Unreal and production
  - **Unreal Export:** Maya to Unreal export tool dialog


### Houdini
Undini can be started by clicking the undini icon in the `icons` folder or running the `houdini.sh` script directly, (e.g. `/groups/unfamiliar/anim_pipeline/launch/houdini.sh`).

#### File menu
Undini provides a custom file menu, UnPipe, that provides shot functionality. 
 - **Shot>Checkout:** checks out a shot 
 - **Shot>Return:** returns a shot

#### Shelves
Undini provides several custom shelves with functionality specifically for Unfamiliar. 
 - UnAnim
   - **Layout:** brings in an `unlayout` node that imports the USD layout
   - **Singe:** brings in an `unanim` node that imports the Singe model. Also warns the user if they have not checked out a shot.
   - **Maggie:** brings in an `unanim` node that imports the Maggie model. Also warns the user if they have not checked out a shot.
   - **Kelleth:** brings in an `unanim` node that imports the Kelleth model. Also warns the user if they have not checked out a shot.
 - UnShading
   - Edit Model
   - Edit Shader
   - Build Shader
   - Txmake Repath
   - Tex Delete


#### Nodes
UnDini defines many custom nodes with functionality specifically for Unfamiliar.
 - **unlayout:** imports the USD layout with the correct scale.
 - **uncamera:** brings the camera in to an OBJ context and allows for exporting into the pipeline.
 - **unanim:** imports a specified character for animation.
 - **untpose:** imports a character in t-pose at the correct scale.
 - **unfx:** ask Brendan
 - **uncloth:** used by the `unfx` node
 - **unhair:** used by the `unfx` node


### Nuke



## Development
This pipeline consists of toolsets for several DCC packages. 


### Autodesk Maya 2023
The `maya.sh` file found in the `launch/` folder is a bash script that sets many environment variables and settings for Maya before launching it. 
The `userSetup.py` file located in the `pipe` folder sets up the custom shelves and keyboard shortcuts that turn Maya into the unmaya we all know and love.

It can be started by running the script directly, (e.g. `/groups/unfamiliar/anim_pipeline/launch/maya.sh`) or clicking the unmaya icon in the `icons` folder.

To edit Maya environment variables, make changes within the `maya.sh` file.

To add a new shelf, create a json file within `/pipe/tools/maya/custom`. It will be automatically detected when unmaya launches. 

To add a button to the shelf, add a new JSON entry (see other buttons for examples). It will be automatically detected when unmaya launches. Button icons are located in the `icons` folder and should be pathed relative to that folder (e.g. an icon located at `/icons/discordIcons/desktop.png` should have its path provided as `"discordIcons/desktop.png"`)

To create a new keyboard shortcut, add a new entry to `/pipe/tools/maya/UnDev/setupHotkeys.py` at the bottom of the file such that it is added to the unfamiliarHotkeySet. Make sure to not overwrite any existing keyboard shortcuts, since this change will propogate to everybody and could destroy expected functionality.

### SideFX Houdini 19.5

### Nuke
-->

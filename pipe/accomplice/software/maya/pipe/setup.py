import http.client
import os
import time

import maya.cmds as cmds
import maya.mel as mel

from pathlib import Path

import pipe.shelves

# Initialize the custom Maya UI elements after the UI is fully loaded
#cmds.evalDeferred("import pipe.tools.maya.ui")

#from requests import Response

#from pipe.shared.env.vars import SERVER_PORT
#from pipe.shared.server import ServerSession

#from . import pipe  # For coding
#import pipe         # For runtime

#pipe.get_asset('ed')

#conn = pipe._get_connection()
#conn.request('GET', '/')
#conn.getresponse()

#conn.request('GET', '/something')
#conn.getresponse()


#pipe._get_session().get('/')
#pipe._get_session().get('/test1')

#pipe.register()
#pipe.request_cmdport()

#server_port = os.getenv(SERVER_PORT)


# Notify the proxy of which port is the command port
# with ServerSession(server_port) as s:
#     response = s.post('/software/register')
    #response.

# conn = http.client.HTTPConnection('localhost', server_port)
# conn.request('PUT', '/')
# r1 = conn.getresponse()
# print(r1.status, r1.reason)

# time.sleep(10)
# conn.request('POST', '/', 'exit')
# r2 = conn.getresponse()
# print(r2.status, r2.reason)
# conn.close()


# # Open the command port
# if not cmds.commandPort(':' + cmd_port, query=True):
#     cmds.commandPort(name=':' + cmd_port)

# # Create job to clean up the command port when Maya exits
# cmds.scriptJob(
#     event=['quitApplication',
#            f"cmds.commandPort(name=':{cmd_port}', close=True)"],
#     permanent=True
# )

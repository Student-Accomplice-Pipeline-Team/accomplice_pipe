"""The interface for BYU's Student Accomplice (2024) film pipeline."""

from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from .software.baseclass import ProxyHTTPRequestHandler

__all__ = []

import logging
import os
import time
import glob
from enum import Enum
from http.server import HTTPServer, HTTPStatus
from queue import Queue
from threading import Thread
from typing import Mapping, Any, MutableSet, MutableSequence

from baseclass import SimplePipe

#from .sg_config import SG_CONFIG
#from database.ShotGridDatabase import ShotGridDatabase

from . import software
from .software.interface import SoftwareProxyInterface
from urllib.parse import urlparse, parse_qs

log = logging.getLogger(__name__)

# One proxy per software instance, or one proxy per software package?
#   PER INSTANCE:
#   Pros:
#       No extra data required for identification
#   Cons:
#       Potential for unnecessary processes
#
#   PER PACKAGE:
#   Pros:
#       Centralized management
#       Efficieny
#   Cons:
#       Figuring out which instance sent what

# Communicate with proxies through queues or sockets?
#   QUEUES
#   Pros:
#       Clear hierarchy and linking
#       Standard for threading
#   Cons:
#       Figuring out polling sockets and queues at the same time
#
#   SOCKETS
#   Pros:
#       Allows proxies to be launched at will
#       Bidirectional, so it's easy to tell which proxy sent what
#   Cons:
#       Disconnects the pipe and software proxies
#       Seems overcomplicated?

# IDEAL
#   Pipe communicates to proxies through function calls, and the proxies
#   handle everything else internally
#
#   Proxies communicate to pipe via...? (see above)
#       Not function calls because then they're dependent on the pipe
#
#   Software instances open command ports to receive commands from the
#   proxies and connect to the proxies' sockets to make requests
#       Maya: https://www.xingyulei.com/post/maya-commandport/
#       Houdini: https://www.sidefx.com/docs/houdini/commands/openport.html
#       Nuke: https://github.com/TomMinor/Nuke-CommandPort
#
#   When inside software, ``import pipe`` imports the software's pipe tools


class PipeRequestHandler(BaseHTTPRequestHandler):
    pipe = None

    def __init__(self, pipe: SimplePipe, *args) -> None:
        self.pipe = pipe
        super().__init__(*args)

    def send_okay(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        log.info(f"Handling GET request with path {self.path}")

        try:
            url = urlparse(self.path)

            if url.path == '/assets':
                assets = self.pipe.get_assets(parse_qs(url.query))
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()

                asset_data = ''
                for asset in assets:
                    asset_data += asset + ','
                if asset_data.endswith(','):
                    asset_data = asset_data[:-1]

                self.wfile.write(asset_data.encode('utf-8'))
            elif url.path == '/shots':
                shots = self.pipe.get_shots(parse_qs(url.query))
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()

                shot_data = ''
                for shot in shots:
                    shot_data += shot + ','
                if shot_data.endswith(','):
                    shot_data = shot_data[:-1]

                self.wfile.write(shot_data.encode('utf-8'))
            else:
                self.send_response(HTTPStatus.NOT_IMPLEMENTED)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
        except Exception as ex:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, message=ex.__str__)
            

        # Get the request content, if any
        # content_len = int(self.headers.get('Content-Length', failobj=0))
        # if content_len > 0:
        #     content = self.rfile.read(content_len)
        #     try:
        #         encoding = self.headers.get('Content-Encoding', 'utf-8')
        #         content = content.decode(encoding)
        #     except UnicodeDecodeError:
        #         log.error("Could not decode data", exc_info=True)
        #         self.send_error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        #         return

        # self.send_response(200)
        # self.send_header('Content-type', 'text/html')
        # self.end_headers()
        # log.info(f"GET request, Path: {self.path}\nHeaders:\n{self.headers}\n")


class AccomplicePipe(SimplePipe):
    """BYU's Student Accomplice (2024) pipeline."""

    asset_lookup: dict = {
        ### Props
        # Hero
        'clipboard':    '/props/hero/clipboard',
        'gun':          '/props/hero/gun',
        'moneybag':     '/props/hero/moneybag',
        'pen':          '/props/hero/pen',
        'trashcan':     '/props/hero/trashcan',
        'trashcanlid':  '/props/hero/trashcanlid',

        # Generic
        'broom':        '/props/generic/broom',

        ### Environment
        # Buildings: Hero
        'bank':             '/environment/buildings/hero/bank',
        'policestation':    '/environment/buildings/hero/policestation',

        # Buildings: Generic
        'bookshop':         '/environment/buildings/generic/bookshop',
        'chickenshop':      '/environment/buildings/generic/chickenshop',
        'coffeeshop':       '/environment/buildings/generic/coffeeshop',
        'flowershop':       '/environment/buildings/generic/flowershop',
        'movietheatre':     '/environment/buildings/generic/movietheatre',
        'oystershop':       '/environment/buildings/generic/oystershop',

        # Buildings: Components
        'entrance':         '/environment/buildings/components/entrance',
        'door':             '/environment/buildings/components/door',
        'cornerbase':       '/environment/buildings/components/cornerbase',
        'cornermiddle':     '/environment/buildings/components/cornermiddle',
        'cornertop':        '/environment/buildings/components/cornertop',
        'ledgebottom':      '/environment/buildings/components/ledgebottom',
        'ledgemiddle':      '/environment/buildings/components/ledgemiddle',
        'ledgetop':         '/environment/buildings/components/ledgetop',
        'steps':            '/environment/buildings/components/steps',
        'window':           '/environment/buildings/components/window',

        # Buildings: Ornaments
        'acroofbox':        '/environment/buildings/ornaments/acroofbox',
        'acwindowbox':      '/environment/buildings/ornaments/acwindowbox',
        'chimney':          '/environment/buildings/ornaments/chimney',
        'electricalbox':    '/environment/buildings/ornaments/electricalbox',
        'sign':             '/environment/buildings/ornaments/sign',
        'stormdrain':       '/environment/buildings/ornaments/stormdrain',
        'tvantenna':        '/environment/buildings/ornaments/tvantenna',
        'tvdish':           '/environment/buildings/ornaments/tvdish',
        'windowbase':       '/environment/buildings/ornaments/windowbase',

        # Ground: Components
        'sewergrate':       '/environment/ground/components/sewergrate',
        'sewerlid':         '/environment/ground/components/sewerlid',
        
        # Setdressing
        'bench':            '/environments/setdressing/bench',
        'bicyclerack':      '/environments/setdressing/bicyclerack',
        'chair':            '/environments/setdressing/chair',
        'cinderblock':      '/environments/setdressing/cinderblock',
        'dumpster':         '/environments/setdressing/dumpster',
        'firehydrant':      '/environments/setdressing/firehydrant',
        'lamp':             '/environments/setdressing/lamp',
        'mailbox':          '/environments/setdressing/mailbox',
        'parkingmeter':     '/environments/setdressing/parkingmeter',
        'recyclebin':       '/environments/setdressing/recyclebin',
        'shrub':            '/environments/setdressing/shrub',
        'sign':             '/environments/setdressing/sign',
        'stoplight':        '/environments/setdressing/stoplight',
        'table':            '/environments/setdressing/table',
        'trafficcone':      '/environments/setdressing/trafficcone',
        'trash':            '/environments/setdressing/trash',
        'trashbag':         '/environments/setdressing/trashbag',
        'trashcan':         '/environments/setdressing/trashcan',
        'tree':             '/environments/setdressing/tree',
        'treebase':         '/environments/setdressing/treebase',

        ### Vehicles
        'backgroundcar':    '/vehicles/backgroundcar',
        'licenseplate':     '/vehicles/licenseplate',
        'policecar':        '/vehicles/policecar',
        'studentcar':       '/vehicles/studentcar',
    }

    shot_lookup = {
        'A_010': '/A/shots/010',
        'A_020': '/A/shots/020',
        'A_030': '/A/shots/030',
        'A_040': '/A/shots/040',
        'A_050': '/A/shots/050',
        'A_060': '/A/shots/060',
        'A_070': '/A/shots/070',
        'A_080': '/A/shots/080',
        'A_090': '/A/shots/090',
        'A_100': '/A/shots/100',
        'A_110': '/A/shots/110',
        'A_120': '/A/shots/120',
        'A_130': '/A/shots/130',
        'A_140': '/A/shots/140',
        'A_150': '/A/shots/150',
        'A_160': '/A/shots/160',
        'A_170': '/A/shots/170',
        'A_180': '/A/shots/180',
        'B_010': '/B/shots/010',
        'C_010': '/C/shots/010',
        'D_010': '/D/shots/010',
        'E_010': '/E/shots/010',
        'F_010': '/F/shots/010',
        'G_010': '/G/shots/010',
    }

    ### Temp script for creating paths:
    # import os
    #
    # pipe_path = "/groups/accomplice/pipeline/production/asset"
    #
    # for key in asset_lookup:
    #     path = pipe_path + asset_lookup[key]
    #     if not os.path.exists(path):
    #         os.makedirs(path)
    #         print(path)
    

    _proxies: dict = {}
    """Maps software names to their respective proxy instance."""

    _httpd = None

    _data_root = "/groups/accomplice/pipeline/production"

#    _database = ShotGridDatabase(
#        SG_CONFIG['SITE_NAME'],
#        SG_CONFIG['SCRIPT_NAME'],
#        SG_CONFIG['SCRIPT_KEY'],
#        SG_CONFIG['ACCOMPLICE_ID']
#    )

    @property
    def port(self) -> int:
        """The port the pipe's HTTP server is running on."""
        if self._httpd is None:
            return 0
        else:
            return self._httpd.server_port

    def __init__(self, *software: str) -> None:
        log.info("Initializing the pipeline")

        # Initialize the superclass
        super().__init__()

        # Launch the pipe if software was specified
        if software is not None:
            self.launch(*software)

    def launch(self, *software: str) -> None:
        for name in software:
            if name == 'houdini_old':
                self.launch_software(name)
            else:
                # Initialize the pipe server
                log.info(f"Initializing pipe server on port {self.port}")
                self._httpd = HTTPServer(
                    ('localhost', self.port), partial(PipeRequestHandler, self))
                log.info(f"Pipe server initialized on port {self.port}")

                log.info("Launching software")
                self.launch_software(name)

                # time.sleep(15)

                log.info("Starting pipe server")
                try:
                    self._httpd.serve_forever()
                except KeyboardInterrupt:
                    log.info("Keyboard interrupt")
                    pass

                log.info("Shutting down pipe server")
                self._httpd.server_close()
                log.info("Exiting software")
                self._get_proxy(name).exit()

        # Check if any software was specified
        # if software is not None:
            # Launch the software
        #    for name in software:
        #        self.launch_software(name)
                # if name == 'maya':
                #     time.sleep(30)
                #     self._get_proxy(name).exit()

    def _get_proxy(self, name: str) -> SoftwareProxyInterface:
        """Return a proxy object for the given software."""
        # Check if a proxy already exists or not
        proxy = self._proxies.get(name)
        if proxy is None:
            # Create a proxy for the software
            proxy = software.create_proxy(name, self.port)
            self._proxies.update({name: proxy})

        # Return the proxy
        return proxy

    def launch_software(self, name: str):
        """Launch the 'Student Accomplice' cut of the given software.

        Overrides SimplePipe.launch_software().
        """
        log.info(f"Launching {name.capitalize()}")
        self._get_proxy(name).launch()
    
    def get_assets(self, query: Mapping[str, Any]) -> MutableSet:
        # Get the key for all assets
        if 'list' in query:
            list_type = query.get('list')
            if 'name' in list_type:
                return self.asset_lookup.keys()
                #return self._database.get_asset_list()

        # Get the specified assets
        if 'name' in query:
            return set([self.asset_lookup.get(asset) for asset in query.get('name')])
            #return set(self._database.get_assets(query.get('name')))
        
        return self.asset_lookup
    
    def get_shots(self, query: Mapping[str, Any]) -> MutableSet:
        # Get the key for all shots
        if 'list' in query:
            list_type = query.get('list')
            if 'name' in list_type:
                return self.shot_lookup.keys()
                #return self._database.get_shot_list()

        # Get the specified shots
        if 'name' in query:
            return set([self.shot_lookup.get(shot) for shot in query.get('name')])
            #return set(self._database.get_assets(query.get('name')))
        
        return self.shot_lookup

    def get_asset_dir(self, asset, category, hero: bool = False):
        """Get the filepath to the specified asset."""
        path = os.path.join(self._data_root, 'asset', category)
        if hero:
            return os.path.join(path, 'hero', asset)
        else:
            return os.path.join(path, 'generic', asset)

    # temporary... since I'm just referencing this function directly from Houdini for now...
    @staticmethod
    def get_asset_dir(asset, category: str = None, hero: bool = False):
        """Get the filepath to the specified asset."""
        asset = asset.lower()
        data_root = "/groups/accomplice/pipeline/production"
        # searching the asset directory of production
        path = os.path.join(data_root, 'asset')
        # add on category to path name if provided
        if category is not None:
            path = os.path.join(path, category)

        # make a regex for the path search
        found_file = False
        path_regex = os.path.join(path, "**", "*" + asset + "*")
        matching_dirs = []

        for filename in glob.iglob(path_regex, recursive=True):
            found_file = True
            if os.path.isdir(filename):
                matching_dirs.append(filename)

        # sort the list of matching directories by length to get the uppermost matching directory
        matching_dirs.sort(key=lambda x: len(x))

        # no files found
        if not found_file:
            return None
        else:
            return matching_dirs[0]

    def get_shot_dir(self, sequence, shot):
        pass

    class FilmItemType(Enum):
        ASSET = 1
        SHOT = 2

    # def reference_asset(self, software, pid, asset, category, hero):
    #     # Get pathing

    #     proxy.reference_usd(pid, asset, category, hero)

    # def publish_geo(self, asset_name, is_hero=False):
    #     """Overrides PipeInterface.publish_geo()"""
    #     pass

    # def publish_material(self, asset_name, is_hero=False):
    #     """Overrides PipeInterface.publish_material()"""
    #     pass

    # def publish_rig(self, asset_name, is_hero=False):
    #     """Overrides PipeInterface.publish_rig()"""
    #     pass

    # def publish_asset(self, asset_name, is_hero=False):
    #     """Overrides PipeInterface.publish_asset()"""
    #     pass

    # # Multiple animations per shot?
    # def publish_anim(self, shot_name):
    #     """Overrides PipeInterface.publish_anim()"""
    #     pass

    # def publish_camera(self, shot_name):
    #     """Overrides PipeInterface.publish_camera()"""
    #     pass

    # # Multiple fx per shot?
    # def publish_fx(self, shot_name):
    #     """Overrides PipeInterface.publish_fx()"""
    #     pass

    # def publish_layout(self, shot_name):
    #     """Overrides PipeInterface.publish_layout()"""
    #     pass

    # def publish_lighting(self, shot_name):
    #     """Overrides PipeInterface.publish_lighting()"""
    #     pass

    # def checkout_geo(self, asset_name, is_hero=False):
    #     """Overrides PipeInterface.checkout_geo()"""
    #     pass

    # def checkout_material(self, asset_name, is_hero=False):
    #     """Overrides PipeInterface.checkout_material()"""
    #     pass

    # def checkout_rig(self, asset_name, is_hero=False):
    #     """Overrides PipeInterface.checkout_rig()"""
    #     pass

    # def checkout_asset(self, asset_name, is_hero=False):
    #     """Overrides PipeInterface.checkout_asset()"""
    #     pass

    # # Multiple animations per shot?
    # def checkout_anim(self, shot_name):
    #     """Overrides PipeInterface.checkout_anim()"""
    #     pass

    # def checkout_camera(self, shot_name):
    #     """Overrides PipeInterface.checkout_camera()"""
    #     pass

    # # Multiple fx per shot?
    # def checkout_fx(self, shot_name):
    #     """Overrides PipeInterface.checkout_fx()"""
    #     pass

    # def checkout_layout(self, shot_name):
    #     """Overrides PipeInterface.checkout_layout()"""
    #     pass

    # def checkout_lighting(self, shot_name):
    #     """Overrides PipeInterface.checkout_lighting()"""
    #     pass

    # def reference_rig(self, asset_type, asset_name):
    #     """Overrides PipeInterface.reference_rig()"""
    #     pass

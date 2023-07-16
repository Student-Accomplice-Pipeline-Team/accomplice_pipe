from ..baseclass import SoftwareProxy

class NukeProxy(SoftwareProxy):
    def launch(self):
        """Overrides SoftwareProxy.launch()"""
        print("Launching Nuke")
        pass

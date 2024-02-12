import hou
import os
import pipe


class AssetPublisher:
    def publish(node):
        if not AssetPublisher._check_inputs(node):
            return

        AssetPublisher.update_asset_parms(node)
        
        if os.path.exists(node.evalParm("lopoutput")):
            response = hou.ui.displayMessage(
                f"\"{node.evalParm('name')}\" already exists in the pipe. Are you sure you want to overwrite it?",
                buttons=("Overwrite", "Cancel"),
                severity=hou.severityType.ImportantMessage,
                default_choice=1
            )
            if response == 1:
                return
        
        output_node = node.node("componentoutput1")
        output_node.parm("execute").pressButton()
        output_node.parm("addtogallery").pressButton()
        hou.hipFile.save()
    
    
    def generate_thumbnail(node):
        node.node("componentoutput1").parm("executeviewport").pressButton()


    def update_asset_parms(node):
        for ancestor in node.inputAncestors():
            if ancestor.type().name().split(":")[0] == "accomp_geo_variant":
                asset_name = ancestor.evalParm("asset")
        
        if not asset_name:
            return
        
        asset = pipe.server.get_asset(asset_name)
        asset_file_name = asset_name + ".usd"
        asset_path = os.path.join(asset.path, asset_file_name)
        
        node.parm("name").set(asset_name)
        node.parm("filename").set(asset_file_name)
        node.parm("lopoutput").set(asset_path)    

                
    def _check_inputs(node):
        # Make sure there's at least one input node
        if len(node.inputAncestors()) < 1:
            hou.ui.displayMessage(
                "At least one input Geo Variant is required.",
                severity=hou.severityType.Error
            )
            return False

        # Make sure all Geo Variant node ancestors have compatible asset and variant values
        ancestor_assets = []
        ancestor_variants = []
        for ancestor in node.inputAncestors():
            if ancestor.type().name().split(":")[0] == "accomp_geo_variant":
                asset = ancestor.evalParm("asset")
                if asset != "None" and asset is not None:
                    ancestor_assets.append(asset)
                else:
                    hou.ui.displayMessage(
                        "At least one of the input Geo Variant nodes does not have an asset set.",
                        severity=hou.severityType.Error
                    )
                    return False
                    
                    
                variant = ancestor.evalParm("variant")
                if variant != "None" and variant is not None:
                    ancestor_variants.append(variant)
                else:
                    hou.ui.displayMessage(
                        "At least one of the input Geo Variant nodes does not have a variant set.",
                        severity=hou.severityType.Error
                    )
                    return False
        
        if not all(asset == ancestor_assets[0] for asset in ancestor_assets):
            hou.ui.displayMessage(
                "The input Geo Variant nodes are set to mismatching assets. Set them all to the "
                "same asset to continue.",
                severity=hou.severityType.Error
            )
            return False
        
        if len(ancestor_variants) > len(set(ancestor_variants)):
            hou.ui.displayMessage(
                "Some of the input Geo Variant nodes are set to matching variants. Set them all "
                "to the different variants to continue.",
                severity=hou.severityType.Error
            )
            return False
        
        # Make sure that each input branch has a Geo Variant node in it.
        for input in node.inputs():
            if input.type().name().split(":")[0] == "accomp_geo_variant":
                continue
            else:
                ancestor_types = []
                for ancestor in input.inputAncestors():
                    ancestor_types.append(ancestor.type().name().split(":")[0])
                if "accomp_geo_variant" not in ancestor_types:
                    hou.ui.displayMessage(
                        "At least one of the input branches is missing a Geo Variant node. "
                        "Disconnect the branch or give it a Geo Variant node to continue.",
                        severity=hou.severityType.Error
                    )
                    return False

        return True

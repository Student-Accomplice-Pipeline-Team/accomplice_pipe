import hou
from pipe.shared.helper.utilities.houdini_utils import HoudiniUtils, HoudiniFXUtils, HoudiniNodeUtils

class InvertTransformSystem:
    @staticmethod
    def on_created(myself):
        InvertTransformSystem.set_fbx_file_location(myself)
        imported_fbx_null = InvertTransformSystem.import_fbx(myself)
        myself.parm('imported_null').set(imported_fbx_null.path())
        InvertTransformSystem.update_transforms(myself)

    @staticmethod
    def get_imported_fbx_null_path(myself):
        return myself.parm('imported_null').eval()

    @staticmethod
    def set_fbx_file_location(myself):
        shot = HoudiniUtils.get_shot_for_file()
        location_of_fbx = HoudiniFXUtils.get_car_fbx_transform_path(shot)
        myself.parm('fbx_file_location').set(location_of_fbx)

    @staticmethod
    def import_fbx(myself) -> hou.Node:
        location_of_fbx = myself.parm('fbx_file_location').eval()
        imported_fbx_null = hou.hipFile.importFBX(location_of_fbx)[0].children()[0]
        return imported_fbx_null

    @staticmethod
    def update_transforms(myself):
        assert InvertTransformSystem.get_imported_fbx_null_path(myself) != '', 'No imported null path'
        imported_fbx_null = hou.node(InvertTransformSystem.get_imported_fbx_null_path(myself))

        HoudiniNodeUtils.link_fields(
            imported_fbx_null,
            myself.node('dive_target/invert_transform'),
            [
                'tx',
                'ty',
                'tz',
                'rx',
                'ry',
                'rz'
            ]
        )
        


    # path = myself.parm('imported_null').eval()
    # def link_expression(parm_name:str ):
    #     # global myself
    #     expression = 'ch("' + path + '/' + parm_name + '")'
    #     print(expression)
    #     target_node = myself.node('dive_target/invert_transform')
    #     print(target_node)
    #     target_parm = target_node.parm(parm_name)
    #     print(target_parm)
    #     target_parm.setExpression(expression) # This node is already set to invert the transformation itself

    # link_expression('tx')
    # link_expression('ty')
    # link_expression('tz')

    # link_expression('rx')
    # link_expression('ry')
    # link_expression('rz')
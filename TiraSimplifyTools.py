bl_info = {
    "name": "Tira's Simplify Tools",
    "author": "Tira Zhang <tira.zzhang@gmail.com>",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "category": "Object",
    #"location": "Operator Search",
    "description": "Make it Simple!",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
}
import bpy
from math import radians
from bpy.props import *
import bmesh



class EeveeHighPerformanceSetup(bpy.types.Operator):
    bl_idname = "object.high_performance_operator"
    bl_label = "Eevee High Performance Setup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        ###Turn on AO [distance = 1m], Bloom, Screen Space Reflections, Motion Blur
        ###High-def Shadow: Cube Size 4096px, Cascade Size 4096px, High Bit Depth

        bpy.context.scene.eevee.taa_render_samples = 256
        bpy.context.scene.eevee.taa_samples = 64

        bpy.context.scene.eevee.use_gtao = True
        bpy.context.scene.eevee.gtao_distance = 1

        bpy.context.scene.eevee.use_bloom = True
        bpy.context.scene.eevee.use_ssr = True
        bpy.context.scene.eevee.use_motion_blur = True

        bpy.context.scene.eevee.shadow_cube_size = '4096'
        bpy.context.scene.eevee.shadow_cascade_size = '4096'
        bpy.context.scene.eevee.use_shadow_high_bitdepth = True
        bpy.context.scene.eevee.use_soft_shadows = True

        bpy.context.scene.eevee.volumetric_end = 10000
        bpy.context.scene.eevee.volumetric_tile_size = '16'
        bpy.context.scene.eevee.volumetric_samples = 256

        return {'FINISHED'}

class QuickVolumetricLighting(bpy.types.Operator):
    bl_idname = "object.quick_volume_operator"
    bl_label = "Quick Volume"
    bl_options = {'REGISTER', 'UNDO'}
    
    #create properties
    volume_density : FloatProperty(
        name = "Volume Desity",
        description = "The density of the volumetric fog",
        default = 1.0,
        min = 0.0,
        soft_max = 10.0,
    )
    
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 0.1   #set default background color darker

        bpy.ops.mesh.primitive_cube_add(size=20, location=(0, 0, 0), scale=(1, 1, 1))  #create volume cube
        vc = bpy.context.active_object
        vc.display_type = 'WIRE'

        M_volume = bpy.data.materials.new(name = "M_volume")
        vc.data.materials.append(M_volume)

        M_volume.use_nodes = True
        nodes = M_volume.node_tree.nodes   ###
        material_output = nodes.get("Material Output")

        node_pVolume = nodes.new(type='ShaderNodeVolumePrincipled')

        node_pVolume.inputs[2].default_value = self.volume_density * 0.01      #input volume density
        links = M_volume.node_tree.links   ###
        new_link = links.new(node_pVolume.outputs[0], material_output.inputs[1])

        node_pBSDF = nodes.get("Principled BSDF")
        nodes.remove(node_pBSDF)


        return {'FINISHED'}

class QuickRockGenerator(bpy.types.Operator):
    bl_idname = "object.quick_rock_operator"
    bl_label = "Quick Rock"
    bl_options = {'REGISTER', 'UNDO'}

    # create properties
    texture_strength: FloatProperty(
        name="Volume Desity",
        description="The density of the volumetric fog",
        default=0.4,
        soft_min=0.0,
        soft_max=1.0,
    )

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(scale=(1, 1, 1))
        rock = bpy.context.active_object
        rock.name = "rock"

        mesh = rock.data
        for face in mesh.polygons:
           face.use_smooth = True

        mod_ss = rock.modifiers.new("Subdivision", 'SUBSURF')
        mod_ss.levels = 5
        mod_ss.render_levels = 5

        mod_displace = rock.modifiers.new("Displace", 'DISPLACE')

        tex_voro = bpy.data.textures.new("Voronoi Texture", 'VORONOI')
        tex_voro.noise_scale = 1.0
        tex_voro.distance_metric = 'DISTANCE_SQUARED'

        mod_displace.texture = tex_voro
        mod_displace.strength = self.texture_strength
        mod_displace.texture_coords = 'GLOBAL'

        return {'FINISHED'}

class QuickStudioStaging(bpy.types.Operator):
    bl_idname = "object.studio_stage_operator"
    bl_label = "Studio Stage"
    bl_options = {'REGISTER', 'UNDO'}

    # create properties
    stage_scale: FloatProperty(
        name="Stage Scale",
        description="The scale of the stage",
        default=1.0,
        soft_min=0.0,
        soft_max=100.0,
    )

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1), scale=(2, 1, 1)) ###
        stage = bpy.context.active_object
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.transform.resize(value=(self.stage_scale, self.stage_scale, self.stage_scale), orient_type='GLOBAL')

        mesh = stage.data
        for face in mesh.polygons:
           face.use_smooth = True

        mod_bevel = stage.modifiers.new("Bevel", 'BEVEL')
        mod_bevel.width = 0.5
        mod_bevel.segments = 5

        ###delete 4 faces  (not index 1 & 4)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()

        for face in bm.faces:
           face.select = False
        bm.faces[0].select = True
        bm.faces[2].select = True
        bm.faces[3].select = True
        bm.faces[5].select = True

        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}

class ToonShaderSetup(bpy.types.Operator):
    bl_idname = "object.toon_shader_operator"
    bl_label = "Toon Shader Setup"
    bl_options = {'REGISTER', 'UNDO'}

    # create properties
    toon_influence: FloatProperty(
        name="Toon Influence",
        description="The scale of the stage",
        default=0.0,
        soft_min=-10.0,
        soft_max=10.0,
    )

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        so = bpy.context.active_object
        for i in so.material_slots:
            so.active_material_index = 0
            bpy.ops.object.material_slot_remove()

        M_toon = bpy.data.materials.new(name="M_toon")
        so.data.materials.append(M_toon)

        M_toon.use_nodes = True
        nodes = M_toon.node_tree.nodes  ###
        material_output = nodes.get("Material Output")

        node_dBSDF = nodes.new(type="ShaderNodeBsdfDiffuse")
        node_S2RGB = nodes.new(type="ShaderNodeShaderToRGB")
        node_Math = nodes.new(type="ShaderNodeMath")
        node_colorRamp = nodes.new(type="ShaderNodeValToRGB")  # colorramp
        node_mixRGB = nodes.new(type="ShaderNodeMixRGB")
        node_emission = nodes.new(type="ShaderNodeEmission")

        node_Math.inputs[1].default_value = self.toon_influence    ### Math-add value

        node_colorRamp.color_ramp.elements[0].position = 0.45
        node_colorRamp.color_ramp.elements[0].color = (0, 0.16, 0.34, 1)
        node_colorRamp.color_ramp.elements[1].position = 0.5
        node_colorRamp.color_ramp.elements[1].color = (1, 1, 1, 1)

        node_mixRGB.blend_type = 'MULTIPLY'
        node_mixRGB.inputs[0].default_value = 1
        node_mixRGB.inputs[1].default_value = (0.9, 0.65, 1, 1)

        links = M_toon.node_tree.links
        links.new(node_dBSDF.outputs[0], node_S2RGB.inputs[0])
        links.new(node_S2RGB.outputs[0], node_Math.inputs[0])#
        links.new(node_Math.outputs[0], node_colorRamp.inputs[0])#
        links.new(node_colorRamp.outputs[0], node_mixRGB.inputs[2])
        links.new(node_mixRGB.outputs[0], node_emission.inputs[0])
        links.new(node_emission.outputs[0], material_output.inputs[0])

        node_pBSDF = nodes.get("Principled BSDF")
        nodes.remove(node_pBSDF)


        return {'FINISHED'}

class TransparentGradientShaderSetup(bpy.types.Operator):
    bl_idname = "object.transparent_gradient_operator"
    bl_label = "Transparent Gradient Shader Setup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        so = bpy.context.active_object
        for i in so.material_slots:
            so.active_material_index = 0
            bpy.ops.object.material_slot_remove()

        M_alpha = bpy.data.materials.new(name = "M_alpha")
        so.data.materials.append(M_alpha)

        M_alpha.use_nodes = True
        nodes = M_alpha.node_tree.nodes   ###
        material_output = nodes.get("Material Output")
        node_pBSDF = nodes.get("Principled BSDF")

        bpy.context.object.active_material.blend_method = 'HASHED'
        bpy.context.object.active_material.shadow_method = 'HASHED'

        node_texCoord = nodes.new(type="ShaderNodeTexCoord")
        node_mapping = nodes.new(type="ShaderNodeMapping")
        node_gradient = nodes.new(type="ShaderNodeTexGradient")
        node_transparent = nodes.new(type="ShaderNodeBsdfTransparent")
        node_mixShader = nodes.new(type="ShaderNodeMixShader")

        links = M_alpha.node_tree.links
        links.new(node_texCoord.outputs[0], node_mapping.inputs[0])
        links.new(node_mapping.outputs[0], node_gradient.inputs[0])
        links.new(node_gradient.outputs[0], node_mixShader.inputs[0])
        links.new(node_transparent.outputs[0], node_mixShader.inputs[1])
        links.new(node_pBSDF.outputs[0], node_mixShader.inputs[2])
        links.new(node_mixShader.outputs[0], material_output.inputs[0])

        return {'FINISHED'}

class NoiseAndFresnelTextureSetup(bpy.types.Operator):
    bl_idname = "object.noise_fresnel_operator"
    bl_label = "Noise And Fresnel Texture Setup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        M_selected = bpy.context.active_object.active_material
        nodes = M_selected.node_tree.nodes

        tex_noise_1 = nodes.new(type="ShaderNodeTexNoise")
        tex_noise_2 = nodes.new(type="ShaderNodeTexNoise")
        node_colorRamp_1 = nodes.new(type="ShaderNodeValToRGB")
        node_colorRamp_2 = nodes.new(type="ShaderNodeValToRGB")
        node_mixRGB_1 = nodes.new(type="ShaderNodeMixRGB")

        tex_noise_1.inputs[2].default_value = 10.0
        tex_noise_1.inputs[3].default_value = 8.0
        tex_noise_1.inputs[4].default_value = 1.0

        tex_noise_2.inputs[2].default_value = 3.0
        tex_noise_2.inputs[3].default_value = 2.0
        tex_noise_2.inputs[4].default_value = 0.5

        nodes_frame = nodes.new(type="NodeFrame")
        tex_noise_1.parent = nodes_frame
        tex_noise_2.parent = nodes_frame
        node_colorRamp_1.parent = nodes_frame
        node_colorRamp_2.parent = nodes_frame
        node_mixRGB_1.parent = nodes_frame

        links = M_selected.node_tree.links
        links.new(tex_noise_1.outputs[0], node_colorRamp_1.inputs[0])
        links.new(tex_noise_2.outputs[0], node_colorRamp_2.inputs[0])
        links.new(node_colorRamp_1.outputs[0], node_mixRGB_1.inputs[1])
        links.new(node_colorRamp_2.outputs[0], node_mixRGB_1.inputs[2])

        #fresnel
        node_layerWeight = nodes.new(type="ShaderNodeLayerWeight")
        node_colorRamp_3 = nodes.new(type="ShaderNodeValToRGB")
        node_mixRGB_2 = nodes.new(type="ShaderNodeMixRGB")

        node_colorRamp_3.color_ramp.elements[0].color = (1, 1, 1, 1) #white
        node_colorRamp_3.color_ramp.elements[1].color = (0, 0, 0, 1) #black

        links.new(node_layerWeight.outputs[1], node_colorRamp_3.inputs[0])
        links.new(node_colorRamp_3.outputs[0], node_mixRGB_2.inputs[1])
        links.new(node_mixRGB_1.outputs[0], node_mixRGB_2.inputs[2])

        node_layerWeight.parent = nodes_frame
        node_colorRamp_3.parent = nodes_frame
        node_mixRGB_2.parent = nodes_frame


        return {'FINISHED'}



#################  UI   ####################
class VIEW3D_PT_Simplify_Tools(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tira"
    bl_label = "Tools"
    
    def draw(self, context):
        col = self.layout.column(align=True)
        props = col.operator("object.high_performance_operator",
            text = "Eevee High Performance Setup",
            #description = "haha",
            icon = 'PREFERENCES')

        col = self.layout.column(align = True)
        col.operator("object.quick_volume_operator",
            text = "Quick Volume",
            icon = 'SNAP_VOLUME')
        #props.volume_density = 1.425
        col.operator("object.quick_rock_operator",
            text="Quick Rock Generator",
            icon='MESH_ICOSPHERE')
        col.operator("object.studio_stage_operator",
                     text="Quick Studio Stage",
                     icon='AXIS_SIDE')

        col = self.layout.column(align=True)
        col.label(text='select a mesh first')
        col.operator("object.toon_shader_operator",
                     text="Toon Shader Setup",
                     icon='NODE_MATERIAL')
        col.operator("object.transparent_gradient_operator",
                     text="Transparent Gradient Shader",
                     icon='NODE_MATERIAL')

        col = self.layout.column(align=True)
        col.label(text='select a shader first')
        col.operator("object.noise_fresnel_operator",
                     text="Noise Fresnel Texture",
                     icon='TEXTURE_DATA')


def register():
    bpy.utils.register_class(EeveeHighPerformanceSetup)

    bpy.utils.register_class(QuickVolumetricLighting)
    bpy.utils.register_class(QuickRockGenerator)
    bpy.utils.register_class(QuickStudioStaging)

    bpy.utils.register_class(ToonShaderSetup)
    bpy.utils.register_class(TransparentGradientShaderSetup)

    bpy.utils.register_class(NoiseAndFresnelTextureSetup)

    bpy.utils.register_class(VIEW3D_PT_Simplify_Tools)



def unregister():
    bpy.utils.unregister_class(EeveeHighPerformanceSetup)

    bpy.utils.unregister_class(QuickVolumetricLighting)
    bpy.utils.unregister_class(QuickRockGenerator)
    bpy.utils.unregister_class(QuickStudioStaging)

    bpy.utils.unregister_class(ToonShaderSetup)
    bpy.utils.unregister_class(TransparentGradientShaderSetup)

    bpy.utils.unregister_class(NoiseAndFresnelTextureSetup)

    bpy.utils.unregister_class(VIEW3D_PT_Simplify_Tools)



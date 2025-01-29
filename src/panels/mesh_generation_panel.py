import bpy


class MeshGenerationPanel(bpy.types.Panel):
    bl_label = "Mesh Generation Panel"
    bl_idname = "OBJECT_PT_MeshGenerationPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.mesh_generation_properties

        layout.label(text="Hunyuan3D-2 3D Generation Settings")
        layout.prop(props, "api_url")
        layout.prop(props, "prompt")
        layout.prop(props, "image_path")
        layout.prop(props, "octree_resolution")
        layout.prop(props, "num_inference_steps")
        layout.prop(props, "guidance_scale")
        layout.prop(props, "texture")

        row = layout.row()
        row.enabled = not props.is_processing
        row.operator("diffusion.generate_3d")

        if props.is_processing:
            for line in props.status_message.split("\n"):
                layout.label(text=line)


def register():
    bpy.utils.register_class(MeshGenerationPanel)


def unregister():
    bpy.utils.unregister_class(MeshGenerationPanel)

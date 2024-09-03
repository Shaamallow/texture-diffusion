import bpy


# Define the panel class
class DiffusionPanel(bpy.types.Panel):
    bl_label = "Diffusion Panel"
    bl_idname = "OBJECT_PT_DiffusionPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        diffusion_properties = scene.diffusion_properties

        layout.prop(diffusion_properties, "models_available")

        layout.prop(diffusion_properties, "prompt")
        layout.prop(diffusion_properties, "n_steps")

        row = layout.row()
        row.prop(diffusion_properties, "cfg_scale")
        row.prop(diffusion_properties, "controlnet_scale")

        row = layout.row()
        row.prop(diffusion_properties, "seed")
        row.prop(diffusion_properties, "random_seed")

        layout.prop(diffusion_properties, "show_advanced")

        # TODO : Turn this into a Advanced Panel using a new class
        if diffusion_properties.show_advanced:
            layout.prop(diffusion_properties, "negative_prompt")
            layout.prop(diffusion_properties, "scheduler")

        # Add a visual separator and different background for the mesh collection
        layout.separator()
        box = layout.box()
        box.label(text="Select Mesh", icon="MESH_DATA")

        # Button to add a mesh object to the collection
        box.operator("diffusion.add_mesh", text="Select Mesh")

        # Display the mesh_objects collection with remove buttons
        for i, mesh_item in enumerate(diffusion_properties.mesh_objects):
            row = box.row(align=True)
            row.label(text=mesh_item.name)
            row.operator("diffusion.remove_mesh", text="", icon="REMOVE").index = i

        # Add a big "Generate" button at the bottom of the panel
        layout.separator()
        layout.operator("diffusion.generate", text="Generate", icon="RENDER_STILL")


# Register the panel and properties


def register():
    bpy.utils.register_class(DiffusionPanel)


def unregister():
    bpy.utils.unregister_class(DiffusionPanel)

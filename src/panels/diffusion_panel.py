from typing import Optional

import bpy

# pyright: reportAttributeAccessIssue=false


class DiffusionPanel(bpy.types.Panel):
    bl_label = "Diffusion Panel"
    bl_idname = "OBJECT_PT_DiffusionPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None
        layout = self.layout

        scene = context.scene
        diffusion_properties = scene.diffusion_properties

        layout.prop(diffusion_properties, "models_available")
        layout.prop(diffusion_properties, "prompt")
        layout.prop(diffusion_properties, "n_steps")

        row = layout.row()

        row = layout.row()
        row.prop(diffusion_properties, "seed")
        row.prop(diffusion_properties, "random_seed")

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

        layout.separator()

        layout.operator("diffusion.camera_setup", text="GENERATE", icon="RENDER_STILL")


class AdvancedDiffusionPanel(bpy.types.Panel):
    bl_label = "Advanced Diffusion"
    bl_idname = "OBJECT_PT_AdvancedDiffusion"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"
    bl_parent_id = "OBJECT_PT_DiffusionPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None
        layout = self.layout
        diffusion_properties = context.scene.diffusion_properties

        layout.prop(diffusion_properties, "negative_prompt")
        layout.prop(diffusion_properties, "cfg_scale")

        layout.separator()

        layout.prop(diffusion_properties, "scheduler")
        layout.prop(diffusion_properties, "sampler_name")

        layout.separator()

        layout.prop(diffusion_properties, "controlnet_scale")


class LoRAPanel(bpy.types.Panel):
    bl_label = "LoRA"
    bl_idname = "OBJECT_PT_LoRA"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"
    bl_parent_id = "OBJECT_PT_DiffusionPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None
        layout = self.layout
        diffusion_properties = context.scene.diffusion_properties

        layout.prop(diffusion_properties, "loras_available")
        layout.prop(diffusion_properties, "lora_scale")


class IPAdapterPanel(bpy.types.Panel):
    bl_label = "IPAdapter"
    bl_idname = "OBJECT_PT_IPAdapter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"
    bl_parent_id = "OBJECT_PT_DiffusionPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None
        layout = self.layout
        diffusion_properties = context.scene.diffusion_properties

        layout.prop(diffusion_properties, "toggle_ipadapter")

        layout.prop(diffusion_properties, "scale_ipadapter")
        layout.prop(diffusion_properties, "toggle_instantstyle")

        layout.operator("image.open", text="Load Image")
        layout.prop_search(
            diffusion_properties,
            "ip_adapter_image",
            bpy.data,
            "images",
            text="Select Image",
        )


class InpaintingPanel(bpy.types.Panel):
    bl_label = "Inpainting"
    bl_idname = "OBJECT_PT_Inpainting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"
    bl_parent_id = "OBJECT_PT_DiffusionPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None
        layout = self.layout
        diffusion_properties = context.scene.diffusion_properties

        layout.prop(diffusion_properties, "toggle_inpainting")
        layout.prop(diffusion_properties, "inpainting_mode")
        layout.prop(diffusion_properties, "denoising_strength")


# Register classes
def register():
    bpy.utils.register_class(DiffusionPanel)
    bpy.utils.register_class(AdvancedDiffusionPanel)
    bpy.utils.register_class(LoRAPanel)
    bpy.utils.register_class(IPAdapterPanel)
    bpy.utils.register_class(InpaintingPanel)


def unregister():
    bpy.utils.unregister_class(DiffusionPanel)
    bpy.utils.unregister_class(AdvancedDiffusionPanel)
    bpy.utils.unregister_class(LoRAPanel)
    bpy.utils.unregister_class(IPAdapterPanel)
    bpy.utils.unregister_class(InpaintingPanel)

import bpy


class MeshItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Mesh Name")


class DiffusionProperties(bpy.types.PropertyGroup):

    mesh_objects: bpy.props.CollectionProperty(type=MeshItem)

    models_available: bpy.props.EnumProperty(
        name="Models",
        description="Pick a model from the available models you have downloaded",
        items=[("sdxl", "SDXL", "Base SDXL model available on huggingface")],
        default=None,
    )
    prompt: bpy.props.StringProperty(
        name="Prompt", description="Text prompt for the diffusion effect"
    )
    n_steps: bpy.props.IntProperty(
        name="N_Steps",
        description="Number of steps for the diffusion process",
        default=30,
        min=1,
    )
    cfg_scale: bpy.props.FloatProperty(
        name="CFG Scale",
        description="Classifier-Free Guidance scale for the diffusion process",
        default=5.5,
        min=0.0,
    )
    controlnet_scale: bpy.props.FloatProperty(
        name="ControlNet Scale",
        description="Controlnet Strengh for the conditioning. 0 means no depth conditioning",
        default=0.7,
        min=0.0,
    )
    seed: bpy.props.IntProperty(
        name="seed",
        description="Seed for the generation.",
        default=42,
        min=0,
        max=1000000,
    )
    random_seed: bpy.props.BoolProperty(
        name="Use a random seed",
        description="Toggle random seed for generationg",
        default=False,
    )
    show_advanced: bpy.props.BoolProperty(
        name="Show Advanced Parameters",
        description="Toggle advanced parameters",
        default=False,
    )
    negative_prompt: bpy.props.StringProperty(
        name="Negative Prompt",
        description="Negative text prompt for the diffusion effect",
    )
    scheduler: bpy.props.EnumProperty(
        name="Scheduler",
        description="Scheduler for the diffusion process",
        items=[("DDIM", "DDIM", ""), ("DDPM", "DDPM", ""), ("LCM", "LCM", "")],
        default="DDIM",
    )

    height: bpy.props.IntProperty(
        name="Height", description="Height of the generated image", default=1024
    )

    width: bpy.props.IntProperty(
        name="Width", description="Height of the generated image", default=1024
    )

    def update_mesh_collection(self, context):
        """Update the mesh_objects collection to match the current scene"""
        self.mesh_objects.clear()
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH":
                mesh_item = self.mesh_objects.add()
                mesh_item.name = obj.name

    # New property for mesh selection
    mesh_objects: bpy.props.CollectionProperty(type=MeshItem)


def register():
    bpy.utils.register_class(MeshItem)
    bpy.utils.register_class(DiffusionProperties)
    bpy.types.Scene.diffusion_properties = bpy.props.PointerProperty(
        type=DiffusionProperties
    )


def unregister():
    bpy.utils.unregister_class(MeshItem)
    bpy.utils.unregister_class(DiffusionProperties)
    del bpy.types.Scene.diffusion_properties

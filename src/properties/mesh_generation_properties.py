import bpy


class MeshGenerationProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Text Prompt", description="Describe what you want to generate", default=""
    )
    api_url: bpy.props.StringProperty(
        name="API URL",
        description="URL of the Text-to-3D API service",
        default="http://localhost:8080",
    )
    is_processing: bpy.props.BoolProperty(name="Processing", default=False)
    job_id: bpy.props.StringProperty(name="Job ID", default="")
    status_message: bpy.props.StringProperty(name="Status Message", default="")
    image_path: bpy.props.StringProperty(
        name="Image", description="Select an image to upload", subtype="FILE_PATH"
    )
    octree_resolution: bpy.props.IntProperty(
        name="Octree Resolution",
        description="Octree resolution for the 3D generation",
        default=256,
        min=128,
        max=512,
    )
    num_inference_steps: bpy.props.IntProperty(
        name="Number of Inference Steps",
        description="Number of inference steps for the 3D generation",
        default=20,
        min=20,
        max=50,
    )
    guidance_scale: bpy.props.FloatProperty(
        name="Guidance Scale",
        description="Guidance scale for the 3D generation",
        default=5.5,
        min=1.0,
        max=10.0,
    )
    texture: bpy.props.BoolProperty(
        name="Generate Texture",
        description="Whether to generate texture for the 3D model",
        default=False,
    )


def register():
    bpy.utils.register_class(MeshGenerationProperties)
    bpy.types.Scene.mesh_generation_properties = bpy.props.PointerProperty(
        type=MeshGenerationProperties
    )


def unregister():
    bpy.utils.unregister_class(MeshGenerationProperties)
    del bpy.types.Scene.mesh_generation_properties

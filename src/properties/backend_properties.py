import bpy


class BackendProperties(bpy.types.PropertyGroup):

    backend_availables: bpy.props.EnumProperty(
        name="Backend",
        description="Pick a backend from the supported ones",
        items=[
            ("comfyui", "ComfyUI", "A self-hosted diffusion backend"),
            ("replicate", "Replicate", "Online interaface to run models using API"),
        ],
        default=None,
    )
    url: bpy.props.StringProperty(
        name="URL",
        description="URL to access the backend",
        default="http://localhost:8188",
    )

    timeout_retry: bpy.props.IntProperty(
        name="Timeout Retry",
        description="Maximum number of retries (1 per second) to fetch the image before a timeout",
        default=60,
        min=1,
        max=1000,
    )

    expected_completion: bpy.props.IntProperty(
        name="Expected Completion",
        description="Expected time in seconds to complete the image generation",
        default=60,
        min=1,
        max=1000,
    )

    history_collection_name: bpy.props.StringProperty(
        name="History Collection Name", default="Diffusion Camera History"
    )


def register():
    bpy.utils.register_class(BackendProperties)
    bpy.types.Scene.backend_properties = bpy.props.PointerProperty(
        type=BackendProperties
    )


def unregister():
    bpy.utils.unregister_class(BackendProperties)
    del bpy.types.Scene.backend_properties

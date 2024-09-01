import bpy

# pyright: reportInvalidTypeForm=false
# Refer to this issue as to why this is disabled : https://github.com/microsoft/pylance-release/issues/5457


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

    show_token: bpy.props.BoolProperty(
        name="Show API Token",
        description="Toggle to show token",
        default=False,
    )

    token: bpy.props.StringProperty(
        name="Token",
        description="Token for the backend",
    )


def register():
    bpy.utils.register_class(BackendProperties)
    bpy.types.Scene.backend_properties = bpy.props.PointerProperty(
        type=BackendProperties
    )


def unregister():
    bpy.utils.unregister_class(BackendProperties)
    del bpy.types.Scene.backend_properties

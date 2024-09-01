# pyright: reportUnboundVariable=false
# Need to add the following because of blender reloading behaviour

bl_info = {
    "name": "Blender Diffusion",
    "blender": (4, 1, 1),
    "author": "Shaamallow",
    "category": "3D View",
    "version": "0.0.1",
    "description": "Create textures using Diffusion Models in blender",
}

if "bpy" in locals():
    # Extra Blender imports to allow reloading
    import importlib

    importlib.reload(properties)
    importlib.reload(panels)
    importlib.reload(operators)

else:
    from .src import panels, properties, operators

import bpy


def register():
    properties.register()
    panels.register()
    operators.register()


def unregister():
    panels.unregister()
    properties.unregister()
    operators.unregister()


if __name__ == "__main__":
    register()

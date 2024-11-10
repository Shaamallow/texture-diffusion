# pyright: reportUnboundVariable=false
# Need to add the following because of blender reloading behaviour

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

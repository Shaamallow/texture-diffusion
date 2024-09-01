from .generation import register as generation_register
from .generation import unregister as generation_unregister
from .mesh_collection import register as mesh_collection_register
from .mesh_collection import unregister as mesh_collection_unregister


def register():
    mesh_collection_register()
    generation_register()


def unregister():
    mesh_collection_unregister()
    generation_unregister()

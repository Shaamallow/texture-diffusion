from .generation_operators import generation_register, generation_unregister
from .history_collection_operators import (history_collection_register,
                                           history_collection_unregister)
from .image_render_operators import (image_render_register,
                                     image_render_unregister)
from .mesh_collection_operators import (mesh_collection_register,
                                        mesh_collection_unregister)


def register():
    mesh_collection_register()
    generation_register()
    history_collection_register()
    image_render_register()


def unregister():
    mesh_collection_unregister()
    generation_unregister()
    history_collection_unregister()
    image_render_unregister()

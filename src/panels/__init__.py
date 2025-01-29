from .backend_panel import register as backend_register
from .backend_panel import unregister as backend_unregister
from .diffusion_panel import register as diffusion_register
from .diffusion_panel import unregister as diffusion_unregister
from .history_panel import register as history_register
from .history_panel import unregister as history_unregister
from .mesh_generation_panel import register as mesh_generation_register
from .mesh_generation_panel import unregister as mesh_generation_unregister


def register():
    diffusion_register()
    history_register()
    backend_register()
    mesh_generation_register()


def unregister():
    diffusion_unregister()
    history_unregister()
    backend_unregister()
    mesh_generation_unregister()

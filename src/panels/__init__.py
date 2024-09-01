from .backend_panel import register as backend_register
from .backend_panel import unregister as backend_unregister
from .diffusion_panel import register as diffusion_register
from .diffusion_panel import unregister as diffusion_unregister


def register():
    diffusion_register()
    backend_register()


def unregister():
    diffusion_unregister()
    backend_unregister()

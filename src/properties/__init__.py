from .backend_properties import register as backend_register
from .backend_properties import unregister as backend_unregister
from .diffusion_properties import register as diffusion_register
from .diffusion_properties import unregister as diffusion_unregister
from .history_properties import register as history_register
from .history_properties import unregister as history_unregister


def register():
    diffusion_register()
    history_register()
    backend_register()


def unregister():
    diffusion_unregister()
    history_unregister()
    backend_unregister()

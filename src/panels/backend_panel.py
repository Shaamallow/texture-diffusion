import bpy


class BackendPanel(bpy.types.Panel):
    bl_label = "Backend Panel"
    bl_idname = "OBJECT_PT_BackendPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        backend_properties = scene.backend_properties

        layout.label(text="Backend Settings")
        layout.prop(backend_properties, "backend_availables")
        layout.prop(backend_properties, "url")

        layout.prop(backend_properties, "timeout_retry")


def register():
    bpy.utils.register_class(BackendPanel)


def unregister():
    bpy.utils.unregister_class(BackendPanel)

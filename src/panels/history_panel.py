import bpy


class HistoryPanel(bpy.types.Panel):
    bl_label = "Backend Panel"
    bl_idname = "OBJECT_PT_BackendPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="History")

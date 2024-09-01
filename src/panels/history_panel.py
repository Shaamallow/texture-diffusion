import bpy


class HistoryPanel(bpy.types.Panel):
    bl_label = "History Panel"
    bl_idname = "OBJECT_PT_HistoryPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        history_props = scene.history_properties

        layout.label(text="History")
        box = layout.box()

        box.label(text="Generation History", icon="PACKAGE")
        head_row = box.row(align=False)
        split = head_row.split(factor=0.8)
        row = split.column().row()
        row.label(text="ID")
        row.label(text="Prompt")
        row.label(text="Seed")

        row = split.column().row()
        row.label(text="Assign")
        row.label(text="Remove")

        for i, mesh_item in enumerate(history_props.history_collection):
            row = box.row(align=True)
            split = row.split(factor=0.8)
            row = split.column().row()
            row.label(text=f"{mesh_item.id}")
            row.label(text=f"{mesh_item.prompt}")
            row.label(text=f"{mesh_item.seed}")

            row = split.column().row()
            assign_button = row.operator(
                "diffusion.assign_history", text="", icon="RESTRICT_SELECT_OFF"
            )
            assign_button.id = mesh_item.id
            remove_button = row.operator(
                "diffusion.remove_history", text="", icon="REMOVE"
            )
            remove_button.index = i
            remove_button.id = mesh_item.id


def register():
    bpy.utils.register_class(HistoryPanel)


def unregister():
    bpy.utils.unregister_class(HistoryPanel)

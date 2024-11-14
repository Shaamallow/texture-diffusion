from typing import Optional

import bpy

# pyright: reportAttributeAccessIssue=false


class HistoryPanel(bpy.types.Panel):
    bl_label = "History Panel"
    bl_idname = "OBJECT_PT_HistoryPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Diffusion"

    def draw(self, context: Optional[bpy.types.Context]):
        assert context is not None

        layout = self.layout
        scene = context.scene
        history_props = scene.history_properties
        backend_props = scene.backend_properties

        layout.label(text="History")
        box = layout.box()

        box.label(text="Generation History", icon="PACKAGE")
        head_row = box.row(align=False)
        split = head_row.split(factor=0.8)

        row = split.column().row()
        row.label(text="ID")
        row.label(text="Prompt")
        row.label(text="Seed")
        row.label(text="Progress")

        row = split.column().row()
        row.label(text="Assign")
        row.label(text="Remove")

        for i, history_item in enumerate(history_props.history_collection):
            headrow = box.row(align=True)
            split = headrow.split(factor=0.8)
            row = split.column().row()

            row.label(text=f"{history_item.id}")
            row.label(text=f"{history_item.prompt}")
            row.label(text=f"{history_item.seed}")

            if history_item.received:
                progress_value = 1.0
            else:
                timeout_progress_value = (
                    history_item.fetching_attempts / backend_props.timeout_retry
                )
                expected_progress_value = (
                    history_item.fetching_attempts / backend_props.expected_completion
                )

                if expected_progress_value >= 1.0:
                    progress_value = timeout_progress_value
                else:
                    progress_value = expected_progress_value

            row.progress(factor=progress_value, type="RING")

            row = split.column().row()
            assign_button = row.operator(
                "diffusion.assign_history", text="", icon="RESTRICT_SELECT_OFF"
            )
            assign_button.id = history_item.id
            remove_button = row.operator(
                "diffusion.remove_history", text="", icon="REMOVE"
            )
            remove_button.index = i
            remove_button.id = history_item.id


def register():
    bpy.utils.register_class(HistoryPanel)


def unregister():
    bpy.utils.unregister_class(HistoryPanel)

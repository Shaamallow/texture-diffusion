import bpy


class UpdateHistoryItem(bpy.types.Operator):
    bl_idname = "diffusion.update_history"
    bl_label = "Update History Item"

    def execute(self, context):
        scene = context.scene
        history_props = scene.history_properties
        diffusion_props = scene.diffusion_properties

        # Update the history item at the given index
        history_item = history_props.history_collection.add()
        history_item.prompt = diffusion_props.prompt
        history_item.seed = diffusion_props.seed
        history_item.cfg_scale = diffusion_props.cfg_scale
        history_item.n_steps = diffusion_props.n_steps
        history_item.scheduler = diffusion_props.scheduler
        history_item.negative_prompt = diffusion_props.negative_prompt
        return {"FINISHED"}


class RemoveHistoryItem(bpy.types.Operator):
    bl_idname = "diffusion.remove_history"
    bl_label = "Remove History Item"
    index: bpy.props.IntProperty()
    id: bpy.props.IntProperty()

    def check_collection(self, collections):
        for collection in collections:
            if collection.name == "Diffusion Camera History":
                return collection
        camera_history_collection = bpy.data.collections.new("Diffusion Camera History")
        bpy.context.scene.collection.children.link(camera_history_collection)
        return camera_history_collection

    def execute(self, context):
        scene = context.scene
        history_props = scene.history_properties

        # Remove the history item at the given index
        history_props.history_collection.remove(self.index)

        # Loop through the cameras in the diffusion history collection
        # remove the camera with the right id

        history_camera_collection = self.check_collection(scene.collection.children)
        for obj in history_camera_collection.objects:
            if obj.name == f"Camera {self.id}":
                history_camera_collection.objects.unlink(obj)
                bpy.data.objects.remove
                break

        return {"FINISHED"}


class AssignHistoryItem(bpy.types.Operator):
    bl_idname = "diffusion.assign_history"
    bl_label = "Assign History Item"
    id: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        history_props = scene.history_properties
        diffusion_props = scene.diffusion_properties

        # Loop through the history collection and find the item with the right id
        for history_item in history_props.history_collection:
            if history_item.id == self.id:
                # Update all props
                diffusion_props.prompt = history_item.prompt
                diffusion_props.seed = history_item.seed
                diffusion_props.cfg_scale = history_item.cfg_scale
                diffusion_props.n_steps = history_item.n_steps
                diffusion_props.scheduler = history_item.scheduler
                diffusion_props.negative_prompt = history_item.negative_prompt
                break

        return {"FINISHED"}


def history_collection_register():
    bpy.utils.register_class(UpdateHistoryItem)
    bpy.utils.register_class(RemoveHistoryItem)
    bpy.utils.register_class(AssignHistoryItem)


def history_collection_unregister():
    bpy.utils.unregister_class(UpdateHistoryItem)
    bpy.utils.unregister_class(RemoveHistoryItem)
    bpy.utils.unregister_class(AssignHistoryItem)

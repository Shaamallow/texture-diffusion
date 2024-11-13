import functools
from io import BytesIO
from typing import Optional

import bpy
import requests
from PIL import Image

# pyright: reportAttributeAccessIssue=false


def fetch_image(history_item):

    base_url = history_item.url
    uuid = history_item.uuid
    file_name = f"{uuid}_output_00001_.png"

    view_image_url = f"{base_url}/view?filename={file_name}&type=output"

    if history_item.fetching_attempts < 1:
        print(view_image_url)

    try:
        params = {
            "filename": file_name,
            "subfolder": "blender-texture",
            "type": "output",
        }
        url = f"{base_url}/view"
        response = requests.get(url, params=params)

        # Check if the response is successful
        if response.status_code == 200:
            # Load the image from the response content
            print("Image fetched successfully")
            image = Image.open(BytesIO(response.content))

            file_path = bpy.data.scenes["Scene"].render.filepath
            save_path = f"{file_path}Generation_{history_item.id}.png"

            print(f"Saving image to {save_path}")
            image.save(save_path)
            bpy.data.images.load(save_path, check_existing=True)

            print(f"Applying the Texture {history_item.id}")
            bpy.ops.diffusion.apply_texture(id=history_item.id)

            return

        else:
            print(
                f"Failed to retrieve image. Status code: {response.status_code}. Attempt : {history_item.fetching_attempts}"
            )
            history_item.fetching_attempts += 1

            if history_item.fetching_attempts > 60:
                print("Failed to retrieve image after 60 attempts")
                return
            return 1.0

    except OSError as e:

        print(f"Failed to retrieve image. Error: {e}")
        history_item.fetching_attempts += 1

        if history_item.fetching_attempts > 60:
            print("Failed to retrieve image after 60 attempts")
            return

        return 1.0


class UpdateHistoryItem(bpy.types.Operator):
    bl_idname = "diffusion.update_history"
    bl_label = "Update History Item"

    uuid: bpy.props.StringProperty(name="UUID")

    def execute(self, context):
        assert context is not None
        scene = context.scene
        history_props = scene.history_properties
        diffusion_props = scene.diffusion_properties
        backend_props = scene.backend_properties

        # Update the history item at the given index
        history_item = history_props.history_collection.add()
        history_item.id = history_props.history_counter
        history_item.prompt = diffusion_props.prompt
        history_item.seed = diffusion_props.seed
        history_item.cfg_scale = diffusion_props.cfg_scale
        history_item.n_steps = diffusion_props.n_steps
        history_item.scheduler = diffusion_props.scheduler
        history_item.negative_prompt = diffusion_props.negative_prompt
        history_item.width = diffusion_props.width
        history_item.width = diffusion_props.height
        history_item.uuid = self.uuid
        history_item.url = backend_props.url
        history_item.fetching_attemps = 0
        history_item.mesh = diffusion_props.mesh_objects[0].name

        # TODO:
        # - add inpainting parameters
        # - add camera position and orientation parameters

        return {"FINISHED"}


class FetchHistoryItem(bpy.types.Operator):
    """Launch the texture fetching process using the given uuid"""

    bl_idname = "diffusion.fetch_history"
    bl_label = "Fetch History Item"
    uuid: bpy.props.StringProperty(name="UUID")

    def get_history_item(self, context: bpy.types.Context) -> Optional[dict]:
        history_props = context.scene.history_properties
        for item in history_props.history_collection:
            if item.uuid == self.uuid:
                return item
        return None

    def execute(self, context: Optional[bpy.types.Context]) -> set[str]:
        assert context is not None
        assert bpy.context is not None

        scene = context.scene
        history_props = scene.history_properties

        history_item = self.get_history_item(context)
        if history_item is None:
            self.report({"ERROR"}, "History item not found")
            return {"CANCELLED"}

        # Add a register on a 1Hz frequency to fetch image result using the id / uuid
        bpy.app.timers.register(
            functools.partial(fetch_image, history_item), first_interval=1.0
        )

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
        assert bpy.context is not None

        bpy.context.scene.collection.children.link(camera_history_collection)
        return camera_history_collection

    def execute(self, context):
        assert context is not None

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
        assert context is not None

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
    bpy.utils.register_class(FetchHistoryItem)


def history_collection_unregister():
    bpy.utils.unregister_class(UpdateHistoryItem)
    bpy.utils.unregister_class(RemoveHistoryItem)
    bpy.utils.unregister_class(AssignHistoryItem)
    bpy.utils.unregister_class(FetchHistoryItem)

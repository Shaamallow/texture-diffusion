import os
from typing import Optional

import bpy
import numpy as np
from PIL import Image

from ..functions.utils import (linear_to_srgb_array, normalize_array,
                               reverse_color, send_image_function)

# pyright: reportAttributeAccessIssue=false


class DepthRenderOperator(bpy.types.Operator):
    """Render the depth map of the current object from the active camera view,
    process it to normalize depth values,and apply color grading to improve visual representation.
    The operator is called automatically after the camera_setup operator
    """

    bl_idname = "diffusion.render_depth"
    bl_label = "Render Depth Map"
    bl_description = "Render the depth map of the current object from the view, process the depth map to be normalized with proper color grading"

    uuid: bpy.props.StringProperty(name="UUID")

    def get_history_item(self, context: bpy.types.Context) -> Optional[dict]:
        history_props = context.scene.history_properties
        for item in history_props.history_collection:
            if item.uuid == self.uuid:
                return item
        return None

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene

        history_item = self.get_history_item(context)
        if history_item is None:
            self.report({"ERROR"}, "History item not found")
            return {"CANCELLED"}

        ID = history_item.id
        uuid_value = history_item.uuid

        scene.use_nodes = True
        tree = scene.node_tree
        assert tree is not None

        bpy.context.scene.view_layers["ViewLayer"].use_pass_z = True

        links = tree.links

        # Render Nodes
        rl = tree.nodes.new("CompositorNodeRLayers")
        rl.location = 185, 285

        # create output viewer node
        v = tree.nodes.new("CompositorNodeViewer")
        v.location = 750, 210
        v.use_alpha = False

        bpy.data.scenes["Scene"].render.resolution_x = 1024
        bpy.data.scenes["Scene"].render.resolution_y = 1024

        links.new(rl.outputs["Depth"], v.inputs[0])

        # Compute Render
        bpy.ops.render.render()

        # get viewer pixels
        viewer_image = bpy.data.images["Viewer Node"]

        # Process the depthmap
        if viewer_image.size[0] > 0 and viewer_image.size[1] > 0:

            width, height = viewer_image.size
            pixels = np.array(viewer_image.pixels[:])  # pyright: ignore
            arr = pixels.reshape((height, width, 4))

        else:
            self.report({"ERROR"}, "The Viewer Node does not have any image data")
            return {"CANCELLED"}

        # Flip X axis and Drop the alpha layer for the depthmap
        arr = arr[::-1, :, :-1]

        positions = np.unique(arr)
        if len(positions) <= 2:
            self.report(
                {"ERROR"},
                "No Depth detected, aborting the generation",
            )
            return {"CANCELLED"}

        threshold_distance = positions[-2] * 1.05

        arr = np.minimum(arr, threshold_distance)
        arr = normalize_array(arr)
        image_array = linear_to_srgb_array(arr)
        reverse = reverse_color(image_array)

        # Convert to PIL format before sending request

        image = Image.fromarray(reverse)
        file_path = bpy.data.scenes["Scene"].render.filepath
        save_path = os.path.join(file_path, f"depth_{ID}.png")
        image.save(save_path)
        bpy.data.images.load(save_path, check_existing=True)

        # TODO: Pop the render view for the loaded image

        input_depth_name = f"{uuid_value}_depth.png"

        # Call the sending request function
        response_code = send_image_function(
            scene=scene, image=image, image_name=input_depth_name
        )
        if response_code == 200:
            self.report(
                {"INFO"},
                f"Depth map has been sent to the server successfully",
            )
        else:
            self.report(
                {"ERROR"},
                f"Failed to send the image to the server, response code: {response_code}",
            )
            return {"CANCELLED"}

        return {"FINISHED"}


class ImageRenderOperator(bpy.types.Operator):
    """Render the opengl view from the current view,
    will be used for inpainting to generate part of a texture as a new texture
    """

    bl_idname = "diffusion.render_image"
    bl_label = "Render Image"
    bl_description = (
        "Render the current view of the 3D mesh to have a image2image workflow"
    )

    uuid: bpy.props.StringProperty(name="UUID")

    def get_history_item(self, context: bpy.types.Context) -> Optional[dict]:
        history_props = context.scene.history_properties
        for item in history_props.history_collection:
            if item.uuid == self.uuid:
                return item
        return None

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene

        history_item = self.get_history_item(context)
        if history_item is None:
            self.report({"ERROR"}, "History item not found")
            return {"CANCELLED"}

        ID = history_item.id
        uuid_value = history_item.uuid

        overlay_previous_status = bpy.context.space_data.overlay.show_overlays
        previous_output_path = context.scene.render.filepath
        bpy.context.space_data.overlay.show_overlays = False

        # change the output path to have the openGL output
        save_path = os.path.join(
            previous_output_path, f"tmp_render_opengl_inpainting_{ID}.png"
        )
        context.scene.render.filepath = save_path
        bpy.ops.render.opengl(write_still=True)
        bpy.context.space_data.overlay.show_overlays = overlay_previous_status

        context.scene.render.filepath = previous_output_path

        image = Image.open(save_path)

        # TODO: Pop the render view for the loaded image
        input_depth_name = f"{uuid_value}_depth.png"

        # Call the sending request function
        response_code = send_image_function(
            scene=scene, image=image, image_name=input_depth_name
        )
        if response_code == 200:
            self.report(
                {"INFO"},
                f"Inpainting image has been sent to the server successfully",
            )
        else:
            self.report(
                {"ERROR"},
                f"Failed to send the image to the server, response code: {response_code}",
            )
            return {"CANCELLED"}

        return {"FINISHED"}


def image_render_register():
    bpy.utils.register_class(DepthRenderOperator)
    bpy.utils.register_class(ImageRenderOperator)


def image_render_unregister():
    bpy.utils.unregister_class(DepthRenderOperator)
    bpy.utils.unregister_class(ImageRenderOperator)

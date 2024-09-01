import json
import random
import time
from pathlib import Path
from urllib import request

import bpy
import numpy as np
import requests
from PIL import Image

from ..functions.utils import (convert_to_bytes, linear_to_srgb_array,
                               normalize_array, reverse_color)


class GenerateDiffusionOperator(bpy.types.Operator):
    bl_idname = "diffusion.generate"
    bl_label = "Generate"

    # Open the depth.json file

    def send_request(self, scene, depth_image: Image.Image):
        diffusion_props = scene.diffusion_properties
        backend_props = scene.backend_properties

        # Get request parameters
        url = backend_props.url

        # Get request payload
        buffer = convert_to_bytes(depth_image)
        json_path = (
            Path(__file__).parent.parent.parent / "workflows" / "controlnet_depth.json"
        )
        with open(json_path) as f:
            prompt_text = f.read()
        prompt_request = json.loads(prompt_text)

        # Prepare the multipart/form-data payload
        files = {"image": ("blender_depth.png", buffer, "image/png")}

        # Additional data can be added to the request if needed
        data = {
            "type": "input",
            "overwrite": "true",
        }
        response = requests.post(f"{url}/upload/image", files=files, data=data)

        if response.status_code != 200:
            print("Error occured")
            return

        # Get Generation Parameters
        positive_prompt = diffusion_props.prompt
        seed = diffusion_props.seed

        if seed == 0:
            seed = random.randint(1, 1000000)
        prompt_request["6"]["inputs"]["text"] = positive_prompt

        # input parameters
        prompt_request["3"]["inputs"]["seed"] = seed
        prompt_request["3"]["inputs"]["cfg"] = diffusion_props.cfg_scale
        prompt_request["3"]["inputs"]["steps"] = diffusion_props.n_steps

        # Save format
        prompt_request["9"]["inputs"]["filename_prefix"]

        # Send Request to queue
        p = {"prompt": prompt_request}
        data = json.dumps(p).encode("utf-8")
        req = request.Request(f"{url}/prompt", data=data)
        request.urlopen(req)

        print("Request Sent!")

        return

    # Rework as operator as well
    def check_collection(self, collections):
        for collection in collections:
            if collection.name == "Diffusion Camera History":
                return collection
        camera_history_collection = bpy.data.collections.new("Diffusion Camera History")
        bpy.context.scene.collection.children.link(camera_history_collection)
        return camera_history_collection

    # Main function
    def execute(self, context):
        scene = context.scene
        diffusion_props = scene.diffusion_properties
        history_props = scene.history_properties

        # Check if any objects have been selected in the diffusion_props.mesh_objects collection
        if not diffusion_props.mesh_objects:
            self.report({"WARNING"}, "No objects selected in the Mesh Collection")
            return {"CANCELLED"}

        # Step 1 & 2: Loop over all available objects in the scene and store their current visibility state
        original_visibility = {}
        for obj in scene.objects:
            original_visibility[obj.name] = obj.hide_render

        # Step 3: Set all objects not in the diffusion_props.mesh_objects collection as hidden for rendering
        for obj in scene.objects:
            if obj.name not in [
                mesh_item.name for mesh_item in diffusion_props.mesh_objects
            ]:
                obj.hide_render = True
            else:
                obj.hide_render = False

        # Add a camera in Camera History Collection
        diffusion_history_collection = self.check_collection(scene.collection.children)

        # Increment ID and generate camera with corresponding ID
        print(history_props.history_counter)
        history_props.history_counter += 1
        ID = history_props.history_counter

        camera_data = bpy.data.cameras.new(name="Camera")
        camera_object = bpy.data.objects.new(f"Camera {ID}", camera_data)
        diffusion_history_collection.objects.link(camera_object)

        # camera = context.active_object
        scene.camera = camera_object

        assert camera_object is not None
        bpy.ops.view3d.camera_to_view()

        # switch on nodes
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

        # Get Dimensions and reshape to proper image format
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

        # TODO : Replace this with save to tmp dir + render view
        image = Image.fromarray(reverse)
        image.save("test.png")

        # Clean node tree and camera
        # TODO : Add option for camera removal and modification of camera layout setup
        # bpy.data.objects.remove(camera_object)

        for obj in scene.objects:
            if obj.name not in diffusion_history_collection.objects:
                obj.hide_render = original_visibility[obj.name]

        tree.nodes.remove(rl)
        tree.nodes.remove(v)

        self.send_request(scene, image)
        # Call operator diffusion.update_history
        bpy.ops.diffusion.update_history()

        return {"FINISHED"}


def generation_register():
    bpy.utils.register_class(GenerateDiffusionOperator)


def generation_unregister():
    bpy.utils.unregister_class(GenerateDiffusionOperator)

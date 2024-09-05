import json
import os
import random
import uuid
from pathlib import Path
from urllib import request

import bpy
import numpy as np
import requests
from PIL import Image

from ..functions.utils import (convert_to_bytes, linear_to_srgb_array,
                               normalize_array, reverse_color)


class ApplyTextureOperator(bpy.types.Operator):
    bl_idname = "diffusion.apply_texture"
    bl_label = "Apply Texture"
    bl_description = "Create a new material for object, project UV from relevant Camera, load generated image and set it in the shading node"

    id: bpy.props.IntProperty(name="ID")

    def find_history_item(self, collection):
        for history_item in collection:
            print(history_item.id, self.id)
            if history_item.id == self.id:
                return history_item
        return None

    def find_camera_object(self, context, collections):

        backend_props = context.scene.backend_properties

        for collection in collections:
            # TODO: replace hardcoded value with backend prop
            if collection.name == backend_props.history_collection_name:
                for obj in collection.objects:
                    if obj.name == f"Camera {self.id}":
                        return obj
        return None

    def execute(self, context):
        scene = context.scene
        history_props = scene.history_properties
        diffusion_props = scene.diffusion_properties
        backend_props = scene.backend_properties

        # Loop through the history collection and find the item with the right id
        history_item = self.find_history_item(history_props.history_collection)

        if history_item is None:
            self.report({"ERROR"}, "No mesh found with the given ID")
            return {"CANCELLED"}

        mesh_name = history_item.mesh
        mesh = bpy.data.objects[mesh_name]

        # Create a new uv mesh
        mesh.data.uv_layers.new(name=f"Texture {self.id}")

        ### Projection

        # Add Projection modifier with mesh and camera
        modifier = mesh.modifiers.new(name="Projection", type="UV_PROJECT")
        modifier.uv_layer = f"Texture {self.id}"
        modifier.projector_count = 1

        # Get the right camera from the diffusion history collection
        camera = self.find_camera_object(context, scene.collection.children)
        if camera is None:
            self.report({"ERROR"}, "No camera found with the given ID")
            return {"CANCELLED"}

        modifier.projectors[0].object = camera

        # Apply the projection with context override
        context_override = context.copy()
        context_override["object"] = mesh
        with context.temp_override(**context_override):
            bpy.ops.object.modifier_apply(modifier=modifier.name)

        ### Materials and Textures
        # Create a new material for the selected object
        material = bpy.data.materials.new(name=f"Material {self.id}")
        material.use_nodes = True

        # Add the material to the object
        mesh.data.materials.append(material)

        # Add nodes
        tree = material.node_tree
        assert tree is not None
        nodes = tree.nodes
        assert nodes is not None
        links = tree.links
        assert links is not None

        uv_node = nodes.new("ShaderNodeUVMap")
        image_node = nodes.new("ShaderNodeTexImage")

        # Set values
        uv_node.uv_map = f"Texture {self.id}"
        image_node.image = bpy.data.images[f"Generation_{self.id}.png"]

        # Links the nodes
        links.new(uv_node.outputs[0], image_node.inputs[0])
        links.new(image_node.outputs[0], nodes["Principled BSDF"].inputs[0])

        # Set the material as active
        mesh.active_material = material

        return {"FINISHED"}


class GenerateDiffusionOperator(bpy.types.Operator):
    bl_idname = "diffusion.generate"
    bl_label = "Generate"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def send_request(self, scene, depth_image: Image.Image, uuid: str):
        diffusion_props = scene.diffusion_properties
        backend_props = scene.backend_properties

        # Get request parameters
        url = backend_props.url
        input_name = f"{uuid}_depth.png"
        output_prefix = f"blender-texture/{uuid}_output"

        # Get request payload
        buffer = convert_to_bytes(depth_image)
        json_path = (
            Path(__file__).parent.parent.parent / "workflows" / "controlnet_depth.json"
        )
        with open(json_path) as f:
            prompt_text = f.read()
        prompt_request = json.loads(prompt_text)

        # Prepare the multipart/form-data payload
        files = {"image": (input_name, buffer, "image/png")}

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

        if diffusion_props.random_seed:
            seed = random.randint(1, 1000000)
            diffusion_props.seed = seed
        prompt_request["6"]["inputs"]["text"] = positive_prompt

        # input parameters
        prompt_request["3"]["inputs"]["seed"] = seed
        prompt_request["3"]["inputs"]["cfg"] = diffusion_props.cfg_scale
        prompt_request["3"]["inputs"]["steps"] = diffusion_props.n_steps
        prompt_request["11"]["inputs"]["strength"] = diffusion_props.controlnet_scale

        # Input-Output Name format
        prompt_request["12"]["inputs"]["image"] = input_name
        prompt_request["9"]["inputs"]["filename_prefix"] = output_prefix
        # output_name = f"{output_prefix}_output_00001_.png"
        # Add view register using this output_name

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
        history_props.history_counter += 1
        ID = history_props.history_counter

        camera_data = bpy.data.cameras.new(name="Camera")
        camera_object = bpy.data.objects.new(f"Camera {ID}", camera_data)
        diffusion_history_collection.objects.link(camera_object)

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

        image = Image.fromarray(reverse)
        file_path = bpy.data.scenes["Scene"].render.filepath
        # TODO: replace with os.path.join
        save_path = os.path.join(file_path, f"depth_{ID}.png")
        image.save(save_path)
        bpy.data.images.load(save_path, check_existing=True)

        for obj in scene.objects:
            if obj.name not in diffusion_history_collection.objects:
                obj.hide_render = original_visibility[obj.name]

        tree.nodes.remove(rl)
        tree.nodes.remove(v)

        # Generate an uuid for the request
        request_uuid = str(uuid.uuid4())
        print(request_uuid)

        self.send_request(scene, image, request_uuid)
        # Call operator diffusion.update_history
        bpy.ops.diffusion.update_history(uuid=request_uuid)

        # TODO: FIX PIL dep + IO Error trunckated image file

        return {"FINISHED"}


def generation_register():
    bpy.utils.register_class(GenerateDiffusionOperator)
    bpy.utils.register_class(ApplyTextureOperator)


def generation_unregister():
    bpy.utils.unregister_class(GenerateDiffusionOperator)
    bpy.utils.unregister_class(ApplyTextureOperator)
